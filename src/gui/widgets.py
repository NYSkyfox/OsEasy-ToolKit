# src/gui/widgets.py
# 通用 UI 控件工厂（纯 tkinter，零业务依赖）

import ctypes
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk


def make_scrollable(parent) -> tuple[tk.Canvas, ttk.Frame]:
    """创建一个可按需滚动的容器，返回 (canvas, inner_frame)。

    内容高度 ≤ 可视区域 → 隐藏滚动条，禁止滚动
    内容高度 > 可视区域 → 显示滚动条，允许滚动

    用法: 把需要滚动的控件 pack 进 inner_frame 即可。
    注意: 不要对返回的 inner_frame 再调用 pack()/grid()。
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


def make_output_text(parent, height: int = 6) -> tk.Text:
    """创建一个标准输出日志 Text 控件（深色终端风格，只读）"""
    txt = tk.Text(parent, wrap=tk.WORD, state=tk.DISABLED,
                  bg="#1e1e1e", fg="#d4d4d4", insertbackground="white",
                  font=("Consolas", 9), height=height)
    scroll = ttk.Scrollbar(txt, orient=tk.VERTICAL, command=txt.yview)
    txt.configure(yscrollcommand=scroll.set)
    scroll.pack(side=tk.RIGHT, fill=tk.Y)
    txt.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    return txt


def append_text(txt: tk.Text, text: str, root: tk.Tk):
    """向 Text 控件追加一行（线程安全）"""
    def _do():
        txt.configure(state=tk.NORMAL)
        txt.insert(tk.END, text + "\n")
        txt.see(tk.END)
        txt.configure(state=tk.DISABLED)
    root.after(0, _do)


def clear_text(txt: tk.Text):
    """清空 Text 控件"""
    txt.configure(state=tk.NORMAL)
    txt.delete(1.0, tk.END)
    txt.configure(state=tk.DISABLED)


def show_native_context_menu(hwnd: int, x: int, y: int, items) -> None:
    """弹出 Windows 原生主题右键菜单（系统绘制，圆角/悬停高亮原生效果）。

    :param hwnd: 父窗口句柄（Tk 下用 root.winfo_id()）
    :param x, y: 屏幕坐标（event.x_root / event.y_root）
    :param items: 列表，元素为 (文本, 回调) 元组；None 表示分隔线

    同步阻塞直到菜单关闭，选中后调用对应回调。
    """
    _user32 = ctypes.windll.user32
    HMENU = wintypes.HANDLE

    _user32.CreatePopupMenu.restype = HMENU
    _user32.CreatePopupMenu.argtypes = []
    _user32.AppendMenuW.restype = wintypes.BOOL
    _user32.AppendMenuW.argtypes = [HMENU, wintypes.UINT, ctypes.c_size_t, wintypes.LPCWSTR]
    _user32.TrackPopupMenu.restype = ctypes.c_int
    _user32.TrackPopupMenu.argtypes = [HMENU, wintypes.UINT, ctypes.c_int, ctypes.c_int,
                                       ctypes.c_int, wintypes.HWND, ctypes.c_void_p]
    _user32.DestroyMenu.restype = wintypes.BOOL
    _user32.DestroyMenu.argtypes = [HMENU]
    _user32.SetCursor.restype = wintypes.HANDLE
    _user32.SetCursor.argtypes = [wintypes.HANDLE]
    _user32.LoadCursorW.restype = wintypes.HANDLE
    # LoadCursorW 第二参是资源 ID 或字符串指针（MAKEINTRESOURCE），用 LPCWSTR 承载两种
    _user32.LoadCursorW.argtypes = [wintypes.HANDLE, wintypes.LPCWSTR]

    MF_STRING = 0x0000
    MF_SEPARATOR = 0x0800
    TPM_LEFTALIGN = 0x0000
    TPM_RIGHTBUTTON = 0x0002
    TPM_RETURNCMD = 0x0100

    hmenu = _user32.CreatePopupMenu()
    if not hmenu:
        return

    # 强制系统箭头光标（IDC_ARROW=32512），避免菜单上显示文本输入光标
    # 资源 ID 需用 MAKEINTRESOURCE 包装（整数→指针）
    _idc_arrow = ctypes.cast(32512, wintypes.LPCWSTR)
    _user32.SetCursor(_user32.LoadCursorW(None, _idc_arrow))

    cmds = {}
    base = 0x9000  # 命令 ID 起始，避开系统保留值
    try:
        for idx, item in enumerate(items):
            if item is None:
                _user32.AppendMenuW(hmenu, MF_SEPARATOR, 0, None)
            else:
                text, cb = item
                cmd_id = base + idx
                _user32.AppendMenuW(hmenu, MF_STRING, cmd_id, text)
                cmds[cmd_id] = cb

        sel = _user32.TrackPopupMenu(
            hmenu, TPM_RETURNCMD | TPM_RIGHTBUTTON | TPM_LEFTALIGN,
            x, y, 0, hwnd, None)
        if sel in cmds:
            cmds[sel]()
    finally:
        _user32.DestroyMenu(hmenu)