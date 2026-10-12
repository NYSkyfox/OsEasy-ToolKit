# src/gui/app.py
# ManagerHelper 主 UI 框架 —— 顶部导航栏 + 下部内容区（ttk 版）
#
# 结构：
#   ┌─────────────────────────────────────────┐
#   │  主页 | Patch | 双开 | 截屏               │  ← 顶部导航（Notebook tab）
#   ├─────────────────────────────────────────┤
#   │                                         │
#   │              当前页面内容区              │  ← 下部内容区
#   │                                         │
#   ├─────────────────────────────────────────┤
#   │  状态栏                                  │  ← 底部状态栏
#   └─────────────────────────────────────────┘

import os
import queue
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox

from config import APP_VERSION, RELEASE_NAME
from src.gui.style import apply_theme, disable_widget_focus
from src.gui.widgets import append_text
from src.gui.pages import (
    PageOverview, PagePatches, PageDuo, PageCapture, PageNoshutdown,
)


class Ui:

    def __init__(self) -> None:
        self.release_name = RELEASE_NAME
        self.version = APP_VERSION

        # tkinter 根窗口（延迟创建）
        self.root = None
        self.notebook = None
        self.status_var = None
        self.status_label = None
        self._pages = []
        self._status_clear_job = None
        self._confirm_q = queue.Queue()

    # ============================================================
    #  主入口
    # ============================================================

    def main(self) -> None:
        self.root = tk.Tk()
        self.root.title(self.release_name)
        self.root.geometry("720x560")
        self.root.minsize(560, 460)

        # 主题
        apply_theme(self.root)

        # 全局去掉按钮/复选框点击虚线焦点框
        self.root.option_add("*Button.highlightThickness", 0)
        self.root.option_add("*Checkbutton.highlightThickness", 0)

        # 图标（若存在 logo.ico）
        self._try_set_icon()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ---- 底部状态栏（先 pack，保证在底部） ----
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="就绪")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      relief=tk.SUNKEN, anchor=tk.W,
                                      wraplength=680, justify=tk.LEFT)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=1)

        # ---- 顶部导航 + 内容区（Notebook） ----
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=(5, 0))

        self._pages = [
            PageOverview(self),
            PagePatches(self),
            PageDuo(self),
            PageCapture(self),
            PageNoshutdown(self),
        ]
        tab_labels = ["主页", "Patch", "双开", "截屏", "拦截关机"]

        for page, label in zip(self._pages, tab_labels):
            frame = page.build()
            self.notebook.add(frame, text=label)

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # 全局关闭非输入控件焦点虚线
        disable_widget_focus(self.root)

        # 启动
        self.show_status(f"已加载 · {self.release_name}")
        self._pump_confirm()
        self.root.mainloop()

    # ============================================================
    #  通用方法
    # ============================================================

    def _try_set_icon(self) -> None:
        """尝试加载 logo.ico（若打包资源存在）。"""
        try:
            base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            ico = os.path.join(base, "logo.ico")
            if os.path.exists(ico):
                self.root.iconbitmap(ico)
        except Exception:
            pass

    def _on_close(self) -> None:
        """窗口关闭：取消各页定时器后销毁。"""
        for page in self._pages:
            after_id = getattr(page, "_after_id", None)
            if after_id:
                try:
                    self.root.after_cancel(after_id)
                except Exception:
                    pass
        try:
            self.root.destroy()
        except Exception:
            pass

    def _on_tab_changed(self, event=None) -> None:
        """切换页面时，刷新该页的 _refresh（若实现）。"""
        try:
            idx = self.notebook.index(self.notebook.select())
            page = self._pages[idx]
            if hasattr(page, "_refresh"):
                page._refresh()
        except Exception:
            pass

    def show_status(self, text: str, sticky: bool = False) -> None:
        """状态栏显示消息。sticky=False 时 4 秒后恢复为默认。"""
        if not self.status_var:
            return
        self.status_var.set(text)
        if self._status_clear_job:
            try:
                self.root.after_cancel(self._status_clear_job)
            except Exception:
                pass
        if not sticky:
            self._status_clear_job = self.root.after(
                4000, lambda: self.status_var and self.status_var.set("就绪"))

    def run_in_thread(self, func, on_done=None, label: str = "操作") -> None:
        """后台线程执行 func()，避免阻塞 UI；结束后回调 on_done(result, ok)。"""
        def _wrap():
            result = None
            ok = True
            try:
                result = func()
            except Exception as e:
                ok = False
                result = e
                print(f"[线程 {label}] 异常: {e}")
            if on_done:
                try:
                    self.root.after(0, lambda: on_done(result, ok))
                except Exception:
                    pass
        threading.Thread(target=_wrap, daemon=True).start()

    # ============================================================
    #  线程安全确认桥（messagebox 只能在主线程调用）
    # ============================================================

    def confirm(self, msg: str) -> bool:
        """线程安全的阻塞式确认对话框。

        - 主线程调用（按钮回调等）：直接同步弹 messagebox。
          若此时也走“入队 + ev.wait”，主循环会因阻塞停转，
          导致 _pump_confirm（after 回调）永不触发 → 死锁，整窗卡死 120s。
        - 后台线程调用：把请求入队，由主线程 _pump_confirm 弹出 messagebox，
          后台线程阻塞等待结果（主循环持续运行，不卡 UI）。
        """
        if threading.current_thread() is threading.main_thread():
            try:
                return messagebox.askyesno("确认", msg)
            except Exception:
                return False
        result = []
        ev = threading.Event()
        self._confirm_q.put((msg, result, ev))
        ev.wait(timeout=120)
        return bool(result[0]) if result else False

    def _pump_confirm(self) -> None:
        """主线程轮询确认队列（每 80ms 一次）。"""
        try:
            while True:
                msg, result, ev = self._confirm_q.get_nowait()
                try:
                    result.append(messagebox.askyesno("确认", msg))
                except Exception:
                    result.append(False)
                finally:
                    ev.set()
        except Exception:
            pass
        try:
            self.root.after(80, self._pump_confirm)
        except Exception:
            pass

    def log(self, txt, line: str) -> None:
        """线程安全地向某页日志框追加一行。"""
        if txt is not None and self.root is not None:
            append_text(txt, line, self.root)

    def run_with_log(self, func, txt, on_done=None, label: str = "操作") -> None:
        """后台线程执行 func()，并把其 stdout 输出实时写入日志框 txt。

        适用于 module 内部用 print() 输出日志的场景（duo_open / screen_capture）。
        on_done(ok) 在主线程回调，ok 表示 func 正常返回（无异常）。
        """
        q = queue.Queue()
        ok_holder = [True]

        class _W:
            def __init__(self, qq):
                self.qq = qq
            def write(self, s):
                if s and s.strip():
                    self.qq.put(s.rstrip("\n"))
            def flush(self):
                pass

        def _wrap():
            old = sys.stdout
            sys.stdout = _W(q)
            ok_holder[0] = True
            try:
                func()
            except Exception as e:
                ok_holder[0] = False
                print(f"!! 运行出错: {e}")
            finally:
                sys.stdout = old
                q.put(None)   # 结束哨兵

        def _pump():
            got_done = False
            try:
                while True:
                    item = q.get_nowait()
                    if item is None:
                        got_done = True
                        break
                    append_text(txt, item, self.root)
            except Exception:
                pass
            if got_done:
                if on_done:
                    try:
                        on_done(ok_holder[0])
                    except Exception:
                        pass
                return
            self.root.after(60, _pump)

        threading.Thread(target=_wrap, daemon=True).start()
        self.root.after(60, _pump)

    def _get_page(self, cls) -> object:
        for page in self._pages:
            if isinstance(page, cls):
                return page
        return None


# 全局单例（入口 import 后调用 main()）
app = Ui()