# src/gui/pages/page_patches.py
# Patch 管理页（页面 1）—— 固定偏移 patch（引擎驱动）
#
# 布局：
#   [目标下拉]  [描述]
#   [路径]      [浏览…]
#   [□ 开关]    （对应可选 patch 点，如“屏幕广播”）
#   [预览] [应用 Patch] [还原] [刷新状态]
#   [日志]
#
# 新增固定偏移 patch：在 src/patches/ 注册后，本页下拉框自动出现。

import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.core import PatchEngine, resolve_target, ST_DONE, ST_NONE, ST_BAD, ST_SKIP
from src.patches import ALL_TARGETS
from src.gui.widgets import make_scrollable, make_output_text, clear_text


class PagePatches:

    def __init__(self, ui):
        self.ui = ui
        self._after_id = None
        self._target = None
        self._toggles = []          # 当前目标的可变开关 [(key, var, label)]

    # ------------------------------------------------------------
    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)
        self._frame = frame
        _, scroll = make_scrollable(frame)

        # ── 目标选择 ──
        top = ttk.LabelFrame(scroll, text="Patch 目标", padding=8)
        top.pack(fill=tk.X, padx=5, pady=3)
        top.columnconfigure(1, weight=1)

        ttk.Label(top, text="选择目标", width=10, anchor=tk.W).grid(
            row=0, column=0, sticky=tk.W, pady=2)
        self._sel_var = tk.StringVar()
        self._combo = ttk.Combobox(top, textvariable=self._sel_var,
                                   state="readonly", width=40)
        self._combo["values"] = [t.name for t in ALL_TARGETS]
        self._combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=4)
        self._combo.bind("<<ComboboxSelected>>", lambda e: self._on_select())
        if ALL_TARGETS:
            self._combo.current(0)

        # 描述
        self._desc_var = tk.StringVar(value="")
        desc_lbl = ttk.Label(scroll, textvariable=self._desc_var, anchor=tk.W,
                             foreground="gray", wraplength=640, justify=tk.LEFT)
        desc_lbl.pack(fill=tk.X, padx=10, pady=(0, 4))

        # ── 路径 ──
        pf = ttk.LabelFrame(scroll, text="目标文件路径", padding=8)
        pf.pack(fill=tk.X, padx=5, pady=3)
        pf.columnconfigure(1, weight=1)
        self._path_var = tk.StringVar(value="")
        ttk.Entry(pf, textvariable=self._path_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.EW, pady=2)
        ttk.Button(pf, text="浏览…", width=8,
                   command=self._browse).grid(
            row=0, column=2, padx=(4, 0))
        # 提示：留空则自动搜索
        ttk.Label(pf, text="（留空则按候选目录自动搜索）", foreground="gray",
                  font=("", 8)).grid(row=1, column=0, columnspan=3,
                                     sticky=tk.W, pady=(2, 0))

        # ── 开关 ──
        self._toggle_frame = ttk.LabelFrame(scroll, text="选项", padding=8)
        self._toggle_frame.pack(fill=tk.X, padx=5, pady=3)

        # ── 按钮 ──
        bar = ttk.Frame(scroll)
        bar.pack(fill=tk.X, padx=5, pady=4)
        ttk.Button(bar, text="预览 (Dry-run)", command=self._do_preview).pack(
            side=tk.LEFT, padx=(0, 6))
        ttk.Button(bar, text="应用 Patch", command=self._do_apply).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(bar, text="还原", command=self._do_restore).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(bar, text="刷新状态", command=self._refresh).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(bar, text="清空日志", command=lambda: clear_text(self._log)).pack(
            side=tk.RIGHT, padx=(6, 0))

        # ── 日志 ──
        self._log = make_output_text(scroll, height=12)
        self._log.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # 初始
        self._on_select()
        return frame

    # ------------------------------------------------------------
    def _on_select(self):
        """下拉框变化：载入目标，重建开关。"""
        idx = self._combo.current()
        if idx < 0 or idx >= len(ALL_TARGETS):
            return
        self._target = ALL_TARGETS[idx]
        self._desc_var.set(self._target.description)
        self._rebuild_toggles()
        self._refresh()

    def _rebuild_toggles(self):
        """根据当前目标的可选 patch 点重建开关。"""
        for w in self._toggle_frame.winfo_children():
            w.destroy()
        self._toggles = []
        if not self._target:
            return
        for p in self._target.patches:
            if not p.toggle_key:
                continue
            var = tk.BooleanVar(value=True)   # 默认启用
            cb = ttk.Checkbutton(self._toggle_frame,
                                 text=f"同时 patch：{p.label}", variable=var)
            cb.pack(anchor=tk.W, padx=4, pady=2)
            self._toggles.append((p.toggle_key, var))

    def _current_skips(self):
        """返回未勾选的 toggle_key 列表。"""
        skips = []
        for key, var in self._toggles:
            if not var.get():
                skips.append(key)
        return skips

    def _resolved_path(self):
        """返回用户指定路径或自动搜索结果；无效则弹窗。"""
        p = self._path_var.get().strip()
        if p:
            if os.path.isfile(p):
                return p
            messagebox.showerror("路径无效", f"文件不存在：\n{p}")
            return None
        auto = resolve_target(self._target.sample_name)
        if auto:
            self._path_var.set(auto)
            return auto
        messagebox.showwarning(
            "未找到文件",
            f"未在候选目录找到 {self._target.sample_name}\n请在上方手动指定路径。")
        return None

    def _browse(self):
        p = filedialog.askopenfilename(
            title=f"选择 {self._target.sample_name}",
            filetypes=[("可执行文件", "*.exe"), ("DLL", "*.dll"), ("所有文件", "*.*")])
        if p:
            self._path_var.set(p)
            self._refresh()

    def _make_engine(self):
        path = self._resolved_path()
        if not path:
            return None
        log_box = self._log
        root = self.ui.root

        def _log(line):
            if root is not None:
                from src.gui.widgets import append_text
                append_text(log_box, line, root)

        return PatchEngine(self._target, path, log=_log)

    def _confirm(self, msg):
        """委托给 ui 的线程安全确认桥（messagebox 由主线程弹出）。"""
        return self.ui.confirm(msg)

    # ------------------------------------------------------------
    def _do_preview(self):
        if not self._target:
            return
        eng = self._make_engine()
        if eng is None:
            return
        skips = self._current_skips()
        clear_text(self._log)
        self._log_configure(True)
        self.ui.run_in_thread(
            lambda: eng.dry_run(toggles=skips),
            on_done=lambda r, ok: self._log_configure(False))

    def _do_apply(self):
        if not self._target:
            return
        eng = self._make_engine()
        if eng is None:
            return
        skips = self._current_skips()
        clear_text(self._log)
        self._log_configure(True)

        def work():
            return eng.apply(toggles=skips, confirm=self._confirm)

        def done(result, ok):
            self._log_configure(False)
            if ok and result:
                self.ui.show_status(f"Patch 完成：{self._target.name}")
                self._refresh()
            else:
                self.ui.show_status("Patch 未完成，查看日志")

        self.ui.run_in_thread(work, on_done=done, label="patch")

    def _do_restore(self):
        if not self._target:
            return
        eng = self._make_engine()
        if eng is None:
            return
        clear_text(self._log)
        self._log_configure(True)

        def work():
            return eng.restore(confirm=self._confirm)

        def done(result, ok):
            self._log_configure(False)
            if ok and result:
                self.ui.show_status(f"已还原：{self._target.name}")
                self._refresh()
            else:
                self.ui.show_status("还原未完成，查看日志")

        self.ui.run_in_thread(work, on_done=done, label="restore")

    def _log_configure(self, busy):
        """busy 时禁用按钮。"""
        # 简单处理：靠状态栏提示，按钮不强制禁用（操作本身幂等且快速）
        return

    # ------------------------------------------------------------
    def _refresh(self):
        if not self._target:
            return
        eng = self._make_engine()
        if eng is None:
            return
        st = eng.status(toggles=self._current_skips())
        if not st.get("exists"):
            clear_text(self._log)
            from src.gui.widgets import append_text
            append_text(self._log, f"文件不存在：{self._target.sample_name}",
                        self.ui.root)
            return
        lines = [
            f"── {self._target.name} 状态 ──",
            f"路径   : {st['path']}",
            f"大小   : {st['size']}  (预期 {self._target.size})",
            f"MD5    : {st['md5']}  {'✓ 匹配' if st.get('md5_ok') else '⚠ 不匹配'}",
            "Patch 点:",
        ]
        for label, state, detail in st.get("points", []):
            icon = "●" if state == ST_DONE else ("!" if state == ST_BAD else "○")
            lines.append(f"   {icon} {label:<12} {state}  {detail}")
        clear_text(self._log)
        from src.gui.widgets import append_text
        for ln in lines:
            append_text(self._log, ln, self.ui.root)