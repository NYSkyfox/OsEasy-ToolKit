# src/gui/pages/page_settings.py
# 设置页（页面 5）

import os

import flet as ft

from src.core.helpers import del_historyrem
from src.utils.program.persistent_switch import PersistentSwitch


class PageSettings:

    def __init__(self, ui):
        self.ui = ui

    def _open_reset_dlg(self, *e):
        self.ui.page.dialog = self._reset_dlg
        self._reset_dlg.open = True
        self.ui.page.update()

    def _close_reset_dlg(self, confirm):
        self._reset_dlg.open = False
        self.ui.page.update()
        if confirm:
            self._do_reset()

    def _do_reset(self):
        """重置工具箱：清除外观设置 + 配置文件 + IFEO劫持 + 清理日志 + 删除已生成脚本"""
        ui = self.ui
        # 1. 清理数据文件
        del_historyrem()
        from src.core.runtime_config import toolkit_cfg
        try:
            os.remove(toolkit_cfg.config_file_path)
        except FileNotFoundError:
            pass
        toolkit_cfg._data_cache = None  # 清空内存缓存，强制下次重读
        from src.utils.system.ifeo import remove_ifeo_debugger
        for exe in ("sethc.exe", "shutdown.exe", "Student.exe"):
            remove_ifeo_debugger(exe)
        from src.modules.file_handler import del_self_cmd_files
        del_self_cmd_files()
        from src.core.constants import log_dir_path
        import glob
        for f in glob.glob(os.path.join(log_dir_path, "*.log")):
            try:
                os.remove(f)
            except OSError:
                pass
        # 2. 热重载 UI 状态到默认值
        ui.loaded_bg = False
        ui.bgtmd = 0.6
        ui.bgpath = ""
        ui.yiyanfpath = ""
        ui.zdy_fontpath = ""
        ui.font_loadtime = 1
        ui.random_yy_enabled = False
        ui.follow_system_accent = True
        ui.theme_mode_key = "system"
        from src.utils.system.win_utils import get_windows_accent_color
        ui.accent_color = get_windows_accent_color()
        ui.set_theme_mode()
        ui.pick_a_random_yiyan()
        toolkit_cfg.set_config_key_data("theme_mode", "system")
        # 3. 刷新界面
        from config import DEFAULT_ACCENT_COLOR
        ui.page.theme = ui.page.theme.__class__(
            font_family=ui.page.theme.font_family,
            color_scheme_seed=ui.accent_color,
        )
        ui.page.theme_mode = ft.ThemeMode.SYSTEM if hasattr(ft.ThemeMode, "SYSTEM") else ft.ThemeMode.LIGHT
        ui.selPages_Helper(int(ui.NowSelIndex))
        ui.show_snakemessage("工具箱已重置，设置已恢复默认值")

    def build(self):
        ui = self.ui

        self._reset_dlg = ft.AlertDialog(
            modal=True, title=ft.Text("重置工具箱设置"),
            content=ft.Text(
                "将清除以下内容：\n"
                "  • 外观设置（背景/字体/一言）\n"
                "  • 配置文件 (config.json)\n"
                "  • IFEO 注册表劫持项\n"
                "  • 所有已生成的脚本 (.bat/.ps1)\n"
                "  • 所有日志文件 (.log)\n\n"
                "下次启动恢复默认设置。"
            ),
            actions=[
                ft.TextButton("确认重置", on_click=lambda _: self._close_reset_dlg(True)),
                ft.TextButton("取消", on_click=lambda _: self._close_reset_dlg(False)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        ui.bgfilepick = ft.ElevatedButton(
            "切换背景图片",
            icon=ft.icons.UPLOAD_FILE,
            on_click=lambda _: ui.pick_files_dialog.pick_files(
                allow_multiple=False, file_type="IMAGE"
            ),
            tooltip="选择一张图片作为工具箱背景",
        )
        ui.zitibtn = ft.ElevatedButton(
            "更换显示字体",
            icon=ft.icons.UPLOAD_SHARP,
            on_click=lambda _: ui.font_pick_files_dialog.pick_files(
                allow_multiple=False, allowed_extensions=["ttf"]
            ),
            tooltip="选择TTF字体文件替换工具箱显示字体",
        )
        ui.yiyanbtn = ft.ElevatedButton(
            "加载外部一言文件",
            icon=ft.icons.UPLOAD_SHARP,
            on_click=lambda _: ui.yiyan_pick_files_dialog.pick_files(
                allow_multiple=False, allowed_extensions=["txt"]
            ),
            tooltip="加载TXT文件作为自定义一言列表（每行一句）",
        )
        ui.random_yiyan_swc = PersistentSwitch(
            config_key="random_yiyan_enabled",
            label="随机一言",
            on_toggle=ui.toggle_random_yiyan,
        )
        ui.remove_rem = ft.ElevatedButton(
            "重置工具箱设置",
            icon=ft.icons.DELETE_OUTLINE,
            on_click=self._open_reset_dlg,
            tooltip="清除外观设置、删除日志文件和已生成的脚本",
        )
        ui.theme_dropdown = ft.Dropdown(
            label="主题模式",
            value=ui.theme_mode_key,
            on_change=ui.set_theme_mode,
            options=[
                ft.dropdown.Option("system", "跟随系统"),
                ft.dropdown.Option("light", "浅色模式"),
                ft.dropdown.Option("dark", "深色模式"),
            ],
        )
        ui.system_accent_swc = PersistentSwitch(
            config_key="follow_system_accent",
            label="系统主题颜色",
            default_value=True,
            on_toggle=ui.toggle_system_accent,
        )
        ui.bgtmd_text = ft.Text("滑动以调整背景图片不透明度")
        ui.bgtmdb = ft.Slider(
            min=0.0, max=1.0, divisions=0.1, value=ui.bgtmd,
            on_change_end=ui.change_bg_btmd, disabled=not ui.loaded_bg,
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ui.theme_dropdown, ui.system_accent_swc, ui.random_yiyan_swc, ui.remove_rem, ui.zitibtn,
            ui.bgfilepick, ui.bgtmd_text, ui.bgtmdb, ui.yiyanbtn,
            ui.hide_tbox_swc,
        ])