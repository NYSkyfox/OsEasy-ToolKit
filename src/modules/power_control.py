# src/modules/power_control.py
# 电源管控 —— IFEO 劫持 shutdown.exe / Student.exe 防远程关机重启

import os

from src.core.settings import toolkit_cfg
from src.core.bridge import show_snack
from src.utils.ifeo import add_ifeo_debugger, remove_ifeo_debugger, query_ifeo_debugger


def _get_fake_shutdown_path():
    """获取假体 shutdown 脚本路径（同 cmd_file_path）"""
    from src.core.constants import cmd_file_path
    return os.path.join(cmd_file_path, "IFEO-Shutdown.bat")


def _ensure_fake_shutdown_bat():
    """生成假体 bat：什么都不做，直接退出"""
    path = _get_fake_shutdown_path()
    # 内容：静默退出，code 0 表示"成功"让远程端以为命令已执行
    content = "@echo off\r\necho 已为您拦截教师端的远程关机\r\ntimeout /t 5 /nobreak >nul\r\nexit /b 0\r\n"
    with open(path, "w", encoding="gbk") as f:
        f.write(content)
    return path


def hijack_shutdown():
    """劫持 shutdown.exe，使远程重启命令失效"""
    from src.utils.logger import info
    fake_path = _ensure_fake_shutdown_bat()
    add_ifeo_debugger("shutdown.exe", fake_path)
    info("已劫持 shutdown.exe，远程关机将被拦截")
    show_snack("已劫持 shutdown.exe，远程关机将被拦截")


def release_shutdown_hijack():
    """解除 shutdown.exe 劫持"""
    from src.utils.logger import info
    remove_ifeo_debugger("shutdown.exe")
    fake_path = _get_fake_shutdown_path()
    if os.path.isfile(fake_path):
        os.remove(fake_path)
    info("已解除 shutdown.exe 劫持，远程关机恢复正常")
    show_snack("已解除 shutdown.exe 劫持，远程关机恢复正常")


def is_shutdown_hijacked():
    """检测当前是否已劫持 shutdown.exe（Debugger 存在且指向本工具假体脚本）"""
    fake_path = _get_fake_shutdown_path()
    debugger = query_ifeo_debugger("shutdown.exe")
    if debugger is None:
        return False
    return fake_path.lower() == debugger.lower()


def is_shutdown_hijacked_by_others():
    """检测 Debugger 键值是否存在但不是本工具设置的（可能被其他程序劫持）"""
    fake_path = _get_fake_shutdown_path()
    debugger = query_ifeo_debugger("shutdown.exe")
    if debugger is None:
        return False
    return fake_path.lower() != debugger.lower()


# ═══════════════════════════════════════════════════════════════
#  Student.exe IFEO 劫持 —— 摘除 SeShutdownPrivilege 防远程重启
# ═══════════════════════════════════════════════════════════════

def _get_student_launcher_bat():
    """获取 Student.exe 劫持用的启动 bat 路径"""
    from src.core.constants import cmd_file_path
    return os.path.join(cmd_file_path, "IFEO-Student_Reboot.bat")


def _ensure_student_launcher_bat() -> str:
    """生成劫持 bat：调 Python 脚本，摘除关机权限后启动真 Student.exe"""
    import sys

    bat_path = _get_student_launcher_bat()

    # 找到 student_launcher.py 的路径（和本文件同目录）
    launcher_py = os.path.join(os.path.dirname(os.path.abspath(__file__)), "student_launcher.py")

    # 使用完整路径而非依赖 PATH 中的 pythonw
    pythonw = sys.executable[: sys.executable.rfind("python")] + "pythonw.exe"

    content = (
        "@echo off\r\n"
        f'"{pythonw}" "{launcher_py}"\r\n'
        "exit /b 0\r\n"
    )
    with open(bat_path, "w", encoding="gbk") as f:
        f.write(content)
    return bat_path


def hijack_student_restart():
    """劫持 Student.exe，移除其关机权限，使远程重启失效。

    流程:
    1. 注册 IFEO: Student.exe → launcher.bat
    2. 当 Student.exe 被启动时，launcher 临时解除 IFEO → 摘除权限 → 启动原版 Student.exe → 恢复 IFEO
    3. 子进程继承无 SeShutdownPrivilege 的令牌，进程名保持 Student.exe（MMPC 可识别）
    """
    from src.utils.logger import info
    from src.utils.fs import file_exists

    student_path = os.path.join(toolkit_cfg.oseasy_path, "Student.exe")

    if not file_exists(student_path):
        show_snack("未找到 Student.exe，请先执行进程管理页面的检测")
        return

    bat_path = _ensure_student_launcher_bat()
    add_ifeo_debugger("Student.exe", bat_path)
    info("已劫持 Student.exe，远程重启将被拦截")
    show_snack("已劫持 Student.exe\n远程重启将被拦截 (ExitWindowsEx 权限已移除)")


def release_student_hijack():
    """解除 Student.exe IFEO 劫持"""
    from src.utils.logger import info
    remove_ifeo_debugger("Student.exe")
    bat_path = _get_student_launcher_bat()
    if os.path.isfile(bat_path):
        os.remove(bat_path)
    info("已解除 Student.exe 劫持")
    show_snack("已解除 Student.exe 劫持")


def is_student_hijacked():
    """检测 Student.exe 是否已被劫持"""
    debugger = query_ifeo_debugger("Student.exe")
    return debugger is not None