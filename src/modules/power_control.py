# src/modules/power_control.py
# 电源管控 —— 拦截教师端远程关机/重启（文件 patch / 内存 patch 双模式）
#
# 逆向结论（Ghidra, Student.exe, PE32, ImageBase=0x400000）：
#   远程"重启"与"关机"共用同一个函数 FUN_004a9660，靠入参区分，
#   两条路径最终都调 ExitWindowsEx（重启=0x006 REBOOT|FORCE，
#   关机=0x00D SHUTDOWN|FORCE|POWEROFF），全程不经过 shutdown.exe。
#
#   Patch 策略：将该函数入口 3 字节
#       55 8B EC  (push ebp; mov ebp, esp)
#       -> 31 C0 C3 (xor eax,eax; ret)
#   使函数进入即返回，重启 + 关机指令同时失效。
#
# 两种模式：
#   文件版 —— 改磁盘上的 Student.exe（持久，需先结束学生端进程）
#   内存版 —— 改运行中进程内存（抗 ASLR，进程重启自动恢复，无需杀进程）

import os
import struct

from src.core.settings import toolkit_cfg
from src.core.bridge import show_snack
from src.utils.logger import info, warn

# ── 目标常量（来自 Ghidra 逆向 + PE 实测） ─────────────────────
FUNC_RVA     = 0x0A9660                 # FUN_004a9660, ImageBase 0x400000
ORIG_BYTES   = bytes.fromhex("558BEC")  # push ebp; mov ebp, esp
PATCH_BYTES  = bytes.fromhex("31C0C3")  # xor eax,eax; ret
BACKUP_SUFFIX = ".power.bak"

# 已知合法 MD5（仅作提示，不强校验）
KNOWN_MD5 = {
    "326a77edb4b5d03eaeeb7dafa2d9e08e": "Student.exe 原版",
    "aa2e24bc4912e8f57a3dd2b3df6cb6e1": "Student_duo_open.exe 双开版",
}


# ═══════════════════════════════════════════════════════════════
#  基础：路径 / PE 解析
# ═══════════════════════════════════════════════════════════════
def _student_exe_path() -> str:
    return os.path.join(toolkit_cfg.oseasy_path, "Student.exe")


def _backup_path() -> str:
    return _student_exe_path() + BACKUP_SUFFIX


def _rva_to_off(data: bytes, rva: int) -> int:
    """RVA -> 文件偏移（PE32/PE64 通用）。"""
    pe = struct.unpack_from("<I", data, 0x3C)[0]
    if data[pe:pe + 4] != b"PE\0\0":
        raise ValueError("不是有效的 PE 文件")
    coff = pe + 4
    _machine, nsec, _ts, _sym, _nsym, opt_size, _char = struct.unpack_from(
        "<HHIIIHH", data, coff)
    opt = coff + 20
    _magic = struct.unpack_from("<H", data, opt)[0]
    sec_off = opt + opt_size
    for i in range(nsec):
        so = sec_off + i * 40
        vsize = struct.unpack_from("<I", data, so + 8)[0]
        va = struct.unpack_from("<I", data, so + 12)[0]
        rawsz = struct.unpack_from("<I", data, so + 16)[0]
        rawptr = struct.unpack_from("<I", data, so + 20)[0]
        if va <= rva < va + max(vsize, rawsz):
            return rawptr + (rva - va)
    raise ValueError("RVA 0x%x 不在任何 section（版本可能不匹配）" % rva)


def _entry_off(path: str) -> int:
    """定位 patch 点文件偏移，并强校验入口字节。"""
    with open(path, "rb") as f:
        data = f.read()
    off = _rva_to_off(data, FUNC_RVA)
    cur = data[off:off + 3]
    if cur not in (ORIG_BYTES, PATCH_BYTES):
        raise ValueError(
            "入口字节 %s 与预期 %s / %s 不符，可能是未知版本，已拒绝操作" % (
                cur.hex(" "), ORIG_BYTES.hex(" "), PATCH_BYTES.hex(" ")))
    return off


def _student_running() -> bool:
    from src.utils.process import is_process_running
    for name in ("Student.exe", "MmcStudent.exe"):
        try:
            if is_process_running(name):
                return True
        except Exception:
            pass
    return False


