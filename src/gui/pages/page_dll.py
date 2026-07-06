# src/gui/pages/page_dll.py
# DLL 工具页（页面 4）

import ctypes
from ctypes import wintypes

import flet as ft

from src.modules.dll_manager import run_easy_dll, easy_dll
from src.core.runtime_config import toolbox_cfg
from src.core.helpers import Ui_call_show_snake_message


def query_all_control_status():
    """同时查询 USB 和网络管控状态并汇总显示"""
    msgs = []

    # ---- USB 管控 ----
    dll_path = toolbox_cfg.oseasy_path + "\\x64\\easyusbctrl.dll"
    try:
        dll_loader = easy_dll(dll_path)
        runner = dll_loader.setup_function(
            "EasyUsb_IsWorking",
            restype=ctypes.c_int,
            argtypes=[ctypes.POINTER(wintypes.DWORD)],
        )
        buf = wintypes.DWORD(0)
        result = runner(buf)
        msgs.append(f"USB管控: 返回值 {result}, 输出参数 {buf.value}")
        if result != 0:
            msgs.append(f"  → 错误: {dll_loader.get_error_message(result)}")
    except Exception as e:
        msgs.append(f"USB管控查询异常: {e}")

    # ---- 网络管控 ----
    dll_path = toolbox_cfg.oseasy_path + "\\x64\\OeNetlimit.dll"
    try:
        dll_loader = easy_dll(dll_path)
        runner = dll_loader.setup_function("EnableNet", restype=ctypes.c_int, argtypes=[])
        result = runner()
        msgs.append(f"网络管控(EnableNet): 返回值 {result}")
        if result != 0:
            msgs.append(f"  → 错误: {dll_loader.get_error_message(result)}")
    except Exception as e:
        msgs.append(f"网络管控查询异常: {e}")

    Ui_call_show_snake_message("\n".join(msgs))


class PageDll:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        ui.dll_usb_1 = ft.FilledTonalButton(
            text="执行:关闭USB管控",
            on_click=lambda _: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_StopWorking", ctypes.c_int, [], None),
            icon=ft.icons.USB,
        )
        ui.dll_usb_2 = ft.FilledTonalButton(
            text="执行:启动USB管控",
            on_click=lambda _: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_StartWorking", ctypes.c_int, [], None),
            icon=ft.icons.USB_OFF,
        )
        ui.dll_usb_3 = ft.FilledTonalButton(
            text="查询管控状态(USB+网络)",
            on_click=lambda _: query_all_control_status(),
            icon=ft.icons.QUERY_STATS,
        )
        ui.dll_net_1 = ft.FilledTonalButton(
            text="执行:开启网络管控",
            on_click=lambda _: run_easy_dll("\\x64\\OeNetlimit.dll", "DisableInternet", ctypes.c_int, [], None),
            icon=ft.icons.SIGNAL_WIFI_CONNECTED_NO_INTERNET_4,
        )
        ui.dll_net_2 = ft.FilledTonalButton(
            text="执行:关闭网络管控",
            on_click=lambda _: run_easy_dll("\\x64\\OeNetlimit.dll", "EnableNet", ctypes.c_int, [], None),
            icon=ft.icons.SIGNAL_WIFI_4_BAR,
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ui.dll_usb_1, ui.dll_usb_2, ui.dll_usb_3,
            ui.dll_net_1, ui.dll_net_2,
        ])