# src/gui/pages/page_noshutdown.py
# 拦截远程关机 / 重启页（页面 4）
#
# 驱动 src/modules/noshutdown.py：
#   文件版  file_dry_run / file_patch / file_restore / file_status
#   内存版  mem_status / mem_patch / mem_restore   （仅 Windows + 管理员）
#
# 输出经 ui.run_with_log 捕获（module 内部用 print / log=print）。

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.gui.widgets import make_scrollable, make_output_text, clear_text
from src.core import resolve_target


class PageNoshutdown:

    def __init__(self, ui):
        self.ui = ui
        self._after_id = None

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)
        self._frame = frame
        _, scroll = make_scrollable(frame)

        # ── 文件选择 ──
        ff = ttk.LabelFrame(scroll, text="目标文件 (Student.exe)", padding=8)
        ff.pack(fill=tk.X, padx=5, pady=3)
        ff.columnconfigure(1, weight=1)
        self.var_path = tk.StringVar()
        ttk.Label(ff, text="路径", anchor=tk.W).grid(row=0, column=0,
                                                     sticky=tk.W, padx=6, pady=4)
        ttk.Entry(ff, textvariable=self.var_path).grid(row=0, column=1,
                                                       sticky=tk.EW, padx=4)
        ttk.Button(ff, text="浏览…", width=8, command=self._browse).grid(
            row=0, column=2, padx=6)

        # ── 运行方式 ──
        mf = ttk.LabelFrame(scroll, text="运行方式", padding=8)
        mf.pack(fill=tk.X, padx=5, pady=3)
        mf.columnconfigure(1, weight=1)
        self.mode = tk.StringVar(value="file")
        ttk.Radiobutton(mf, text="文件版 —— 改磁盘上的 Student.exe（持久，需先结束学生端再启动）",
                        variable=self.mode, value="file").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=4)
        ttk.Radiobutton(mf, text="内存版 —— 改运行中进程内存（抗 ASLR，进程重启自动恢复；仅 Windows+管理员）",
                        variable=self.mode, value="mem").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=4)

        # ── 文件版子选项 ──
        of = ttk.LabelFrame(scroll, text="文件版写入方式", padding=8)
        of.pack(fill=tk.X, padx=5, pady=3)
        of.columnconfigure(1, weight=1)
        self.fmode = tk.StringVar(value="newfile")
        ttk.Radiobutton(of, text="生成新文件  *.noshutdown.exe（推荐，不动原文件）",
                        variable=self.fmode, value="newfile").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=4)
        ttk.Radiobutton(of, text="原地修改（自动备份 <文件>.noshutdown.bak）",
                        variable=self.fmode, value="inplace").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=4)

        # ── 按钮 ──
        bar = ttk.Frame(scroll)
        bar.pack(fill=tk.X, padx=5, pady=4)
        ttk.Button(bar, text="预览 / 状态", command=self._do_preview).pack(
            side=tk.LEFT, padx=(0, 6))
        ttk.Button(bar, text="执行拦截", command=self._do_build).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(bar, text="还原", command=self._do_restore).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(bar, text="打开目录", command=self._open_dir).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(bar, text="清空日志", command=lambda: clear_text(self._log)).pack(
            side=tk.RIGHT, padx=(6, 0))

        # ── 日志 ──
        self._log = make_output_text(scroll, height=14)
        self._log.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # 自动填充默认路径
        self.ui.root.after(30, self._autofill)
        return frame

    # ------------------------------------------------------------
    def _autofill(self):
        if not self.var_path.get().strip():
            p = resolve_target("Student.exe")
            if p:
                self.var_path.set(p)

    def _browse(self):
        p = filedialog.askopenfilename(
            title="选择 Student.exe",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")])
        if p:
            self.var_path.set(p)

    def _path(self):
        p = self.var_path.get().strip()
        if not p:
            messagebox.showwarning("缺少文件", "请先选择 Student.exe 路径（文件版需要）。")
            return None
        if not os.path.exists(p):
            messagebox.showerror("文件不存在", p)
            return None
        return p

    def _mem_guard(self):
        from src.modules import noshutdown
        if not noshutdown.is_windows():
            messagebox.showinfo("仅 Windows",
                                "内存版仅支持 Windows（需管理员权限）。\n"
                                "当前运行在非 Windows 环境，无法操作进程内存。")
            return False
        return True

    def _run(self, func, ok_msg, fail_msg):
        clear_text(self._log)
        self.ui.run_with_log(func, self._log,
                             on_done=lambda ok: self.ui.show_status(
                                 ok_msg if ok else fail_msg),
                             label="noshutdown")

    # ------------------------------------------------------------
    def _do_preview(self):
        from src.modules import noshutdown
        if self.mode.get() == "mem":
            if not self._mem_guard():
                return

            def func():
                noshutdown.mem_status()
            self._run(func, "状态刷新完成", "状态读取失败，查看日志")
            return

        p = self._path()
        if not p:
            return

        def func():
            noshutdown.file_dry_run(p, strict=False)
        self._run(func, "预览完成（未写盘）", "预览出错，查看日志")

    def _do_build(self):
        from src.modules import noshutdown
        if self.mode.get() == "mem":
            if not self._mem_guard():
                return
            if not self.ui.confirm("将修改运行中 Student.exe 进程内存。\n需要管理员权限。继续？"):
                return

            def func():
                noshutdown.mem_patch()
            self._run(func, "已拦截（内存版）", "拦截失败，查看日志")
            return

        p = self._path()
        if not p:
            return
        inplace = (self.fmode.get() == "inplace")
        if inplace and not self.ui.confirm(
                "将直接修改原文件（自动生成 .noshutdown.bak 备份）。\n"
                "请确保学生端进程已关闭。确定继续？"):
            return

        def func():
            noshutdown.file_patch(p, inplace=inplace, strict=False)
        self._run(func, "拦截完成", "拦截失败，查看日志")

    def _do_restore(self):
        from src.modules import noshutdown
        if self.mode.get() == "mem":
            if not self._mem_guard():
                return

            def func():
                noshutdown.mem_restore()
            self._run(func, "还原完成（内存版）", "还原失败，查看日志")
            return

        p = self._path()
        if not p:
            return

        def func():
            noshutdown.file_restore(p)
        self._run(func, "还原完成", "还原失败，查看日志")

    def _open_dir(self):
        d = self.var_path.get().strip()
        if not d:
            return
        d = os.path.dirname(d)
        if not d:
            return
        try:
            if os.name == "nt":
                os.startfile(d)
            else:
                os.system(f'xdg-open "{d}" 2>/dev/null || open "{d}"')
        except Exception as e:
            messagebox.showerror("无法打开目录", str(e))