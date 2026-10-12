# src/core/va_patch.py
# 统一 VA 型 patch 执行器 —— 供 GUI / CLI 共用
#
# 设计：
#   VA_PatchPoint   单个 patch 点（VA + 原字节 + 新字节 + 可选 sanity + shellcode 模式）
#   VA_FileTarget   一个目标文件（角色 + 文件名 + patch 点列表）
#   VA_PatchTarget  一个 patch 目标（可含多个文件，如 duo_open 有 Teacher + Student）
#   VAPatchExecutor 对单个文件执行 dry_run / patch / restore / status / 内存操作
#
# 与 patch_engine.py（固定偏移型）的区别：
#   - 通过 PE section 表将 VA 解析为文件偏移（抗 ASLR 重定位）
#   - 支持 shellcode 模式（替换整个函数体）
#   - 支持内存版（运行时写进程内存）
#   - 支持 mode 标签（同一文件的不同 patch 模式，如 screen_capture 的 nop/fake）
#
# 配置来源：src/modules/patches/*.py（纯数据，无执行逻辑）

import os
import struct
import shutil
import hashlib
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional


# ═══════════════════════════════════════════════════════════════
#  数据定义
# ═══════════════════════════════════════════════════════════════

@dataclass
class VA_PatchPoint:
    """单个 VA 型 patch 点。"""
    label: str                    # 唯一标签（GUI/CLI 按 label 选择执行子集）
    va: int                       # 绝对 VA
    orig: bytes                   # 期望的原始字节
    new: bytes                    # 替换字节（shellcode 模式下忽略，由生成器产出）
    # ── shellcode 模式 ──
    shellcode_mode: bool = False  # True = 替换整个函数体（func_size 字节）
    func_size: int = 0            # shellcode 模式下函数体总大小
    # ── sanity 校验 ──
    sanity_window: int = 0        # >0 时从入口起扫描此范围
    sanity_pattern: Optional[bytes] = None  # 必须出现在窗口内
    section_check: Optional[str] = None     # 必须在指定 section（如 .text）
    expected_offset: Optional[int] = None   # 若设置，文件偏移必须精确匹配


@dataclass
class VA_FileTarget:
    """目标文件定义（一个 VA_PatchTarget 可含多个文件）。"""
    role: str                     # 角色标识（"teacher"/"student"/"default"）
    sample_name: str              # 文件名（如 "Teacher.exe"）
    patch_points: List[VA_PatchPoint] = field(default_factory=list)


@dataclass
class VA_PatchTarget:
    """一个 VA 型 patch 目标（可含多个文件 + 多个 patch 点）。"""
    key: str
    name: str
    description: str
    image_base: int
    files: List[VA_FileTarget] = field(default_factory=list)
    known_md5: Dict[str, str] = field(default_factory=dict)
    supports_memory: bool = False
    backup_ext: str = ".bak"                 # 备份文件后缀
    newfile_suffix: str = "_patched"         # 生成新文件时插入扩展名前
    # ── shellcode 参数（screen_capture 假截图模式用） ──
    shellcode_iat: Dict[str, int] = field(default_factory=dict)
    shellcode_fp_off: int = 0                # filepath 字符串在函数体内的偏移
    shellcode_rf_off: int = 0                # "ReadFile\0" 在函数体内的偏移
    shellcode_max_fp: int = 0                # filepath 最大长度


# ═══════════════════════════════════════════════════════════════
#  PE 解析（纯标准库，PE32/PE32+ x86/x64）
# ═══════════════════════════════════════════════════════════════

