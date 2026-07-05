# src/gui/pages/page_about.py
# 关于页（页面 6）

import flet as ft

from src.core.helpers import open_github_page


class PageAbout:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        return ft.Column(controls=[
            ft.Text("此工具箱在Github上发布", size=22),
            ft.Text("愿我们的电脑课都不再无聊~🥳", size=22),
            ft.ElevatedButton("点我打开工具箱Github页", on_click=open_github_page),
            ui.hide_tbox_swc,
        ])