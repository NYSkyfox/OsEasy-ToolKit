# src/gui/pages/page_process.py
# 进程管理页（页面 1）

import tkinter as tk
from tkinter import ttk, messagebox
import os

from src.core.settings import toolkit_cfg
from src.modules.killer import (
    launch_oe_toolkit, is_sethc_hijacked, is_killer_protected,
)
from src.modules.power_control import hijack_shutdown, release_shutdown_hijack, is_shutdown_hijacked, is_shutdown_hijacked_by_others
from src.modules.power_control import hijack_student_restart, release_student_hijack, is_student_hijacked
from src.modules.service_manager import handle_start_student_client
from src.gui.switch import PersistentSwitch


class PageProcess:

    def __init__(self, ui):
        self.ui = ui

    def _on_shutdown_toggle(self, e=None):
        if e.value:
            if is_shutdown_hijacked_by_others():
                if messagebox.askyesno("检测到冲突", "似乎有别的程序劫持了该键值，你确定要继续吗？"):
                    hijack_shutdown()
                else:
                    e.value = False
            else:
                hijack_shutdown()
        else:
            release_shutdown_hijack()

    def _on_student_restart_toggle(self, e=None):
        if e.value:
            hijack_student_restart()
        else:
            release_student_hijack()

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # ---- 上部：控件（可滚动） ----
        _, ctrl_frame = ui.make_scrollable(frame)

        proc_frame = ttk.LabelFrame(ctrl_frame, text="进程操作", padding=5)
        proc_frame.pack(fill=tk.X, pady=2)
        btn1 = ttk.Button(proc_frame, text="重启学生端", command=handle_start_student_client)
        btn1.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn1, "FUNC_RESTART_STUDENT")
        btn2 = ttk.Button(proc_frame, text="重新获取学生端路径", command=ui.reflashStudentPath)
        btn2.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn2, "FUNC_REFRESH_STUDENT_PATH")

        switch_frame = ttk.LabelFrame(ctrl_frame, text="功能开关", padding=5)
        switch_frame.pack(fill=tk.X, pady=2)
        ui.sethc_swc = PersistentSwitch(switch_frame, live_getter=is_sethc_hijacked, verifier=is_sethc_hijacked,
                                         label="劫持粘滞键 (sethc.exe)", on_toggle=ui._on_sethc_toggle)
        ui.sethc_swc.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.sethc_swc, "FUNC_HIJACK_SETHC")
        ui.protect_swc = PersistentSwitch(switch_frame, config_key="protect_killer_enabled",
                                           label="循环杀死学生端", verifier=is_killer_protected,
                                           on_toggle=ui._on_protect_killer_changed)
        ui.protect_swc.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.protect_swc, "FUNC_PROTECT_KILLER")
        ui.guaqi_sw = PersistentSwitch(switch_frame, config_key="guaqi_enabled",
                                        label="挂起学生端", on_toggle=ui._on_guaqi_changed)
        ui.guaqi_sw.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.guaqi_sw, "FUNC_SUSPEND_STUDENT")

        # 防护（从原"其他管理"页移入）
        protect_frame = ttk.LabelFrame(ctrl_frame, text="防护", padding=5)
        protect_frame.pack(fill=tk.X, pady=2)
        sw1 = PersistentSwitch(protect_frame,
                               label="拦截教师端远程关机 (劫持shutdown.exe)",
                               live_getter=is_shutdown_hijacked, verifier=is_shutdown_hijacked,
                               on_toggle=self._on_shutdown_toggle)
        sw1.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(sw1, "FUNC_HIJACK_SHUTDOWN")
        sw2 = PersistentSwitch(protect_frame,
                               label="拦截教师端远程重启 (摘Student关机权限)（请勿尝试，暂不可用）",
                               live_getter=is_student_hijacked, verifier=is_student_hijacked,
                               on_toggle=self._on_student_restart_toggle)
        sw2.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(sw2, "FUNC_HIJACK_RESTART")

        quick_frame = ttk.LabelFrame(ctrl_frame, text="快捷操作", padding=5)
        quick_frame.pack(fill=tk.X, pady=2)
        btn3 = ttk.Button(quick_frame, text="打开噢易自带工具", command=launch_oe_toolkit)
        btn3.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn3, "FUNC_LAUNCH_OE_TOOLKIT")
        btn4 = ttk.Button(quick_frame, text="打开OsEasy安装目录", command=self.open_oseasy_dir)
        btn4.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn4, "FUNC_OPEN_OE_DIR")
        btn5 = ttk.Button(quick_frame, text="打开ToolKit数据文件夹", command=self.open_toolkit_data_dir)
        btn5.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn5, "FUNC_OPEN_DATA_DIR")

        # ---- 下部：输出区域（固定底部） ----
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.output_text = ui.make_output_text(output_frame, height=5)

        return frame

    def open_oseasy_dir(self, *e):
        path = toolkit_cfg.oseasy_path
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.ui.show_snakemessage(f"目录不存在: {path}")

    def open_toolkit_data_dir(self, *e):
        from config import DATA_ROOT_TEMPLATE
        path = DATA_ROOT_TEMPLATE.format(username=os.environ.get('USERNAME', 'Default'))
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.ui.show_snakemessage(f"目录不存在: {path}")