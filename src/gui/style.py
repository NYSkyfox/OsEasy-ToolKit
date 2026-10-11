# src/gui/style.py
# ttk 主题配置 —— vista 主题 + 主题色微调
#
# 仅依赖 tkinter，零业务依赖。

import tkinter as tk
from tkinter import ttk


def apply_theme(root: tk.Tk) -> ttk.Style:
    """在 root 上启用 vista 主题并做基础微调，返回 Style 实例。

    主题回退顺序：vista → winnative → xpnative → clam。
    """
    style = ttk.Style(root)
    for t in ("vista", "winnative", "xpnative", "clam"):
        if t in style.theme_names():
            style.theme_use(t)
            break

    # 标签页：内边距 + 去掉点击后的虚线焦点框
    style.configure("TNotebook.Tab", padding=[10, 4])
    style.layout("TNotebook.Tab", [
        ("Notebook.tab", {"sticky": "nswe", "children": [
            ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
                ("Notebook.label", {"side": "top", "sticky": ""}),
            ]}),
        ]}),
    ])
    # 按钮 / 复选框 / 单选框：去掉焦点虚线
    style.configure("TButton", focuscolor="none")
    style.configure("TCheckbutton", focuscolor="none")
    style.configure("TRadiobutton", focuscolor="none")
    # 统一行距
    style.configure("TLabelframe.Label", padding=4)
    return style


def disable_widget_focus(widget) -> None:
    """递归关闭非输入控件的焦点（去掉点击后的虚线焦点框）。"""
    _NO_FOCUS = ("TButton", "TCheckbutton", "TRadiobutton", "Button",
                 "Checkbutton", "Radiobutton", "TSpinbox", "TNotebook")
    try:
        if widget.winfo_class() in _NO_FOCUS:
            try:
                widget.configure(takefocus=0)
            except Exception:
                pass
    except Exception:
        pass
    try:
        for child in widget.winfo_children():
            disable_widget_focus(child)
    except Exception:
        pass