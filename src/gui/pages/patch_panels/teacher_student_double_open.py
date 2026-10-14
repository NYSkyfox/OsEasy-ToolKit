# src/gui/pages/patch_panels/teacher_student_double_open.py
# 「双开教师端 / 学生端」面板 —— VA 型 patch
# 驱动 src/core/va_patch.VAPatchExecutor + src/modules/patches/duo_open 配置。
# 配置含两个文件（Teacher.exe / Student.exe），各建一个执行器。
# 面板契约：__init__(ui, detail, log_text)，build 进 detail，日志写 log_text。

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.gui.widgets import clear_text
from src.core import resolve_target
from src.core.va_patch import VAPatchExecutor
from src.modules.patches import get_va_target


class TeacherStudentDoubleOpen:

    VA_KEY = "duo_open"

    def __init__(self, ui, detail, log_text):
        self.ui = ui
        self._detail = detail
        self._log = log_text
        self._target = get_va_target(self.VA_KEY)
        self._build()

    # ------------------------------------------------------------
    def _build(self):
        d = self._detail

        # ── 文件选择 ──
        ff = ttk.LabelFrame(d, text="目标文件", padding=8)
        ff.pack(fill=tk.X, padx=2, pady=3)
        ff.columnconfigure(1, weight=1)
        self.var_tea = tk.StringVar()
        self.var_stu = tk.StringVar()
        self._file_row(ff, 0, "教师端 Teacher.exe", self.var_tea, "Teacher.exe")
        self._file_row(ff, 1, "学生端 Student.exe", self.var_stu, "Student.exe")

        # ── 选项 ──
        of = ttk.LabelFrame(d, text="选项", padding=8)
        of.pack(fill=tk.X, padx=2, pady=3)
        of.columnconfigure(1, weight=1)
        self.mode = tk.StringVar(value="newfile")
        ttk.Radiobutton(of, text="生成新文件  *_duo_open.exe（推荐，不动原文件）",
                        variable=self.mode, value="newfile").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=4)
        ttk.Radiobutton(of, text="原地修改（自动备份 <文件>.duo_open.bak）",
                        variable=self.mode, value="inplace").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=4)
        self.strict = tk.BooleanVar(value=True)
        ttk.Checkbutton(of, text="严格校验（函数特征缺失时中止）",
                        variable=self.strict).grid(
            row=2, column=0, columnspan=2, sticky=tk.W, padx=4, pady=(2, 4))

        # 自动填充默认路径（延迟到 root 可用）
        self.ui.root.after(30, self._autofill)

    def _file_row(self, parent, row, label, var, default_name):
        ttk.Label(parent, text=label).grid(row=row, column=0, sticky=tk.W,
                                           padx=6, pady=4)
        ttk.Entry(parent, textvariable=var).grid(row=row, column=1,
                                                 sticky=tk.EW, padx=4)
        ttk.Button(parent, text="浏览…", width=8,
                   command=lambda: self._browse(var, label, default_name)).grid(
            row=row, column=2, padx=6)

    def _autofill(self):
        if not self.var_tea.get().strip():
            p = resolve_target("Teacher.exe")
            if p:
                self.var_tea.set(p)
        if not self.var_stu.get().strip():
            p = resolve_target("Student.exe")
            if p:
                self.var_stu.set(p)

    def _browse(self, var, title, default_name):
        p = filedialog.askopenfilename(
            title=f"选择 {default_name}",
            filetypes=[("可执行文件", "*.exe"), ("所有文件", "*.*")])
        if p:
            var.set(p)

    def _paths(self):
        t = self.var_tea.get().strip()
        s = self.var_stu.get().strip()
        if not t or not s:
            messagebox.showwarning("缺少文件", "请先选择 Teacher.exe 和 Student.exe。")
            return None
        for p in (t, s):
            if not os.path.exists(p):
                messagebox.showerror("文件不存在", p)
                return None
        return t, s

    def _executors(self):
        t, s = self._paths() or (None, None)
        if not t or not s:
            return None, None
        return (VAPatchExecutor(self._target, t, role="teacher"),
                VAPatchExecutor(self._target, s, role="student"))

    def _run(self, func, ok_msg, fail_msg):
        clear_text(self._log)
        self.ui.run_with_log(func, self._log,
                             on_done=lambda ok: self.ui.show_status(
                                 ok_msg if ok else fail_msg),
                             label="duo_open")

    # ------------------------------------------------------------
    def _do_preview(self):
        if not self._paths():
            return
        tea, stu = self._executors()

        def func():
            tea.dry_run(strict=self.strict.get())
            stu.dry_run(strict=self.strict.get())

        self._run(func, "预览完成（未写盘）", "预览出错，查看日志")

    def _do_build(self):
        if not self._paths():
            return
        tea, stu = self._executors()
        inplace = (self.mode.get() == "inplace")
        if inplace and not self.ui.confirm(
                "将直接修改原文件（自动生成 .duo_open.bak 备份）。\n确定继续？"):
            return

        def func():
            tea.patch(inplace=inplace, strict=self.strict.get())
            stu.patch(inplace=inplace, strict=self.strict.get())

        self._run(func, "双开版生成完成", "生成失败，查看日志")

    def _do_restore(self):
        if not self._paths():
            return
        tea, stu = self._executors()

        def func():
            tea.restore()
            stu.restore()

        self._run(func, "还原完成", "还原失败，查看日志")

    def _open_dir(self):
        d = None
        for v in (self.var_tea, self.var_stu):
            if v.get().strip():
                d = os.path.dirname(v.get().strip())
                break
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
            ("预览 (Dry-run)", self._do_preview),
            ("生成双开版", self._do_build),
            ("还原（原地模式）", self._do_restore),
            ("打开目录", self._open_dir),
        ]