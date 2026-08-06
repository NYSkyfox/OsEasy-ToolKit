# src/modules/shutdown_hijack.py
# shutdown.exe 映像劫持 —— 防止教师端远程重启

import os

from src.core.runtime_config import toolkit_cfg
from src.core.helpers import show_snack
from src.utils.system.ifeo import add_ifeo_debugger, remove_ifeo_debugger, query_ifeo_debugger


def _get_fake_shutdown_path():
    """获取假体 shutdown 脚本路径（同 cmd_file_path）"""
    from src.core.constants import cmd_file_path
    return os.path.join(cmd_file_path, "fake_shutdown.bat")


def _ensure_fake_shutdown_bat():
    """生成假体 bat：什么都不做，直接退出"""
    path = _get_fake_shutdown_path()
    # 内容：静默退出，code 0 表示"成功"让远程端以为命令已执行
    content = "@echo off\r\necho 已为您拦截教师端的远程重启\r\ntimeout /t 5 /nobreak >nul\r\nexit /b 0\r\n"
    with open(path, "w", encoding="gbk") as f:
        f.write(content)
    return path


def hijack_shutdown():
    """劫持 shutdown.exe，使远程重启命令失效"""
    fake_path = _ensure_fake_shutdown_bat()
    add_ifeo_debugger("shutdown.exe", fake_path)
    show_snack("已劫持 shutdown.exe，远程重启将被拦截")


def release_shutdown_hijack():
    """解除 shutdown.exe 劫持"""
    remove_ifeo_debugger("shutdown.exe")
    fake_path = _get_fake_shutdown_path()
    if os.path.isfile(fake_path):
        os.remove(fake_path)
    show_snack("已解除 shutdown.exe 劫持")


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