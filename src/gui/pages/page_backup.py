# src/gui/pages/page_backup.py
# 备份/恢复页 —— 管理 OsEasy 关键文件的备份与恢复

import flet as ft

from src.modules.file_handler import backup_oe_files, restore_oe_file, restore_oe_key_dlls
from config import BACKUP_FILES


class PageBackup:

    def __init__(self, ui):
        self.ui = ui

    # ---- 回调 ----

    def _backup_all(self, *e):
        backup_oe_files()
        self.ui.show_snakemessage(f"已备份 {len(BACKUP_FILES)} 个关键文件")

    def _restore_all(self, *e):
        restore_oe_key_dlls()
        self.ui.show_snakemessage(f"已恢复 {len(BACKUP_FILES)} 个关键文件")

    def _restore_one(self, filename):
        def _do(*e):
            restore_oe_file(filename)
            self.ui.show_snakemessage(f"已恢复: {filename}")
        return _do

    # ---- 构建页面 ----

    def build(self):
        ui = self.ui

        # 分组显示恢复按钮
        groups = [
            ("🔒 锁定相关", ["LockKeyboard.dll", "LoadDriver.exe", "KbDriver.exe"]),
            ("🖥️ 黑屏/控屏", ["BlackSlient.exe", "MultiClient.exe"]),
            ("🌐 网络/USB", ["OeNetLimit.sys", "OeNetLimitSetup.exe", "oenetlimitx64.cat", "easyusbflt.sys", "ProcFireWall.sys"]),
            ("📡 嗅探", ["x86\\LISSNetInfoSniffer.exe"]),
        ]

        restore_controls = []
        for title, files in groups:
            restore_controls.append(ft.Text(title, size=16, weight=ft.FontWeight.BOLD))
            for f in files:
                restore_controls.append(
                    ft.FilledTonalButton(
                        text=f"恢复 {f}",
                        on_click=self._restore_one(f),
                        tooltip=f"从备份恢复 {f} 到 OsEasy 安装目录",
                    )
                )

        return ft.Column(controls=[
            ui.yiyanshowtext, ft.Divider(height=1),
            ft.Text("📦 备份", size=18, weight=ft.FontWeight.BOLD),
            ft.FilledTonalButton(
                text="备份所有关键文件",
                icon=ft.Icons.BACKUP,
                on_click=self._backup_all,
                tooltip=f"将 {len(BACKUP_FILES)} 个 OsEasy 关键文件备份到工具箱数据目录",
            ),
            ft.Divider(height=1),
            ft.Text("🔄 恢复", size=18, weight=ft.FontWeight.BOLD),
            ft.FilledTonalButton(
                text="恢复所有关键文件",
                icon=ft.Icons.RESTORE,
                on_click=self._restore_all,
                tooltip=f"从备份恢复全部 {len(BACKUP_FILES)} 个文件到 OsEasy 安装目录",
            ),
            *restore_controls,
        ])
