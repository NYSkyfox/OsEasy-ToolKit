# student_launcher.py
# IFEO 劫持 Student.exe → 移除 SeShutdownPrivilege → 启动真 Student.exe
#
# 用法: 注册 IFEO Debugger 指向本脚本
#   reg add "HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options\Student.exe" /v Debugger /t REG_SZ /d "python 本脚本路径" /f
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
import time

from ctypes import wintypes

# ── 常量 ──────────────────────────────────────────────────────
TOKEN_ADJUST_PRIVILEGES = 0x0020
TOKEN_QUERY = 0x0008
SE_PRIVILEGE_REMOVED = 0x00000004
SE_SHUTDOWN_NAME = "SeShutdownPrivilege"

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


def find_real_student() -> str | None:
    """找到真正的 Student.exe 路径。
    IFEO 劫持后，Student.exe 不能直接启动（会循环劫持），
    优先查找 Student_Real.exe（重命名后的副本）。"""
    import config
    from config import DEFAULT_OSEASY_PATH
    from src.core.settings import toolkit_cfg

    # 尝试读取之前保存的路径
    try:
        path = toolkit_cfg.oseasy_path
        real = os.path.join(path, "Student_Real.exe")
        if os.path.exists(real):
            return real
    except Exception:
        pass

    # 回退默认路径，优先找重命名后的
    default = DEFAULT_OSEASY_PATH
    real = os.path.join(default, "Student_Real.exe")
    if os.path.exists(real):
        return real

    return os.path.join(default, "Student.exe")


def launch_student():
    """启动真正的 Student.exe。"""
    real = find_real_student()
    print(f"[Launcher] 启动: {real}")
    subprocess.Popen([real], creationflags=subprocess.CREATE_NEW_CONSOLE)


def main():
    strip_shutdown_privilege()
    launch_student()


if __name__ == "__main__":
    main()
