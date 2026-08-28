# src/gui/pages/page_about.py
# 关于页（页面 6）

import os
import tkinter as tk
from tkinter import ttk

from config import BUILD_DATE
from src.utils.network import open_github_page


_PRIV_METHOD_LABELS = {
    "bypass_fodhelper": "提权方式: Fodhelper 注册表绕过 (静默)",
    "bypass_eventvwr": "提权方式: Eventvwr 注册表绕过 (静默备选)",
    "uac_dialog": "提权方式: UAC 弹窗确认",
    "manifest": "提权方式: 应用清单 (manifest) / 已为管理员",
}


def _get_admin_status() -> tuple[str, str | None]:
    """获取当前管理员权限状态，返回 (状态文本, 提权方式文本或None)"""
    try:
        from src.utils.uac import is_admin
        admin = is_admin()
    except Exception:
        return ("未知权限", None)

    if admin:
        method = os.environ.get("OSEASY_PRIV_METHOD", "")
        method_label = _PRIV_METHOD_LABELS.get(method, f"提权方式: 未知 ({method})") if method else "提权方式: 未知"
        return ("当前权限：管理员", method_label)
    else:
        return ("当前权限：普通用户", None)


class PageAbout:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # 可滚动容器，随窗口自适应
        _, inner = ui.make_scrollable(frame)

        admin_label, extra = _get_admin_status()

        # 标题
        title_frame = ttk.Frame(inner)
        title_frame.pack(fill=tk.X, padx=10, pady=10)
        ttk.Label(title_frame, text=ui.release_name, font=("", 14, "bold")).pack(anchor=tk.W)

        # GitHub
        ttk.Button(inner, text="GitHub", command=open_github_page).pack(anchor=tk.W, padx=10, pady=5)

        ttk.Separator(inner, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=10, pady=5)

        # 权限状态
        admin_color = "green" if "管理员" in admin_label else "orange"
        ttk.Label(inner, text=admin_label, foreground=admin_color).pack(anchor=tk.W, padx=10, pady=2)

        if extra is not None:
            ttk.Label(inner, text=extra, foreground="gray").pack(anchor=tk.W, padx=10, pady=2)
        elif "普通用户" in admin_label:
            ttk.Label(inner,
                      text="纳尼？你是以普通用户身份运行的？劳资的提权方案失效了？快去 GitHub 上提 issues 吧！",
                      foreground="orange").pack(anchor=tk.W, padx=10, pady=2)

        if BUILD_DATE:
            ttk.Label(inner, text=f"构建日期：{BUILD_DATE}", foreground="gray").pack(anchor=tk.W, padx=10, pady=2)

        ttk.Label(inner, text="愿我们的电脑课都不再无聊~🥳", foreground="gray").pack(anchor=tk.W, padx=10, pady=5)

        return frame