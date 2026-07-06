# src/modules/shutdown_hijack.py
# shutdown.exe 映像劫持 —— 防止教师端远程重启

import os

from src.core.runtime_config import toolbox_cfg
from src.core.helpers import run_sigle_cmd, Ui_call_show_snake_message


# IFEO 注册表路径
SHUTDOWN_IFEO_KEY = (
    r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion"
    r"\Image File Execution Options\shutdown.exe"
)


def _get_fake_shutdown_path():
    """获取假体 shutdown 脚本路径（同 cmd_file_path）"""
    from src.core.constants import cmd_file_path
    return os.path.join(cmd_file_path, "fake_shutdown.bat")


def _ensure_fake_shutdown_bat():
    """生成假体 bat：什么都不做，直接退出"""
    path = _get_fake_shutdown_path()
    # 内容：静默退出，code 0 表示"成功"让远程端以为命令已执行
    content = "@echo off\r\nexit /b 0\r\n"
    with open(path, "w") as f:
        f.write(content)
    return path


def hijack_shutdown():
    """劫持 shutdown.exe，使远程重启命令失效"""
    fake_path = _ensure_fake_shutdown_bat()
    cmd = (
        f'REG ADD "{SHUTDOWN_IFEO_KEY}" /v Debugger '
        f'/t REG_SZ /d "{fake_path}" /f'
    )
    run_sigle_cmd(cmd)
    Ui_call_show_snake_message("已劫持 shutdown.exe，远程重启将被拦截")


def release_shutdown_hijack():
    """解除 shutdown.exe 劫持"""
    cmd = f'REG DELETE "{SHUTDOWN_IFEO_KEY}" /v Debugger /f'
    run_sigle_cmd(cmd)
    # 顺便删除假体文件
    fake_path = _get_fake_shutdown_path()
    if os.path.isfile(fake_path):
        os.remove(fake_path)
    Ui_call_show_snake_message("已解除 shutdown.exe 劫持")


def is_shutdown_hijacked():
    """检测当前是否已劫持 shutdown.exe"""
    import subprocess
    try:
        result = subprocess.run(
            f'reg query "{SHUTDOWN_IFEO_KEY}" /v Debugger',
            shell=True,
            capture_output=True,
            text=True,
        )
        return "Debugger" in result.stdout
    except Exception:
        return False
