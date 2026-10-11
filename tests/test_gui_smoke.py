#!/usr/bin/env python3
# GUI 构建冒烟测试：实例化全部 5 页并 build + 一次 update，验证无运行时错误。
# 不进入真实 mainloop（用 update 后 destroy）。messagebox 置 no-op（无 Os-Easy 文件时不弹窗阻塞）。
import os
import sys
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import tkinter as tk
from tkinter import ttk, messagebox

# no-op 弹窗（冒烟环境无 Os-Easy 文件，避免 resolve 失败弹窗阻塞）
messagebox.showwarning = lambda *a, **k: None
messagebox.showerror = lambda *a, **k: None
messagebox.showinfo = lambda *a, **k: None
messagebox.askyesno = lambda *a, **k: False

from src.gui.style import apply_theme, disable_widget_focus
from src.gui import app as appmod
from src.gui.pages import PageOverview, PagePatches, PageDuo, PageCapture, PageNoshutdown

ui = appmod.Ui()
ui.root = tk.Tk()
ui.root.title("smoke")
ui.root.geometry("720x560")
apply_theme(ui.root)

sf = ttk.Frame(ui.root)
sf.pack(side=tk.BOTTOM, fill=tk.X)
ui.status_var = tk.StringVar(value="smoke")
ui.status_label = ttk.Label(sf, textvariable=ui.status_var, relief=tk.SUNKEN)
ui.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=1)

ui.notebook = ttk.Notebook(ui.root)
ui.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

pages = [PageOverview(ui), PagePatches(ui), PageDuo(ui), PageCapture(ui), PageNoshutdown(ui)]
for p in pages:
    f = p.build()
    ui.notebook.add(f, text="x")

disable_widget_focus(ui.root)
ui.root.update()
# 让 after 回调（_refresh/_autofill/_on_select）跑一轮
ui.root.after(150, ui.root.destroy)
ui.root.mainloop()

print("GUI BUILD SMOKE OK — 5 页全部 build 成功")