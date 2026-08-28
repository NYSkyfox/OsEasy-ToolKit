# src/gui/pages/page_unlock.py
# 解锁管理页 —— 所有解除管控的操作集中于此

import tkinter as tk
from tkinter import ttk, messagebox

from src.modules.unlock_native import (
    usb_unlock, network_unlock, keyboard_unlock, unlock_all,
    screen_control_unlock, black_screen_unlock,
)


class PageUnlock:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # ---- 上部：操作按钮（可滚动） ----
        _, ctrl_frame = ui.make_scrollable(frame)

        all_frame = ttk.LabelFrame(ctrl_frame, text="一键操作", padding=5)
        all_frame.pack(fill=tk.X, pady=2)
        btn_all = ttk.Button(all_frame, text="一键脱离管控（解锁全部）",
                   command=lambda: self._confirm(
                       "一键脱离管控",
                       "将依次解锁：\n  • 网络管控 (OeNetLimit + ProcFireWall)\n  • USB 管控 (easyusbflt)\n  • 键盘鼠标锁 (KbFilter)\n  • 屏幕广播 / 黑屏肃静\n  • 目录保护 (FbdATS)",
                       unlock_all,
                   ))
        btn_all.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_all, "FUNC_UNLOCK_ALL")

        single_frame = ttk.LabelFrame(ctrl_frame, text="单项解锁", padding=5)
        single_frame.pack(fill=tk.X, pady=2)
        btn_kb = ttk.Button(single_frame, text="仅解锁键盘鼠标驱动",
                   command=lambda: self._confirm(
                       "解锁键盘鼠标",
                       "将停止 KbFilter/ProcFireWall 驱动、清理注册表过滤驱动、删除驱动文件",
                       keyboard_unlock,
                   ))
        btn_kb.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_kb, "FUNC_UNLOCK_KB")
        btn_net = ttk.Button(single_frame, text="仅停止网络管控服务",
                   command=lambda: self._confirm(
                       "解锁网络",
                       "将停止 MMPC / OeNetLimit / ProcFireWall 网络管控服务",
                       network_unlock,
                   ))
        btn_net.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_net, "FUNC_UNLOCK_NET")
        btn_usb = ttk.Button(single_frame, text="仅关闭USB管控服务",
                   command=lambda: self._confirm(
                       "关闭USB管控",
                       "将停删 easyusbflt USB 过滤驱动、清理注册表过滤驱动、删除驱动文件",
                       usb_unlock,
                   ))
        btn_usb.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_usb, "FUNC_UNLOCK_USB")
        btn_bs = ttk.Button(single_frame, text="仅移除黑屏肃静",
                   command=lambda: self._confirm(
                       "移除黑屏肃静",
                       "将结束 BlackSlient 进程并删除黑屏肃静相关文件",
                       black_screen_unlock,
                   ))
        btn_bs.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_bs, "FUNC_UNLOCK_BLACKSCREEN")
        btn_sc = ttk.Button(single_frame, text="仅移除屏幕广播",
                   command=lambda: self._confirm(
                       "移除屏幕广播",
                       "将结束广播进程并删除控屏相关文件",
                       screen_control_unlock,
                   ))
        btn_sc.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_sc, "FUNC_UNLOCK_SCREENCAST")

        # ---- 下部：输出区域（固定底部） ----
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.output_text = ui.make_output_text(output_frame, height=5)

        return frame

    # ============================================================
    #  自定义确认弹窗（带“自动注销”开关）
    # ============================================================

    def _confirm(self, title: str, desc: str, unlock_func):
        """弹出确认对话框，含 '操作完成后自动注销' 开关。
        确认后执行 unlock_func(logout=开关状态)。"""
        win = tk.Toplevel(self.ui.root)
        win.title(title)
        win.transient(self.ui.root)
        win.grab_set()                      # 模态
        win.geometry("+%d+%d" % (self.ui.root.winfo_rootx() + 60,
                                 self.ui.root.winfo_rooty() + 80))
        win.resizable(False, False)

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=desc, justify=tk.LEFT, wraplength=340, anchor=tk.W).pack(anchor=tk.W, pady=(0, 8))

        logout_var = tk.BooleanVar(value=False)
        logout_cb = ttk.Checkbutton(frame, text="操作完成后自动注销", variable=logout_var)
        logout_cb.pack(anchor=tk.W, pady=(0, 8))

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        can_btn = ttk.Button(btn_frame, text="取消", command=win.destroy)
        can_btn.pack(side=tk.RIGHT, padx=(4, 0))
        ok_btn = ttk.Button(btn_frame, text="确认", command=lambda: self._do_unlock(win, unlock_func, logout_var))
        ok_btn.pack(side=tk.RIGHT)

        # 回车=确认，Esc=取消
        win.bind("<Return>", lambda e: ok_btn.invoke())
        win.bind("<Escape>", lambda e: win.destroy())
        ok_btn.focus_set()

    def _do_unlock(self, win, unlock_func, logout_var):
        """确认后关闭弹窗，在后台线程执行解锁（避免 UI 卡死）。
        on_output 由 append_text 经 root.after 回调到 UI 线程，线程安全。"""
        import threading
        logout = bool(logout_var.get())
        win.destroy()
        self.ui.clear_text(self.output_text)
        self.ui.append_text(self.output_text, "正在执行...", self.ui.root)

        def _worker():
            try:
                unlock_func(
                    logout=logout,
                    on_output=lambda line: self.ui.append_text(self.output_text, line, self.ui.root),
                )
            except Exception as e:
                self.ui.append_text(self.output_text, f"[错误]{e}", self.ui.root)

        threading.Thread(target=_worker, daemon=True).start()