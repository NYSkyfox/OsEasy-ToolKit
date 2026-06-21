"""
页面基类 - 所有页面的抽象基类
"""

import tkinter as tk
from tkinter import ttk
from abc import ABC, abstractmethod


class BasePage(ABC, tk.Frame):
    """
    页面基类

    所有功能页面都继承此类，实现 create_widgets 和 refresh 方法
    """

    def __init__(self, parent, app, **kwargs):
        """
        Args:
            parent: 父容器
            app: ToolKitTk 主应用实例
            **kwargs: 其他参数
        """
        super().__init__(parent, **kwargs)
        self.app = app
        # 所有页面都需要的核心服务
        self.student = app.student_service
        self.broadcast = app.broadcast_service
        self.unlock = app.unlock_service

        # 创建页面内容
        self.create_widgets()

    @abstractmethod
    def create_widgets(self) -> None:
        """
        创建页面控件
        子类必须实现此方法
        """
        pass

    def refresh(self) -> None:
        """
        刷新页面状态
        子类可重写此方法以更新动态内容
        """
        pass

    def show_status(self, message: str, msg_type: str = "info") -> None:
        """
        显示状态消息

        Args:
            message: 消息内容
            msg_type: 类型 (info, success, warning, error)
        """
        self.app.show_status(message, msg_type)

    def create_card(self, parent, title: str = None) -> ttk.LabelFrame:
        """
        创建卡片式容器（使用 ttk LabelFrame）

        Args:
            parent: 父容器
            title: 卡片标题

        Returns:
            卡片 Frame
        """
        card = ttk.LabelFrame(parent, text=title, padding=10)
        return card

    def create_button(self, parent, text: str, command,
                      style: str = "primary", width: int = 25) -> ttk.Button:
        """
        创建统一风格的按钮

        使用 ttk.Button，风格取自系统主题。
        style 参数仅用于语义区分（上层可参考），实际样式由系统决定。

        Args:
            parent: 父容器
            text: 按钮文字
            command: 点击回调
            style: 语义标记 (primary, danger, success) — 当前统一使用系统默认样式
            width: 宽度

        Returns:
            ttk.Button
        """
        btn = ttk.Button(
            parent,
            text=text,
            command=command,
            width=width,
        )
        return btn

    def create_label(self, parent, text: str,
                    font_size: int = 9, bold: bool = False,
                    fg: str = None) -> ttk.Label:
        """
        创建统一风格的标签

        Args:
            parent: 父容器
            text: 文字内容
            font_size: 字号
            bold: 是否加粗
            fg: 前景色（ttk 下固定为系统色，此参数仅保留兼容）

        Returns:
            ttk.Label
        """
        font = ("Microsoft YaHei", font_size, "bold" if bold else "normal")
        label = ttk.Label(
            parent,
            text=text,
            font=font,
            wraplength=380,
            justify="left"
        )
        return label

    def create_entry(self, parent, placeholder: str = "") -> ttk.Entry:
        """
        创建输入框

        Args:
            parent: 父容器
            placeholder: 占位提示文字

        Returns:
            ttk.Entry
        """
        entry = ttk.Entry(
            parent,
            font=("Microsoft YaHei", 9)
        )

        if placeholder:
            entry.insert(0, placeholder)

            def on_focus_in(event):
                if entry.get() == placeholder:
                    entry.delete(0, tk.END)

            def on_focus_out(event):
                if not entry.get():
                    entry.insert(0, placeholder)

            entry.bind("<FocusIn>", on_focus_in)
            entry.bind("<FocusOut>", on_focus_out)

        return entry