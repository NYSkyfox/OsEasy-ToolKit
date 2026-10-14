# src/gui/pages/page_overview.py
# 主页（页面 0）—— 环境信息 + Patch 状态 + 模块状态 + 快捷入口
#
# 显示：
#   1. 环境：Os-Easy 安装目录（探测结果）
#   2. Patch 目标状态：遍历注册表，显示每个目标文件的指纹 + 各 patch 点状态
#   3. 功能模块：双开 / 截屏（就绪状态）
#   4. 快捷入口：跳转到各功能页 + 刷新

import tkinter as tk
from tkinter import ttk

from config import FEATURE_DESC
from src.core import find_oseasy_dir, resolve_target, PatchEngine, ST_DONE, ST_BAD
from src.patches import ALL_TARGETS
from src.gui.widgets import make_scrollable


class PageOverview:

    def __init__(self, ui):
        self.ui = ui
        self._after_id = None

    # ------------------------------------------------------------
    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)
        self._frame = frame

        _, scroll = make_scrollable(frame)
        self._build_env(scroll)
        self._build_patch_status(scroll)
        self._build_modules(scroll)
        self._build_shortcuts(scroll)

        # 首次刷新
        self.ui.root.after(50, self._refresh)
        return frame

    # ------------------------------------------------------------
    #  环境
    # ------------------------------------------------------------
    def _build_env(self, parent):
        box = ttk.LabelFrame(parent, text="环境信息", padding=8)
        box.pack(fill=tk.X, padx=5, pady=3)
        box.columnconfigure(1, weight=1)

        ttk.Label(box, text="Os-Easy 目录", width=14, anchor=tk.W).grid(
            row=0, column=0, sticky=tk.W, pady=2)
        self.env_dir_var = tk.StringVar(value="探测中...")
        self.env_dir_lbl = ttk.Label(box, textvariable=self.env_dir_var,
                                     anchor=tk.W, foreground="gray")
        self.env_dir_lbl.grid(row=0, column=1, sticky=tk.W, pady=2)

        ttk.Label(box, text="数据目录", width=14, anchor=tk.W).grid(
            row=1, column=0, sticky=tk.W, pady=2)
        from src.core import data_root
        ttk.Label(box, text=data_root, anchor=tk.W, foreground="gray").grid(
            row=1, column=1, sticky=tk.W, pady=2)

    # ------------------------------------------------------------
    #  Patch 目标状态
    # ------------------------------------------------------------
    def _build_patch_status(self, parent):
        box = ttk.LabelFrame(parent, text="Patch 目标状态", padding=8)
        box.pack(fill=tk.X, padx=5, pady=3)
        box.columnconfigure(1, weight=1)

        self._patch_rows = []   # [(target_key, labels...)]
        row = 0
        for t in ALL_TARGETS:
            ttk.Label(box, text=f"{t.name}", width=14, anchor=tk.W,
                      font=("", 9, "bold")).grid(row=row, column=0,
                                                 sticky=tk.NW, pady=(4, 0))
            # 文件状态行
            file_var = tk.StringVar(value="—")
            ttk.Label(box, textvariable=file_var, anchor=tk.W,
                      foreground="gray", font=("", 8)).grid(
                row=row, column=1, sticky=tk.W, pady=(4, 0))
            row += 1
            # 各 patch 点行
            point_vars = {}
            for p in t.patches:
                var = tk.StringVar(value="—")
                ttk.Label(box, text=f"  · {p.label}", anchor=tk.W,
                          font=("", 8)).grid(row=row, column=0,
                                             sticky=tk.W, pady=1)
                plbl = ttk.Label(box, textvariable=var, anchor=tk.W,
                                 font=("", 8), foreground="gray")
                plbl.grid(row=row, column=1, sticky=tk.W, pady=1)
                point_vars[p.label] = (var, plbl)
                row += 1
            self._patch_rows.append({
                "target": t, "file_var": file_var, "point_vars": point_vars,
            })

    # ------------------------------------------------------------
    #  功能模块
    # ------------------------------------------------------------
    def _build_modules(self, parent):
        box = ttk.LabelFrame(parent, text="功能模块", padding=8)
        box.pack(fill=tk.X, padx=5, pady=3)
        box.columnconfigure(1, weight=1)

        self._module_rows = {}
        row = 0
        for key, (name, desc) in FEATURE_DESC.items():
            if key in ("multiclient_disable", "screenrender_windowed"):
                continue  # 这两个在 Patch 状态区已展示
            ttk.Label(box, text=name, width=14, anchor=tk.W,
                      font=("", 9, "bold")).grid(row=row, column=0,
                                                 sticky=tk.NW, pady=4)
            var = tk.StringVar(value="就绪")
            lbl = ttk.Label(box, textvariable=var, anchor=tk.W, foreground="gray",
                            font=("", 8))
            lbl.grid(row=row, column=1, sticky=tk.W, pady=4)
            self._module_rows[key] = (var, lbl)
            row += 1

    # ------------------------------------------------------------
    #  快捷入口
    # ------------------------------------------------------------
    def _build_shortcuts(self, parent):
        bar = ttk.Frame(parent)
        bar.pack(fill=tk.X, padx=5, pady=6)

        ttk.Button(bar, text="刷新状态", command=self._refresh).pack(
            side=tk.LEFT, padx=(0, 6))

        # 全部 patch 目标现统一在 Patch 页，快捷入口跳转并选中具体目标
        navs = [
            ("全部 Patch", None),
            ("双开", "va:duo_open"),
            ("截屏", "va:screen_capture"),
            ("拦截关机", "va:noshutdown"),
        ]
        for text, key in navs:
            ttk.Button(bar, text=text,
                       command=lambda k=key: self.ui.goto_patch(k)).pack(
                side=tk.LEFT, padx=3)

    # ------------------------------------------------------------
    #  刷新
    # ------------------------------------------------------------
    def _refresh(self):
        # 环境
        d = find_oseasy_dir()
        if d:
            self.env_dir_var.set(d)
            self.env_dir_lbl.configure(foreground="green")
        else:
            self.env_dir_var.set("未找到（候选目录均无组件）")
            self.env_dir_lbl.configure(foreground="orange")

        # Patch 目标
        for entry in self._patch_rows:
            t = entry["target"]
            path = resolve_target(t.sample_name)
            if not path:
                entry["file_var"].set("文件未找到")
                for v, _lbl in entry["point_vars"].values():
                    v.set("—")
                continue
            try:
                engine = PatchEngine(t, path)
                st = engine.status()
            except Exception:
                entry["file_var"].set(f"{t.sample_name}（读取失败）")
                continue

            ok = st.get("md5_ok", False)
            entry["file_var"].set(
                f"{t.sample_name} · MD5 {'匹配' if ok else '不匹配'}")
            states = {lbl: state for lbl, state, _ in st.get("points", [])}
            for lbl, (var, plbl) in entry["point_vars"].items():
                s = states.get(lbl)
                if s == ST_DONE:
                    var.set("已 patch"); plbl.configure(foreground="green")
                elif s == ST_BAD:
                    var.set("异常"); plbl.configure(foreground="red")
                else:
                    var.set("未 patch"); plbl.configure(foreground="gray")

        # 模块
        for key, (var, lbl) in self._module_rows.items():
            var.set("就绪 · 可用")
            lbl.configure(foreground="green")