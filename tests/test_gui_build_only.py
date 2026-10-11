#!/usr/bin/env python3
# GUI 构建验证（build-only，不进 mainloop 事件泵）。
# 目的：在受 Xvfb/Xlib 多线程断言限制的环境里，单独验证“控件创建 + 变量绑定 +
# pack/grid”在目标 Python 版本无运行时错误。build 成功后立即 destroy。
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
from src.gui.pages import PageOverview, PagePatches, PageDuo, PageCapture, PageNoshutdown

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

pages = []
for cls in (PageOverview, PagePatches, PageDuo, PageCapture, PageNoshutdown):
    p = cls(ui)
    ui.notebook.add(p.build(), text="x")
    pages.append(p)
ui._pages = pages

# 触发各页 build 期间挂的 _refresh/_autofill 之外的纯构建逻辑
disable_widget_focus(ui.root)
ui.root.update_idletasks()
ui.root.update()

# 手动跑一次 overview 的 _refresh（纯构建后逻辑，不依赖事件泵）
try:
    pages[0]._refresh()
    ui.root.update()
    print("overview._refresh OK")
except Exception as e:
    import traceback
    traceback.print_exc()
    raise

ui.root.destroy()
print("BUILD-ONLY OK on", sys.version.split()[0], "— 4 页 build + refresh 无运行时错误")