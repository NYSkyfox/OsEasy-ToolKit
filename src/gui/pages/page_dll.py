# src/gui/pages/page_dll.py
# DLL 工具页（页面 4）

import ctypes
from ctypes import wintypes
import tkinter as tk
from tkinter import ttk

from src.modules.dll_manager import run_easy_dll, easy_dll
from src.core.settings import toolkit_cfg


class PageDll:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # ---- 上部：控件（可滚动） ----
        _, ctrl_frame = ui.make_scrollable(frame)

        usb_frame = ttk.LabelFrame(ctrl_frame, text="USB 管控", padding=5)
        usb_frame.pack(fill=tk.X, pady=2)
        btn1 = ttk.Button(usb_frame, text="关闭USB管控",
                   command=lambda: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_StopWorking", ctypes.c_int, [], None)
                   )
        btn1.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn1, "FUNC_DLL_USB_STOP")
        btn2 = ttk.Button(usb_frame, text="启动USB管控",
                   command=lambda: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_StartWorking", ctypes.c_int, [], None)
                   )
        btn2.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn2, "FUNC_DLL_USB_START")

        net_frame = ttk.LabelFrame(ctrl_frame, text="网络管控", padding=5)
        net_frame.pack(fill=tk.X, pady=2)
        btn3 = ttk.Button(net_frame, text="开启网络管控",
                   command=lambda: run_easy_dll("\\x64\\OeNetlimit.dll", "DisableInternet", ctypes.c_int, [], None)
                   )
        btn3.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn3, "FUNC_DLL_NET_ENABLE")
        btn4 = ttk.Button(net_frame, text="关闭网络管控",
                   command=lambda: run_easy_dll("\\x64\\OeNetlimit.dll", "EnableNet", ctypes.c_int, [], None)
                   )
        btn4.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn4, "FUNC_DLL_NET_DISABLE")

        query_frame = ttk.Frame(ctrl_frame)
        query_frame.pack(fill=tk.X, pady=2)
        btn5 = ttk.Button(query_frame, text="查询管控状态",
                   command=self._query_status)
        btn5.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn5, "FUNC_DLL_QUERY")

        # ---- 下部：输出区域（固定底部） ----
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.output_text = ui.make_output_text(output_frame, height=5)

        return frame

    def _query_status(self):
        ui = self.ui
        self.ui.clear_text(self.output_text)
        self.ui.append_text(self.output_text, "正在查询管控状态...", ui.root)
        msgs = []

        dll_path = toolkit_cfg.oseasy_path + "\\x64\\easyusbctrl.dll"
        try:
            dll_loader = easy_dll(dll_path)
            runner = dll_loader.setup_function(
                "EasyUsb_IsWorking", restype=ctypes.c_int, argtypes=[ctypes.POINTER(wintypes.DWORD)],
            )
            buf = wintypes.DWORD(0)
            result = runner(buf)
            msgs.append(f"USB管控: 返回值 {result}, 输出参数 {buf.value}")
            if result != 0:
                msgs.append(f"  -> 错误: {dll_loader.get_error_message(result)}")
        except Exception as e:
            msgs.append(f"USB管控查询异常: {e}")

        try:
            import subprocess
            # 不弹控制台窗口（避免打包为无控制台 exe 时闪现黑框）
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            result = subprocess.run(["sc", "query", "OeNetLimit"], capture_output=True, text=True, creationflags=flags)
            running = "RUNNING" in result.stdout
            msgs.append(f"网络管控(OeNetLimit): {'已启用' if running else '未运行'}")
        except Exception as e:
            msgs.append(f"网络管控查询异常: {e}")

        for m in msgs:
            self.ui.append_text(self.output_text, m, ui.root)