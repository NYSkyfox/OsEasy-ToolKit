# src/gui/pages/page_dll.py
# DLL 工具页（页面 4）

import ctypes
from ctypes import wintypes

import flet as ft

from src.modules.dll_manager import run_easy_dll


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
            text="执行:查询USB管控状态",
            on_click=lambda _: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_IsWorking", ctypes.c_int, [ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD(0)),
            icon=ft.icons.CODE,
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