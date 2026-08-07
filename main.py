# main.py
# ToolKit 程序入口

import os
import sys
import time

from config import RELEASE_NAME, DATA_ROOT_TEMPLATE

# ── 日志预初始化（UAC 提权前，尽可能早） ──
_username = os.environ.get('USERNAME', 'Default')
_log_dir = DATA_ROOT_TEMPLATE.format(username=_username)
from src.utils.system.logger import pre_init, error as _log_error, exception as _log_exception
pre_init(_log_dir)

# ── 顶层异常捕获：确保任何崩溃（包括 import 阶段的 SyntaxError）都写入日志 ──
try:

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
            from src.utils.system.logger import info
            info("检测到已有实例运行，退出")
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

    # ── 日志正式初始化（UI 启动后，数据目录确认存在） ──
    from src.utils.system.logger import init
    init(os.path.dirname(toolkit_cfg.config_file_path))

    # 首次启动时的特殊操作
    fstst = toolkit_cfg.first_launch_check()
    if fstst == True:
        autodesk_dll = r"C:\Program Files\Autodesk\Autodesk Sync\AdSyncNamespace.dll"
        if os.path.exists(autodesk_dll):
            use_bat_file_to_run_cmd(
                f'rename "{autodesk_dll}" "AdSyncNamespace.dll.bak"'
            )
    # fixed pyqt bind to autodesk360 dll

    import flet as ft
    from src.gui.app import ToolKit

    ft.app(target=ToolKit.main)

except SystemExit:
    raise
except BaseException:
    _log_exception("ToolKit 未捕获异常，即将退出")
    raise