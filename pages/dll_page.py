"""
DLL 工具页面
"""

import tkinter as tk
from tkinter import ttk
from pages.base_page import BasePage


class DllPage(BasePage):
    """DLL 工具页面"""

    def __init__(self, parent, app):
        self.dll = app.dll_service
        super().__init__(parent, app)

    def create_widgets(self) -> None:
        """创建 DLL 工具页面控件"""
        # 一言
        self.yiyan_label = self.create_label(
            self, self.app.get_random_yiyan(),
            font_size=10, bold=True
        )
        self.yiyan_label.pack(pady=(15, 10), padx=20)

        # 分隔线
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=5)

        # USB 管控卡片
        usb_card = self.create_card(self, "USB 管控 (easyusbctrl.dll)")
        usb_card.pack(fill="x", padx=20, pady=10)

        usb_btn_frame = ttk.Frame(usb_card)
        usb_btn_frame.pack(fill="x", pady=5)

        usb_start_btn = self.create_button(
            usb_btn_frame, "启动 USB 管控",
            self._usb_start, "primary", 15
        )
        usb_start_btn.pack(side="left", padx=2)

        usb_stop_btn = self.create_button(
            usb_btn_frame, "停止 USB 管控",
            self._usb_stop, "primary", 15
        )
        usb_stop_btn.pack(side="right", padx=2)

        usb_status_btn = self.create_button(
            usb_card, "查询 USB 管控状态",
            self._usb_status, "primary", 32
        )
        usb_status_btn.pack(pady=5)

        # 网络管控卡片
        net_card = self.create_card(self, "网络管控 (OeNetlimit.dll)")
        net_card.pack(fill="x", padx=20, pady=10)

        net_btn_frame = ttk.Frame(net_card)
        net_btn_frame.pack(fill="x", pady=5)

        net_enable_btn = self.create_button(
            net_btn_frame, "开启网络管控",
            self._net_enable, "primary", 15
        )
        net_enable_btn.pack(side="left", padx=2)

        net_disable_btn = self.create_button(
            net_btn_frame, "关闭网络管控",
            self._net_disable, "primary", 15
        )
        net_disable_btn.pack(side="right", padx=2)

        # 结果展示
        result_card = self.create_card(self, "调用结果")
        result_card.pack(fill="both", expand=True, padx=20, pady=10)

        self.result_text = tk.Text(
            result_card,
            height=8,
            font=("Consolas", 9),
            wrap="word",
            state="disabled"
        )
        self.result_text.pack(fill="both", expand=True, pady=5)
    
    def _show_result(self, text: str) -> None:
        """显示调用结果"""
        self.result_text.config(state="normal")
        self.result_text.delete("1.0", tk.END)
        self.result_text.insert("1.0", text)
        self.result_text.config(state="disabled")
    
    def _usb_start(self) -> None:
        """启动 USB 管控"""
        result = self.dll.usb_start()
        self._show_result(result)
        self.show_status("USB 管控启动命令已发送")
    
    def _usb_stop(self) -> None:
        """停止 USB 管控"""
        result = self.dll.usb_stop()
        self._show_result(result)
        self.show_status("USB 管控停止命令已发送")
    
    def _usb_status(self) -> None:
        """查询 USB 管控状态"""
        result = self.dll.usb_status()
        self._show_result(result)
        self.show_status("USB 管控状态已查询")
    
    def _net_enable(self) -> None:
        """开启网络管控"""
        result = self.dll.net_enable()
        self._show_result(result)
        self.show_status("网络管控已开启")
    
    def _net_disable(self) -> None:
        """关闭网络管控"""
        result = self.dll.net_disable()
        self._show_result(result)
        self.show_status("网络管控已关闭")
    
    def refresh(self) -> None:
        """刷新页面"""
        self.yiyan_label.config(text=self.app.get_random_yiyan())