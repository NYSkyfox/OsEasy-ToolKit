# src/gui/pages/page_other.py
# 其他管理页（页面 1）

import flet as ft

from src.modules.file_handler import del_self_cmd_files
from src.modules.power_control import hijack_shutdown, release_shutdown_hijack, is_shutdown_hijacked, is_shutdown_hijacked_by_others
from src.modules.power_control import hijack_student_restart, release_student_hijack, is_student_hijacked
from src.utils.program.persistent_switch import PersistentSwitch


class PageOther:

    def __init__(self, ui):
        self.ui = ui

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

    def _on_student_restart_toggle(self, e):
        if e.control.value:
            hijack_student_restart()
        else:
            release_student_hijack()

    def build(self):
        ui = self.ui

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ft.Text("🧹 清理", size=18, weight=ft.FontWeight.BOLD),
            ft.FilledTonalButton(text="删除脚本文件", icon=ft.icons.CLEANING_SERVICES_OUTLINED, on_click=lambda _: del_self_cmd_files(), tooltip="删除工具箱生成的所有脚本文件"),
            ft.Divider(height=1),
            ft.Text("📸 截图", size=18, weight=ft.FontWeight.BOLD),
            ui.FastGetSC,
            ft.Divider(height=1),
            ft.Text("🛡️ 防护", size=18, weight=ft.FontWeight.BOLD),
            PersistentSwitch(
                label="拦截教师端远程关机 (劫持shutdown.exe)",
                live_getter=is_shutdown_hijacked,
                verifier=is_shutdown_hijacked,
                on_toggle=self._on_shutdown_toggle,
            ),
            PersistentSwitch(
                label="拦截教师端远程重启 (摘Student关机权限)",
                live_getter=is_student_hijacked,
                verifier=is_student_hijacked,
                on_toggle=self._on_student_restart_toggle,
            ),
        ])