class PE:
    """最小 PE 解析，提供 VA -> 文件偏移 映射。"""

    def __init__(self, path: str):
        self.path = path
        with open(path, "rb") as f:
            self.data = f.read()
        self._parse()

    def _parse(self):
        d = self.data
        e_lfanew = struct.unpack_from("<I", d, 0x3C)[0]
        if d[e_lfanew:e_lfanew + 4] != b"PE\0\0":
            raise ValueError("不是 PE 文件")
        coff = e_lfanew + 4
        self.machine = struct.unpack_from("<H", d, coff)[0]
        nsec = struct.unpack_from("<H", d, coff + 2)[0]
        opt_size = struct.unpack_from("<H", d, coff + 16)[0]
        opt = coff + 20
        magic = struct.unpack_from("<H", d, opt)[0]
        if magic == 0x20B:
            self.image_base = struct.unpack_from("<Q", d, opt + 24)[0]
            self.is64 = True
        else:
            self.image_base = struct.unpack_from("<I", d, opt + 28)[0]
            self.is64 = False
        sec_tbl = opt + opt_size
        self.sections: List[tuple] = []
        for i in range(nsec):
            s = sec_tbl + i * 40
            name = d[s:s + 8].rstrip(b"\x00").decode("latin1")
            vsize, va, rawsz, rawptr = struct.unpack_from("<IIII", d, s + 8)
            self.sections.append((name, va, vsize, rawptr, rawsz))

    def va_to_off(self, va: int) -> Optional[int]:
        """VA -> 文件偏移。不在任何 section 时返回 None。"""
        rva = va - self.image_base
        for _name, va_s, vs, _rp, rs in self.sections:
            if va_s <= rva < va_s + max(vs, rs):
                return _rp + (rva - va_s)
        return None

    def section_of(self, va: int) -> Optional[str]:
        rva = va - self.image_base
        for name, va_s, vs, _rp, rs in self.sections:
            if va_s <= rva < va_s + max(vs, rs):
                return name
        return None

    @property
    def md5(self) -> str:
        return hashlib.md5(self.data).hexdigest()


# ═══════════════════════════════════════════════════════════════
#  Shellcode 生成器（screen_capture 假截图模式）
# ═══════════════════════════════════════════════════════════════

class _CodeBuilder:
    """x86 机器码构建器（支持短跳转/长跳转补丁）。"""

    def __init__(self):
        self.code = bytearray()
        self.labels: Dict[str, int] = {}
        self.jumps: List[tuple] = []

    def emit(self, *data):
        for d in data:
            if isinstance(d, int):
                self.code.append(d)
            elif isinstance(d, (bytes, bytearray)):
                self.code.extend(d)

    def d(self, val):
        self.emit(struct.pack("<I", val & 0xFFFFFFFF))

    def label(self, name):
        self.labels[name] = len(self.code)

    def push_imm32(self, val):
        self.emit(0x68)
        self.d(val)

    def push_imm8(self, val):
        self.emit(0x6A, val & 0xFF)

    def push_reg(self, reg):
        self.emit(0x50 | reg)

    def push_mem_ebp(self, disp):
        self.emit(0xFF, 0x75, disp & 0xFF)

    def call_iat(self, va):
        self.emit(0xFF, 0x15)
        self.d(va)

    def call_mem_ebp(self, disp):
        self.emit(0xFF, 0x55, disp & 0xFF)

    def jmp_short(self, target):
        self.emit(0xEB, 0x00)
        self.jumps.append((len(self.code) - 1, target, False))

    def je_short(self, target):
        self.emit(0x74, 0x00)
        self.jumps.append((len(self.code) - 1, target, False))

    def jne_short(self, target):
        self.emit(0x75, 0x00)
        self.jumps.append((len(self.code) - 1, target, False))

    def je_rel32(self, target):
        self.emit(0x0F, 0x84, 0, 0, 0, 0)
        self.jumps.append((len(self.code) - 4, target, True))

    def _patch_jumps(self):
        for off, target, is32 in self.jumps:
            tgt = self.labels[target]
            if is32:
                struct.pack_into("<i", self.code, off, tgt - (off + 4))
            else:
                rel = tgt - (off + 1)
                if not (-128 <= rel <= 127):
                    raise ValueError("Short jump out of range: %s" % target)
                self.code[off] = rel & 0xFF

    def to_bytes(self):
        self._patch_jumps()
        return bytes(self.code)


