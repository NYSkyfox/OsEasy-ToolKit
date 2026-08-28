# src/gui/pages/page_overview.py
# 概览页（页面 0）—— 显示工具箱和系统的大致状态

import tkinter as tk
from tkinter import ttk

from src.core.settings import toolkit_cfg
from src.modules.service_manager import query_service_state
from src.utils.process import is_process_running


class PageOverview:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)
        self._frame = frame

        # 可滚动容器，按需显示滚动条
        _, scroll_frame = ui.make_scrollable(frame)

        # ---- 状态信息 ----
        status_frame = ttk.LabelFrame(scroll_frame, text="工具箱状态", padding=8)
        status_frame.pack(fill=tk.X, padx=5, pady=2)
        status_frame.columnconfigure(1, weight=1)

        ttk.Label(status_frame, text="版本", width=12, anchor=tk.W).grid(
            row=0, column=0, sticky=tk.W, padx=(0, 6), pady=2)
        ttk.Label(status_frame, text=ui.release_name, anchor=tk.W).grid(
            row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(status_frame, text="学生端路径", width=12, anchor=tk.W).grid(
            row=1, column=0, sticky=tk.W, padx=(0, 6), pady=2)
        self.student_path_var = tk.StringVar(value=toolkit_cfg.oseasy_path)
        ttk.Label(status_frame, textvariable=self.student_path_var, anchor=tk.W).grid(
            row=1, column=1, sticky=tk.W, pady=2)

        ttk.Label(status_frame, text="学生端进程", width=12, anchor=tk.W).grid(
            row=2, column=0, sticky=tk.W, padx=(0, 6), pady=2)
        self.student_exe_var = tk.StringVar(value=toolkit_cfg.student_exe_name)
        ttk.Label(status_frame, textvariable=self.student_exe_var, anchor=tk.W).grid(
            row=2, column=1, sticky=tk.W, pady=2)

        ttk.Label(status_frame, text="学生端版本", width=12, anchor=tk.W).grid(
            row=3, column=0, sticky=tk.W, padx=(0, 6), pady=2)
        self.student_ver_var = tk.StringVar(value="检测中...")
        self.student_ver_lbl = ttk.Label(status_frame, textvariable=self.student_ver_var,
                                         anchor=tk.W, foreground="gray")
        self.student_ver_lbl.grid(row=3, column=1, sticky=tk.W, pady=2)
        self._student_ver_ok = None

        self.update_student_info()

        # ---- 服务 + 进程 并排双列 ----
        svc_proc_row = ttk.Frame(scroll_frame)
        svc_proc_row.pack(fill=tk.X, padx=5, pady=2)
        svc_proc_row.columnconfigure(0, weight=1, uniform="svcproc")
        svc_proc_row.columnconfigure(1, weight=1, uniform="svcproc")

        self.svc_frame = ttk.LabelFrame(svc_proc_row, text="学生端服务", padding=8)
        self.svc_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        self.proc_frame = ttk.LabelFrame(svc_proc_row, text="学生端进程", padding=8)
        self.proc_frame.grid(row=0, column=1, sticky="nsew", padx=(2, 0))

        self._svc_labels = {}
        self._proc_labels = {}
        self._build_live_status()

        refresh_btn = ttk.Button(scroll_frame, text="刷新状态", command=self._refresh)
        refresh_btn.pack(pady=10)
        ui.bind_tooltip(refresh_btn, "FUNC_OVERVIEW_REFRESH")

        # 首次刷新延迟到 UI 就绪后（避免阻塞窗口显示）
        self.ui.root.after(50, self._refresh)

        # 每 3 秒自动刷新（仅当概览页可见时生效）
        self._after_id = None
        self._start_auto_refresh()

        return frame

    def _is_visible(self) -> bool:
        """当前概览页是否显示在标签页中"""
        try:
            nb = self.ui.notebook
            return nb.index(nb.select()) == nb.index(self._frame)
        except Exception:
            return False

    def _start_auto_refresh(self):
        """重新调度 3 秒后的自动刷新"""
        try:
            self._after_id = self.ui.root.after(3000, self._on_auto_refresh)
        except Exception:
            pass

    def _on_auto_refresh(self):
        """定时刷新：仅当概览页可见时才执行检测，然后继续调度"""
        if self._is_visible():
            try:
                self._refresh()
            except Exception:
                pass
        self._start_auto_refresh()

    def _build_live_status(self):
        # 学生端服务（可检测的 Windows 服务/驱动）—— 双列网格
        services = [
            ("mmpc", "MMPC"),
            ("netlimit", "OeNetLimit"),
            ("usbflt", "easyusbflt"),
            ("kbfilter", "KbFilter"),
            ("pcfw", "ProcFireWall"),
            ("fbdats", "FbdATS"),
        ]
        self._build_status_rows(self.svc_frame, services, self._svc_labels)

        # 学生端进程 —— 双列网格
        processes = [
            ("student_exe", None),  # 动态：使用版本检测到的 student_exe_name
            ("multi_client", "MultiClient.exe"),
            ("blacksilent", "BlackSlient.exe"),
            ("device_ctl", "DeviceControl_x64.exe"),
            ("screen_render", "ScreenRender.exe"),
            ("lisshelper", "LissHelper.exe"),
        ]
        self._student_exe_name_lbl = None
        self._build_status_rows(self.proc_frame, processes, self._proc_labels)

    def _build_status_rows(self, parent, items, label_store):
        """在父容器内构建三列 grid 状态行：名称 | 圆点 | 状态。

        所有行共享同一套列（名称列 / 圆点列 / 状态列），三种行自动对齐。
        """
        # 三列：名称、圆点、状态。名称列宽度自动取最宽项，状态列占满剩余宽度
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=0)
        parent.columnconfigure(2, weight=1)

        for i, (key, name_or_exe) in enumerate(items):
            name = toolkit_cfg.student_exe_name if name_or_exe is None else name_or_exe

            # 名称列（左对齐）
            name_lbl = ttk.Label(parent, text=name, anchor=tk.W, padding=(4, 1))
            name_lbl.grid(row=i, column=0, sticky=tk.W, padx=(2, 4))

            # 圆点列（固定宽，居中）
            dot_lbl = ttk.Label(parent, text="○", foreground="gray", width=2)
            dot_lbl.grid(row=i, column=1, sticky=tk.W)

            # 状态列（靠右对齐）
            status_lbl = ttk.Label(parent, text="检测中...", foreground="gray", anchor=tk.E)
            status_lbl.grid(row=i, column=2, sticky=tk.E, padx=(2, 0))

            if key == "student_exe":
                self._student_exe_name_lbl = name_lbl

            label_store[key] = status_lbl
            # 给圆点赋予引用，方便 _set_*_status 更新颜色
            label_store.setdefault("__dot__", {})[key] = dot_lbl

    def _set_svc_status(self, key, state):
        """state: 'running'/'stopped'/'missing'"""
        lbl = self._svc_labels.get(key)
        if not lbl:
            return
        dot = self._svc_labels.get("__dot__", {}).get(key)
        if state == "running":
            lbl.configure(text="运行中", foreground="green")
            if dot:
                dot.configure(text="●", foreground="green")
        elif state == "stopped":
            lbl.configure(text="未运行", foreground="orange")
            if dot:
                dot.configure(text="○", foreground="orange")
        else:
            lbl.configure(text="不存在", foreground="gray")
            if dot:
                dot.configure(text="○", foreground="gray")

    def _set_proc_status(self, key, running):
        lbl = self._proc_labels.get(key)
        if not lbl:
            return
        dot = self._proc_labels.get("__dot__", {}).get(key)
        if running:
            lbl.configure(text="运行中", foreground="green")
            if dot:
                dot.configure(text="●", foreground="green")
        else:
            lbl.configure(text="未运行", foreground="orange")
            if dot:
                dot.configure(text="○", foreground="orange")

    def update_student_info(self):
        """刷新学生端路径 / 进程名 / 版本（由 ui.reflashStudentPath 调用）"""
        self.student_path_var.set(toolkit_cfg.oseasy_path)
        self.student_exe_var.set(toolkit_cfg.student_exe_name)
        ver = getattr(toolkit_cfg, "student_version", 0)
        ver_str = getattr(toolkit_cfg, "student_version_str", "") or ""
        if ver:
            if ver_str:
                text, color = f"学生端版本：V{ver_str}", "green"
            else:
                text, color = f"学生端版本：v{ver / 10}", "green"
        else:
            text, color = "学生端版本：检测失败（学生端未运行或未知版本）", "red"
        self.student_ver_var.set(text)
        if self.student_ver_lbl:
            self.student_ver_lbl.configure(foreground=color)

        # 同步更新“学生端进程”分组里的动态进程行标签（Student.exe → 版本检测结果）
        name_lbl = getattr(self, "_student_exe_name_lbl", None)
        if name_lbl is not None:
            name_lbl.configure(text=toolkit_cfg.student_exe_name)

    def _refresh(self):
        ui = self.ui

        # ---- 学生端服务 ----
        svc_list = [
            ("mmpc", "MMPC"),
            ("netlimit", "OeNetLimit"),
            ("usbflt", "easyusbflt"),
            ("kbfilter", "KbFilter"),
            ("pcfw", "ProcFireWall"),
            ("fbdats", "FbdATS"),
        ]
        for key, name in svc_list:
            try:
                self._set_svc_status(key, query_service_state(name))
            except Exception:
                self._set_svc_status(key, "missing")

        # ---- 学生端进程 ----
        proc_list = [
            ("student_exe", toolkit_cfg.student_exe_name),  # 动态：版本检测到的进程名
            ("multi_client", "MultiClient.exe"),
            ("blacksilent", "BlackSlient.exe"),
            ("device_ctl", "DeviceControl_x64.exe"),
            ("screen_render", "ScreenRender.exe"),
            ("lisshelper", "LissHelper.exe"),
        ]
        for key, exe in proc_list:
            try:
                self._set_proc_status(key, is_process_running(exe))
            except Exception:
                self._set_proc_status(key, False)