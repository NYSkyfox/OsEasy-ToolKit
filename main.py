# main.py
# OsEasy-ToolBox 程序入口

import os
import sys
import ctypes
import time

# ── 单实例检测（防止重复启动） ──
def check_single_instance():
    """防止程序重复运行"""
    try:
        import win32event
        import win32api
        import winerror
        mutex = win32event.CreateMutex(None, False, "OsEasyToolKit_Mutex")
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            # 已有实例在运行，激活已存在的窗口并退出
            try:
                import win32gui
                hwnd = win32gui.FindWindow(None, "OsEasy-ToolBox")
                if hwnd:
                    win32gui.ShowWindow(hwnd, 5)  # SW_SHOW
                    win32gui.SetForegroundWindow(hwnd)
            except:
                pass
            sys.exit(0)
    except ImportError:
        # 如果没有pywin32，使用简单端口检测
        try:
            import socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('127.0.0.1', 49152))
            sock.close()
        except OSError:
            sys.exit(0)
    except:
        pass  # 检测失败则继续运行

# ── 自动提权：已禁用，改为打包时通过 manifest 提权 ──
# def run_as_admin():
#     """检测是否管理员身份，不是则弹 UAC 提权"""
#     try:
#         if ctypes.windll.shell32.IsUserAnAdmin() == 0:
#             ctypes.windll.shell32.ShellExecuteW(
#                 None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1
#             )
#             sys.exit(0)
#     except:
#         pass  # 提权失败则继续以当前权限运行

# 先检测是否已有实例运行
check_single_instance()

# 再执行提权（已禁用）
# run_as_admin()

# CI 测试模式：只 import 关键依赖并初始化，不启动 GUI
if os.environ.get("OSEASY_TEST_MODE") == "1":
    from src.core.runtime_config import toolbox_cfg
    from src.core.helpers import use_bat_file_to_run_cmd
    import flet as ft
    from src.gui.app import ToolBox
    print("OSEASY_TEST_MODE OK")
    sys.exit(0)

from src.core.runtime_config import toolbox_cfg
from src.core.helpers import use_bat_file_to_run_cmd

# 首次启动时的特殊操作
fstst = toolbox_cfg.first_launch_check()
if fstst == True:
    use_bat_file_to_run_cmd(
        'rename "C:\\Program Files\\Autodesk\\Autodesk Sync\\AdSyncNamespace.dll" "AdSyncNamespace.dll.bak"'
    )
# fixed pyqt bind to autodesk360 dll

import flet as ft
from src.gui.app import ToolBox

ft.app(target=ToolBox.main)