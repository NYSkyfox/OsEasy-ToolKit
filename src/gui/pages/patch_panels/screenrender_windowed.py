# src/gui/pages/patch_panels/screenrender_windowed.py
# 「屏幕广播窗口化」面板 —— 固定偏移 patch（PatchEngine 驱动）
# 目标：src/patches/screenrender_windowed（ScreenRender.exe fullscreen 赋值点）
# 面板契约：__init__(ui, detail, log_text)，build 进 detail，日志写 log_text。

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.core import PatchEngine, resolve_target, ST_DONE, ST_BAD
from src.patches import get_target
from src.gui.widgets import append_text, clear_text


class ScreenrenderWindowed:

    TARGET_KEY = "screenrender_windowed"

    def __init__(self, ui, detail, log_text):
        self.ui = ui
        self._detail = detail
        self._log = log_text
        self._target = get_target(self.TARGET_KEY)
        self._toggles = []          # [(toggle_key, var)]
        self._build()

    # ------------------------------------------------------------
    def _build(self):
        t = self._target
        d = self._detail
        ttk.Label(d, text=t.description, anchor=tk.W, foreground="gray",
                  wraplength=660, justify=tk.LEFT).pack(fill=tk.X, padx=2, pady=(0, 4))

        # 路径
        pf = ttk.LabelFrame(d, text="目标文件路径 (ScreenRender.exe)", padding=8)
        pf.pack(fill=tk.X, padx=2, pady=3)
        pf.columnconfigure(1, weight=1)
        self._path_var = tk.StringVar(value="")
        ttk.Entry(pf, textvariable=self._path_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.EW, pady=2)
        ttk.Button(pf, text="浏览…", width=8, command=self._browse).grid(
            row=0, column=2, padx=(4, 0))
        ttk.Label(pf, text="（留空则按候选目录自动搜索）", foreground="gray",
                  font=("", 8)).grid(row=1, column=0, columnspan=3,
                                     sticky=tk.W, pady=(2, 0))

        # 可勾选选项（toggle_key 点，默认启用）；本目标无可选项则隐藏该框
        self._toggle_frame = ttk.LabelFrame(d, text="可勾选项", padding=8)
        self._toggle_frame.pack(fill=tk.X, padx=2, pady=3)
        for p in t.patches:
            if not p.toggle_key:
                continue
            var = tk.BooleanVar(value=True)
            ttk.Checkbutton(self._toggle_frame, text=f"同时 patch：{p.label}",
                            variable=var).pack(anchor=tk.W, padx=4, pady=2)
            self._toggles.append((p.toggle_key, var))
        if not self._toggles:
            self._toggle_frame.pack_forget()

        self._refresh()

    # ------------------------------------------------------------
    def _skips(self):
        return [k for k, var in self._toggles if not var.get()]

    def _resolved_path(self):
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
            title="选择 ScreenRender.exe",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")])
        if p:
            self._path_var.set(p)
            self._refresh()

    def _engine(self):
        path = self._resolved_path()
        if not path:
            return None
        log_box, root = self._log, self.ui.root

        def _log(line):
            if root is not None:
                append_text(log_box, line, root)

        return PatchEngine(self._target, path, log=_log)

    def _confirm(self, msg):
        return self.ui.confirm(msg)

    # ------------------------------------------------------------
    def _do_preview(self):
        eng = self._engine()
        if eng is None:
            return
        clear_text(self._log)
        self.ui.run_in_thread(lambda: eng.dry_run(toggles=self._skips()))

    def _do_apply(self):
        eng = self._engine()
        if eng is None:
            return
        clear_text(self._log)

        def work():
            return eng.apply(toggles=self._skips(), confirm=self._confirm)

        def done(result, ok):
            if ok and result:
                self.ui.show_status(f"Patch 完成：{self._target.name}")
                self._refresh()
            else:
                self.ui.show_status("Patch 未完成，查看日志")

        self.ui.run_in_thread(work, on_done=done, label="patch")

    def _do_restore(self):
        eng = self._engine()
        if eng is None:
            return
        clear_text(self._log)

        def work():
            return eng.restore(confirm=self._confirm)

        def done(result, ok):
            if ok and result:
                self.ui.show_status(f"已还原：{self._target.name}")
                self._refresh()
            else:
                self.ui.show_status("还原未完成，查看日志")

        self.ui.run_in_thread(work, on_done=done, label="restore")

    def _refresh(self):
        eng = self._engine()
        if eng is None:
            return
        st = eng.status(toggles=self._skips())
        if not st.get("exists"):
            clear_text(self._log)
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
        for ln in lines:
            append_text(self._log, ln, self.ui.root)

    # ------------------------------------------------------------
    def buttons(self):
        return [
            ("预览 (Dry-run)", self._do_preview),
            ("应用 Patch", self._do_apply),
            ("还原", self._do_restore),
            ("刷新状态", self._refresh),
        ]