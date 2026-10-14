# src/gui/pages/patch_panels/student_fake_screenshot.py
# 「阻止 / 使用假屏幕截图」面板 —— VA 型 patch
# 驱动 src/core/va_patch.VAPatchExecutor + src/modules/patches/screen_capture 配置。
# 配置含 5 个点：4 个 NOP 点（pipeline/bplt/screenrender/wsasend）+ 1 个假截图 shellcode 点。
# 两种工作模式（对应 GUI 单选）：
#   nop   —— 勾选要 patch 的 NOP 点（默认 pipeline），传入 labels
#   fake  —— 用本地 BMP 替换 BitBlt（传 labels=["fake_screen"] + fake_screen=BMP 路径）
# 面板契约：__init__(ui, detail, log_text)，build 进 detail，日志写 log_text。

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.gui.widgets import clear_text
from src.core import resolve_target
from src.core.va_patch import VAPatchExecutor, validate_bmp, convert_bmp_topdown
from src.modules.patches import get_va_target

# NOP 点标签的中文说明（用于复选框显示）
_NOP_DESC = {
    "pipeline": "屏幕截图完整流水线（截屏→编码→BMP→WSASend）",
    "bplt": "BitBlt 全屏截图",
    "screenrender": "ScreenRender 子进程启动（远程监视推流）",
    "wsasend": "WSASend 通用网络发送（影响面大）",
}