def _kill_student():
    """结束学生端进程（释放文件占用），忽略未找到。"""
    from src.utils.process import kill_process
    for name in ("Student.exe", "MmcStudent.exe"):
        try:
            kill_process(name)
        except Exception:
            pass


# ═══════════════════════════════════════════════════════════════
#  文件版：patch / restore / status
# ═══════════════════════════════════════════════════════════════
def is_file_patched() -> bool:
    """检测 Student.exe 文件是否已被 patch。"""
    path = _student_exe_path()
    if not os.path.isfile(path):
        return False
    try:
        off = _entry_off(path)
        with open(path, "rb") as f:
            f.seek(off)
            return f.read(3) == PATCH_BYTES
    except Exception:
        return False


def patch_file() -> bool:
    """文件版拦截：结束学生端 -> 备份 -> patch 入口 3 字节。"""
    from src.utils.fs import file_exists
    path = _student_exe_path()
    if not file_exists(path):
        show_snack("未找到 Student.exe，请先在进程管理页检测学生端路径")
        return False

    try:
        off = _entry_off(path)
    except ValueError as e:
        warn("patch 校验失败: %s" % e)
        show_snack("无法识别的 Student.exe 版本，已拒绝操作")
        return False

    with open(path, "rb") as f:
        f.seek(off)
        if f.read(3) == PATCH_BYTES:
            show_snack("Student.exe 已处于拦截状态")
            return True

    if _student_running():
        info("结束学生端进程以释放文件占用")
        _kill_student()
        import time
        time.sleep(1)

    bak = _backup_path()
    if not os.path.exists(bak):
        try:
            with open(path, "rb") as f:
                data = f.read()
            with open(bak, "wb") as f:
                f.write(data)
            import hashlib
            md5 = hashlib.md5(data).hexdigest()
            tag = KNOWN_MD5.get(md5, "未知版本")
            info("已备份 Student.exe (MD5 %s / %s)" % (md5, tag))
        except Exception as e:
            show_snack("备份失败: %s" % e)
            return False

    try:
        with open(path, "r+b") as f:
            f.seek(off)
            f.write(PATCH_BYTES)
    except PermissionError:
        show_snack("Student.exe 被占用，无法写入。\n请确认学生端已完全结束后重试")
        return False
    except Exception as e:
        show_snack("写入失败: %s" % e)
        return False

    info("已 patch Student.exe 入口 (文件版)")
    show_snack("已拦截（文件版）\n请重启学生端使 patch 生效")
    return True


def restore_file() -> bool:
    """文件版还原：结束学生端 -> 从备份还原。"""
    path = _student_exe_path()
    bak = _backup_path()
    if not os.path.isfile(path):
        show_snack("未找到 Student.exe")
        return False
    if not os.path.isfile(bak):
        show_snack("未找到备份，无法还原")
        return False

    try:
        off = _entry_off(path)
        with open(path, "rb") as f:
            f.seek(off)
            if f.read(3) == ORIG_BYTES:
                show_snack("Student.exe 当前已是原始状态")
                return True
    except ValueError:
        pass

    if _student_running():
        _kill_student()
        import time
        time.sleep(1)

    try:
        with open(bak, "rb") as f:
            orig = f.read()
        with open(path, "wb") as f:
            f.write(orig)
    except PermissionError:
        show_snack("Student.exe 被占用，无法还原")
        return False
    except Exception as e:
        show_snack("还原失败: %s" % e)
        return False

    info("已还原 Student.exe (文件版)")
    show_snack("已还原（文件版）\n请重启学生端")
    return True


# ═══════════════════════════════════════════════════════════════
#  内存版：patch / restore / status（Windows only，需管理员）
# ═══════════════════════════════════════════════════════════════
def _get_k32():
    import ctypes
    return ctypes.windll.kernel32


def _find_student_pids() -> list:
    """通过 Toolhelp 快照枚举 Student.exe 进程。"""
    import ctypes
    from ctypes import wintypes

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

    k32 = _get_k32()
    TH32CS_SNAPPROCESS = 0x00000002
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if not snap:
        return []
    ent = P32()
    ent.dwSize = ctypes.sizeof(P32)
    pids = []
    if k32.Process32First(snap, ctypes.byref(ent)):
        while True:
            name = ent.szExeFile.decode("latin1").lower()
            if name in ("student.exe", "mmcstudent.exe"):
                pids.append(ent.th32ProcessID)
            if not k32.Process32Next(snap, ctypes.byref(ent)):
                break
    k32.CloseHandle(snap)
    return pids


