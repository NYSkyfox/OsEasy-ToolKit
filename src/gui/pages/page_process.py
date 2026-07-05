# src/gui/pages/page_process.py
# 进程管理页（页面 0）

import flet as ft
from pynput import keyboard

from src.core.runtime_config import toolbox_cfg
from src.core.helpers import run_sigle_cmd
from src.modules.killer import (
    register_killer_script, del_register_killer, killer_script_protect,
    start_oseasy_self_toolbox,
)
from src.modules.process_manager import get_scshot
from src.modules.service_manager import check_mmpc_status, handle_start_student_client


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
            text="长按开&关学生端根服务",
            icon=ft.icons.BACK_HAND_OUTLINED,
            on_long_press=lambda _: run_sigle_cmd("sc stop MMPC") if check_mmpc_status() else run_sigle_cmd("sc start MMPC"),
            on_hover=self.only_update_MMPC_status,
        )

        ui.FastGetSC = ft.Switch(
            label="Alt+X 快捷键屏幕截图",
            active_color=ui.accent_color,
            on_change=lambda _: ui.hotkeyManager.switch_reg_helper(
                ui.FastGetSC.value, [keyboard.Key.alt_l, 'x'], get_scshot
            ),
        )

        ui.guaqi_sw = ft.Switch(
            label="挂起学生端",
            active_color=ui.accent_color,
            on_change=ui.guaqi_chufa,
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ui.mmpc_Stext, ui.mmpc_sw,
            ft.FilledTonalButton(text="长按重启学生端", icon=ft.icons.RESTORE, on_long_press=handle_start_student_client),
            ft.FilledTonalButton(text="重新获取学生端路径", icon=ft.icons.REFRESH, on_click=ui.reflashStudentPath),
            ft.FilledTonalButton(text="注册粘滞键替换", icon=ft.icons.FILE_COPY_ROUNDED, on_click=lambda _: register_killer_script()),
            ft.FilledTonalButton(text="还原粘滞键", icon=ft.icons.FILE_COPY_ROUNDED, on_click=lambda _: del_register_killer()),
            ft.Switch(label="外部cmd守护进程", active_color=ui.accent_color, on_change=lambda _: killer_script_protect()),
            ui.guaqi_sw,
            ft.FilledTonalButton(text="打开噢易自带工具", icon=ft.icons.OPEN_IN_NEW, on_click=start_oseasy_self_toolbox),
        ])

    def only_update_MMPC_status(self, *e):
        ui = self.ui
        st = check_mmpc_status()
        ui.show_snakemessage(f"根服务状态: {st}")
        ui.mmpc_Stext.value = "正在运行" if st else "未运行"
        ui.page.update()