class StudentFakeScreenshot:

    VA_KEY = "screen_capture"

    def __init__(self, ui, detail, log_text):
        self.ui = ui
        self._detail = detail
        self._log = log_text
        self._target = get_va_target(self.VA_KEY)
        self._nop_vars = {}     # label -> BooleanVar
        self._build()

    # ------------------------------------------------------------
    def _build(self):
        d = self._detail

        # ── 目标 DLL ──
        ff = ttk.LabelFrame(d, text="目标文件", padding=8)
        ff.pack(fill=tk.X, padx=2, pady=3)
        ff.columnconfigure(1, weight=1)
        self.dll_var = tk.StringVar()
        ttk.Label(ff, text="StudentLogic.dll：").grid(row=0, column=0, sticky=tk.W,
                                                      padx=4)
        ttk.Entry(ff, textvariable=self.dll_var).grid(row=0, column=1,
                                                      sticky=tk.EW, padx=4)
        ttk.Button(ff, text="浏览…", width=8, command=self._browse_dll).grid(
            row=0, column=2, padx=4)

        # ── 工作模式 ──
        mf = ttk.LabelFrame(d, text="工作模式", padding=8)
        mf.pack(fill=tk.X, padx=2, pady=3)
        self.mode_var = tk.StringVar(value="nop")
        ttk.Radiobutton(mf, text="停止截图发送（教师端画面定格，状态灯在线）",
                        variable=self.mode_var, value="nop").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=4)
        ttk.Radiobutton(mf, text="假截图（用本地 BMP 替换，教师端显示固定假画面）",
                        variable=self.mode_var, value="fake").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=4)

        # ── NOP 点选择（nop 模式才显示） ──
        self._nop_frame = ttk.LabelFrame(
            d, text="NOP 模式 · 选择要 patch 的点", padding=8)
        self._nop_frame.columnconfigure(1, weight=1)
        self._build_nop_checkboxes(self._nop_frame)

        # ── 假截图 BMP（fake 模式才显示） ──
        self._bmp_frame = ttk.LabelFrame(
            d, text="假截图 BMP（32bpp 无压缩，路径 ≤ %d 字符）" %
            self._target.shellcode_max_fp, padding=8)
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

        # ── 输出选项 ──
        self._options_frame = ttk.LabelFrame(d, text="输出选项", padding=8)
        self._options_frame.pack(fill=tk.X, padx=2, pady=3)
        self.out_var = tk.StringVar(value="newfile")
        ttk.Radiobutton(self._options_frame, text="生成新文件（不动原文件）",
                        variable=self.out_var, value="newfile").grid(
            row=0, column=0, columnspan=2, sticky=tk.W, padx=4)
        ttk.Radiobutton(self._options_frame, text="原地修改（自动备份 <文件>.bak）",
                        variable=self.out_var, value="inplace").grid(
            row=1, column=0, columnspan=2, sticky=tk.W, padx=4)

        # mode 两个 frame 都先 pack 到输出选项上方（nop 在 bmp 之上），
        # 再由 _on_mode_changed 按模式切换显示
        self._bmp_frame.pack(fill=tk.X, padx=2, pady=3,
                             before=self._options_frame)
        self._nop_frame.pack(fill=tk.X, padx=2, pady=3,
                             before=self._options_frame)

        # 默认 nop 模式
        self.mode_var.trace_add("write", self._on_mode_changed)
        self._on_mode_changed()

        # 自动填充 DLL 路径
        self.ui.root.after(30, self._autofill)

    def _build_nop_checkboxes(self, parent):
        """从配置读取所有 NOP 点，构建复选框（默认勾选 pipeline）。"""
        for ft in self._target.files:
            for p in ft.patch_points:
                if p.shellcode_mode:
                    continue
                var = tk.BooleanVar(value=(p.label == "pipeline"))
                desc = _NOP_DESC.get(p.label, p.label)
                cb = ttk.Checkbutton(parent, text=p.label + " — " + desc,
                                     variable=var)
                cb.pack(anchor=tk.W, padx=4, pady=2)
                self._nop_vars[p.label] = var

    def _selected_nop_labels(self):
        return [lbl for lbl, var in self._nop_vars.items() if var.get()]

    def _autofill(self):
        if not self.dll_var.get().strip():
            p = resolve_target("StudentLogic.dll")
            if p:
                self.dll_var.set(p)

    def _on_mode_changed(self, *args):
        fake = (self.mode_var.get() == "fake")
        if fake:
            if self._bmp_frame.winfo_manager() != "pack":
                self._bmp_frame.pack(fill=tk.X, padx=2, pady=3,
                                     before=self._options_frame)
            if self._nop_frame.winfo_manager() == "pack":
                self._nop_frame.pack_forget()
        else:
            if self._nop_frame.winfo_manager() != "pack":
                self._nop_frame.pack(fill=tk.X, padx=2, pady=3,
                                     before=self._options_frame)
            if self._bmp_frame.winfo_manager() == "pack":
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

    def _executor(self, dll):
        return VAPatchExecutor(self._target, dll)

    def _resolve_bmp(self):
        """fake 模式：校验 BMP + 可选转换。返回 (bmp_path, ok)。"""
        bmp = self.bmp_var.get().strip()
        if not bmp:
            messagebox.showwarning("缺少 BMP", "假截图模式需指定 BMP 文件。")
            return None, False
        if len(bmp) > self._target.shellcode_max_fp:
            messagebox.showerror(
                "路径过长",
                "BMP 路径 %d 字符 > %d，请改用短路径（如 C:\\os_fake.bmp）。"
                % (len(bmp), self._target.shellcode_max_fp))
            return None, False
        if not os.path.isfile(bmp):
            messagebox.showerror("文件不存在", bmp)
            return None, False
        try:
            hdr = validate_bmp(bmp)
        except Exception as e:
            messagebox.showerror("BMP 校验失败", str(e))
            return None, False
        self.ui.show_status(
            "BMP %dx%d %dbpp" % (hdr["bi_width"], hdr["abs_height"],
                                 hdr["bi_bitcount"]))
        if hdr["is_bottom_up"] and self.convert_var.get():
            bmp = convert_bmp_topdown(bmp)
        elif hdr["is_bottom_up"]:
            messagebox.showwarning(
                "BMP 方向",
                "BMP 是 bottom-up！请勾选自动转换，或手动转换为 top-down。")
        return bmp, True

    # ------------------------------------------------------------
    def _do_preview(self):
        dll = self._dll()
        if not dll:
            return
        ex = self._executor(dll)
        if self.mode_var.get() == "fake":
            bmp, ok = self._resolve_bmp()
            if not ok:
                return

            def func():
                ex.dry_run(labels=["fake_screen"])
        else:
            labels = self._selected_nop_labels()
            if not labels:
                messagebox.showwarning("未选点", "请至少勾选一个 NOP 点。")
                return

            def func():
                ex.dry_run(labels=labels)

        self._run(func, "预览完成（未写盘）", "预览出错，查看日志")

    def _do_apply(self):
        dll = self._dll()
        if not dll:
            return
        ex = self._executor(dll)
        inplace = self.out_var.get() == "inplace"
        if inplace and not self.ui.confirm(
                "将直接修改原文件（自动生成 .bak 备份）。\n确定继续？"):
            return

        if self.mode_var.get() == "fake":
            bmp, ok = self._resolve_bmp()
            if not ok:
                return

            def func():
                ex.patch(inplace=inplace, labels=["fake_screen"], fake_screen=bmp)
        else:
            labels = self._selected_nop_labels()
            if not labels:
                messagebox.showwarning("未选点", "请至少勾选一个 NOP 点。")
                return

            def func():
                ex.patch(inplace=inplace, labels=labels)

        self._run(func, "Patch 完成", "应用失败，查看日志")

    def _do_restore(self):
        dll = self._dll()
        if not dll:
            return
        ex = self._executor(dll)

        def func():
            ex.restore()

        self._run(func, "已还原", "还原失败，查看日志")

    def _run(self, func, ok_msg, fail_msg):
        clear_text(self._log)
        self.ui.run_with_log(func, self._log,
                             on_done=lambda ok: self.ui.show_status(
                                 ok_msg if ok else fail_msg),
                             label="screen_capture")

    # ------------------------------------------------------------
    def buttons(self):
        return [
            ("预览 (Dry-run)", self._do_preview),
            ("应用", self._do_apply),
            ("还原", self._do_restore),
        ]