def build_fake_screen_shellcode(filepath: str, target: VA_PatchTarget,
                                func_size: int) -> bytes:
    """生成假截图 shellcode（替换 StudentLogic.dll FUN_1008cb70 函数体）。

    从 target 读取 IAT 地址和布局参数，结合 filepath 生成完整字节。
    """
    iat = target.shellcode_iat
    fp_off = target.shellcode_fp_off
    rf_off = target.shellcode_rf_off
    max_fp = target.shellcode_max_fp

    if max_fp and len(filepath) > max_fp:
        raise ValueError("Filepath too long: %d > %d" % (len(filepath), max_fp))

    # VA 计算（filepath / "ReadFile" 字符串在函数体内的绝对 VA）
    base_va = iat.get("_func_base", 0)
    va_fp = base_va + fp_off
    va_rf = base_va + rf_off

    cb = _CodeBuilder()

    # PROLOGUE
    cb.emit(0x55)                          # push ebp
    cb.emit(0x8B, 0xEC)                    # mov ebp, esp
    cb.emit(0x83, 0xEC, 0xC0)              # sub esp, 0xC0
    cb.emit(0x89, 0x45, 0xFC)             # mov [ebp-4], eax (param_1)

    # RESOLVE ReadFile
    cb.push_imm32(0)                       # push NULL
    cb.call_iat(iat["GetModuleHandleA"])
    cb.push_imm32(va_rf)                   # push "ReadFile"
    cb.push_reg(0)                         # push hKernel32
    cb.call_iat(iat["GetProcAddress"])
    cb.emit(0x89, 0x45, 0xF8)             # mov [ebp-8], eax

    # CreateFileA
    cb.push_imm32(0)
    cb.push_imm32(0)
    cb.push_imm8(3)
    cb.push_imm32(0)
    cb.push_imm8(1)
    cb.push_imm32(0x80000000)
    cb.push_imm32(va_fp)
    cb.call_iat(iat["CreateFileA"])
    cb.emit(0x83, 0xC4, 0x1C)

    cb.emit(0x3D, 0xFF, 0xFF, 0xFF, 0xFF)
    cb.je_rel32("fallback")
    cb.emit(0x89, 0x45, 0xF4)             # mov [ebp-0xC], eax (hFile)

    # ReadFile: header (54 bytes)
    cb.emit(0x8D, 0x45, 0xA0)             # lea eax, [ebp-0x60]
    cb.emit(0x8D, 0x4D, 0xF0)             # lea ecx, [ebp-0x10]
    cb.push_imm32(0)
    cb.push_reg(1)
    cb.push_imm32(54)
    cb.push_reg(0)
    cb.push_mem_ebp(-0x0C)
    cb.call_mem_ebp(-0x08)
    cb.emit(0x83, 0xC4, 0x14)
    cb.emit(0x85, 0xC0)
    cb.je_short("do_close")

    # Validate: "BM"
    cb.emit(0x8B, 0x45, 0xA0)
    cb.emit(0x3D, 0x42, 0x4D, 0x00, 0x00)
    cb.jne_short("do_close")

    # Validate: 32bpp
    cb.emit(0x0F, 0xB7, 0x45, 0xBC)
    cb.emit(0x3D, 0x20, 0x00, 0x00, 0x00)
    cb.jne_short("do_close")

    # Validate: width matches
    cb.emit(0x8B, 0x45, 0xBA)             # bmp width
    cb.emit(0x8B, 0x55, 0xFC)             # param_1
    cb.emit(0x39, 0x02)
    cb.jne_short("do_close")

    # Validate: height matches
    cb.emit(0x8B, 0x45, 0xBE)             # biHeight
    cb.emit(0x8B, 0x55, 0xFC)             # param_1
    cb.emit(0x03, 0x42, 0x04)             # add eax, [edx+4]
    cb.jne_short("do_close")

    # SetFilePointer
    cb.emit(0x8B, 0x45, 0xAC)             # offBits
    cb.push_imm32(0)
    cb.push_reg(0)
    cb.push_mem_ebp(-0x0C)
    cb.call_iat(iat["SetFilePointer"])
    cb.emit(0x83, 0xC4, 0x0C)

    # ReadFile: pixels
    cb.emit(0x8B, 0x55, 0xFC)
    cb.emit(0x8B, 0x02)                   # width
    cb.emit(0x0F, 0xAF, 0x42, 0x04)       # width * height
    cb.emit(0xC1, 0xE0, 0x02)             # * 4

    cb.emit(0x8D, 0x4D, 0xF0)
    cb.push_imm32(0)
    cb.push_reg(1)
    cb.push_reg(0)
    cb.emit(0x8B, 0x42, 0x08)             # buffer
    cb.push_reg(0)
    cb.push_mem_ebp(-0x0C)
    cb.call_mem_ebp(-0x08)
    cb.emit(0x83, 0xC4, 0x14)

    # do_close
    cb.label("do_close")
    cb.push_mem_ebp(-0x0C)
    cb.call_iat(iat["CloseHandle"])
    cb.emit(0x83, 0xC4, 0x04)
    cb.jmp_short("epilogue")

    # fallback: zero-fill (black screen)
    cb.label("fallback")
    cb.emit(0x8B, 0x55, 0xFC)
    cb.emit(0x8B, 0x02)
    cb.emit(0x0F, 0xAF, 0x42, 0x04)
    cb.emit(0x89, 0xC1)
    cb.emit(0x8B, 0x7A, 0x08)
    cb.emit(0x31, 0xC0)
    cb.emit(0xF3, 0xAB)

    # epilogue
    cb.label("epilogue")
    cb.emit(0x5D)
    cb.emit(0xC9)
    cb.emit(0xC3)

    code = cb.to_bytes()
    if fp_off and len(code) > fp_off:
        raise ValueError("Code too large: %d > %d" % (len(code), fp_off))

    blob = bytearray(code)
    blob.extend(b"\xCC" * (fp_off - len(code)))
    fp = filepath.encode("ascii") + b"\x00"
    blob.extend(fp)
    blob.extend(b"\xCC" * (rf_off - fp_off - len(fp)))
    blob.extend(b"ReadFile\x00")
    blob.extend(b"\xCC" * (func_size - len(blob)))
    assert len(blob) == func_size
    return bytes(blob)


