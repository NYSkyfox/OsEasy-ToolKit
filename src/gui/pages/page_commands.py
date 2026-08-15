# src/gui/pages/page_commands.py
# 广播命令页（页面 3）

import flet as ft

from src.modules.broadcast_handler import (
    save_now_broadcast_cmd, extract_yc_cmd_from_log,
    handin_save_yc_cmd, generate_remote_cmd_and_save,
    start_log_monitor, stop_log_monitor, is_log_monitor_running,
)
from src.utils.program.persistent_switch import PersistentSwitch


class PageCommands:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        ui.teachIp_input = ft.TextField(label="输入教师机IP地址")
        ui.auto_gennerate_cmd = ft.FilledTonalButton(
            text="由教师机IP生成远程命令", icon=ft.Icons.DRAW,
            on_click=lambda _: generate_remote_cmd_and_save(ui.teachIp_input.value),
            tooltip="根据教师机IP地址自动生成完整的远程广播控制命令",
        )
        ui.conl_save_ycCmd_input = ft.TextField(label="键入完整的远程广播命令")
        ui.conl_ycCmd_update_with_replace_ip = ft.FilledTonalButton(
            "自动替换本地IP并更新命令",
            on_click=lambda _: handin_save_yc_cmd(ui.conl_save_ycCmd_input.value, True),
            icon=ft.Icons.DRAW,
            tooltip="自动检测本机IP地址并替换更新远程广播命令",
        )
        ui.conl_ycCmd_update = ft.FilledTonalButton(
            "手动更新完整远程广播命令",
            on_click=lambda _: handin_save_yc_cmd(ui.conl_save_ycCmd_input.value, False),
            icon=ft.Icons.MODE_EDIT_SHARP,
            tooltip="手动输入并保存完整的远程广播控制命令",
        )
        ui.conl_from_log_get_cmd = ft.FilledTonalButton(
            text="从日志文件获取远程命令", icon=ft.Icons.BOOK,
            on_click=lambda _: extract_yc_cmd_from_log(),
            tooltip="从ScreenRender.log日志中提取教师端远程广播命令",
        )
        ui.conl_getyccmd_btn = ft.FilledTonalButton(
            text="读取已拦截的广播命令", icon=ft.Icons.BOOK,
            on_click=self.dev_read_lj_cmd_loj,
            tooltip="读取之前已拦截并保存的广播控制命令",
        )
        ui.monitor_swc = PersistentSwitch(
            config_key="log_monitor_enabled",
            label="自动监控广播日志 (全屏自动转窗口)",
            live_getter=is_log_monitor_running,
            verifier=is_log_monitor_running,
            on_toggle=self._on_monitor_toggle,
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ui.conl_save_ycCmd_input, ui.conl_ycCmd_update,
            ui.conl_ycCmd_update_with_replace_ip,
            ui.teachIp_input, ui.auto_gennerate_cmd,
            ui.conl_from_log_get_cmd, ui.conl_getyccmd_btn,
            ui.monitor_swc,
        ])

    def _on_monitor_toggle(self, e):
        ui = self.ui
        if e.control.value:
            start_log_monitor(auto_windowed=True)
            ui.show_snakemessage("广播日志监控已启动")
        else:
            stop_log_monitor()
            ui.show_snakemessage("广播日志监控已停止")

    def dev_read_lj_cmd_loj(self, *e):
        ui = self.ui
        status = save_now_broadcast_cmd()
        if not status:
            ui.show_snakemessage("未拦截到控制命令参数")
        else:
            ui.show_snakemessage("保存拦截命令成功")