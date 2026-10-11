# src/modules/noshutdown.py
# 拦截远程关机 / 重启 —— Student.exe 核心逻辑（文件版 + 内存版）
#
# 自 tools/oseasy_noshutdown.py 迁入，裁掉独立 GUI / CLI，仅保留核心函数。
# 所有函数带 log=print 参数，GUI 经 ui.run_with_log 捕获 stdout。
#
# 逆向结论（Student.exe, PE32, ImageBase=0x400000）:
#   远程重启与远程关机共用同一个函数 FUN_004a9660:
#       if (param == 0) ExitWindowsEx(6, 0);    // 0x6 = REBOOT|FORCE       -> 重启
#       else            ExitWindowsEx(0xd, 0);  // 0xd = SHUTDOWN|FORCE|POWEROFF -> 关机
#   该函数先 AdjustTokenPrivileges 启用 SeShutdownPrivilege 再调 ExitWindowsEx。
#   StudentLogic.dll 完全不参与，Student.exe 二进制内无 "shutdown.exe" 字符串，
#   因此"劫持 shutdown.exe"对远程关机无效（红鲱鱼）。
#
#   Patch 策略: 将 FUN_004a9660 函数入口 3 字节
#       55 8b ec  (push ebp; mov ebp, esp)
#   替换为
#       31 c0 c3  (xor eax, eax; ret)
#   使函数进入即返回，重启/关机指令全部失效。一个点封两个动作，随时可还原。
#
# 两种运行方式:
#   文件版  —— 直接改磁盘上的 Student.exe（持久，需先结束学生端进程再启动新文件）
#   内存版  —— 改运行中 Student.exe 进程内存（抗 ASLR 动态定位，进程重启自动恢复，仅 Windows+管理员）

import os
import struct
import hashlib

# ─────────────────────────────────────────────────────────────
# 目标常量（来自 Ghidra 逆向 + PE 实测）
# ─────────────────────────────────────────────────────────────
TARGET_MODULE = "Student.exe"
IMAGE_BASE    = 0x400000
FUNC_VA       = 0x4A9660            # FUN_004a9660 绝对 VA
FUNC_RVA      = FUNC_VA - IMAGE_BASE  # 0x0A9660
ORIG_BYTES    = bytes.fromhex("558bec")  # push ebp; mov ebp,esp
PATCH_BYTES   = bytes.fromhex("31c0c3")  # xor eax,eax; ret
PATCH_LEN     = 3

# 已知合法 MD5（原版 + 双开产物；布局相同，RVA 一致）
KNOWN_MD5 = {
    "326a77edb4b5d03eaeeb7dafa2d9e08e": "Student.exe 原版",
    "aa2e24bc4912e8f57a3dd2b3df6cb6e1": "Student_duo_open.exe 双开版",
}
BACKUP_EXT = ".noshutdown.bak"


def is_windows():
    """内存版仅 Windows 可用；文件版跨平台。"""
    return os.name == "nt"


