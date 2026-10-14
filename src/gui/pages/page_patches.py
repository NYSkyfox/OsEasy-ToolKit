# src/gui/pages/page_patches.py
# 统一 Patch 页 —— 把两套 patch 机制（固定偏移 / VA 型）的所有目标收在一页
#
# 布局：
#   [目标下拉 ▾]              ← 列出全部 patch 目标（自动发现）
#   ┌─────────────────────────┐
#   │  目标详情面板（动态重建）  │   ← 每个目标的控件（路径/选项/模式…）
#   ├─────────────────────────┤
#   │  [按钮栏（随目标变化）]    │   ← 预览/应用/还原/打开目录…
#   ├─────────────────────────┤
#   │  日志（共享，深色）        │
#   └─────────────────────────┘
#
# 面板契约见 src/gui/pages/patch_panels/__init__.py。
# 新增 patch 目标只需在对应注册表登记，本页下拉框自动出现，无需改这里。

import tkinter as tk
from tkinter import ttk

from src.gui.widgets import make_scrollable, make_output_text, clear_text
from src.gui.pages.patch_panels import REGISTRY


class PagePatches:

    def __init__(self, ui):
        self.ui = ui
        self._after_id = None
        self._entry = None        # 当前选中的 REGISTRY 条目
        self._panel = None        # 当前面板实例
        self._buttons = []        # 当前按钮栏 widget（用于重建前销毁）

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
                                   state="readonly", width=48)
        self._combo["values"] = [e["label"] for e in REGISTRY]
        self._combo.grid(row=0, column=1, sticky=tk.W, pady=2, padx=4)
        self._combo.bind("<<ComboboxSelected>>", lambda e: self._on_select())
        if REGISTRY:
            self._combo.current(0)

        # ── 详情面板容器（动态重建） ──
        self._detail = ttk.LabelFrame(scroll, text="详情", padding=6)
        self._detail.pack(fill=tk.X, padx=5, pady=3)

        # ── 按钮栏（动态重建） ──
        self._bar = ttk.Frame(scroll)
        self._bar.pack(fill=tk.X, padx=5, pady=4)

        # ── 共享日志 ──
        self._log = make_output_text(scroll, height=12)
        self._log.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # 初始选中第一项
        self._on_select()
        return frame

    # ------------------------------------------------------------
    def select_index(self, idx: int):
        """供外部（主页快捷入口）按 REGISTRY 下标选中某目标。"""
        if 0 <= idx < len(REGISTRY):
            self._combo.current(idx)
            self._on_select()

    def select_key(self, key: str):
        """按 key（如 'va:duo_open' / 'fixed:multiclient_disable'）选中。"""
        for i, e in enumerate(REGISTRY):
            if e["key"] == key:
                self._combo.current(i)
                self._on_select()
                return

    def _on_select(self):
        idx = self._combo.current()
        if idx < 0 or idx >= len(REGISTRY):
            return
        self._entry = REGISTRY[idx]

        # 重建详情面板
        for w in self._detail.winfo_children():
            w.destroy()
        self._panel = self._entry["factory"](
            self.ui, self._detail, self._log)

        # 重建按钮栏
        for w in self._buttons:
            w.destroy()
        self._buttons = []
        for i, (text, cmd) in enumerate(self._panel.buttons()):
            b = ttk.Button(self._bar, text=text, command=cmd)
            b.pack(side=tk.LEFT, padx=(0 if i == 0 else 6, 0))
            self._buttons.append(b)
        # 清空日志按钮（右对齐，常驻）
        cb = ttk.Button(self._bar, text="清空日志",
                        command=lambda: clear_text(self._log))
        cb.pack(side=tk.RIGHT, padx=(6, 0))
        self._buttons.append(cb)

    # ------------------------------------------------------------
    def _refresh(self):
        """tab 切回本页时调用：刷新当前面板（若实现）。"""
        if self._panel is not None and hasattr(self._panel, "_refresh"):
            try:
                self._panel._refresh()
            except Exception:
                pass