# ═══════════════════════════════════════════════════════════════
#  BMP 处理（假截图模式的前置校验 / 方向转换）
# ═══════════════════════════════════════════════════════════════

def parse_bmp_header(data: bytes) -> dict:
    """解析 BMP 头。返回 dict，失败抛 ValueError。"""
    if len(data) < 54:
        raise ValueError("文件太小，不是有效 BMP")
    if data[0:2] != b"BM":
        raise ValueError("不是 BMP 文件（缺 BM 魔数）")
    fsize = struct.unpack_from("<I", data, 2)[0]
    off_bits = struct.unpack_from("<I", data, 10)[0]
    bi_width = struct.unpack_from("<i", data, 18)[0]
    bi_height = struct.unpack_from("<i", data, 22)[0]
    bi_bitcount = struct.unpack_from("<H", data, 28)[0]
    bi_compression = struct.unpack_from("<I", data, 30)[0]
    return {
        "fsize": fsize, "off_bits": off_bits,
        "bi_width": bi_width, "bi_height": bi_height,
        "bi_bitcount": bi_bitcount, "bi_compression": bi_compression,
        "is_bottom_up": bi_height > 0,
        "abs_height": abs(bi_height),
        "pixel_size": abs(bi_width) * abs(bi_height) * (bi_bitcount // 8),
    }


def validate_bmp(path: str) -> dict:
    """校验 BMP（须 32bpp 无压缩）。返回 header dict。"""
    with open(path, "rb") as f:
        data = f.read()
    hdr = parse_bmp_header(data)
    if hdr["bi_bitcount"] != 32:
        raise ValueError("BMP 须为 32bpp（实际 %d）" % hdr["bi_bitcount"])
    if hdr["bi_compression"] != 0:
        raise ValueError("BMP 须无压缩 BI_RGB（实际 %d）" % hdr["bi_compression"])
    if len(data) < hdr["off_bits"] + hdr["pixel_size"]:
        raise ValueError("文件尺寸 %d < 像素数据末端 %d"
                         % (len(data), hdr["off_bits"] + hdr["pixel_size"]))
    return hdr


def convert_bmp_topdown(path: str, log: Optional[Callable] = None) -> str:
    """bottom-up BMP 转 top-down（shellcode 要求负 biHeight）。
    返回转换后文件路径（原文件不动）。已是 top-down 时原样返回。"""
    log = log or print
    with open(path, "rb") as f:
        data = bytearray(f.read())
    hdr = parse_bmp_header(data)
    if not hdr["is_bottom_up"]:
        log("  BMP 已是 top-down，无需转换")
        return path
    w, h = hdr["bi_width"], abs(hdr["bi_height"])
    row_bytes = w * 4
    off = hdr["off_bits"]
    for i in range(h // 2):
        sa = off + i * row_bytes
        sb = off + (h - 1 - i) * row_bytes
        data[sa:sa + row_bytes], data[sb:sb + row_bytes] = \
            data[sb:sb + row_bytes], data[sa:sa + row_bytes]
    struct.pack_into("<i", data, 22, -h)
    base, ext = os.path.splitext(path)
    out = base + "_topdown" + ext
    with open(out, "wb") as f:
        f.write(bytes(data))
    log("  已转换 bottom-up → top-down: %s" % out)
    return out


# ═══════════════════════════════════════════════════════════════
#  内存操作辅助（Windows only）
# ═══════════════════════════════════════════════════════════════

def _is_windows() -> bool:
    return os.name == "nt"


def _find_processes(exe_name: str) -> List[int]:
    """通过 Toolhelp 快照枚举进程，匹配 exe_name，返回 PID 列表。"""
    if not _is_windows():
        raise RuntimeError("内存操作仅支持 Windows")
    import ctypes
    from ctypes import wintypes

    TH32CS_SNAPPROCESS = 0x00000002

    class P32(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.c_void_p),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", ctypes.c_char * 260),
        ]

    k32 = ctypes.windll.kernel32
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == ctypes.c_void_p(-1).value or snap is None:
        return []
    ent = P32()
    ent.dwSize = ctypes.sizeof(P32)
    pids = []
    lower = exe_name.lower()
    if k32.Process32First(snap, ctypes.byref(ent)):
        while True:
            name = ent.szExeFile.decode("latin1").lower()
            if name == lower:
                pids.append(ent.th32ProcessID)
            if not k32.Process32Next(snap, ctypes.byref(ent)):
                break
    k32.CloseHandle(snap)
    return pids


def _module_base(pid: int) -> tuple:
    """返回 (base, name) —— 主模块基址。"""
    import ctypes
    k32 = ctypes.windll.kernel32
    MOD_LIST_FLAGS_32BIT = 0x03
    MOD_LIST_ALL = 0x00
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise PermissionError("OpenProcess 失败（需要管理员权限），pid=%d" % pid)
    for flags in (MOD_LIST_FLAGS_32BIT, MOD_LIST_ALL):
        bufsz = ctypes.c_ulong(65536)
        needed = ctypes.c_ulong(0)
        buf = (ctypes.c_byte * 65536)()
        ok = k32.EnumProcessModulesEx(h, buf, bufsz, ctypes.byref(needed), flags)
        if ok and needed.value > 0:
            n = needed.value // 4
            addrs = struct.unpack_from("<%dI" % n, bytes(buf[:needed.value]), 0)
            for a in addrs:
                namebuf = ctypes.create_unicode_buffer(520)
                if k32.GetModuleBaseNameW(h, a, namebuf, 520):
                    return a, namebuf.value
    k32.CloseHandle(h)
    raise RuntimeError("未能在 pid=%d 中枚举到模块" % pid)


def _mem_read(h, addr, n):
    import ctypes
    k32 = ctypes.windll.kernel32
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t(0)
    if k32.ReadProcessMemory(h, addr, buf, n, ctypes.byref(got)) == 0:
        raise ctypes.WinError()
    return buf.raw[:got.value]


def _mem_write(h, addr, data):
    import ctypes
    k32 = ctypes.windll.kernel32
    got = ctypes.c_size_t(0)
    if k32.WriteProcessMemory(h, addr, data, len(data), ctypes.byref(got)) == 0:
        raise ctypes.WinError()
    return got.value


def _mem_protect(h, addr, n, newprot):
    import ctypes
    k32 = ctypes.windll.kernel32
    old = ctypes.c_ulong(0)
    if k32.VirtualProtectEx(h, addr, n, newprot, ctypes.byref(old)) == 0:
        raise ctypes.WinError()
    return old.value


PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_READ = 0x20
PROCESS_VM_WRITE = 0x0010
PROCESS_VM_READ = 0x0010
PROCESS_QUERY = 0x0008


# ═══════════════════════════════════════════════════════════════
#  统一执行器
# ═══════════════════════════════════════════════════════════════

class VAPatchExecutor:
    """统一的 VA 型 patch 执行器。

    用法：
        target = get_va_target("noshutdown")
        ex = VAPatchExecutor(target, "C:\\...\\Student.exe")
        ex.dry_run()
        ex.patch(inplace=True)
        ex.restore()
        ex.mem_patch()   # 仅 supports_memory=True 时

    screen_capture（同文件多标签点）：
        ex = VAPatchExecutor(target, "C:\\...\\StudentLogic.dll")
        ex.all_labels()                       # 查看所有可选点
        ex.dry_run(labels=["pipeline"])       # 只校验 pipeline 点
        ex.patch(inplace=True, labels=["pipeline"])
        ex.patch(inplace=True, labels=["fake_screen"],
                 fake_screen=r"C:\\os_fake.bmp")   # 假截图（shellcode）
    """

    def __init__(self, target: VA_PatchTarget, path: str,
                 role: Optional[str] = None,
                 log: Optional[Callable] = None):
        self.target = target
        self.path = path
        self.log = log or print
        # 确定使用哪个 file target
        if role:
            self._file_target = next(
                (f for f in target.files if f.role == role), None)
        else:
            # 自动匹配：按 sample_name 匹配路径，或取第一个
            base = os.path.basename(path).lower()
            self._file_target = next(
                (f for f in target.files if f.sample_name.lower() == base),
                target.files[0] if target.files else None)
        if self._file_target is None:
            raise ValueError("目标 %s 未定义任何文件" % target.key)

    # ── 基础属性 ──────────────────────────────────────────
    @property
    def bak_path(self) -> str:
        return self.path + self.target.backup_ext

    @property
    def sample_name(self) -> str:
        return self._file_target.sample_name

    def _active_points(self, labels: Optional[List[str]]) -> List[VA_PatchPoint]:
        """按 label 选 patch 点子集。

        labels=None   → 全部点（GUI 可先 dry_run 展示所有点供用户参考）
        labels=[...]  → 仅这些 label 的点（GUI 按用户选择传入）
        """
        if labels is None:
            return list(self._file_target.patch_points)
        lbl_set = set(labels)
        return [p for p in self._file_target.patch_points if p.label in lbl_set]

    def all_labels(self) -> List[str]:
        """返回当前文件所有 patch 点的 label（供 GUI 构建选择器）。"""
        return [p.label for p in self._file_target.patch_points]

    # ── 校验 ─────────────────────────────────────────────
    def _check_point(self, point: VA_PatchPoint, data: bytes,
                     off: Optional[int], sec: Optional[str]) -> tuple:
        """校验单个 patch 点。返回 (state, detail)。
        state: 'ok' | 'patched' | 'bad' | 'not_found'
        """
        if off is None:
            return "not_found", "VA 0x%x 不在任何 section" % point.va
        if sec and point.section_check and sec != point.section_check:
            return "bad", "VA 0x%x 在 %s（期望 %s）" % (point.va, sec, point.section_check)
        if point.expected_offset is not None and off != point.expected_offset:
            return "bad", "偏移 0x%x ≠ 期望 0x%x" % (off, point.expected_offset)

        cur = bytes(data[off:off + len(point.orig)])
        if point.shellcode_mode:
            # shellcode 模式：shellcode prologue 也是 55 8b ec，入口字节无法区分
            # 未 patch / 已 patch，统一按入口=orig 视为"可应用"（重复应用幂等）
            if cur != point.orig:
                return "bad", "入口 %s ≠ 期望 %s" % (cur.hex(" "), point.orig.hex(" "))
        else:
            if cur == point.new:
                return "patched", cur.hex(" ")
            if cur != point.orig:
                return "bad", "入口 %s ≠ 期望 %s" % (cur.hex(" "), point.orig.hex(" "))

        # sanity check
        if point.sanity_window and point.sanity_pattern:
            window = data[off:off + point.sanity_window]
            if point.sanity_pattern not in window:
                return "bad", "函数体 %d 字节内未找到特征 %s" % (
                    point.sanity_window, point.sanity_pattern.hex(" "))
        return "ok", cur.hex(" ")

    # ── dry_run ──────────────────────────────────────────
    def dry_run(self, strict: bool = True,
            labels: Optional[List[str]] = None) -> bool:
        if not os.path.isfile(self.path):
            self.log("  ✗ 文件不存在: %s" % self.path)
            return False
        pe = PE(self.path)
        self.log("  文件: %s" % os.path.basename(self.path))
        self.log("  大小: %d  MD5: %s" % (len(pe.data), pe.md5))
        if pe.md5 in self.target.known_md5:
            self.log("  MD5 匹配: %s" % self.target.known_md5[pe.md5])
        else:
            self.log("  MD5 不在已知列表（继续按 VA 校验）")
        self.log("  ImageBase=0x%x" % pe.image_base)
        if labels is not None:
            self.log("  选中标签: %s" % ", ".join(labels))

        points = self._active_points(labels)
        if not points:
            self.log("  ✗ 选中标签下无 patch 点")
            return False
        all_ok = True
        for point in points:
            off = pe.va_to_off(point.va)
            sec = pe.section_of(point.va)
            state, detail = self._check_point(point, pe.data, off, sec)
            icon = {"ok": "✓", "patched": "○", "bad": "✗", "not_found": "✗"}[state]
            self.log("  %s %-16s VA=0x%x off=0x%x  %s" % (
                icon, point.label, point.va, off or 0, detail))
            if state in ("bad", "not_found"):
                all_ok = False
                if strict:
                    self.log("  [--strict] 校验失败，中止")
                    return False
        if all_ok:
            self.log("  ==> dry-run 通过")
        return all_ok

    # ── patch（文件版） ──────────────────────────────────
    def patch(self, inplace: bool = True, strict: bool = True,
              fake_screen: Optional[str] = None,
              labels: Optional[List[str]] = None) -> bool:
        """执行文件 patch。

        inplace=True: 直接改原文件（先备份）
        inplace=False: 生成新文件（原名 + newfile_suffix）
        fake_screen: shellcode 模式下的 BMP 路径
        labels: 仅处理指定 label 的点（None=全部）
        """
        if not os.path.isfile(self.path):
            self.log("  ✗ 文件不存在: %s" % self.path)
            return False

        # dry_run 校验
        if not self.dry_run(strict=strict, labels=labels):
            return False

        pe = PE(self.path)
        data = bytearray(pe.data)
        changed_bytes = 0
        points = self._active_points(labels)

        for point in points:
            off = pe.va_to_off(point.va)
            if off is None:
                self.log("  ✗ %s: VA 未找到" % point.label)
                return False

            if point.shellcode_mode:
                if not fake_screen:
                    self.log("  ✗ %s: shellcode 模式需要 BMP 路径" % point.label)
                    return False
                sc = build_fake_screen_shellcode(fake_screen, self.target,
                                                 point.func_size)
                data[off:off + point.func_size] = sc
                changed_bytes += point.func_size
                self.log("  ✓ %-16s off=0x%x  shellcode %dB" % (
                    point.label, off, point.func_size))
            else:
                cur = bytes(data[off:off + len(point.orig)])
                if cur == point.new:
                    self.log("  ○ %-16s 已是 patch 状态，跳过" % point.label)
                    continue
                data[off:off + len(point.orig)] = point.new
                changed_bytes += len(point.new)
                self.log("  ✓ %-16s off=0x%x  %s → %s" % (
                    point.label, off, cur.hex(" "), point.new.hex(" ")))

        if changed_bytes == 0:
            self.log("  无需写入（全部已 patch）")
            return True

        # 备份 + 写入
        if inplace:
            if not os.path.exists(self.bak_path):
                shutil.copy2(self.path, self.bak_path)
                self.log("  备份 → %s" % os.path.basename(self.bak_path))
            out = self.path
        else:
            root, ext = os.path.splitext(self.path)
            out = root + self.target.newfile_suffix + ext

        with open(out, "wb") as f:
            f.write(bytes(data))
        self.log("  写入 %d 字节 → %s" % (changed_bytes, os.path.basename(out)))

        # 回读验证（shellcode 点跳过精确校验，仅验证非 shellcode 点）
        with open(out, "rb") as f:
            vdata = f.read()
        for point in points:
            off = pe.va_to_off(point.va)
            if point.shellcode_mode:
                continue
            cur = bytes(vdata[off:off + len(point.new)])
            if cur != point.new:
                self.log("  ✗ %s 回读验证失败" % point.label)
                return False
        self.log("  ✓ 回读验证通过")
        return True

    # ── restore ──────────────────────────────────────────
    def restore(self) -> bool:
        if not os.path.exists(self.bak_path):
            self.log("  ✗ 备份不存在: %s" % self.bak_path)
            return False
        shutil.copy2(self.bak_path, self.path)
        self.log("  ✓ 已从备份还原")
        pe = PE(self.path)
        self.log("  还原后 MD5: %s" % pe.md5)
        return True

    # ── status ───────────────────────────────────────────
    def status(self, labels: Optional[List[str]] = None) -> dict:
        if not os.path.isfile(self.path):
            return {"exists": False, "points": []}
        pe = PE(self.path)
        points = []
        for point in self._active_points(labels):
            off = pe.va_to_off(point.va)
            sec = pe.section_of(point.va)
            state, detail = self._check_point(point, pe.data, off, sec)
            label = {"ok": "未 patch", "patched": "已 patch",
                     "bad": "异常", "not_found": "VA 未找到"}[state]
            points.append((point.label, label, detail))
        return {
            "exists": True,
            "path": self.path,
            "size": len(pe.data),
            "md5": pe.md5,
            "points": points,
            "has_backup": os.path.exists(self.bak_path),
        }

    # ── 内存版操作（Windows only） ──────────────────────
    def _mem_run(self, pid: Optional[int], direction: str) -> bool:
        """direction: 'patch' 或 'restore'。"""
        if not self.target.supports_memory:
            self.log("  ✗ 该目标不支持内存模式")
            return False
        if not _is_windows():
            self.log("  ✗ 内存版仅支持 Windows")
            return False
        import ctypes
        k32 = ctypes.windll.kernel32

        exe_name = self._file_target.sample_name
        pids = [pid] if pid else _find_processes(exe_name)
        if not pids:
            self.log("  未找到运行中的 %s" % exe_name)
            return False

        all_ok = True
        for p in pids:
            self.log("  --- pid=%d ---" % p)
            base, name = _module_base(p)
            self.log("  主模块 %s 基址=0x%x" % (name, base))
            h = k32.OpenProcess(PROCESS_VM_WRITE | PROCESS_VM_READ | PROCESS_QUERY,
                                False, p)
            if not h:
                self.log("    OpenProcess 失败（需管理员）")
                all_ok = False
                continue
            for point in self._file_target.patch_points:
                if point.shellcode_mode:
                    self.log("    %-16s shellcode 模式不支持内存版，跳过" % point.label)
                    continue
                rva = point.va - self.target.image_base
                addr = base + rva
                cur = _mem_read(h, addr, len(point.orig))
                if direction == "patch":
                    if cur == point.new:
                        self.log("    %-16s 已 patch，跳过" % point.label)
                    elif cur == point.orig:
                        _mem_protect(h, addr, len(point.new), PAGE_EXECUTE_READWRITE)
                        _mem_write(h, addr, point.new)
                        _mem_protect(h, addr, len(point.new), PAGE_EXECUTE_READ)
                        v = _mem_read(h, addr, len(point.new))
                        ok = (v == point.new)
                        self.log("    %-16s %s → %s  %s" % (
                            point.label, cur.hex(" "), v.hex(" "),
                            "OK" if ok else "FAIL"))
                        all_ok = all_ok and ok
                    else:
                        self.log("    %-16s 入口 %s 非预期，跳过" % (point.label, cur.hex(" ")))
                        all_ok = False
                else:  # restore
                    if cur == point.orig:
                        self.log("    %-16s 已还原" % point.label)
                    elif cur == point.new:
                        _mem_protect(h, addr, len(point.orig), PAGE_EXECUTE_READWRITE)
                        _mem_write(h, addr, point.orig)
                        _mem_protect(h, addr, len(point.orig), PAGE_EXECUTE_READ)
                        v = _mem_read(h, addr, len(point.orig))
                        ok = (v == point.orig)
                        self.log("    %-16s %s → %s  %s" % (
                            point.label, cur.hex(" "), v.hex(" "),
                            "OK" if ok else "FAIL"))
                        all_ok = all_ok and ok
                    else:
                        self.log("    %-16s 入口非预期，跳过" % point.label)
                        all_ok = False
            k32.CloseHandle(h)
        return all_ok

    def mem_patch(self, pid: Optional[int] = None) -> bool:
        return self._mem_run(pid, "patch")

    def mem_restore(self, pid: Optional[int] = None) -> bool:
        return self._mem_run(pid, "restore")

    def mem_status(self) -> Optional[List[int]]:
        if not self.target.supports_memory:
            self.log("  ✗ 该目标不支持内存模式")
            return None
        if not _is_windows():
            self.log("  ✗ 内存版仅支持 Windows")
            return None
        import ctypes
        k32 = ctypes.windll.kernel32

        exe_name = self._file_target.sample_name
        pids = _find_processes(exe_name)
        if not pids:
            self.log("  未找到运行中的 %s" % exe_name)
            return None
        for p in pids:
            base, name = _module_base(p)
            h = k32.OpenProcess(PROCESS_VM_READ | PROCESS_QUERY, False, p)
            if not h:
                self.log("  pid=%d 读取失败" % p)
                continue
            for point in self._file_target.patch_points:
                if point.shellcode_mode:
                    self.log("  pid=%d %-16s shellcode 模式不支持内存版" % (p, point.label))
                    continue
                rva = point.va - self.target.image_base
                addr = base + rva
                cur = _mem_read(h, addr, len(point.orig))
                if cur == point.new:
                    st = "已 patch"
                elif cur == point.orig:
                    st = "未 patch"
                else:
                    st = "未知 %s" % cur.hex(" ")
                self.log("  pid=%d %-16s %s (入口=%s)" % (p, point.label, st, cur.hex(" ")))
            k32.CloseHandle(h)
        return pids