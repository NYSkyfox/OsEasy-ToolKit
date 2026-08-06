# src/gui/app.py
# 工具箱主 UI 类 — 框架 + 通用方法

import os
import time
import random

import flet as ft
from pynput import keyboard

from config import APP_VERSION, RELEASE_NAME, DEFAULT_YIYAN_LIST, DEFAULT_SHOW_YIYAN, DEFAULT_ACCENT_COLOR

from src.core.runtime_config import toolkit_cfg
from src.core.helpers import pass_ui_class, run_sigle_cmd
from src.modules.service_manager import detect_student_version
from src.modules.process_manager import utils, get_scshot

from src.modules.broadcast_handler import (
    from_log_file_get_remote_cmd, build_run_broadcast_cmd,
)

from src.gui.hotkey_manager import hotkey_manager
from src.utils.program.persistent_switch import PersistentSwitch
from src.gui.pages import (
    PageProcess, PageOther, PageBroadcast, PageCommands,
    PageDll, PageSettings, PageAbout,
)
from src.utils.system.win_utils import get_windows_accent_color, get_windows_default_font

# 配置文件中保存的设置 key 名
_SETTING_KEYS = {
    "theme_mode": "theme_mode",
    "follow_system_accent": "follow_system_accent",
    "random_yiyan": "random_yiyan_enabled",
    "bg_opacity": "bg_opacity",
    "hide_tbox": "hide_tbox_hotkey",
    "fast_screenshot": "fast_screenshot_hotkey",
    "run_window_broadcast": "run_window_broadcast_hotkey",
    "kill_screen_render": "kill_screen_render_hotkey",
    "run_fullscreen_broadcast": "run_fullscreen_broadcast_hotkey",
    "guaqi": "guaqi_enabled",
    "protect_killer": "protect_killer_enabled",
}

fontpath = get_windows_default_font()


