# src/gui/pages/page_appearance.py
# 外观页（页面 5）

import os

import flet as ft

from src.core.helpers import del_historyrem
from src.core.runtime_config import toolbox_cfg


class PageAppearance:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        ui.bgfilepick = ft.ElevatedButton(
            "切换背景图片",
            icon=ft.icons.UPLOAD_FILE,
            on_click=lambda _: ui.pick_files_dialog.pick_files(
                allow_multiple=False, file_type="IMAGE"
            ),
        )
        ui.zitibtn = ft.ElevatedButton(
            "更换显示字体",
            icon=ft.icons.UPLOAD_SHARP,
            on_click=lambda _: ui.font_pick_files_dialog.pick_files(
                allow_multiple=False, allowed_extensions=["ttf"]
            ),
        )
        ui.yiyanbtn = ft.ElevatedButton(
            "加载外部一言文件",
            icon=ft.icons.UPLOAD_SHARP,
            on_click=lambda _: ui.yiyan_pick_files_dialog.pick_files(
                allow_multiple=False, allowed_extensions=["txt"]
            ),
        )
        ui.random_yiyan_swc = ft.Switch(
            label="随机一言",
            on_change=ui.toggle_random_yiyan,
            value=ui.random_yy_enabled,
        )
        ui.remove_rem = ft.ElevatedButton(
            "清除历史路径记忆",
            icon=ft.icons.DELETE_OUTLINE,
            on_click=del_historyrem,
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
        ui.system_accent_swc = ft.Switch(
            label="系统主题颜色",
            on_change=ui.toggle_system_accent,
            value=ui.follow_system_accent,
        )
        ui.bgtmd_text = ft.Text("滑动以调整背景图片不透明度")
        ui.bgtmdb = ft.Slider(
            min=0.0, max=1.0, divisions=0.1, value=ui.bgtmd,
            on_change_end=ui.change_bg_btmd, disabled=not ui.loaded_bg,
            active_color=ui.accent_color,
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ui.theme_dropdown, ui.system_accent_swc, ui.random_yiyan_swc, ui.remove_rem, ui.zitibtn,
            ui.bgfilepick, ui.bgtmd_text, ui.bgtmdb, ui.yiyanbtn,
        ])