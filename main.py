# main.py
# OsEasy-ToolBox 程序入口

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