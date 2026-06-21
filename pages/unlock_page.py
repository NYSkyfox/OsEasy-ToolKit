"""
其他管理/解锁页面
"""

import tkinter as tk
from tkinter import ttk, messagebox
from pages.base_page import BasePage
from utils.helpers import check_file_exists


class UnlockPage(BasePage):
    """解锁管理页面"""

    def __init__(self, parent, app):
        self.network = app.network_service
        self.usb = app.usb_service
        super().__init__(parent, app)

    def create_widgets(self) -> None:
        """创建解锁页面控件"""
        # 一言
        self.yiyan_label = self.create_label(
            self, self.app.get_random_yiyan(),
            font_size=10, bold=True
        )
        self.yiyan_label.pack(pady=(15, 10), padx=20)

        # 分隔线
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=5)

        # 解锁操作卡片
        unlock_card = self.create_card(self, "解锁操作")
        unlock_card.pack(fill="x", padx=20, pady=10)

        # 删除关键文件
        del_btn = self.create_button(
            unlock_card, "删除键盘锁&控屏&黑屏安静（注销）",
            self._run_full_unlock, "primary", 30
        )
        del_btn.pack(pady=5)

        del_info = self.create_label(
            unlock_card,
            "将删除 LockKeyboard.dll、MultiClient.exe、BlackSlient.exe\n"
            "执行后会注销系统",
            font_size=8
        )
        del_info.pack()

        # 仅删除控屏
        del_mc_btn = self.create_button(
            unlock_card, "仅删除控屏锁定程序",
            self._run_del_multiclient, "primary", 30
        )
        del_mc_btn.pack(pady=5)

        # 网络解锁
        net_card = self.create_card(self, "网络解锁")
        net_card.pack(fill="x", padx=20, pady=10)

        net_btn = self.create_button(
            net_card, "停止网络管控服务",
            self._unlock_network, "primary", 25
        )
        net_btn.pack(pady=5)

        net_info = self.create_label(
            net_card,
            "停止 OeNetlimit 服务并 kill 相关进程",
            font_size=8
        )
        net_info.pack()

        # USB 解锁
        usb_card = self.create_card(self, "USB 解锁")
        usb_card.pack(fill="x", padx=20, pady=10)

        usb_btn = self.create_button(
            usb_card, "关闭 USB 管控（实验性）",
            self._unlock_usb, "primary", 25
        )
        usb_btn.pack(pady=5)

        usb_info = self.create_label(
            usb_card,
            "删除 easyusbflt 驱动，可能需要注销生效",
            font_size=8
        )
        usb_info.pack()

        # 恢复操作卡片
        restore_card = self.create_card(self, "恢复操作")
        restore_card.pack(fill="x", padx=20, pady=10)

        restore_all_btn = self.create_button(
            restore_card, "恢复所有备份文件",
            self._restore_all, "primary", 25
        )
        restore_all_btn.pack(pady=3)

        # 单个恢复
        single_frame = ttk.Frame(restore_card)
        single_frame.pack(fill="x", pady=5)

        restore_mc_btn = self.create_button(
            single_frame, "恢复 MultiClient",
            lambda: self._restore_single("MultiClient.exe"), "primary", 15
        )
        restore_mc_btn.pack(side="left", padx=2)

        restore_bs_btn = self.create_button(
            single_frame, "恢复 BlackSlient",
            lambda: self._restore_single("BlackSlient.exe"), "primary", 15
        )
        restore_bs_btn.pack(side="right", padx=2)

        # 清理脚本
        clean_btn = self.create_button(
            restore_card, "清理生成的脚本文件",
            self._clean_scripts, "primary", 25
        )
        clean_btn.pack(pady=5)
    
    def _run_full_unlock(self) -> None:
        """执行完整解锁"""
        if messagebox.askyesno(
            "确认", 
            "将删除关键文件并注销系统，是否继续？"
        ):
            self.unlock.run_unlock(del_multiclient=True, logout=True)
            self.show_status("解锁脚本已启动，系统将注销", "warning")
    
    def _run_del_multiclient(self) -> None:
        """仅删除控屏程序"""
        if messagebox.askyesno(
            "确认",
            "将仅删除 MultiClient.exe，是否继续？"
        ):
            self.unlock.run_unlock(del_multiclient=True, logout=False)
            self.show_status("控屏程序删除脚本已启动", "warning")
    
    def _unlock_network(self) -> None:
        """解锁网络"""
        result = self.network.unlock_network(self.student)
        self.show_status(result, "success")
    
    def _unlock_usb(self) -> None:
        """解锁 USB"""
        result = self.usb.unlock_usb()
        self.show_status(result, "warning")
    
    def _restore_all(self) -> None:
        """恢复所有备份"""
        success, failed = self.unlock.restore_files()
        if success:
            self.show_status("所有文件恢复成功", "success")
        else:
            msg = f"以下文件恢复失败: {', '.join(failed)}"
            self.show_status(msg, "error")
    
    def _restore_single(self, filename: str) -> None:
        """恢复单个文件"""
        if self.unlock.restore_single_file(filename):
            self.show_status(f"{filename} 恢复成功", "success")
        else:
            self.show_status(f"{filename} 恢复失败", "error")
    
    def _clean_scripts(self) -> None:
        """清理脚本文件"""
        import os
        import config as cfg
        
        files = ["killer.bat", "unlock.bat", "unlock_net.bat", 
                 "temp.bat", "killer_v2.bat"]
        cleaned = 0
        
        for filename in files:
            path = os.path.join(cfg.CMD_FILE_PATH, filename)
            if check_file_exists(path):
                try:
                    os.remove(path)
                    cleaned += 1
                except:
                    pass
        
        self.show_status(f"已清理 {cleaned} 个脚本文件", "success")
    
    def refresh(self) -> None:
        """刷新页面"""
        self.yiyan_label.config(text=self.app.get_random_yiyan())