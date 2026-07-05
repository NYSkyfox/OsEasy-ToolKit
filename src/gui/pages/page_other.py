# src/gui/pages/page_other.py
# 其他管理页（页面 1）

import flet as ft

from src.modules.file_handler import (
    restone_oe_backup_key_dll, restone_sigle_oe_backup_file,
    del_self_cmd_files,
)
from src.modules.usb_network_unlock import usb_unlock, handle_run_old_unlock_net


class PageOther:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ft.FilledTonalButton(text="长按以删除脚本文件", icon=ft.icons.CLEANING_SERVICES_OUTLINED, on_long_press=lambda _: del_self_cmd_files()),
            ft.FilledTonalButton(text="删除键盘锁驱动&控屏锁定程序", icon=ft.icons.KEYBOARD_SHARP, on_click=ui.open_askdel_dlg),
            ft.FilledTonalButton(text="长按恢复所有备份文件", icon=ft.icons.RESTORE, on_long_press=lambda _: restone_oe_backup_key_dll()),
            ft.FilledTonalButton(text="长按以恢复黑屏安静程序", icon=ft.icons.ACCOUNT_BOX, on_long_press=lambda _: restone_sigle_oe_backup_file("BlackSlient.exe")),
            ft.FilledTonalButton(text="长按以仅恢复控屏锁定程序", icon=ft.icons.SCREEN_SHARE_SHARP, on_long_press=lambda _: restone_sigle_oe_backup_file("MultiClient.exe")),
            ft.FilledTonalButton(text="停止网络管控服务(不可逆)", icon=ft.icons.WIFI_PASSWORD_SHARP, on_click=lambda _: handle_run_old_unlock_net()),
            ft.FilledTonalButton(text="[无法正常工作] 关闭USB管控服务", icon=ft.icons.USB_SHARP, on_click=lambda _: usb_unlock()),
            ui.FastGetSC,
        ])