class Ui:

    def __init__(self) -> None:
        self.ver = APP_VERSION
        self.release_name = RELEASE_NAME
        self.hotkeyManager = hotkey_manager()
        self.guaqi_runstatus = False
        self.bgtmd = 0.6
        self.defult_yy = True
        self.random_yy_enabled = False
        self.follow_system_accent = True  # 默认跟随系统主题色
        self.accent_color = get_windows_accent_color()
        self.theme_mode_key = "system"
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
        if getattr(self, 'KillSCR_swc', None) is None:
            self.show_snakemessage("请先打开广播管理页再使用此功能")
            return
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

    def update_theme(self, font_family=None):
        if font_family is None:
            font_family = getattr(self.page.theme, "font_family", "ht")
        self.page.theme = ft.Theme(
            font_family=font_family,
            color_scheme_seed=self.accent_color,
        )

    def hide_toolkit_helper(self):
        self.page.window_visible = not self.page.window_visible
        self.page.update()

    def _on_hide_tbox_changed(self):
        self.hotkeyManager.switch_reg_helper(
            self.hide_tbox_swc.value, [keyboard.Key.caps_lock, keyboard.Key.enter],
            self.hide_toolkit_helper,
        )

    def _on_fast_screenshot_changed(self):
        self.hotkeyManager.switch_reg_helper(
            self.FastGetSC.value, [keyboard.Key.alt_l, 'x'], get_scshot,
        )

    def _on_run_window_broadcast_changed(self):
        self.hotkeyManager.switch_reg_helper(
            self.runwindows_swc.value, [keyboard.Key.alt_l, 'u'],
            self._pages[2].run_win_gbcmd_loj,
        )

    def _on_kill_screen_render_changed(self):
        self.hotkeyManager.switch_reg_helper(
            self.KillSCR_swc.value, [keyboard.Key.alt_l, 'k'],
            self.direct_kill_screen_render,
        )

    def _on_run_fullscreen_broadcast_changed(self):
        self.hotkeyManager.switch_reg_helper(
            self.RunFullSC_swc.value,
            [keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_vk(70)],
            self.direct_run_fullscreen_boradcast_cmd,
        )

    # ============================================================
    #  主入口
    # ============================================================

    def main(self, bruh: ft.Page):
        self.page = bruh
        self.page.title = self.release_name
        self.page.fonts = {"ht": fontpath}
        self.page.theme = ft.Theme(
            font_family="ht",
            color_scheme_seed=self.accent_color,
        )
        self.page.theme_mode = ft.ThemeMode.SYSTEM if hasattr(ft.ThemeMode, "SYSTEM") else ft.ThemeMode.LIGHT
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

        self.hide_tbox_swc = PersistentSwitch(
            config_key=_SETTING_KEYS["hide_tbox"],
            label="capsLock + enter 隐&显工具箱",
            on_toggle=lambda _: self._on_hide_tbox_changed(),
        )

        self.FastGetSC = PersistentSwitch(
            config_key=_SETTING_KEYS["fast_screenshot"],
            label="Alt+X 快捷键屏幕截图",
            on_toggle=lambda _: self._on_fast_screenshot_changed(),
        )

        # ---- 页面实例 ----

        self._pages = [
            PageProcess(self),
            PageOther(self),
            PageBroadcast(self),
            PageCommands(self),
            PageDll(self),
            PageSettings(self),
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
                ft.NavigationRailDestination(icon=ft.icons.SETTINGS_OUTLINED, selected_icon_content=ft.Icon(ft.icons.SETTINGS), label_content=ft.Text("设置")),
                ft.NavigationRailDestination(icon=ft.icons.FAVORITE_BORDER_OUTLINED, selected_icon_content=ft.Icon(ft.icons.FAVORITE, color="red"), label="关于"),
            ],
            on_change=lambda e: self.selPages_Helper(e.control.selected_index),
        )

        # ---- 启动 ----
        self.pick_a_random_yiyan()
        self.selPages_Helper(0)
        self.added_pickdialog()
        self.try_get_history_path()
        self.try_restore_settings()
        self.reflashStudentPath()
        pass_ui_class(self)

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
        self.page.controls = [nedadd]
        self.page.update()

    # ============================================================
    #  学生端相关
    # ============================================================

    def reflashStudentPath(self, *e):
        _ = detect_student_version()
        if toolkit_cfg.oseasypath_have_been_modified:
            guess_msg = f"猜测的学生端版本 v{_ / 10}" if _ != 0 else '检测学生端版本特征失败'
            self.show_snakemessage(f"更新学生端路径成功\n{toolkit_cfg.oseasy_path}\n学生端进程名:{toolkit_cfg.student_exe_name}\n{guess_msg}")
        else:
            self.show_snakemessage("更新路径失败\n也许是学生端未运行??")

    def _on_guaqi_changed(self, *e):
        """挂起学生端开关变更"""
        self.guaqi_chufa()

    def _on_protect_killer_changed(self, *e):
        """外部cmd守护进程开关变更"""
        from src.modules.killer import killer_script_protect
        killer_script_protect()

    def _on_sethc_toggle(self, *e):
        """粘滞键劫持开关"""
        from src.modules.killer import register_killer_script, del_register_killer
        if self.sethc_swc.value:
            register_killer_script()
        else:
            del_register_killer()

    def guaqi_chufa(self, *e):
        if not self.guaqi_runstatus:
            self.page.window_visible = False
            self.page.update()
            status = utils.guaqi_process(toolkit_cfg.student_exe_name)
            utils.guaqi_process("MultiClient.exe")
            if status is True:
                self.guaqi_runstatus = True
                time.sleep(0.8)
                self.page.window_visible = True
                self.page.update()
            else:
                self.page.window_visible = True
                self.guaqi_runstatus = False
                toolkit_cfg.set_config_key_data(_SETTING_KEYS["guaqi"], False)
                self.guaqi_sw.value = False
                self.page.update()
                self.show_snakemessage(status)
        else:
            status = utils.huifu_process(toolkit_cfg.student_exe_name)
            utils.huifu_process("MultiClient.exe")
            if status is True:
                self.guaqi_runstatus = False
                toolkit_cfg.set_config_key_data(_SETTING_KEYS["guaqi"], False)
            else:
                self.guaqi_runstatus = True
                toolkit_cfg.set_config_key_data(_SETTING_KEYS["guaqi"], True)
                self.guaqi_sw.value = True
                self.page.update()
                self.show_snakemessage(status)

    # ============================================================
    #  外观 / 一言
    # ============================================================

    def try_get_history_path(self):
        fstst = toolkit_cfg.first_launch_check()
        if not fstst:
            bgPath = toolkit_cfg.get_style_path("bgPath")
            if bgPath:
                self.bgpath = bgPath
                self.loaded_bg = True
                self.reflash_ui_bg()
            yiyanPath = toolkit_cfg.get_style_path("yiyanPath")
            if yiyanPath:
                self.yiyanfpath = yiyanPath
                self.from_file_load_yiyan()
            fontPath = toolkit_cfg.get_style_path("fontPath")
            if fontPath:
                self.zdy_fontpath = fontPath
                self.setup_zidingyi_font()

    def try_restore_settings(self):
        """从配置文件恢复用户设置状态"""
        # 主题模式
        saved_theme = toolkit_cfg.get_config_key_data(_SETTING_KEYS["theme_mode"])
        if saved_theme in ("system", "light", "dark"):
            self.theme_mode_key = saved_theme
            self.set_theme_mode()
            if hasattr(self, "theme_dropdown"):
                self.theme_dropdown.value = saved_theme

        # 系统主题色跟随
        saved_accent = toolkit_cfg.get_config_key_data(_SETTING_KEYS["follow_system_accent"])
        if saved_accent is not None:
            self.follow_system_accent = bool(saved_accent)
            if not self.follow_system_accent:
                self.accent_color = DEFAULT_ACCENT_COLOR
            self.update_theme()

        # 随机一言
        saved_yy = toolkit_cfg.get_config_key_data(_SETTING_KEYS["random_yiyan"])
        if saved_yy is not None:
            self.random_yy_enabled = bool(saved_yy)
            self.pick_a_random_yiyan()

        # 背景不透明度
        saved_opacity = toolkit_cfg.get_config_key_data(_SETTING_KEYS["bg_opacity"])
        if saved_opacity is not None:
            try:
                self.bgtmd = float(saved_opacity)
            except (TypeError, ValueError):
                pass

        # 挂起学生端状态
        saved_guaqi = toolkit_cfg.get_config_key_data(_SETTING_KEYS["guaqi"])
        if saved_guaqi is not None:
            self.guaqi_runstatus = bool(saved_guaqi)

        # 初始注册快捷键（根据恢复后的状态）
        self.hotkeyManager.switch_reg_helper(
            self.hide_tbox_swc.value,
            [keyboard.Key.caps_lock, keyboard.Key.enter],
            self.hide_toolkit_helper,
        )
        self.hotkeyManager.switch_reg_helper(
            self.FastGetSC.value, [keyboard.Key.alt_l, 'x'], get_scshot,
        )

        # 广播页的快捷键在 page_broadcast.build() 中恢复（此时控件尚未创建）

    def _restore_broadcast_hotkeys(self):
        """广播页快捷键初始注册（首次 build 时调用一次）"""
        if getattr(self, '_broadcast_hotkeys_restored', False):
            return
        self._broadcast_hotkeys_restored = True
        self.hotkeyManager.switch_reg_helper(
            self.runwindows_swc.value,
            [keyboard.Key.alt_l, 'u'],
            self._pages[2].run_win_gbcmd_loj,
        )
        self.hotkeyManager.switch_reg_helper(
            self.KillSCR_swc.value,
            [keyboard.Key.alt_l, 'k'],
            self.direct_kill_screen_render,
        )
        self.hotkeyManager.switch_reg_helper(
            self.RunFullSC_swc.value,
            [keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_vk(70)],
            self.direct_run_fullscreen_boradcast_cmd,
        )

    def reflash_ui_bg(self):
        toolkit_cfg.set_style_path("bgPath", self.bgpath)
        self.loaded_bg = True
        self.col_imgbg = ft.Image(
            src=self.bgpath, height=self.page.window_height,
            width=self.page.window_width - 100, opacity=self.bgtmd,
            fit=ft.ImageFit.SCALE_DOWN,
        )
        self.selPages_Helper(int(self.NowSelIndex))

    def change_bg_btmd(self, e):
        self.bgtmd = e.control.value
        toolkit_cfg.set_config_key_data(_SETTING_KEYS["bg_opacity"], self.bgtmd)
        self.reflash_ui_bg()

    def toggle_system_accent(self, e=None):
        """开关系统主题色跟随"""
        if e:
            self.follow_system_accent = e.control.value
        if self.follow_system_accent:
            self.accent_color = get_windows_accent_color()
        else:
            self.accent_color = DEFAULT_ACCENT_COLOR
        self.update_theme()
        self.page.update()

    def toggle_random_yiyan(self, e=None):
        if e:
            self.random_yy_enabled = e.control.value
        self.pick_a_random_yiyan()

    def set_theme_mode(self, e=None):
        if e:
            self.theme_mode_key = e.control.value
        toolkit_cfg.set_config_key_data(_SETTING_KEYS["theme_mode"], self.theme_mode_key)
        if self.theme_mode_key == "system":
            self.page.theme_mode = ft.ThemeMode.SYSTEM
        elif self.theme_mode_key == "light":
            self.page.theme_mode = ft.ThemeMode.LIGHT
        else:
            self.page.theme_mode = ft.ThemeMode.DARK
        self.page.update()

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
        toolkit_cfg.set_style_path("yiyanPath", self.yiyanfpath)
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
        toolkit_cfg.set_style_path("fontPath", self.zdy_fontpath)
        self.font_loadtime += 1
        if 10 >= self.font_loadtime > 2:
            old = self.font_loadtime - 1
            del self.page.fonts[f"zidingyi{old}"]
        elif self.font_loadtime > 10:
            old = self.font_loadtime - 1
            del self.page.fonts[f"zidingyi{old}"]
            self.font_loadtime = 3
        self.page.fonts.update({f"zidingyi{self.font_loadtime}": self.zdy_fontpath})
        self.update_theme(font_family=f"zidingyi{self.font_loadtime}")
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


ToolKit = Ui()