# src/gui/pages/page_service.py
# 服务管理页 —— 查看/启停学生端相关 Windows 服务与驱动

import tkinter as tk
from tkinter import ttk

from src.modules.service_manager import (
    query_service_state, start_service, stop_service,
    stop_service_detailed, get_service_info, force_stop_driver,
)


class PageService:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # 可滚动内容区
        _, ctrl_frame = ui.make_scrollable(frame)

        # ---- 服务列表 ----
        svc_frame = ttk.LabelFrame(ctrl_frame, text="学生端相关服务", padding=5)
        svc_frame.pack(fill=tk.X, pady=2)

        # 服务名 -> (显示名, 状态标签, 状态变量)
        self._svc_rows = {}
        services = [
            ("MMPC", "噢易多媒体根服务"),
            ("OeNetLimit", "网络管控"),
            ("easyusbflt", "USB 过滤驱动"),
            ("KbFilter", "键盘过滤驱动"),
            ("ProcFireWall", "进程防火墙"),
            ("FbdATS", "文件系统过滤驱动(目录保护)"),
        ]
        for name, desc in services:
            row = ttk.Frame(svc_frame)
            row.pack(fill=tk.X, pady=2)
            row.columnconfigure(1, weight=1)  # 描述列可伸缩，撑满剩余空间

            name_lbl = ttk.Label(row, text=name, width=14, anchor=tk.W)
            name_lbl.grid(row=0, column=0, sticky=tk.W, padx=(2, 4))
            desc_lbl = ttk.Label(row, text=desc, foreground="gray", anchor=tk.W)
            desc_lbl.grid(row=0, column=1, sticky=tk.W, padx=(0, 6))

            status_var = tk.StringVar(value="未知")
            status_lbl = ttk.Label(row, textvariable=status_var, width=6, anchor=tk.CENTER)
            status_lbl.grid(row=0, column=2, sticky=tk.E, padx=(0, 6))

            # 单个操作按钮：根据状态显示“启动”或“停止”
            action_btn = ttk.Button(row, text="启动", width=6, command=lambda n=name: self._toggle_service(n, False))
            action_btn.grid(row=0, column=3, padx=2, sticky=tk.E)

            self._svc_rows[name] = {
                "status_var": status_var,
                "status_lbl": status_lbl,
                "action_btn": action_btn,
            }

        # ---- 操作按钮 ----
        op_frame = ttk.Frame(ctrl_frame)
        op_frame.pack(fill=tk.X, pady=4)
        refresh_btn = ttk.Button(op_frame, text="刷新状态", command=self._refresh)
        refresh_btn.pack(side=tk.LEFT, padx=2)
        ui.bind_tooltip(refresh_btn, "FUNC_SVC_REFRESH")

        # ---- 输出区域 ----
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.output_text = ui.make_output_text(output_frame, height=5)

        # 初始刷新
        self._refresh()

        return frame

    def _toggle_service(self, name: str, start: bool):
        """启动/停止指定服务（原生 SCM API，不弹窗口），并刷新状态"""
        if start:
            ok = start_service(name)
            self.ui.append_text(self.output_text, f"启动服务 {name}: {'成功' if ok else '失败'}", self.ui.root)
        else:
            self._stop_service(name)
        self._refresh()

    def _stop_service(self, name: str):
        """停止服务；对不接受停止控制的内核驱动自动降级为强制卸载（删除服务+清理注册表）"""
        ok, msg = stop_service_detailed(name)
        if ok:
            self.ui.append_text(self.output_text, f"停止服务 {name}: 成功", self.ui.root)
            return

        # 普通停止失败 → 判断是否内核驱动
        is_driver = False
        try:
            info = get_service_info(name)
            is_driver = info.get("type") in ("kernel_driver", "file_system_driver") if info.get("exists") else False
        except Exception:
            pass

        if is_driver:
            self.ui.append_text(
                self.output_text,
                f"停止 {name}: {msg}\n该服务是内核驱动，普通停止无效，正在强制卸载（删除服务+清理注册表过滤项）...",
                self.ui.root,
            )
            for line in force_stop_driver(name):
                self.ui.append_text(self.output_text, f"  {line}", self.ui.root)
        else:
            self.ui.append_text(self.output_text, f"停止服务 {name}: {msg}", self.ui.root)

    def _refresh(self):
        """刷新所有服务状态（运行中/未运行/不存在），并根据状态显示对应的操作按钮"""
        for name, row in self._svc_rows.items():
            try:
                state = query_service_state(name)
            except Exception:
                state = "missing"
            status_var = row["status_var"]
            status_lbl = row["status_lbl"]
            action_btn = row["action_btn"]

            if state == "running":
                status_var.set("运行中")
                status_lbl.configure(foreground="green")
                action_btn.configure(text="停止", state=tk.NORMAL,
                                     command=lambda n=name: self._toggle_service(n, False))
            elif state == "stopped":
                status_var.set("未运行")
                status_lbl.configure(foreground="red")
                action_btn.configure(text="启动", state=tk.NORMAL,
                                     command=lambda n=name: self._toggle_service(n, True))
            else:  # missing
                status_var.set("不存在")
                status_lbl.configure(foreground="gray")
                action_btn.configure(text="启动", state=tk.DISABLED,
                                     command=lambda n=name: self._toggle_service(n, True))
