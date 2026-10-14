#!/usr/bin/env python3
# GUI 构建验证（build-only，不进 mainloop 事件泵）。
# 目的：在受 Xvfb/Xlib 多线程断言限制的环境里，单独验证"控件创建 + 变量绑定 +
# pack/grid"在目标 Python 版本无运行时错误。build 成功后立即 destroy。
#
# 本次额外：遍历统一 Patch 页的 REGISTRY，逐个切换目标并 build 各面板，
# 确保 5 个 patch 目标（2 固定偏移 + 3 VA）的面板均可无错构建。
import os
import sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import tkinter as tk
from tkinter import ttk, messagebox

messagebox.showwarning = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None
messagebox.showinfo = lambda *a, **k: None
messagebox.askyesno = lambda *a, **k: False

from src.gui.style import apply_theme, disable_widget_focus
from src.gui import app as appmod
from src.gui.pages import PageOverview, PagePatches
from src.gui.pages.patch_panels import REGISTRY

ui = appmod.Ui()
ui.root = tk.Tk()
ui.root.title("build-only")
ui.root.geometry("720x560")
apply_theme(ui.root)

sf = ttk.Frame(ui.root)
sf.pack(side=tk.BOTTOM, fill=tk.X)
ui.status_var = tk.StringVar(value="x")
ui.status_label = ttk.Label(sf, textvariable=ui.status_var, relief=tk.SUNKEN)
ui.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=1)

ui.notebook = ttk.Notebook(ui.root)
ui.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

pages = [PageOverview(ui), PagePatches(ui)]
for p in pages:
    ui.notebook.add(p.build(), text="x")
ui._pages = pages
ui.root.update_idletasks()
ui.root.update()

# overview 的 _refresh（纯构建后逻辑，不依赖事件泵）
pages[0]._refresh()
ui.root.update()
print("overview._refresh OK")

# 遍历统一 Patch 页的每个目标，切换面板并验证可构建
pp = pages[1]
for i, entry in enumerate(REGISTRY):
    pp.select_index(i)
    ui.root.update_idletasks()
    ui.root.update()
    assert pp._panel is not None, f"panel not built for {entry['key']}"
    assert pp._panel.buttons(), f"no buttons for {entry['key']}"
    print(f"panel OK  [{i}] {entry['kind']:>5}  {entry['key']}  "
          f"buttons={len(pp._panel.buttons())}")

disable_widget_focus(ui.root)
ui.root.destroy()
print("BUILD-ONLY OK on", sys.version.split()[0],
      "— 2 页 build + %d 个 patch 面板切换无运行时错误" % len(REGISTRY))