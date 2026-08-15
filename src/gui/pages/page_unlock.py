# src/gui/pages/page_unlock.py
# 解锁管理页 —— 所有解除管控的操作集中于此

import flet as ft

from src.modules.unlock_manager import (
    usb_unlock, network_unlock, keyboard_unlock, unlock_all,
    screen_control_unlock, black_screen_unlock,
)


class PageUnlock:

    def __init__(self, ui):
        self.ui = ui

    # ---- 回调 ----

    def _handle_black_screen(self, *e):
        black_screen_unlock()

    def _handle_screen_control(self, *e):
        screen_control_unlock()

    # ---- 对话框 ----

    def _close_unlock_kb_dlg(self, confirm):
        self.ui.page.close(self._unlock_dlg)
        self.ui.page.update()
        if confirm:
            keyboard_unlock()

    def _close_unlock_all_dlg(self, confirm):
        self.ui.page.close(self._unlock_all_dlg)
        self.ui.page.update()
        if confirm:
            unlock_all()

    def _open_unlock_kb_dlg(self, *e):
        self.ui.page.open(self._unlock_dlg)
        self.ui.page.update()

    def _open_unlock_all_dlg(self, *e):
        self.ui.page.open(self._unlock_all_dlg)
        self.ui.page.update()

    # ---- 构建页面 ----

    def build(self):
        ui = self.ui

        self._unlock_all_dlg = ft.AlertDialog(
            modal=True, title=ft.Text("一键脱离管控"),
            content=ft.Text(
                "将依次解锁：\n"
                "  • 网络管控 (OeNetLimit + ProcFireWall)\n"
                "  • USB 管控 (easyusbflt)\n"
                "  • 键盘鼠标锁 (KbFilter)\n\n"
                "⚠️ 操作后将自动注销！"
            ),
            actions=[
                ft.TextButton("确认脱离", on_click=lambda _: self._close_unlock_all_dlg(True)),
                ft.TextButton("取消", on_click=lambda _: self._close_unlock_all_dlg(False)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self._unlock_dlg = ft.AlertDialog(
            modal=True, title=ft.Text("解锁键盘鼠标"),
            content=ft.Text(
                "将停止 KbFilter 键盘过滤驱动、"
                "清理注册表 UpperFilters、"
                "删除驱动文件并注销系统。\n\n"
                "⚠️ 操作后将自动注销！"
            ),
            actions=[
                ft.TextButton("确认解锁", on_click=lambda _: self._close_unlock_kb_dlg(True)),
                ft.TextButton("取消", on_click=lambda _: self._close_unlock_kb_dlg(False)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ft.FilledTonalButton(
                text="一键脱离管控（解锁全部）",
                icon=ft.Icons.LOCK_OPEN_SHARP,
                on_click=self._open_unlock_all_dlg,
                tooltip="依次解锁网络、USB、键盘鼠标管控，操作后自动注销",
            ),
            ft.FilledTonalButton(
                text="仅解锁键盘鼠标驱动",
                icon=ft.Icons.KEYBOARD_SHARP,
                on_click=self._open_unlock_kb_dlg,
                tooltip="停止KbFilter键盘过滤驱动并清理注册表，操作后自动注销",
            ),
            ft.FilledTonalButton(
                text="仅停止网络管控服务",
                icon=ft.Icons.WIFI_PASSWORD_SHARP,
                on_click=lambda _: network_unlock(),
                tooltip="停止OeNetLimit和ProcFireWall服务，不可恢复",
            ),
            ft.FilledTonalButton(
                text="仅关闭USB管控服务",
                icon=ft.Icons.USB_SHARP,
                on_click=lambda _: usb_unlock(),
                tooltip="停止easyusbflt USB过滤驱动服务",
            ),
            ft.FilledTonalButton(
                text="仅移除黑屏肃静",
                icon=ft.Icons.DARK_MODE,
                on_click=self._handle_black_screen,
                tooltip="强制结束BlackSlient.exe黑屏进程",
            ),
            ft.FilledTonalButton(
                text="仅移除屏幕广播",
                icon=ft.Icons.STOP_SCREEN_SHARE,
                on_click=self._handle_screen_control,
                tooltip="关服务 + 杀ScreenRender进程 + 删除控屏程序文件",
            ),
        ])