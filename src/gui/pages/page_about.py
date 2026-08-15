# src/gui/pages/page_about.py
# 关于页（页面 6）

import os

import flet as ft

from config import BUILD_DATE
from src.core.helpers import open_github_page


_PRIV_METHOD_LABELS = {
    "bypass_fodhelper": "提权方式: Fodhelper 注册表绕过 (静默)",
    "bypass_eventvwr": "提权方式: Eventvwr 注册表绕过 (静默备选)",
    "uac_dialog": "提权方式: UAC 弹窗确认",
    "manifest": "提权方式: 应用清单 (manifest) / 已为管理员",
}


def _get_admin_status() -> tuple[str, str, str | None]:
    """获取当前管理员权限状态，返回 (状态文本, 图标, 提权方式文本或None)"""
    try:
        from src.utils.system.uac_elevator import is_admin
        admin = is_admin()
    except Exception:
        return ("未知权限", ft.Icons.HELP_OUTLINE, None)

    if admin:
        method = os.environ.get("OSEASY_PRIV_METHOD", "")
        method_label = _PRIV_METHOD_LABELS.get(method, f"提权方式: 未知 ({method})") if method else "提权方式: 未知"
        return ("当前权限：管理员", ft.Icons.ADMIN_PANEL_SETTINGS, method_label)
    else:
        return ("当前权限：普通用户", ft.Icons.PERSON_OUTLINE, None)


class PageAbout:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        admin_label, admin_icon, extra = _get_admin_status()

        controls = [
            ft.Text(ui.release_name, size=22),
            ft.ElevatedButton("GitHub", icon=ft.Icons.CODE, on_click=open_github_page, tooltip="在浏览器中打开项目GitHub页面"),
            ft.Divider(height=8),
            ft.Row([
                ft.Icon(admin_icon, size=18, color="#4CAF50" if "管理员" in admin_label else "#FF9800"),
                ft.Text(admin_label, size=16),
            ]),
        ]

        if extra is not None:
            controls.append(ft.Text(extra, size=14, color="#888888"))
        elif "普通用户" in admin_label:
            controls.append(
                ft.Text(
                    "纳尼？你是以普通用户身份运行的？劳资的提权方案失效了？快去 GitHub 上提 issues 吧！",
                    size=13,
                    color="#FF9800",
                )
            )

        if BUILD_DATE:
            controls.append(ft.Text(f"构建日期：{BUILD_DATE}", size=13, color="#888888"))

        controls.append(ft.Text("愿我们的电脑课都不再无聊~🥳", size=14, color="#888888"))
        return ft.Column(controls=controls)