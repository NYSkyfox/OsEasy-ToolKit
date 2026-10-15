# src/gui/pages/patch_panels/dog_license.py
# 「教师端 加密狗 / 点数限制 解除」面板
# 驱动 src/core/dog_patch.DogPatchExecutor + src/patches/dog_license 配置。
#
# 与其余 6 个目标不同：本域是 4 个可选方案的组合工具，共享同一安装目录，
# 支持多选、批量检测 / 应用 / 还原。故面板为「目录 + 方案勾选 + 批量操作」布局，
# 而非「单文件路径 + 预览/应用/还原」。
# 面板契约：__init__(ui, detail, log_text)，build 进 detail，日志写 log_text。

import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

from src.gui.widgets import clear_text
from src.core.dog_patch import DogPatchExecutor
from src.patches import DOG_SOLUTIONS


class DogLicense:

    def __init__(self, ui, detail, log_text):
        self.ui = ui
        self._detail = detail
        self._log = log_text
        self._check_vars = {}
        self._build()

    # ------------------------------------------------------------
    def _build(self):
        d = self._detail
        ttk.Label(d, text="教师端授权解除：4 个方案可多选、可单独执行，"
                          "共享同一安装目录，自动备份 .bak、可一键还原。",
                  anchor=tk.W, foreground="gray", wraplength=660,
                  justify=tk.LEFT).pack(fill=tk.X, padx=2, pady=(0, 4))

        # ── 安装目录 ──
        ff = ttk.LabelFrame(d, text="安装目录（含 Teacher.exe / MainLogic.dll / skin\\）",
                            padding=8)
        ff.pack(fill=tk.X, padx=2, pady=3)
        ff.columnconfigure(1, weight=1)
        self.var_dir = tk.StringVar()
        ttk.Entry(ff, textvariable=self.var_dir).grid(
            row=0, column=0, columnspan=2, sticky=tk.EW, padx=2)
        ttk.Button(ff, text="浏览…", width=8, command=self._browse).grid(
            row=0, column=2, padx=(4, 0))

        # ── 方案勾选 ──
        fs = ttk.LabelFrame(d, text="破解方案（可多选）", padding=8)
        fs.pack(fill=tk.X, padx=2, pady=3)
        for i, sol in enumerate(DOG_SOLUTIONS, 1):
            row = ttk.Frame(fs)
            row.pack(fill=tk.X, pady=2)
            var = tk.BooleanVar(value=(sol.key == "max_connect"))
            self._check_vars[sol.key] = var
            head = ttk.Frame(row)
            head.pack(fill=tk.X)
            ttk.Checkbutton(head, text="%d. %s " % (i, sol.name),
                            variable=var).pack(side=tk.LEFT)
            ttk.Label(head, text=sol.tag, foreground="#1a5fb4",
                      font=("", 8)).pack(side=tk.LEFT, padx=4)
            ttk.Label(row, text="    " + sol.desc, foreground="gray",
                      font=("", 8), wraplength=620,
                      justify=tk.LEFT).pack(anchor=tk.W, fill=tk.X)
            if sol.key == "config_limit":
                lf = ttk.Frame(row)
                lf.pack(anchor=tk.W, padx=22)
                ttk.Label(lf, text="Limit 值：").pack(side=tk.LEFT)
                self.var_limit = tk.StringVar(value="999999")
                ttk.Entry(lf, textvariable=self.var_limit, width=12).pack(
                    side=tk.LEFT, padx=4)
                ttk.Label(lf, text="（0=关闭限制；大值≈无限；当前样本无狗=5）",
                          foreground="gray", font=("", 8)).pack(side=tk.LEFT, padx=4)
        if not hasattr(self, "var_limit"):
            self.var_limit = tk.StringVar(value="999999")

    # ------------------------------------------------------------
    def _browse(self):
        d = filedialog.askdirectory(
            title="选择 Os-Easy 教师端安装目录",
            initialdir=self.var_dir.get() or os.path.expanduser("~"))
        if d:
            self.var_dir.set(d)
            self._detect()

    def _dir(self):
        d = self.var_dir.get().strip()
        if not d or not os.path.isdir(d):
            messagebox.showwarning("缺少目录", "请先选择有效的 Os-Easy 教师端安装目录。")
            return None
        return d

    def _selected(self):
        return [s for s in DOG_SOLUTIONS if self._check_vars[s.key].get()]

    def _exec(self):
        d = self._dir()
        if not d:
            return None
        return DogPatchExecutor(d, log=lambda line: self.ui.log(self._log, line))

    # ------------------------------------------------------------
    def _detect(self):
        ex = self._exec()
        if ex is None:
            return
        clear_text(self._log)

        def work():
            ex.detect_all(DOG_SOLUTIONS)

        self.ui.run_in_thread(work, label="dog-detect")

    def _apply(self):
        ex = self._exec()
        if ex is None:
            return
        selected = self._selected()
        if not selected:
            messagebox.showwarning("未选择方案", "请至少勾选一个方案。")
            return
        if not self.ui.confirm(
                "即将对 %d 个方案打补丁（自动备份 .bak）：\n\n%s\n\n继续？" % (
                    len(selected),
                    "\n".join("  - " + s.name for s in selected))):
            return
        limit_val = self.var_limit.get().strip() or "999999"
        clear_text(self._log)

        def work():
            ok = 0
            self.ui.log(self._log, "开始应用补丁…")
            for sol in selected:
                ret, msg = ex.apply(sol, limit_val)
                mark = "OK" if ret else "失败"
                self.ui.log(self._log, "  [%s] %s: %s" % (mark, sol.name, msg))
                if ret:
                    ok += 1
            self.ui.log(self._log, "完成：成功 %d / %d" % (ok, len(selected)))
            ex.detect_all(DOG_SOLUTIONS)
            return ok == len(selected)

        self.ui.run_in_thread(
            work,
            on_done=lambda ok, _ok: self.ui.show_status(
                "授权解除应用完成" if _ok and ok else "应用未完成，查看日志"),
            label="dog-apply")

    def _restore(self):
        ex = self._exec()
        if ex is None:
            return
        if not self.ui.confirm("还原全部（用各自的 .bak 覆盖）？"):
            return
        clear_text(self._log)

        def work():
            self.ui.log(self._log, "开始还原…")
            for sol in DOG_SOLUTIONS:
                ret, msg = ex.restore(sol)
                mark = "OK" if ret else "跳过"
                self.ui.log(self._log, "  [%s] %s: %s" % (
                    mark, os.path.basename(sol.target), msg))
            ex.detect_all(DOG_SOLUTIONS)
            return True

        self.ui.run_in_thread(
            work,
            on_done=lambda _ok, _ok2: self.ui.show_status("还原完成"),
            label="dog-restore")

    def _open_dir(self):
        d = self.var_dir.get().strip()
        if not d:
            return
        try:
            if os.name == "nt":
                os.startfile(d)
            else:
                os.system('xdg-open "%s" 2>/dev/null || open "%s"' % (d, d))
        except Exception as e:
            messagebox.showerror("无法打开目录", str(e))

    # ------------------------------------------------------------
    def _refresh(self):
        self._detect()

    def buttons(self):
        return [
            ("① 检测状态", self._detect),
            ("② 应用选中补丁", self._apply),
            ("③ 还原全部", self._restore),
            ("打开目录", self._open_dir),
        ]