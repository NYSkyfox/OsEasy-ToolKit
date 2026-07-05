# src/gui/pages/page_commands.py
# 广播命令页（页面 3）

import flet as ft

from src.modules.broadcast_handler import (
    save_now_broadcast_cmd, from_scr_log_cmd_get_yccmd,
    handin_save_yc_cmd, generate_remote_cmd_and_save,
)


class PageCommands:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        ui.teachIp_input = ft.TextField(label="输入教师机IP地址")
        ui.auto_gennerate_cmd = ft.FilledTonalButton(
            text="由教师机IP生成远程命令", icon=ft.icons.DRAW,
            on_click=lambda _: generate_remote_cmd_and_save(ui.teachIp_input.value),
        )
        ui.conl_save_ycCmd_input = ft.TextField(label="键入完整的远程广播命令")
        ui.conl_ycCmd_update_with_replace_ip = ft.FilledTonalButton(
            "自动替换本地IP并更新命令",
            on_click=lambda _: handin_save_yc_cmd(ui.conl_save_ycCmd_input.value, True),
            icon=ft.icons.DRAW,
        )
        ui.conl_ycCmd_update = ft.FilledTonalButton(
            "手动更新完整远程广播命令",
            on_click=lambda _: handin_save_yc_cmd(ui.conl_save_ycCmd_input.value, False),
            icon=ft.icons.MODE_EDIT_SHARP,
        )
        ui.conl_from_log_get_cmd = ft.FilledTonalButton(
            text="从日志文件获取远程命令", icon=ft.icons.BOOK,
            on_click=lambda _: from_scr_log_cmd_get_yccmd(),
        )
        ui.conl_getyccmd_btn = ft.FilledTonalButton(
            text="读取已拦截的广播命令", icon=ft.icons.BOOK,
            on_click=self.dev_read_lj_cmd_loj,
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ui.conl_save_ycCmd_input, ui.conl_ycCmd_update,
            ui.conl_ycCmd_update_with_replace_ip,
            ui.teachIp_input, ui.auto_gennerate_cmd,
            ui.conl_from_log_get_cmd, ui.conl_getyccmd_btn,
        ])

    def dev_read_lj_cmd_loj(self, *e):
        ui = self.ui
        status = save_now_broadcast_cmd()
        if status is None:
            ui.show_snakemessage("未拦截到控制命令参数")
        else:
            ui.show_snakemessage("保存拦截命令成功")