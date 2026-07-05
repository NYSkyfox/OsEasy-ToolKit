# src/gui/pages/page_broadcast.py
# 广播管理页（页面 2）

import time

import flet as ft
from pynput import keyboard

from src.core.helpers import run_sigle_cmd
from src.modules.broadcast_handler import (
    replace_screen_render, restone_screen_render,
    check_replace_screen_render_status,
    from_log_file_get_remote_cmd, build_run_broadcast_cmd,
)
from src.modules.service_manager import if_is_high_ver_client_auto_close_mmpc_helper


class PageBroadcast:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        ui.replace_status = ft.TextField(
            label="替换程序状态", value="未知 (点我更新状态)",
            read_only=True, on_focus=self.update_replace_status,
            text_align=ft.TextAlign.CENTER,
        )

        ui.tihuan_scr = ft.FilledTonalButton(
            text="替换拦截命令程序", on_click=self.replace_SCR_loj,
            icon=ft.icons.FIND_REPLACE,
        )
        ui.try_read_sharecmd = ft.FilledTonalButton(
            text="运行窗口化广播命令", on_click=self.run_win_gbcmd_loj,
            icon=ft.icons.WINDOW_SHARP,
        )
        ui.RunFullSC_btn = ft.FilledTonalButton(
            "长按运行全屏广播命令",
            on_long_press=lambda _: ui.direct_run_fullscreen_boradcast_cmd(),
            icon=ft.icons.FULLSCREEN,
        )
        ui.KillSCR_btn = ft.FilledTonalButton(
            "手动杀屏幕广播进程", icon=ft.icons.BACK_HAND_OUTLINED,
            on_click=ui.direct_kill_screen_render,
        )
        ui.restone_scr = ft.FilledTonalButton(
            text="恢复原有屏幕广播程序", on_click=self.restone_SCR_loj,
            icon=ft.icons.RESTORE_PAGE,
        )
        ui.runwindows_swc = ft.Switch(
            label="Alt+U 运行窗口屏幕广播",
            on_change=lambda _: ui.hotkeyManager.switch_reg_helper(
                ui.runwindows_swc.value, [keyboard.Key.alt_l, 'u'],
                self.run_win_gbcmd_loj,
            ),
            active_color=ui.accent_color,
        )
        ui.KillSCR_swc = ft.Switch(
            label="Alt+K 杀屏幕广播进程",
            on_change=lambda _: ui.hotkeyManager.switch_reg_helper(
                ui.KillSCR_swc.value, [keyboard.Key.alt_l, 'k'],
                ui.direct_kill_screen_render,
            ),
            active_color=ui.accent_color,
        )
        ui.RunFullSC_swc = ft.Switch(
            label="Ctrl+Alt+F 以全屏运行广播命令",
            on_change=lambda _: ui.hotkeyManager.switch_reg_helper(
                ui.RunFullSC_swc.value,
                [keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_vk(70)],
                ui.direct_run_fullscreen_boradcast_cmd,
            ),
            active_color=ui.accent_color,
        )

        return ft.Column([
            ui.yiyanshowtext, ft.Divider(height=1),
            ui.col_readme_dig, ui.replace_status,
            ui.tihuan_scr, ui.try_read_sharecmd, ui.RunFullSC_btn,
            ui.KillSCR_btn, ui.restone_scr,
            ui.runwindows_swc, ui.KillSCR_swc, ui.RunFullSC_swc,
        ])

    # ---- 回调 ----

    def run_win_gbcmd_loj(self, *e):
        ui = self.ui
        get = from_log_file_get_remote_cmd()
        if get is None:
            ui.show_snakemessage("未拦截到控制命令参数")
        else:
            bcmd = build_run_broadcast_cmd(YC_command=get)
            bcmd = bcmd.replace("#fullscreen#:1", "#fullscreen#:0")
            run_sigle_cmd(bcmd)

    def replace_SCR_loj(self, *e):
        ui = self.ui
        if_is_high_ver_client_auto_close_mmpc_helper()
        time.sleep(1)
        ui.show_snakemessage("开始替换程序 请稍等...\n这大约需要6秒左右")
        status = replace_screen_render()
        if not status:
            ui.show_snakemessage("替换拦截程序失败 未检测到可替换程序\n请确保ScreenRender_Helper.exe\n与工具箱处在同一目录")
        else:
            ui.show_snakemessage("理论上已经成功替换拦截程序\n可自行检查替换结果")

    def restone_SCR_loj(self, *e):
        ui = self.ui
        if_is_high_ver_client_auto_close_mmpc_helper()
        time.sleep(1)
        ui.show_snakemessage("开始还原替换程序 请稍等...")
        status = restone_screen_render()
        if not status:
            ui.show_snakemessage("尝试恢复拦截程序时失败\n未检测到被重命名的ScreenRender.exe")
        else:
            ui.show_snakemessage("理论上已经成功恢复原有程序")

    def update_replace_status(self, *e):
        ui = self.ui
        if check_replace_screen_render_status():
            ui.show_snakemessage("检测到目录下已有ScreenRender_Y.exe")
            ui.replace_status.value = "已替换"
        else:
            ui.show_snakemessage("未检测到ScreenRender_Y.exe\n也许未执行替换或替换过程被打断")
            ui.replace_status.value = "未替换"
        ui.page.update()