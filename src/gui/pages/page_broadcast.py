# src/gui/pages/page_broadcast.py
# 广播管理页（页面 2）

import time

import flet as ft

from src.core.helpers import run_sigle_cmd
from src.utils.program.hotkey_manager import get_hotkey_label
from src.utils.program.persistent_switch import PersistentSwitch
from src.modules.broadcast_handler import (
    replace_screen_render, restone_screen_render,
    check_replace_screen_render_status,
    force_screenrender_windowed,
)
from src.modules.service_manager import auto_stop_mmpc_if_needed


class PageBroadcast:

    def __init__(self, ui):
        self.ui = ui

    def _close_readme_dlg(self):
        ui = self.ui
        if hasattr(self, '_readme_dlg'):
            self._readme_dlg.open = False
        ui.page.dialog = None
        ui.show_snakemessage("Have Fun")
        ui.page.update()

    def _build_readme_dlg(self):
        return ft.AlertDialog(
            modal=True, title=ft.Text("控屏管理页使用说明"),
            content=ft.Text(
                "在使用前请先使用解锁键盘锁&删除控屏锁定程序功能\n"
                "点击替换拦截程序后再恢复控屏软件\n"
                "等待老师控制屏幕后即完成拦截远程命令\n"
                "完成替换后即可重新删除控屏软件\n"
                "此时当老师处于控制状态时你可以主动运行命令弹出窗口化共享屏幕\n"
                "实现自由的同时不影响听课!!\n"
                "当老师来时你可以使用快捷键启动全屏参数的控制\n"
                "等待老师走后再用快捷键清理进程"
            ),
            actions=[ft.TextButton("晓得了", on_click=lambda _: self._close_readme_dlg())],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda _: self._close_readme_dlg(),
        )

    def _open_readme_dlg(self, *e):
        self._readme_dlg = self._build_readme_dlg()
        self.ui.page.dialog = self._readme_dlg
        self._readme_dlg.open = True
        self.ui.page.update()

    def build(self):
        ui = self.ui

        ui.col_readme_dig = ft.FilledButton(
            "点我查看此页面的使用说明",
            on_click=self._open_readme_dlg,
            tooltip="查看广播管理页的详细使用说明和操作指引",
        )

        ui.replace_status = ft.TextField(
            label="替换程序状态", value="未知 (点我更新状态)",
            read_only=True, on_focus=self.update_replace_status,
            text_align=ft.TextAlign.CENTER,
        )

        ui.tihuan_scr = ft.FilledTonalButton(
            text="替换拦截命令程序", on_click=self.replace_SCR_loj,
            icon=ft.icons.FIND_REPLACE,
            tooltip="用自定义程序替换噢易屏幕广播拦截命令程序",
        )
        ui.try_read_sharecmd = ft.FilledTonalButton(
            text="运行窗口化广播命令", on_click=self.run_win_gbcmd_loj,
            icon=ft.icons.WINDOW_SHARP,
            tooltip="以窗口模式运行教师端屏幕广播命令",
        )
        ui.RunFullSC_btn = ft.FilledTonalButton(
            "运行全屏广播命令",
            on_long_press=lambda _: ui.direct_run_fullscreen_broadcast_cmd(),
            icon=ft.icons.FULLSCREEN,
            tooltip="长按以全屏模式运行教师端屏幕广播命令",
        )
        ui.KillSCR_btn = ft.FilledTonalButton(
            "杀屏幕广播进程", icon=ft.icons.BACK_HAND_OUTLINED,
            on_click=ui.direct_kill_screen_render,
            tooltip="强制结束所有ScreenRender屏幕广播进程",
        )
        ui.restone_scr = ft.FilledTonalButton(
            text="恢复原有屏幕广播程序", on_click=self.restone_SCR_loj,
            icon=ft.icons.RESTORE_PAGE,
            tooltip="恢复被替换的原始屏幕广播程序文件",
        )
        ui.runwindows_swc = PersistentSwitch(
            config_key="run_window_broadcast_hotkey",
            label=get_hotkey_label("run_window_broadcast") + " 运行窗口屏幕广播",
            verifier=lambda: ui.hotkeyManager.is_registered_by_name("run_window_broadcast", self.run_win_gbcmd_loj),
            on_toggle=lambda _: ui._on_run_window_broadcast_changed(),
        )
        ui.KillSCR_swc = PersistentSwitch(
            config_key="kill_screen_render_hotkey",
            label=get_hotkey_label("kill_screen_render") + " 杀屏幕广播进程",
            verifier=lambda: ui.hotkeyManager.is_registered_by_name("kill_screen_render", ui.direct_kill_screen_render),
            on_toggle=lambda _: ui._on_kill_screen_render_changed(),
        )
        ui.RunFullSC_swc = PersistentSwitch(
            config_key="run_fullscreen_broadcast_hotkey",
            label=get_hotkey_label("run_fullscreen_broadcast") + " 运行广播命令",
            verifier=lambda: ui.hotkeyManager.is_registered_by_name("run_fullscreen_broadcast", ui.direct_run_fullscreen_broadcast_cmd),
            on_toggle=lambda _: ui._on_run_fullscreen_broadcast_changed(),
        )

        ui._restore_broadcast_hotkeys()

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
        if force_screenrender_windowed():
            ui.show_snakemessage("已切换为窗口模式")
        else:
            ui.show_snakemessage("未找到广播窗口，可能尚未开始广播")

    def replace_SCR_loj(self, *e):
        ui = self.ui
        auto_stop_mmpc_if_needed()
        time.sleep(1)
        ui.show_snakemessage("开始替换程序 请稍等...\n这大约需要6秒左右")
        status = replace_screen_render()
        if not status:
            ui.show_snakemessage("替换拦截程序失败 未检测到可替换程序\n请确保ScreenRender_Helper.exe\n与工具箱处在同一目录")
        else:
            ui.show_snakemessage("理论上已经成功替换拦截程序\n可自行检查替换结果")

    def restone_SCR_loj(self, *e):
        ui = self.ui
        auto_stop_mmpc_if_needed()
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