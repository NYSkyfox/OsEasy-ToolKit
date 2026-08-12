# src/gui/pages/page_dll.py
# DLL 工具页（页面 4）

import ctypes
from ctypes import wintypes

import flet as ft

from src.modules.dll_manager import run_easy_dll, easy_dll
from src.core.runtime_config import toolkit_cfg
from src.core.helpers import show_snack


def query_all_control_status():
    """同时查询 USB 和网络管控状态并汇总显示"""
    msgs = []

    # ---- USB 管控 ----
    dll_path = toolkit_cfg.oseasy_path + "\\x64\\easyusbctrl.dll"
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
    try:
        from src.core.helpers import run_sigle_cmd
        import subprocess
        result = subprocess.run(
            ["sc", "query", "OeNetLimit"],
            capture_output=True, text=True,
        )
        running = "RUNNING" in result.stdout
        msgs.append(f"网络管控(OeNetLimit): {'已启用' if running else '未运行'}")
    except Exception as e:
        msgs.append(f"网络管控查询异常: {e}")

    show_snack("\n".join(msgs))


class PageDll:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui

        ui.dll_usb_1 = ft.FilledTonalButton(
            text="关闭USB管控",
            on_click=lambda _: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_StopWorking", ctypes.c_int, [], None),
            icon=ft.icons.USB,
            tooltip="调用easyusbctrl.dll停止USB管控功能",
        )
        ui.dll_usb_2 = ft.FilledTonalButton(
            text="启动USB管控",
            on_click=lambda _: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_StartWorking", ctypes.c_int, [], None),
            icon=ft.icons.USB_OFF,
            tooltip="调用easyusbctrl.dll启动USB管控功能",
        )
        ui.dll_usb_3 = ft.FilledTonalButton(
            text="查询管控状态",
            on_click=lambda _: query_all_control_status(),
            icon=ft.icons.QUERY_STATS,
            tooltip="查询USB管控和网络管控的当前启用状态",
        )
        ui.dll_net_1 = ft.FilledTonalButton(
            text="开启网络管控",
            on_click=lambda _: run_easy_dll("\\x64\\OeNetlimit.dll", "DisableInternet", ctypes.c_int, [], None),
            icon=ft.icons.SIGNAL_WIFI_CONNECTED_NO_INTERNET_4,
            tooltip="调用OeNetlimit.dll开启网络管控限制",
        )
        ui.dll_net_2 = ft.FilledTonalButton(
            text="关闭网络管控",
            on_click=lambda _: run_easy_dll("\\x64\\OeNetlimit.dll", "EnableNet", ctypes.c_int, [], None),
            icon=ft.icons.SIGNAL_WIFI_4_BAR,
            tooltip="调用OeNetlimit.dll关闭网络管控限制",
        )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ui.dll_usb_1, ui.dll_usb_2, ui.dll_usb_3,
            ui.dll_net_1, ui.dll_net_2,
        ])