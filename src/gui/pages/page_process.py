# src/gui/pages/page_process.py
# 进程管理页（页面 0）

import flet as ft
import os

from src.core.helpers import run_sigle_cmd
from src.core.runtime_config import toolkit_cfg
from src.modules.killer import (
    launch_oe_toolkit, is_sethc_hijacked, is_killer_protected,
)
from src.modules.service_manager import check_mmpc_status, handle_start_student_client
from src.utils.program.persistent_switch import PersistentSwitch


class PageProcess:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        ui.mmpc_Stext = ft.TextField(
            label="根服务状态", value="未知 (点我更新状态)", read_only=True,
            on_focus=self.only_update_MMPC_status, text_align=ft.TextAlign.CENTER,
        )

        ui.mmpc_sw = ft.FilledTonalButton(
            text="开/关学生端根服务",
            icon=ft.icons.POWER_SETTINGS_NEW,
            on_click=lambda _: run_sigle_cmd("sc stop MMPC") if check_mmpc_status() else run_sigle_cmd("sc start MMPC"),
            on_hover=self.only_update_MMPC_status,
            tooltip="点击切换MMPC服务的启动/停止状态，悬停查看当前状态",
        )

        ui.guaqi_sw = PersistentSwitch(
            config_key="guaqi_enabled",
            label="挂起学生端",
            on_toggle=ui._on_guaqi_changed,
        )

        ui.protect_swc = PersistentSwitch(
            config_key="protect_killer_enabled",
            label="外部cmd守护进程",
            verifier=is_killer_protected,
            on_toggle=ui._on_protect_killer_changed,
        )

        ui.sethc_swc = PersistentSwitch(
            live_getter=is_sethc_hijacked,
            verifier=is_sethc_hijacked,
            label="劫持粘滞键 (sethc.exe)",
            on_toggle=ui._on_sethc_toggle,
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ui.mmpc_Stext, ui.mmpc_sw,
            ft.FilledTonalButton(text="重启学生端", icon=ft.icons.RESTORE, on_click=handle_start_student_client, tooltip="点击以结束并重新启动学生端进程"),
            ft.FilledTonalButton(text="重新获取学生端路径", icon=ft.icons.REFRESH, on_click=ui.reflashStudentPath, tooltip="重新检测OsEasy学生端的安装路径和版本"),
            ui.sethc_swc,
            ui.protect_swc,
            ui.guaqi_sw,
            ft.FilledTonalButton(text="打开噢易自带工具", icon=ft.icons.OPEN_IN_NEW, on_click=launch_oe_toolkit, tooltip="运行OsEasy自带的配置工具"),
            ft.FilledTonalButton(
                text="打开OsEasy安装目录",
                icon=ft.icons.FOLDER_OPEN,
                on_click=self.open_oseasy_dir,
                tooltip="在资源管理器中打开OsEasy安装文件夹",
            ),
            ft.FilledTonalButton(
                text="打开ToolKit数据文件夹",
                icon=ft.icons.FOLDER_SPECIAL,
                on_click=self.open_toolkit_data_dir,
                tooltip="打开工具箱的数据存储目录",
            ),
        ])

    def open_oseasy_dir(self, *e):
        """在资源管理器中打开 OsEasy 安装目录"""
        path = toolkit_cfg.oseasy_path
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.ui.show_snakemessage(f"目录不存在: {path}")

    def open_toolkit_data_dir(self, *e):
        """在资源管理器中打开 ToolKit 数据文件夹"""
        from config import DATA_ROOT_TEMPLATE
        path = DATA_ROOT_TEMPLATE.format(username=os.environ.get('USERNAME', 'Default'))
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.ui.show_snakemessage(f"目录不存在: {path}")

    def only_update_MMPC_status(self, *e):
        ui = self.ui
        st = check_mmpc_status()
        ui.show_snakemessage(f"根服务状态: {st}")
        ui.mmpc_Stext.value = "正在运行" if st else "未运行"
        ui.page.update()