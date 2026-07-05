# src/gui/app.py
# 工具箱主 UI 类 — 框架 + 通用方法

import os
import time
import random

import flet as ft
from pynput import keyboard

from config import APP_VERSION, DEFAULT_FONT_PATH, DEFAULT_YIYAN_LIST, DEFAULT_SHOW_YIYAN, DEFAULT_ACCENT_COLOR

from src.core.runtime_config import toolbox_cfg
from src.core.helpers import pass_ui_class, run_sigle_cmd
from src.modules.service_manager import try_guess_student_client_version
from src.modules.process_manager import utils
from src.modules.broadcast_handler import (
    from_log_file_get_remote_cmd, build_run_broadcast_cmd,
)
from src.modules.killer import del_locked_exe_then_logout
from src.gui.hotkey_manager import hotkey_manager
from src.gui.pages import (
    PageProcess, PageOther, PageBroadcast, PageCommands,
    PageDll, PageAppearance, PageAbout,
)
from src.utils.win_utils import get_windows_accent_color

fontpath = DEFAULT_FONT_PATH


class Ui:

    def __init__(self) -> None:
        self.ver = APP_VERSION
        self.hotkeyManager = hotkey_manager()
        self.guaqi_runstatus = False
        self.bgtmd = 0.6
        self.defult_yy = True
        self.random_yy_enabled = False
        self.follow_system_accent = True  # 默认跟随系统主题色
        self.accent_color = get_windows_accent_color()
        self.font_loadtime = 1
        self.NowSelIndex = "0"
        self.yiyanshowtext = ft.Text("", size=16)
        self.yiyanshowtext2 = ft.Text("", size=16)
        self.loaded_bg = False

    # ============================================================
    #  页面无关的通用回调
    # ============================================================

    def direct_run_fullscreen_boradcast_cmd(self):
        status = from_log_file_get_remote_cmd()
        if self.KillSCR_swc.value:
            if status is None:
                self.show_snakemessage("未拦截到控制命令参数")
            else:
                cmd = status.replace("#fullscreen#:0", "#fullscreen#:1")
                run_sigle_cmd(build_run_broadcast_cmd(cmd))
        else:
            self.show_snakemessage("警告！ 未开启快捷键杀广播进程\n尝试运行的操作已拦截....")

    def direct_kill_screen_render(self, *e):
        run_sigle_cmd("taskkill /f /t /im ScreenRender_Y.exe")
        run_sigle_cmd("taskkill /f /t /im ScreenRender.exe")

    def theme_changed(self, *e):
        self.page.theme_mode = (
            ft.ThemeMode.DARK if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self.ztqhb.label = (
            "亮色主题" if self.page.theme_mode == ft.ThemeMode.LIGHT else "暗色主题"
        )
        self.page.update()

    def close_askdel_dlg(self, xueze):
        self.unlock_func_askdlg.open = False
        self.page.update()
        if xueze is None:
            self.show_snakemessage("取消解锁了")
        else:
            del_locked_exe_then_logout(xueze)

    def open_askdel_dlg(self, *e):
        self.page.dialog = self.unlock_func_askdlg
        self.unlock_func_askdlg.open = True
        self.page.update()

    def close_col_readme_dlg(self):
        self.col_readme_dlg.open = False
        self.show_snakemessage("Have Fun")
        self.page.update()

    def open_col_readme_dlg(self, *e):
        self.page.dialog = self.col_readme_dlg
        self.col_readme_dlg.open = True
        self.page.update()

    def hide_toolbox_helper(self):
        self.page.window_visible = not self.page.window_visible
        self.page.update()

    # ============================================================
    #  主入口
    # ============================================================

    def main(self, bruh: ft.Page):
        self.page = bruh
        self.page.title = self.ver
        self.page.fonts = {"ht": fontpath}
        self.page.theme = ft.Theme(font_family="ht")
        self.page.window_height = 635
        self.page.window_width = 450
        self.page.window_max_height = 2000
        self.page.window_max_width = 455
        self.page.window_min_height = 620
        self.page.window_min_width = 449
        self.page.update()

        # ---- 共享组件 ----

        self.pick_files_dialog = ft.FilePicker(on_result=self.pick_files_result)
        self.yiyan_pick_files_dialog = ft.FilePicker(on_result=self.yiyan_pick_files_result)
        self.font_pick_files_dialog = ft.FilePicker(on_result=self.font_pick_files_result)
        self.list_all_pickdialog = [self.pick_files_dialog, self.yiyan_pick_files_dialog, self.font_pick_files_dialog]

        self.unlock_func_askdlg = ft.AlertDialog(
            modal=True, title=ft.Text("解锁选项"),
            content=ft.Text("选择适合你的选项\n三者一起: 删除黑屏安静+解除键盘锁+删除控屏锁定程序 (需要注销)\n仅控屏: 仅删除控屏锁定程序"),
            actions=[
                ft.TextButton("三者一起", on_click=lambda _: self.close_askdel_dlg(xueze=True)),
                ft.TextButton("仅控屏锁定程序", on_click=lambda _: self.close_askdel_dlg(xueze=False)),
                ft.TextButton("取消", on_click=lambda _: self.close_askdel_dlg(xueze=None)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.col_readme_dlg = ft.AlertDialog(
            modal=True, title=ft.Text("控屏管理页使用说明"),
            content=ft.Text("在使用前请先使用解锁键盘锁&删除控制锁定软件功能\n点击替换拦截程序后再恢复控屏软件\n等待老师控制屏幕后即完成拦截远程命令\n完成替换后即可重新删除控屏软件\n此时当老师处于控制状态时你可以主动运行命令弹出窗口化共享屏幕\n实现自由的同时不影响听课!!\n当老师来时你可以使用快捷键启动全屏参数的控制\n等待老师走后再用快捷键清理进程"),
            actions=[ft.TextButton("晓得了", on_click=lambda _: self.close_col_readme_dlg())],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda _: self.close_col_readme_dlg(),
        )

        self.col_readme_dig = ft.FilledButton("点我查看此页面的使用说明", on_click=self.open_col_readme_dlg)

        self.hide_tbox_swc = ft.Switch(
            label="capsLock + enter 隐&显工具箱",
            on_change=lambda _: self.hotkeyManager.switch_reg_helper(
                self.hide_tbox_swc.value,
                [keyboard.Key.caps_lock, keyboard.Key.enter],
                ToolBox.hide_toolbox_helper,
            ),
            value=True,
            active_color=self.accent_color,
        )

        # ---- 页面实例 ----

        self._pages = [
            PageProcess(self),
            PageOther(self),
            PageBroadcast(self),
            PageCommands(self),
            PageDll(self),
            PageAppearance(self),
            PageAbout(self),
        ]

        # ---- 导航栏 ----

        self.MyRail = ft.NavigationRail(
            selected_index=0, label_type="ALL", min_width=30, min_extended_width=30,
            group_alignment=-0.8, expand=False,
            destinations=[
                ft.NavigationRailDestination(icon_content=ft.Icon(ft.icons.AUTO_FIX_HIGH_OUTLINED), selected_icon_content=ft.Icon(ft.icons.AUTO_FIX_HIGH), label="进程管理"),
                ft.NavigationRailDestination(icon=ft.icons.INTEGRATION_INSTRUCTIONS_OUTLINED, selected_icon_content=ft.Icon(ft.icons.INTEGRATION_INSTRUCTIONS), label_content=ft.Text("其他管理")),
                ft.NavigationRailDestination(icon=ft.icons.SCREEN_SHARE_OUTLINED, selected_icon_content=ft.Icon(ft.icons.SCREEN_SHARE_SHARP), label_content=ft.Text("广播管理")),
                ft.NavigationRailDestination(icon=ft.icons.VPN_KEY_OUTLINED, selected_icon_content=ft.Icon(ft.icons.VPN_KEY), label="广播命令"),
                ft.NavigationRailDestination(icon=ft.icons.KEYBOARD_OPTION_KEY_OUTLINED, selected_icon_content=ft.Icon(ft.icons.KEYBOARD_OPTION_KEY), label="DLL工具"),
                ft.NavigationRailDestination(icon=ft.icons.STYLE_OUTLINED, selected_icon_content=ft.Icon(ft.icons.STYLE), label_content=ft.Text("外观")),
                ft.NavigationRailDestination(icon=ft.icons.FAVORITE_BORDER_OUTLINED, selected_icon_content=ft.Icon(ft.icons.FAVORITE, color="red"), label="关于"),
            ],
            on_change=lambda e: self.selPages_Helper(e.control.selected_index),
        )

        # ---- 启动 ----
        self.pick_a_random_yiyan()
        self.selPages_Helper(0)
        self.added_pickdialog()
        self.try_get_history_path()
        self.reflashStudentPath()
        pass_ui_class(self)
        self.hotkeyManager.switch_reg_helper(
            self.hide_tbox_swc.value,
            [keyboard.Key.caps_lock, keyboard.Key.enter],
            ToolBox.hide_toolbox_helper,
        )

    # ============================================================
    #  页面切换
    # ============================================================

    def selPages_Helper(self, index):
        self.NowSelIndex = str(index)
        self.pick_a_random_yiyan()
        page = self._pages[index]
        self.apply_bg_to_ui(page.build())
        if index == 5:
            self.added_pickdialog()

    def apply_bg_to_ui(self, needLoad_Stuff_list):
        if self.loaded_bg:
            bgb = ft.Stack(controls=[self.col_imgbg, needLoad_Stuff_list])
            nedadd = ft.Row([self.MyRail, ft.VerticalDivider(width=0), bgb],
                            height=self.page.window_height, width=self.page.window_width)
        else:
            nedadd = ft.Row([self.MyRail, ft.VerticalDivider(width=1), needLoad_Stuff_list],
                            height=self.page.window_height, width=self.page.window_width)
        self.page.clean()
        self.page.update()
        self.page.add(nedadd)
        self.page.update()

    # ============================================================
    #  学生端相关
    # ============================================================

    def reflashStudentPath(self, *e):
        _ = try_guess_student_client_version()
        if toolbox_cfg.oseasypath_have_been_modified:
            guess_msg = f"猜测的学生端版本 v{_ / 10}" if _ != 0 else '检测学生端版本特征失败'
            self.show_snakemessage(f"更新学生端路径成功\n{toolbox_cfg.oseasy_path}\n学生端进程名:{toolbox_cfg.student_exe_name}\n{guess_msg}")
        else:
            self.show_snakemessage("更新路径失败\n也许是学生端未运行??")

    def guaqi_chufa(self, *e):
        if not self.guaqi_runstatus:
            self.page.window_visible = False
            self.page.update()
            status = utils.guaqi_process(toolbox_cfg.student_exe_name)
            utils.guaqi_process("MultiClient.exe")
            if status is True:
                self.guaqi_runstatus = True
                time.sleep(0.8)
                self.page.window_visible = True
                self.page.update()
            else:
                self.page.window_visible = True
                self.guaqi_sw.value = False
                self.page.update()
                self.show_snakemessage(status)
        else:
            status = utils.huifu_process(toolbox_cfg.student_exe_name)
            utils.huifu_process("MultiClient.exe")
            if status is True:
                self.guaqi_runstatus = False
            else:
                self.guaqi_sw.value = False
                self.page.update()
                self.show_snakemessage(status)

    # ============================================================
    #  外观 / 一言
    # ============================================================

    def try_get_history_path(self):
        fstst = toolbox_cfg.first_launch_check()
        if not fstst:
            bgPath = toolbox_cfg.get_style_path("bgPath")
            if bgPath:
                self.bgpath = bgPath
                self.loaded_bg = True
                self.reflash_ui_bg()
            yiyanPath = toolbox_cfg.get_style_path("yiyanPath")
            if yiyanPath:
                self.yiyanfpath = yiyanPath
                self.from_file_load_yiyan()
            fontPath = toolbox_cfg.get_style_path("fontPath")
            if fontPath:
                self.zdy_fontpath = fontPath
                self.setup_zidingyi_font()

    def reflash_ui_bg(self):
        toolbox_cfg.set_style_path("bgPath", self.bgpath)
        self.loaded_bg = True
        self.col_imgbg = ft.Image(
            src=self.bgpath, height=self.page.window_height,
            width=self.page.window_width - 100, opacity=self.bgtmd,
            fit=ft.ImageFit.SCALE_DOWN,
        )
        self.selPages_Helper(int(self.NowSelIndex))

    def change_bg_btmd(self, e):
        self.bgtmd = e.control.value
        self.reflash_ui_bg()

    def toggle_system_accent(self, e=None):
        """开关系统主题色跟随"""
        if e:
            self.follow_system_accent = e.control.value
        if self.follow_system_accent:
            self.accent_color = get_windows_accent_color()
        else:
            self.accent_color = DEFAULT_ACCENT_COLOR
        # 刷新当前页面重建控件
        self.selPages_Helper(int(self.NowSelIndex))

    def toggle_random_yiyan(self, e=None):
        if e:
            self.random_yy_enabled = e.control.value
        self.pick_a_random_yiyan()

    def pick_a_random_yiyan(self, *e):
        if self.random_yy_enabled:
            if hasattr(self, "yiyanlist") and self.yiyanlist:
                pickindex = random.randint(0, len(self.yiyanlist) - 1)
                self.yiyanshowtext.value = self.yiyanlist[pickindex]
                self.yiyanshowtext2.value = self.yiyanlist[pickindex]
            else:
                pickindex = random.randint(0, len(DEFAULT_YIYAN_LIST) - 1)
                self.yiyanshowtext.value = DEFAULT_YIYAN_LIST[pickindex]
                self.yiyanshowtext2.value = DEFAULT_YIYAN_LIST[pickindex]
        else:
            self.yiyanshowtext.value = DEFAULT_SHOW_YIYAN
            self.yiyanshowtext2.value = DEFAULT_SHOW_YIYAN
        self.page.update()

    def from_file_load_yiyan(self):
        toolbox_cfg.set_style_path("yiyanPath", self.yiyanfpath)
        try:
            with open(self.yiyanfpath, "r", encoding="utf-8") as fm:
                list_get = fm.read().split("^")
            self.ex_fullindex = len(list_get)
            self.yiyanlist = list_get
            self.defult_yy = False
            self.show_snakemessage("成功加载外部一言库")
        except Exception as e:
            self.show_snakemessage(f"加载外部一言时出现{e}异常")

    def setup_zidingyi_font(self):
        toolbox_cfg.set_style_path("fontPath", self.zdy_fontpath)
        self.font_loadtime += 1
        if 10 >= self.font_loadtime > 2:
            old = self.font_loadtime - 1
            del self.page.fonts[f"zidingyi{old}"]
        elif self.font_loadtime > 10:
            old = self.font_loadtime - 1
            del self.page.fonts[f"zidingyi{old}"]
            self.font_loadtime = 3
        self.page.fonts.update({f"zidingyi{self.font_loadtime}": self.zdy_fontpath})
        self.page.theme = ft.Theme(font_family=f"zidingyi{self.font_loadtime}")
        self.page.update()
        if self.loaded_bg:
            self.reflash_ui_bg()

    # ============================================================
    #  FilePicker 回调
    # ============================================================

    def pick_files_result(self, e):
        try:
            self.bgpath = os.path.join(e.files[0].path)
            self.reflash_ui_bg()
        except TypeError:
            self.show_snakemessage("未选择背景图片")

    def yiyan_pick_files_result(self, e):
        try:
            self.yiyanfpath = os.path.join(e.files[0].path)
            self.from_file_load_yiyan()
        except TypeError:
            self.show_snakemessage("未选择一言文件")

    def font_pick_files_result(self, e):
        try:
            self.zdy_fontpath = os.path.join(e.files[0].path)
            self.setup_zidingyi_font()
        except TypeError:
            self.show_snakemessage("未选择字体文件")

    # ============================================================
    #  通用工具
    # ============================================================

    def show_snakemessage(self, showtext: str):
        self.page.snack_bar = ft.SnackBar(ft.Text(showtext))
        self.page.snack_bar.open = True
        self.page.update()

    def added_pickdialog(self):
        for idlg in self.list_all_pickdialog:
            self.page.add(idlg)
            self.page.update()


ToolBox = Ui()