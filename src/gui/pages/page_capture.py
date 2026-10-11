# src/gui/pages/page_capture.py
# 截屏页（页面 3）—— 阻止 / 使用假屏幕截图
#
# 驱动 src/modules/screen_capture.py：
#   process_one(dll_path, targets, dry_run, inplace, strict, fake_screen, convert_bmp)
#     targets 用于 NOP 模式（key 列表，默认 ['pipeline']）
#     fake_screen 非空时进入假截图模式（BMP 路径）
#   restore_one(dll_path)
#
# 输出经 ui.run_with_log 捕获（module 内部用 print）。

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.gui.widgets import make_scrollable, make_output_text, clear_text
from src.core import resolve_target
from src.modules import screen_capture as sc


class PageCapture:

    def __init__(self, ui):
        self.ui = ui
        self._after_id = None

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)
        self._frame = frame
        _, scroll = make_scrollable(frame)

        # ── 目标 DLL ──
        ff = ttk.LabelFrame(scroll, text="目标文件", padding=8)
        ff.pack(fill=tk.X, padx=5, pady=3)
        ff.columnconfigure(1, weight=1)
        self.dll_var = tk.StringVar()
        ttk.Label(ff, text="StudentLogic.dll：").grid(row=0, column=0, sticky=tk.W,
                                                      padx=4)
        ttk.Entry(ff, textvariable=self.dll_var).grid(row=0, column=1,
                                                      sticky=tk.EW, padx=4)
        ttk.Button(ff, text="浏览…", width=8, command=self._browse_dll).grid(
            row=0, column=2, padx=4)

        # ── 工作模式 ──
        mf = ttk.LabelFrame(scroll, text="工作模式", padding=8)
        mf.pack(fill=tk.X, padx=5, pady=3)
        self.mode_var = tk.StringVar(value="nop")
        ttk.Radiobutton(mf, text="停止截图发送（教师端画面定格，状态灯在线）",
                        variable=self.mode_var, value="nop").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=4)
        ttk.Radiobutton(mf, text="假截图（用本地 BMP 替换，教师端显示固定假画面）",
                        variable=self.mode_var, value="fake").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=4)

        # ── 假截图 BMP（fake 模式才生效） ──
        self._bmp_frame = ttk.LabelFrame(scroll, text="假截图 BMP（32bpp 无压缩，路径 ≤ 23 字符）",
                                         padding=8)
        self._bmp_frame.columnconfigure(1, weight=1)
        self.bmp_var = tk.StringVar()
        ttk.Entry(self._bmp_frame, textvariable=self.bmp_var).grid(
            row=0, column=0, columnspan=2, sticky=tk.EW, padx=4, pady=2)
        ttk.Button(self._bmp_frame, text="浏览…", width=8,
                   command=self._browse_bmp).grid(row=0, column=2, padx=4)
        self.convert_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self._bmp_frame, text="自动转换 bottom-up → top-down",
                        variable=self.convert_var).grid(
            row=1, column=0, columnspan=3, sticky=tk.W, padx=4)

        # ── 选项（BMP 框插入到此框之前） ──
        self._options_frame = ttk.LabelFrame(scroll, text="输出选项", padding=8)
        self._options_frame.pack(fill=tk.X, padx=5, pady=3)
        self.out_var = tk.StringVar(value="newfile")
        ttk.Radiobutton(self._options_frame, text="生成新文件（不动原文件）",
                        variable=self.out_var, value="newfile").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=4)
        ttk.Radiobutton(self._options_frame, text="原地修改（自动备份 <文件>.bak）",
                        variable=self.out_var, value="inplace").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=4)

        # 默认 nop 模式：BMP 框隐藏（模式变化时切换显示）
        self.mode_var.trace_add("write", self._on_mode_changed)

        # ── 按钮 ──
        bar = ttk.Frame(scroll)
        bar.pack(fill=tk.X, padx=5, pady=4)
        ttk.Button(bar, text="预览 (Dry-run)", command=self._do_preview).pack(
            side=tk.LEFT, padx=(0, 6))
        ttk.Button(bar, text="应用", command=self._do_apply).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(bar, text="还原", command=self._do_restore).pack(
            side=tk.LEFT, padx=6)
        ttk.Button(bar, text="清空日志", command=lambda: clear_text(self._log)).pack(
            side=tk.RIGHT, padx=(6, 0))

        # ── 日志 ──
        self._log = make_output_text(scroll, height=12)
        self._log.pack(fill=tk.BOTH, expand=True, padx=5, pady=(0, 5))

        # 自动填充 DLL 路径
        self.ui.root.after(30, self._autofill)
        return frame

    # ------------------------------------------------------------
    def _autofill(self):
        if not self.dll_var.get().strip():
            p = resolve_target("StudentLogic.dll")
            if p:
                self.dll_var.set(p)

    def _on_mode_changed(self, *args):
        if self.mode_var.get() == "fake":
            self._bmp_frame.pack(fill=tk.X, padx=5, pady=3,
                                 before=self._options_frame)
        else:
            self._bmp_frame.pack_forget()

    def _browse_dll(self):
        p = filedialog.askopenfilename(
            title="选择 StudentLogic.dll",
            filetypes=[("DLL", "*.dll"), ("所有文件", "*.*")])
        if p:
            self.dll_var.set(p)

    def _browse_bmp(self):
        p = filedialog.askopenfilename(
            title="选择假截图 BMP",
            filetypes=[("BMP", "*.bmp"), ("所有文件", "*.*")])
        if p:
            self.bmp_var.set(p)

    def _dll(self):
        p = self.dll_var.get().strip()
        if not p:
            messagebox.showwarning("缺少文件", "请先选择 StudentLogic.dll。")
            return None
        if not os.path.isfile(p):
            messagebox.showerror("文件不存在", p)
            return None
        return p

    def _do_preview(self):
        dll = self._dll()
        if not dll:
            return
        fake = self.bmp_var.get().strip() if self.mode_var.get() == "fake" else None
        inplace = self.out_var.get() == "inplace"
        convert = self.convert_var.get()

        def func():
            sc.process_one(dll, sc.DEFAULT_TARGETS, dry_run=True, inplace=inplace,
                           strict=True, fake_screen=fake, convert_bmp=convert)

        self._run(func, "预览完成（未写盘）", "预览出错，查看日志")

    def _do_apply(self):
        dll = self._dll()
        if not dll:
            return
        fake = self.bmp_var.get().strip() if self.mode_var.get() == "fake" else None
        if self.mode_var.get() == "fake" and not fake:
            messagebox.showwarning("缺少 BMP", "假截图模式需指定 BMP 文件。")
            return
        if self.mode_var.get() == "fake" and len(fake) > sc.SC_MAX_FP:
            messagebox.showerror("路径过长",
                                 f"BMP 路径 {len(fake)} 字符 > {sc.SC_MAX_FP}，请改用短路径（如 C:\\os_fake.bmp）。")
            return
        inplace = self.out_var.get() == "inplace"
        convert = self.convert_var.get()
        if inplace and not self.ui.confirm("将直接修改原文件（自动生成 .bak 备份）。\n确定继续？"):
            return

        def func():
            sc.process_one(dll, sc.DEFAULT_TARGETS, dry_run=False, inplace=inplace,
                           strict=True, fake_screen=fake, convert_bmp=convert)

        self._run(func, "Patch 完成", "应用失败，查看日志")

    def _do_restore(self):
        dll = self._dll()
        if not dll:
            return

        def func():
            sc.restore_one(dll)

        self._run(func, "已还原", "还原失败，查看日志")

    def _run(self, func, ok_msg, fail_msg):
        clear_text(self._log)
        self.ui.run_with_log(func, self._log,
                             on_done=lambda ok: self.ui.show_status(
                                 ok_msg if ok else fail_msg),
                             label="screen_capture")