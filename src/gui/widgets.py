# src/gui/widgets.py
# 通用 UI 控件工厂 —— 纯 tkinter，零业务依赖
#
# 提供：
#   make_scrollable  按需滚动的容器
#   make_output_text 深色终端风格只读日志框
#   append_text / clear_text 线程安全的文本追加/清空

import tkinter as tk
from tkinter import ttk


def make_scrollable(parent) -> tuple:
    """创建可按需滚动的容器，返回 (canvas, inner_frame)。

    内容 ≤ 可视区 → 隐藏滚动条；内容 > 可视区 → 显示滚动条。
    用法：把要滚动的控件 pack 进 inner_frame 即可。
    注意：不要再对 inner_frame 调用 pack()/grid()。
    """
    container = ttk.Frame(parent)
    canvas = tk.Canvas(container, highlightthickness=0)
    scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL)
    inner = ttk.Frame(canvas)

    canvas.create_window((0, 0), window=inner, anchor=tk.NW)
    canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    container.pack(fill=tk.BOTH, expand=True)

    def _refresh_scroll():
        canvas.update_idletasks()
        bbox = canvas.bbox("all")
        ch = canvas.winfo_height()
        if bbox and bbox[3] > ch + 2:
            canvas.configure(scrollregion=bbox, yscrollcommand=scrollbar.set)
            scrollbar.configure(command=canvas.yview)
            scrollbar.pack(side=tk.RIGHT, fill=tk.Y, before=canvas)
            scrollbar.lift()
        else:
            scrollbar.pack_forget()
            canvas.configure(scrollregion=(0, 0, 1, 1), yscrollcommand="")
            canvas.yview_moveto(0)

    inner.bind("<Configure>", lambda e: canvas.after(10, _refresh_scroll))
    canvas.bind("<Configure>", lambda e: canvas.after(10, lambda: (
        canvas.itemconfig(1, width=e.width), _refresh_scroll()
    )))

    def _on_mousewheel(event):
        if scrollbar.winfo_ismapped():
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
    canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

    return canvas, inner


def make_output_text(parent, height: int = 8) -> tk.Text:
    """创建深色终端风格只读日志框（带垂直滚动条），返回 Text。"""
    txt = tk.Text(parent, wrap=tk.WORD, state=tk.DISABLED,
                  bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
                  font=("Consolas", 9), height=height)
    scroll = ttk.Scrollbar(parent, orient=tk.VERTICAL, command=txt.yview)
    txt.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    return txt


def append_text(txt: tk.Text, text: str, root: tk.Tk) -> None:
    """线程安全地向 Text 追加一行。"""
    def _do():
        try:
            txt.configure(state=tk.NORMAL)
            txt.insert(tk.END, text + "\n")
            txt.see(tk.END)
            txt.configure(state=tk.DISABLED)
        except Exception:
            pass
    try:
        root.after(0, _do)
    except Exception:
        pass


def clear_text(txt: tk.Text) -> None:
    """清空 Text 控件。"""
    try:
        txt.configure(state=tk.NORMAL)
        txt.delete(1.0, tk.END)
        txt.configure(state=tk.DISABLED)
    except Exception:
        pass