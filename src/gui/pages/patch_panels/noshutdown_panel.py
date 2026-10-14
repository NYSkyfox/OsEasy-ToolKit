# src/gui/pages/patch_panels/noshutdown_panel.py
# 拦截远程关机 / 重启 详情面板（VA 型）
#
# 驱动 src/core/va_patch.VAPatchExecutor + src/modules/patches/noshutdown 配置。
#   文件版  —— executor.dry_run / patch / restore
#   内存版  —— executor.mem_status / mem_patch / mem_restore（仅 Windows + 管理员）
# 面板契约：__init__(ui, detail, log_text) —— 把控件 build 进 detail，日志写入 log_text。

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.gui.widgets import clear_text
from src.core import resolve_target
from src.core.va_patch import VAPatchExecutor, _is_windows
from src.modules.patches import get_va_target


class NoshutdownPanel:

    def __init__(self, ui, detail, log_text):
        self.ui = ui
        self._detail = detail
        self._log = log_text
        self._target = get_va_target("noshutdown")
        self._build()

    # ------------------------------------------------------------
    def _build(self):
        d = self._detail

        # ── 文件选择 ──
        ff = ttk.LabelFrame(d, text="目标文件 (Student.exe)", padding=8)
        ff.pack(fill=tk.X, padx=2, pady=3)
        ff.columnconfigure(1, weight=1)
        self.var_path = tk.StringVar()
        ttk.Label(ff, text="路径", anchor=tk.W).grid(row=0, column=0,
                                                     sticky=tk.W, padx=6, pady=4)
        ttk.Entry(ff, textvariable=self.var_path).grid(row=0, column=1,
                                                       sticky=tk.EW, padx=4)
        ttk.Button(ff, text="浏览…", width=8, command=self._browse).grid(
            row=0, column=2, padx=6)

        # ── 运行方式 ──
        mf = ttk.LabelFrame(d, text="运行方式", padding=8)
        mf.pack(fill=tk.X, padx=2, pady=3)
        mf.columnconfigure(1, weight=1)
        self.mode = tk.StringVar(value="file")
        ttk.Radiobutton(mf, text="文件版 —— 改磁盘上的 Student.exe（持久，需先结束学生端再启动）",
                        variable=self.mode, value="file").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=4)
        ttk.Radiobutton(mf, text="内存版 —— 改运行中进程内存（抗 ASLR，进程重启自动恢复；仅 Windows+管理员）",
                        variable=self.mode, value="mem").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=4)

        # ── 文件版子选项 ──
        of = ttk.LabelFrame(d, text="文件版写入方式", padding=8)
        of.pack(fill=tk.X, padx=2, pady=3)
        of.columnconfigure(1, weight=1)
        self.fmode = tk.StringVar(value="newfile")
        ttk.Radiobutton(of, text="生成新文件  *.noshutdown.exe（推荐，不动原文件）",
                        variable=self.fmode, value="newfile").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=4)
        ttk.Radiobutton(of, text="原地修改（自动备份 <文件>.noshutdown.bak）",
                        variable=self.fmode, value="inplace").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=4)

        # 自动填充默认路径（延迟到 root 可用）
        self.ui.root.after(30, self._autofill)

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

    def _executor(self, path=None):
        """内存版不需要文件路径，但执行器构造需要；用占位（内存操作只用 sample_name）。"""
        p = path or self.var_path.get().strip() or (
            os.path.join("memory_only", self._target.files[0].sample_name))
        return VAPatchExecutor(self._target, p)

    def _mem_guard(self):
        if not _is_windows():
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
        if self.mode.get() == "mem":
            if not self._mem_guard():
                return
            ex = self._executor()

            def func():
                ex.mem_status()
            self._run(func, "状态刷新完成", "状态读取失败，查看日志")
            return

        p = self._path()
        if not p:
            return
        ex = self._executor(p)

        def func():
            ex.dry_run(strict=False)
        self._run(func, "预览完成（未写盘）", "预览出错，查看日志")

    def _do_build(self):
        if self.mode.get() == "mem":
            if not self._mem_guard():
                return
            if not self.ui.confirm("将修改运行中 Student.exe 进程内存。\n需要管理员权限。继续？"):
                return
            ex = self._executor()

            def func():
                ex.mem_patch()
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
        ex = self._executor(p)

        def func():
            ex.patch(inplace=inplace, strict=False)
        self._run(func, "拦截完成", "拦截失败，查看日志")

    def _do_restore(self):
        if self.mode.get() == "mem":
            if not self._mem_guard():
                return
            ex = self._executor()

            def func():
                ex.mem_restore()
            self._run(func, "还原完成（内存版）", "还原失败，查看日志")
            return

        p = self._path()
        if not p:
            return
        ex = self._executor(p)

        def func():
            ex.restore()
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

    # ------------------------------------------------------------
    def buttons(self):
        return [
            ("预览 / 状态", self._do_preview),
            ("执行拦截", self._do_build),
            ("还原", self._do_restore),
            ("打开目录", self._open_dir),
        ]