# ═════════════════════════════════════════════════════════════
# PE 解析（纯标准库）
# ═════════════════════════════════════════════════════════════
class PE:
    def __init__(self, path):
        self.path = path
        with open(path, "rb") as f:
            self.data = bytearray(f.read())
        self.md5 = hashlib.md5(self.data).hexdigest()
        self._parse()

    def _parse(self):
        d = self.data
        pe_off = struct.unpack_from("<I", d, 0x3c)[0]
        assert d[pe_off:pe_off + 4] == b"PE\0\0", "不是 PE 文件"
        coff = pe_off + 4
        machine, nsec, _ts, _sym, _nsym, opt_size, _char = struct.unpack_from(
            "<HHIIIHH", d, coff)
        self.machine = machine
        opt = coff + 20
        magic = struct.unpack_from("<H", d, opt)[0]
        if magic == 0x20b:
            self.image_base = struct.unpack_from("<Q", d, opt + 24)[0]
        else:
            self.image_base = struct.unpack_from("<I", d, opt + 28)[0]
        self.is64 = (magic == 0x20b)
        sec_off = opt + opt_size
        self.sections = []
        for i in range(nsec):
            so = sec_off + i * 40
            name = d[so:so + 8].rstrip(b"\0").decode("latin1")
            vsize, va, rawsz, rawptr = struct.unpack_from("<IIII", d, so + 8)
            self.sections.append((name, va, vsize, rawptr, rawsz))

    def rva2off(self, rva):
        for _n, va, vsize, rawptr, rawsz in self.sections:
            if va <= rva < va + max(vsize, rawsz):
                return rawptr + (rva - va)
        raise ValueError("RVA 0x%x 不在任何 section" % rva)

    @property
    def target_off(self):
        return self.rva2off(FUNC_RVA)

    def check_target(self, strict=True):
        """返回 (ok, msg)。校验目标位置原始字节。"""
        off = self.target_off
        cur = bytes(self.data[off:off + PATCH_LEN])
        if cur == ORIG_BYTES:
            return True, "入口字节 55 8b ec 符合预期"
        if cur == PATCH_BYTES:
            if strict:
                return False, "目标已被 patch（入口已是 31 c0 c3）"
            return True, "目标已被 patch（幂等，跳过）"
        return False, "入口字节 %s 与预期 %s 不符（文件可能已变动/版本不同）" % (
            cur.hex(" "), ORIG_BYTES.hex(" "))


# ═════════════════════════════════════════════════════════════
# 文件版操作
# ═════════════════════════════════════════════════════════════
def file_dry_run(path, strict=True, log=print):
    pe = PE(path)
    log("  文件: %s" % path)
    log("  大小: %d  MD5: %s" % (len(pe.data), pe.md5))
    if pe.md5 in KNOWN_MD5:
        log("  MD5 匹配已知样本: %s" % KNOWN_MD5[pe.md5])
    else:
        log("  警告: MD5 不在已知列表（可能仍是同版本，继续按 RVA 校验）")
    log("  ImageBase=0x%x  RVA=0x%x  fileoff=0x%x" % (
        pe.image_base, FUNC_RVA, pe.target_off))
    ok, msg = pe.check_target(strict=strict)
    log("  校验: %s" % msg)
    cur = bytes(pe.data[pe.target_off:pe.target_off + PATCH_LEN])
    log("  当前入口: %s   目标入口: %s" % (cur.hex(" "), PATCH_BYTES.hex(" ")))
    if ok:
        log("  ==> dry-run 通过，可以执行 patch")
    return ok, pe


def _backup(path, log=print):
    bak = path + BACKUP_EXT
    if not os.path.exists(bak):
        with open(path, "rb") as f:
            data = f.read()
        with open(bak, "wb") as f:
            f.write(data)
        log("  已备份 -> %s" % bak)
    else:
        log("  备份已存在: %s" % bak)
    return bak


def file_patch(path, inplace=True, strict=True, log=print):
    """patch 文件。inplace=True 直接改原文件（先备份）；否则写新文件。"""
    ok, pe = file_dry_run(path, strict=strict, log=log)
    if not ok:
        return False
    off = pe.target_off
    new = bytearray(pe.data)
    new[off:off + PATCH_LEN] = PATCH_BYTES
    changed = sum(1 for a, b in zip(pe.data, new) if a != b)
    if inplace:
        _backup(path, log=log)
        with open(path, "wb") as f:
            f.write(new)
        out = path
    else:
        out = os.path.splitext(path)[0] + ".noshutdown" + os.path.splitext(path)[1]
        with open(out, "wb") as f:
            f.write(new)
    log("  写入 %d 字节差异 -> %s" % (changed, out))
    # 回读验证
    chk = PE(out)
    v = bytes(chk.data[chk.target_off:chk.target_off + PATCH_LEN])
    log("  回读入口: %s  %s" % (v.hex(" "),
         "OK" if v == PATCH_BYTES else "FAIL!"))
    return v == PATCH_BYTES