def _get_module_base(pid: int) -> tuple:
    """返回 (base_addr, module_name) —— 主模块基址（抗 ASLR）。"""
    import ctypes
    from ctypes import wintypes
    k32 = _get_k32()
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    h = k32.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
    if not h:
        raise PermissionError("OpenProcess 失败（需要管理员权限）")
    for flags in (0x03, 0x00):  # MOD_LIST_FLAGS_32BIT, MOD_LIST_ALL
        bufsz = ctypes.c_ulong(65536)
        needed = ctypes.c_ulong(0)
        buf = (ctypes.c_byte * 65536)()
        if k32.EnumProcessModulesEx(h, buf, bufsz, ctypes.byref(needed), flags) and needed.value > 0:
            n = needed.value // 4
            addrs = struct.unpack_from("<%dI" % n, bytes(buf[:needed.value]), 0)
            for a in addrs:
                namebuf = ctypes.create_unicode_buffer(520)
                if k32.GetModuleBaseNameW(h, a, namebuf, 520):
                    k32.CloseHandle(h)
                    return a, namebuf.value
    k32.CloseHandle(h)
    raise RuntimeError("未能枚举到主模块")


def _mem_read(h, addr, n) -> bytes:
    import ctypes
    k32 = _get_k32()
    buf = ctypes.create_string_buffer(n)
    got = ctypes.c_size_t(0)
    if not k32.ReadProcessMemory(h, addr, buf, n, ctypes.byref(got)):
        raise ctypes.WinError()
    return buf.raw[:got.value]


def _mem_write(h, addr, data) -> int:
    import ctypes
    k32 = _get_k32()
    got = ctypes.c_size_t(0)
    if not k32.WriteProcessMemory(h, addr, data, len(data), ctypes.byref(got)):
        raise ctypes.WinError()
    return got.value


def _mem_protect(h, addr, n, newprot):
    import ctypes
    k32 = _get_k32()
    old = ctypes.c_ulong(0)
    if not k32.VirtualProtectEx(h, addr, n, newprot, ctypes.byref(old)):
        raise ctypes.WinError()
    return old.value


PAGE_EXECUTE_READWRITE = 0x40
PAGE_EXECUTE_READ = 0x20


def _mem_patch_pid(pid: int) -> tuple:
    """对单个 pid 执行内存 patch，返回 (success, msg)。"""
    k32 = _get_k32()
    base, name = _get_module_base(pid)
    addr = base + FUNC_RVA
    # 需要 VM_WRITE | VM_READ
    h = k32.OpenProcess(0x0010 | 0x0020 | 0x0008, False, pid)
    if not h:
        return False, "OpenProcess(VM_WRITE) 失败，需要管理员权限"
    try:
        cur = _mem_read(h, addr, 3)
        if cur == PATCH_BYTES:
            return True, "已处于拦截状态，跳过"
        if cur != ORIG_BYTES:
            return False, "入口字节 %s 非预期（可能是未知版本）" % cur.hex(" ")
        _mem_protect(h, addr, 3, PAGE_EXECUTE_READWRITE)
        _mem_write(h, addr, PATCH_BYTES)
        _mem_protect(h, addr, 3, PAGE_EXECUTE_READ)
        verify = _mem_read(h, addr, 3)
        if verify == PATCH_BYTES:
            return True, "OK (基址=0x%x)" % base
        return False, "写入后验证失败"
    finally:
        k32.CloseHandle(h)


