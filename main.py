# main.py
# OsEasy-ToolBox 程序入口

import os
import sys
import ctypes

# ── 自动提权：不是管理员则弹 UAC 提权重启 ──
def run_as_admin():
    """检测是否管理员身份，不是则弹 UAC 提权"""
    try:
        if ctypes.windll.shell32.IsUserAnAdmin() == 0:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv[1:]), None, 1
            )
            sys.exit(0)
    except:
        pass  # 提权失败则继续以当前权限运行

run_as_admin()

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