# student_launcher.py
# IFEO 劫持 Student.exe → 移除 SeShutdownPrivilege → 启动真 Student.exe
#
# 进程名必须保持为 Student.exe，因为 MMPC 服务只认这个进程名。
# 方案：临时解除 IFEO → 启动原版 Student.exe（继承无关机权限的令牌）→ 恢复 IFEO
#
# 原理:
#   教师端远程重启 → Student.exe 调 ExitWindowsEx(EWX_REBOOT)
#   ExitWindowsEx 需要 SeShutdownPrivilege（AdjustTokenPrivileges 获取）
#   本脚本在 Student.exe 启动前，先从父进程令牌中移除该权限
#   子进程 Student.exe 继承令牌 → 没有关机权限 → ExitWindowsEx 失败
#   → 远程重启被拦截

import ctypes
import os
import sys
import subprocess

from ctypes import wintypes

# ── 常量 ──────────────────────────────────────────────────────
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
SE_PRIVILEGE_REMOVED = 0x00000004
SE_SHUTDOWN_NAME = "SeShutdownPrivilege"

IFEO_BASE_KEY = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"
IFEO_KEY_NAME = "Student.exe"

# ── TOKEN_PRIVILEGES 结构体 ────────────────────────────────────
class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]

class LUID_AND_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("Luid", LUID), ("Attributes", wintypes.DWORD)]

class TOKEN_PRIVILEGES(ctypes.Structure):
    _fields_ = [
        ("PrivilegeCount", wintypes.DWORD),
        ("Privileges", LUID_AND_ATTRIBUTES * 1),
    ]

# ── 主体 ──────────────────────────────────────────────────────

def strip_shutdown_privilege() -> bool:
    """从当前进程令牌中移除 SeShutdownPrivilege。"""
    advapi32 = ctypes.windll.advapi32
    kernel32 = ctypes.windll.kernel32

    token = wintypes.HANDLE()
    if not kernel32.OpenProcessToken(
        kernel32.GetCurrentProcess(),
        TOKEN_ADJUST_PRIVILEGES | TOKEN_QUERY,
        ctypes.byref(token),
    ):
        print("[Launcher] OpenProcessToken 失败")
        return False

    luid = LUID()
    if not advapi32.LookupPrivilegeValueW(None, SE_SHUTDOWN_NAME, ctypes.byref(luid)):
        print("[Launcher] LookupPrivilegeValueW 失败")
        kernel32.CloseHandle(token)
        return False

    tp = TOKEN_PRIVILEGES()
    tp.PrivilegeCount = 1
    tp.Privileges[0].Luid = luid
    tp.Privileges[0].Attributes = SE_PRIVILEGE_REMOVED

    ok = advapi32.AdjustTokenPrivileges(
        token, False, ctypes.byref(tp), ctypes.sizeof(tp), None, None
    )
    kernel32.CloseHandle(token)
    if not ok:
        print("[Launcher] AdjustTokenPrivileges 失败")
        return False

    print("[Launcher] SeShutdownPrivilege 已移除")
    return True


def _remove_ifeo_temporarily() -> str | None:
    """临时解除 IFEO 劫持，返回原来的 Debugger 值以便恢复。
    只有这样才能启动真正的 Student.exe 而不触发循环劫持。"""
    try:
        result = subprocess.run(
            f'reg query "{IFEO_BASE_KEY}\\{IFEO_KEY_NAME}" /v Debugger',
            shell=True, capture_output=True, text=True,
        )
        saved_debugger = None
        if "Debugger" in result.stdout and "REG_SZ" in result.stdout:
            for line in result.stdout.splitlines():
                if "Debugger" in line and "REG_SZ" in line:
                    parts = line.split("REG_SZ", 1)
                    if len(parts) == 2:
                        saved_debugger = parts[1].strip()
                        break
        subprocess.run(
            f'REG DELETE "{IFEO_BASE_KEY}\\{IFEO_KEY_NAME}" /v Debugger /f',
            shell=True, capture_output=True,
        )
        print(f"[Launcher] IFEO 已临时解除 (原值: {saved_debugger})")
        return saved_debugger
    except Exception:
        return None


def _restore_ifeo(debugger_path: str) -> None:
    """恢复 IFEO 劫持。"""
    if not debugger_path:
        return
    subprocess.run(
        f'REG ADD "{IFEO_BASE_KEY}\\{IFEO_KEY_NAME}" '
        f'/v Debugger /t REG_SZ /d "{debugger_path}" /f',
        shell=True, capture_output=True,
    )
    print("[Launcher] IFEO 已恢复")


def find_student_exe() -> str | None:
    """找到真正的 Student.exe 路径。"""
    from src.core.settings import toolkit_cfg

    try:
        path = toolkit_cfg.oseasy_path
        exe = os.path.join(path, "Student.exe")
        if os.path.exists(exe):
            return exe
    except Exception:
        pass

    from config import DEFAULT_OSEASY_PATH
    exe = os.path.join(DEFAULT_OSEASY_PATH, "Student.exe")
    if os.path.exists(exe):
        return exe
    return None


def launch_student(saved_debugger: str) -> None:
    """启动真正的 Student.exe → 恢复 IFEO。
    子进程继承当前令牌（已移除 SeShutdownPrivilege），
    进程名保持 Student.exe，MMPC 服务可以识别。"""
    student = find_student_exe()
    if not student:
        print("[Launcher] 找不到 Student.exe，放弃启动")
        _restore_ifeo(saved_debugger)
        sys.exit(1)
    print(f"[Launcher] 启动: {student}")
    subprocess.Popen([student])
    # 等原版 Student.exe 启动后恢复 IFEO，确保下次崩溃重启时劫持生效
    _restore_ifeo(saved_debugger)


def main():
    # 先保存当前 IFEO Debugger 值，用于恢复
    saved = _remove_ifeo_temporarily()
    if not saved:
        print("[Launcher] 未找到 IFEO Debugger 配置，无法继续")
        sys.exit(1)
    strip_shutdown_privilege()
    launch_student(saved)


if __name__ == "__main__":
    main()
