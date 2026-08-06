# main.py
# ToolKit 程序入口

import os
import sys
import time

from config import RELEASE_NAME

# ── 单实例检测（防止重复启动） ──
def check_single_instance():
    """防止程序重复运行（ctypes 实现，零依赖）"""
    import ctypes
    from ctypes import wintypes

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32

    # CreateMutexW
    mutex = kernel32.CreateMutexW(None, False, "OsEasyToolKit_Mutex")
    ERROR_ALREADY_EXISTS = 183
    if kernel32.GetLastError() == ERROR_ALREADY_EXISTS:
        # 已有实例在运行，激活已存在的窗口并退出
        try:
            SW_SHOW = 5
            hwnd = user32.FindWindowW(None, RELEASE_NAME)
            if hwnd:
                user32.ShowWindow(hwnd, SW_SHOW)
                user32.SetForegroundWindow(hwnd)
        except:
            pass
        sys.exit(0)

# 先检测是否已有实例运行
check_single_instance()

# ── UAC 提权 ──
from src.utils.system.uac_elevator import elevate
elevate(__file__)

# CI 测试模式：只 import 关键依赖并初始化，不启动 GUI
if os.environ.get("OSEASY_TEST_MODE") == "1":
    from src.core.runtime_config import toolkit_cfg
    from src.core.helpers import use_bat_file_to_run_cmd
    import flet as ft
    from src.gui.app import ToolKit
    print("OSEASY_TEST_MODE OK")
    sys.exit(0)

from src.core.runtime_config import toolkit_cfg
from src.core.helpers import use_bat_file_to_run_cmd

# 首次启动时的特殊操作
fstst = toolkit_cfg.first_launch_check()
if fstst == True:
    use_bat_file_to_run_cmd(
        'rename "C:\\Program Files\\Autodesk\\Autodesk Sync\\AdSyncNamespace.dll" "AdSyncNamespace.dll.bak"'
    )
# fixed pyqt bind to autodesk360 dll

import flet as ft
from src.gui.app import ToolKit

ft.app(target=ToolKit.main)