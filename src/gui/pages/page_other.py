# src/gui/pages/page_other.py
# 其他管理页（页面 1）

import flet as ft

from src.modules.file_handler import (
    restore_oe_key_dlls, restore_oe_file,
    del_self_cmd_files,
)
from src.modules.usb_network_unlock import usb_unlock, unlock_network
from src.modules.shutdown_hijack import hijack_shutdown, release_shutdown_hijack, is_shutdown_hijacked, is_shutdown_hijacked_by_others
from src.modules.killer import delete_locked_and_logout
from src.utils.program.persistent_switch import PersistentSwitch


class PageOther:

    def __init__(self, ui):
        self.ui = ui

    # ---- 解锁对话框（本页专属） ----

    def _close_unlock_dlg(self, xueze):
        ui = self.ui
        self._unlock_dlg.open = False
        ui.page.update()
        if xueze is None:
            ui.show_snakemessage("取消解锁了")
        else:
            delete_locked_and_logout(xueze)

    def _open_unlock_dlg(self, *e):
        ui = self.ui
        ui.page.dialog = self._unlock_dlg
        self._unlock_dlg.open = True
        ui.page.update()

    # ---- shutdown 劫持冲突确认 ----

    def _do_hijack_shutdown(self):
        hijack_shutdown()

    def _on_shutdown_conflict_confirm(self, e):
        self._conflict_dlg.open = False
        self.ui.page.update()
        self._do_hijack_shutdown()

    def _on_shutdown_conflict_cancel(self, e):
        self._conflict_dlg.open = False
        self.ui.page.update()

    def _on_shutdown_toggle(self, e):
        if e.control.value:
            # 打开劫持：检查是否被别的程序占了
            if is_shutdown_hijacked_by_others():
                self._conflict_dlg = ft.AlertDialog(
                    modal=True,
                    title=ft.Text("检测到冲突"),
                    content=ft.Text("似乎有别的程序劫持了该键值，你确定要继续吗？"),
                    actions=[
                        ft.TextButton("继续", on_click=self._on_shutdown_conflict_confirm),
                        ft.TextButton("取消", on_click=self._on_shutdown_conflict_cancel),
                    ],
                    actions_alignment=ft.MainAxisAlignment.END,
                )
                self.ui.page.dialog = self._conflict_dlg
                self._conflict_dlg.open = True
                self.ui.page.update()
            else:
                self._do_hijack_shutdown()
        else:
            release_shutdown_hijack()

    def build(self):
        ui = self.ui

        self._unlock_dlg = ft.AlertDialog(
            modal=True, title=ft.Text("解锁选项"),
            content=ft.Text(
                "选择适合你的选项\n"
                "三者一起: 删除黑屏安静+解除键盘锁+删除控屏锁定程序 (需要注销)\n"
                "仅控屏: 仅删除控屏锁定程序"
            ),
            actions=[
                ft.TextButton("三者一起", on_click=lambda _: self._close_unlock_dlg(True)),
                ft.TextButton("仅控屏锁定程序", on_click=lambda _: self._close_unlock_dlg(False)),
                ft.TextButton("取消", on_click=lambda _: self._close_unlock_dlg(None)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ft.FilledTonalButton(text="长按以删除脚本文件", icon=ft.icons.CLEANING_SERVICES_OUTLINED, on_long_press=lambda _: del_self_cmd_files()),
            ft.FilledTonalButton(text="删除键盘锁驱动&控屏锁定程序", icon=ft.icons.KEYBOARD_SHARP, on_click=self._open_unlock_dlg),
            ft.FilledTonalButton(text="长按恢复所有备份文件", icon=ft.icons.RESTORE, on_long_press=lambda _: restore_oe_key_dlls()),
            ft.FilledTonalButton(text="长按以恢复黑屏安静程序", icon=ft.icons.ACCOUNT_BOX, on_long_press=lambda _: restore_oe_file("BlackSlient.exe")),
            ft.FilledTonalButton(text="长按以仅恢复控屏锁定程序", icon=ft.icons.SCREEN_SHARE_SHARP, on_long_press=lambda _: restore_oe_file("MultiClient.exe")),
            ft.FilledTonalButton(text="停止网络管控服务(不可逆)", icon=ft.icons.WIFI_PASSWORD_SHARP, on_click=lambda _: unlock_network()),
            ft.FilledTonalButton(text="关闭USB管控服务（测试，不保证可用）", icon=ft.icons.USB_SHARP, on_click=lambda _: usb_unlock()),
            ui.FastGetSC,
            PersistentSwitch(
                label="拦截教师端远程重启 (劫持shutdown.exe)",
                live_getter=is_shutdown_hijacked,
                verifier=is_shutdown_hijacked,
                on_toggle=self._on_shutdown_toggle,
            ),
        ])