def file_restore(path, log=print):
    bak = path + BACKUP_EXT
    if not os.path.exists(bak):
        log("  未找到备份 %s，无法还原" % bak)
        return False
    with open(path, "rb") as f:
        d = f.read()
    pe = PE(path)
    off = pe.target_off
    cur = bytes(d[off:off + PATCH_LEN])
    if cur == ORIG_BYTES:
        log("  文件当前已是原始字节，无需还原")
        return True
    if cur != PATCH_BYTES:
        log("  警告: 入口字节 %s 既非原始也非 patch，仍从备份整体还原" % cur.hex(" "))
    with open(bak, "rb") as f:
        orig = f.read()
    with open(path, "wb") as f:
        f.write(orig)
    log("  已从备份还原 -> %s" % path)
    chk = PE(path)
    v = bytes(chk.data[chk.target_off:chk.target_off + PATCH_LEN])
    log("  回读入口: %s  %s" % (v.hex(" "), "OK" if v == ORIG_BYTES else "FAIL!"))
    return v == ORIG_BYTES


def file_status(path, log=print):
    pe = PE(path)
    off = pe.target_off
    cur = bytes(pe.data[off:off + PATCH_LEN])
    if cur == PATCH_BYTES:
        st = "已拦截（patched）"
    elif cur == ORIG_BYTES:
        st = "未拦截（原始）"
    else:
        st = "未知状态 %s" % cur.hex(" ")
    bak = os.path.exists(path + BACKUP_EXT)
    log("  %s | 入口=%s | 备份=%s" % (st, cur.hex(" "), "有" if bak else "无"))
    return cur


# ═════════════════════════════════════════════════════════════
# 内存版操作（Windows only）
# ═════════════════════════════════════════════════════════════
def _w():
    if not is_windows():
        raise RuntimeError("内存版仅支持 Windows（当前为 %s 平台）" % os.name)
    import ctypes
    from ctypes import wintypes
    return ctypes, wintypes


def _find_student_pids():
    ctypes, _ = _w()
    # 通过 Toolhelp 快照枚举进程，匹配 Student.exe
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
    if k32.Process32First(snap, ctypes.byref(ent)):
        while True:
            name = ent.szExeFile.decode("latin1").lower()
            if name == TARGET_MODULE.lower() or name == "student.exe":
                pids.append(ent.th32ProcessID)
            if not k32.Process32Next(snap, ctypes.byref(ent)):
                break
    k32.CloseHandle(snap)
    return pids


def _module_base(pid):
    """返回 (base, name) —— 主模块（Student.exe）基址。"""
    ctypes, wintypes = _w()
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
    ctypes, _ = _w()
    k32 = ctypes.windll.kernel32
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t(0)
    if k32.ReadProcessMemory(h, addr, buf, n, ctypes.byref(got)) == 0:
        raise ctypes.WinError()
    return buf.raw[:got.value]


def _mem_write(h, addr, data):
    ctypes, _ = _w()
    k32 = ctypes.windll.kernel32
    got = ctypes.c_size_t(0)
    if k32.WriteProcessMemory(h, addr, data, len(data), ctypes.byref(got)) == 0:
        raise ctypes.WinError()
    return got.value


def _mem_protect(h, addr, n, newprot):
    ctypes, _ = _w()
    k32 = ctypes.windll.kernel32
    old = ctypes.c_ulong(0)
    if k32.VirtualProtectEx(h, addr, n, newprot, ctypes.byref(old)) == 0:
        raise ctypes.WinError()
    return old.value


PAGE_EXECUTE_READWRITE = 0x40