def _mem_restore_pid(pid: int) -> tuple:
    """对单个 pid 执行内存还原，返回 (success, msg)。"""
    k32 = _get_k32()
    base, name = _get_module_base(pid)
    addr = base + FUNC_RVA
    h = k32.OpenProcess(0x0010 | 0x0020 | 0x0008, False, pid)
    if not h:
        return False, "OpenProcess(VM_WRITE) 失败，需要管理员权限"
    try:
        cur = _mem_read(h, addr, 3)
        if cur == ORIG_BYTES:
            return True, "已处于原始状态，跳过"
        if cur != PATCH_BYTES:
            return False, "入口字节 %s 非预期" % cur.hex(" ")
        _mem_protect(h, addr, 3, PAGE_EXECUTE_READWRITE)
        _mem_write(h, addr, ORIG_BYTES)
        _mem_protect(h, addr, 3, PAGE_EXECUTE_READ)
        verify = _mem_read(h, addr, 3)
        if verify == ORIG_BYTES:
            return True, "OK (基址=0x%x)" % base
        return False, "还原后验证失败"
    finally:
        k32.CloseHandle(h)


def patch_memory() -> tuple:
    """内存版拦截：对运行中 Student.exe 进程执行内存 patch。

    返回 (success, detail_msg)
    """
    pids = _find_student_pids()
    if not pids:
        return False, "未找到运行中的 Student.exe 进程\n请先启动学生端"
    results = []
    all_ok = True
    for pid in pids:
        ok, msg = _mem_patch_pid(pid)
        results.append("  pid=%d: %s" % (pid, msg))
        all_ok = all_ok and ok
    detail = "\n".join(results)
    if all_ok:
        info("内存 patch 完成: %s" % detail)
        return True, "已拦截（内存版）\n%s" % detail
    else:
        warn("内存 patch 部分失败: %s" % detail)
        return False, "拦截失败\n%s" % detail


def restore_memory() -> tuple:
    """内存版还原：对运行中 Student.exe 进程恢复原始字节。"""
    pids = _find_student_pids()
    if not pids:
        return False, "未找到运行中的 Student.exe 进程"
    results = []
    all_ok = True
    for pid in pids:
        ok, msg = _mem_restore_pid(pid)
        results.append("  pid=%d: %s" % (pid, msg))
        all_ok = all_ok and ok
    detail = "\n".join(results)
    if all_ok:
        info("内存还原完成: %s" % detail)
        return True, "已还原（内存版）\n%s" % detail
    else:
        warn("内存还原部分失败: %s" % detail)
        return False, "还原失败\n%s" % detail


def is_memory_patched() -> tuple:
    """检测运行中进程内存是否已 patch。返回 (found, patched, detail)"""
    pids = _find_student_pids()
    if not pids:
        return False, False, "未找到 Student.exe 进程"
    results = []
    any_patched = False
    for pid in pids:
        try:
            base, name = _get_module_base(pid)
            addr = base + FUNC_RVA
            k32 = _get_k32()
            h = k32.OpenProcess(0x0010 | 0x0008, False, pid)
            if not h:
                results.append("  pid=%d: 读取失败" % pid)
                continue
            cur = _mem_read(h, addr, 3)
            k32.CloseHandle(h)
            if cur == PATCH_BYTES:
                any_patched = True
                results.append("  pid=%d: 已拦截" % pid)
            elif cur == ORIG_BYTES:
                results.append("  pid=%d: 未拦截" % pid)
            else:
                results.append("  pid=%d: 未知 %s" % (pid, cur.hex(" ")))
        except Exception as e:
            results.append("  pid=%d: %s" % (pid, e))
    return True, any_patched, "\n".join(results)


# ═══════════════════════════════════════════════════════════════
#  统一入口（供 GUI 按钮调用）
# ═══════════════════════════════════════════════════════════════
def is_patched() -> bool:
    """综合检测：文件版或内存版任一处于拦截状态。"""
    if is_file_patched():
        return True
    try:
        found, patched, _ = is_memory_patched()
        return found and patched
    except Exception:
        return False


def patch(mode: str) -> tuple:
    """执行拦截。mode='file' 或 'memory'。返回 (success, msg)"""
    if mode == "memory":
        return patch_memory()
    else:
        ok = patch_file()
        return ok, "已拦截（文件版）" if ok else "拦截失败"


def restore(mode: str) -> tuple:
    """执行还原。mode='file' 或 'memory'。返回 (success, msg)"""
    if mode == "memory":
        return restore_memory()
    else:
        ok = restore_file()
        return ok, "已还原（文件版）" if ok else "还原失败"