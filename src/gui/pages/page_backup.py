# src/gui/pages/page_backup.py
# 文件管理页 —— 管理 OsEasy 关键文件的备份与恢复 + 清理脚本

import tkinter as tk
from tkinter import ttk

from src.modules.file_handler import (
    backup_oe_files, backup_oe_file, restore_oe_file,
    restore_oe_key_dlls, del_self_cmd_files,
)
from config import BACKUP_FILES


class PageBackup:

    def __init__(self, ui):
        self.ui = ui

    # 恢复分组（与 BACKUP_FILES 注释分组一致）
    _GROUPS = [
        ("锁定相关", ["LockKeyboard.dll", "LoadDriver.exe", "KbDriver.exe"]),
        ("黑屏/控屏", ["BlackSlient.exe", "MultiClient.exe"]),
        ("网络/USB", ["OeNetLimit.sys", "OeNetLimitSetup.exe", "oenetlimitx64.cat", "easyusbflt.sys", "ProcFireWall.sys"]),
        ("目录保护", ["FbdATS.sys"]),
        ("嗅探", ["x86\\LISSNetInfoSniffer.exe"]),
    ]

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # ---- 上部：控件（可滚动） ----
        _, ctrl_frame = ui.make_scrollable(frame)

        # 左右双列：左=备份，右=恢复
        duo = ttk.Frame(ctrl_frame)
        duo.pack(fill=tk.X, pady=2)
        duo.columnconfigure(0, weight=1, uniform="duo")
        duo.columnconfigure(1, weight=1, uniform="duo")

        # ===== 左列：备份 =====
        left = ttk.Frame(duo)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 2))

        backup_frame = ttk.LabelFrame(left, text="备份", padding=5)
        backup_frame.pack(fill=tk.X)
        btn_bak = ttk.Button(backup_frame, text="备份所有关键文件", command=self._backup_all)
        btn_bak.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_bak, "FUNC_BAK_ALL")

        # 单个文件备份（与恢复列表一一对应）
        for title, files in self._GROUPS:
            gf = ttk.LabelFrame(left, text=title, padding=5)
            gf.pack(fill=tk.X, pady=(4, 0))
            for f in files:
                btn = ttk.Button(gf, text=f"备份 {f}", command=lambda fn=f: self._backup_one(fn))
                btn.pack(fill=tk.X, padx=2, pady=1)
                ui.bind_tooltip(btn, "FUNC_BAK_BACKUP_ONE", filename=f)

        # ===== 右列：恢复 =====
        right = ttk.Frame(duo)
        right.grid(row=0, column=1, sticky="nsew", padx=(2, 0))

        restore_all_frame = ttk.LabelFrame(right, text="恢复", padding=5)
        restore_all_frame.pack(fill=tk.X)
        btn_restore = ttk.Button(restore_all_frame, text="恢复所有关键文件", command=self._restore_all)
        btn_restore.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_restore, "FUNC_BAK_RESTORE_ALL")

        for title, files in self._GROUPS:
            gf = ttk.LabelFrame(right, text=title, padding=5)
            gf.pack(fill=tk.X, pady=(4, 0))
            for f in files:
                btn = ttk.Button(gf, text=f"恢复 {f}", command=lambda fn=f: self._restore_one(fn))
                btn.pack(fill=tk.X, padx=2, pady=1)
                ui.bind_tooltip(btn, "FUNC_BAK_RESTORE_ONE", filename=f)

        # 清理（横跨整行）
        clean_frame = ttk.LabelFrame(ctrl_frame, text="清理", padding=5)
        clean_frame.pack(fill=tk.X, pady=2)
        btn_clean = ttk.Button(clean_frame, text="删除脚本文件", command=lambda: del_self_cmd_files())
        btn_clean.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_clean, "FUNC_DEL_SCRIPTS")

        # ---- 下部：输出区域（固定底部） ----
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.output_text = ui.make_output_text(output_frame, height=5)

        return frame

    def _backup_all(self, *e):
        s = backup_oe_files()
        parts = []
        if s["backed"]:
            parts.append(f"新备份 {s['backed']} 个")
        if s["skipped"]:
            parts.append(f"已有备份跳过 {s['skipped']} 个")
        if s["missing"]:
            parts.append(f"源文件不存在 {s['missing']} 个")
        if s["failed"]:
            parts.append(f"失败 {s['failed']} 个")
        if not parts:
            parts.append("无需备份")
        self.ui.show_snakemessage("；".join(parts))

    def _backup_one(self, filename):
        status = backup_oe_file(filename)
        msg = {
            "ok": f"已备份: {filename}",
            "src_missing": f"备份失败：源文件不存在 {filename}",
            "denied": f"备份失败：权限不足，无法访问 {filename}（请以管理员运行）",
            "dst_exists": f"备份失败：目标已存在 {filename}",
        }.get(status, f"备份失败: {filename}（{status}）")
        self.ui.show_snakemessage(msg)

    def _restore_all(self, *e):
        restore_oe_key_dlls()

    def _restore_one(self, filename):
        status = restore_oe_file(filename)
        msg = {
            "ok": f"已恢复: {filename}",
            "src_missing": f"恢复失败：无备份文件 {filename}（请先执行备份）",
            "denied": f"恢复失败：权限不足，无法写入 {filename}（请以管理员运行）",
        }.get(status, f"恢复失败: {filename}（{status}）")
        self.ui.show_snakemessage(msg)