def mem_patch(pid=None, log=print):
    ctypes, wintypes = _w()
    k32 = ctypes.windll.kernel32
    pids = [pid] if pid else _find_student_pids()
    if not pids:
        log("  未找到运行中的 %s 进程" % TARGET_MODULE)
        return False
    all_ok = True
    for p in pids:
        log("  --- pid=%d ---" % p)
        base, name = _module_base(p)
        log("  主模块 %s 运行时基址 = 0x%x" % (name, base))
        addr = base + FUNC_RVA
        h = k32.OpenProcess(0x0010 | 0x0020 | 0x0008, False, p)  # VM_WRITE|VM_READ|QUERY
        if not h:
            log("    OpenProcess(VM_WRITE) 失败（需管理员）")
            all_ok = False
            continue
        old = _mem_read(h, addr, PATCH_LEN)
        if old == PATCH_BYTES:
            log("    已处于拦截状态（入口=31 c0 c3），跳过")
        elif old == ORIG_BYTES:
            _mem_protect(h, addr, PATCH_LEN, PAGE_EXECUTE_READWRITE)
            _mem_write(h, addr, PATCH_BYTES)
            _mem_protect(h, addr, PATCH_LEN, 0x20)  # PAGE_EXECUTE_READ
            v = _mem_read(h, addr, PATCH_LEN)
            ok = (v == PATCH_BYTES)
            log("    原始 %s -> patch %s  %s" % (old.hex(" "), v.hex(" "),
                 "OK" if ok else "FAIL!"))
            all_ok = all_ok and ok
        else:
            log("    入口字节 %s 非预期，跳过" % old.hex(" "))
            all_ok = False
        k32.CloseHandle(h)
    return all_ok


def mem_restore(pid=None, log=print):
    ctypes, _ = _w()
    k32 = ctypes.windll.kernel32
    pids = [pid] if pid else _find_student_pids()
    if not pids:
        log("  未找到运行中的 %s 进程" % TARGET_MODULE)
        return False
    all_ok = True
    for p in pids:
        log("  --- pid=%d ---" % p)
        base, name = _module_base(p)
        addr = base + FUNC_RVA
        h = k32.OpenProcess(0x0010 | 0x0020 | 0x0008, False, p)
        if not h:
            log("    OpenProcess(VM_WRITE) 失败（需管理员）")
            all_ok = False
            continue
        cur = _mem_read(h, addr, PATCH_LEN)
        if cur == ORIG_BYTES:
            log("    已处于原始状态，无需还原")
        elif cur == PATCH_BYTES:
            _mem_protect(h, addr, PATCH_LEN, PAGE_EXECUTE_READWRITE)
            _mem_write(h, addr, ORIG_BYTES)
            _mem_protect(h, addr, PATCH_LEN, 0x20)
            v = _mem_read(h, addr, PATCH_LEN)
            ok = (v == ORIG_BYTES)
            log("    patch %s -> 还原 %s  %s" % (cur.hex(" "), v.hex(" "),
                 "OK" if ok else "FAIL!"))
            all_ok = all_ok and ok
        else:
            log("    入口字节 %s 非预期，跳过" % cur.hex(" "))
            all_ok = False
        k32.CloseHandle(h)
    return all_ok


def mem_status(log=print):
    ctypes, _ = _w()
    pids = _find_student_pids()
    if not pids:
        log("  未找到运行中的 %s 进程" % TARGET_MODULE)
        return None
    for p in pids:
        base, name = _module_base(p)
        addr = base + FUNC_RVA
        h = ctypes.windll.kernel32.OpenProcess(0x0010 | 0x0008, False, p)
        if not h:
            log("  pid=%d 读取失败（需管理员）" % p)
            continue
        cur = _mem_read(h, addr, PATCH_LEN)
        st = "已拦截" if cur == PATCH_BYTES else (
            "未拦截" if cur == ORIG_BYTES else "未知 %s" % cur.hex(" "))
        log("  pid=%d  基址=0x%x  %s (入口=%s)" % (p, base, st, cur.hex(" ")))
        ctypes.windll.kernel32.CloseHandle(h)
    return pids
