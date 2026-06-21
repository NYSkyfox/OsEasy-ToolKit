"""
广播命令页面 - 手动管理广播命令
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pages.base_page import BasePage


class CommandPage(BasePage):
    """广播命令管理页面"""

    def create_widgets(self) -> None:
        """创建广播命令页面控件"""
        # 一言
        self.yiyan_label = self.create_label(
            self, self.app.get_random_yiyan(),
            font_size=10, bold=True
        )
        self.yiyan_label.pack(pady=(15, 10), padx=20)

        # 分隔线
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=5)

        # 命令输入卡片
        input_card = self.create_card(self, "手动输入命令")
        input_card.pack(fill="x", padx=20, pady=10)

        # 命令输入框
        self.cmd_entry = tk.Text(
            input_card,
            height=4,
            font=("Consolas", 9),
            wrap="word"
        )
        self.cmd_entry.pack(fill="x", pady=5)

        # 如果有已保存的命令，显示出来
        if self.broadcast.cmd:
            self.cmd_entry.insert("1.0", self.broadcast.cmd)

        # 按钮区域
        btn_frame = ttk.Frame(input_card)
        btn_frame.pack(fill="x", pady=5)

        save_btn = self.create_button(
            btn_frame, "保存命令",
            self._save_cmd, "primary", 15
        )
        save_btn.pack(side="left", padx=2)

        save_ip_btn = self.create_button(
            btn_frame, "保存并替换IP",
            self._save_cmd_replace_ip, "primary", 15
        )
        save_ip_btn.pack(side="right", padx=2)

        # 从教师机IP生成
        gen_card = self.create_card(self, "从教师机IP生成")
        gen_card.pack(fill="x", padx=20, pady=10)

        ip_frame = ttk.Frame(gen_card)
        ip_frame.pack(fill="x", pady=5)

        ip_label = self.create_label(ip_frame, "教师机IP:")
        ip_label.pack(side="left")

        self.ip_entry = self.create_entry(ip_frame)
        self.ip_entry.pack(side="left", fill="x", expand=True, padx=5)

        gen_btn = self.create_button(
            gen_card, "生成命令",
            self._generate_from_ip, "primary", 20
        )
        gen_btn.pack(pady=5)

        # 从日志读取
        log_card = self.create_card(self, "从日志读取")
        log_card.pack(fill="x", padx=20, pady=10)

        log_btn = self.create_button(
            log_card, "从 ScreenRender.log 提取命令",
            self._parse_log, "primary", 30
        )
        log_btn.pack(pady=5)

        # 文件操作
        file_card = self.create_card(self, "文件操作")
        file_card.pack(fill="x", padx=20, pady=10)

        file_frame = ttk.Frame(file_card)
        file_frame.pack(fill="x", pady=5)

        export_btn = self.create_button(
            file_frame, "导出到文件",
            self._export_cmd, "primary", 15
        )
        export_btn.pack(side="left", padx=2)

        import_btn = self.create_button(
            file_frame, "从文件导入",
            self._import_cmd, "primary", 15
        )
        import_btn.pack(side="right", padx=2)

        # 当前命令信息
        info_card = self.create_card(self, "当前命令信息")
        info_card.pack(fill="x", padx=20, pady=10)

        self.info_label = self.create_label(
            info_card,
            self._get_cmd_info(),
            font_size=9
        )
        self.info_label.pack(anchor="w")
    
    def _get_cmd_info(self) -> str:
        """获取命令信息文本"""
        if not self.broadcast.cmd:
            return "当前未保存广播命令"
        
        teacher_ip = self.broadcast.extract_teacher_ip() or "未知"
        return (
            f"命令已保存\n"
            f"教师机IP: {teacher_ip}\n"
            f"命令长度: {len(self.broadcast.cmd)} 字符"
        )
    
    def _save_cmd(self) -> None:
        """保存命令"""
        cmd = self.cmd_entry.get("1.0", tk.END).strip()
        if not cmd:
            self.show_status("命令不能为空", "error")
            return
        
        if self.broadcast.save_cmd(cmd, replace_ip=False):
            self.info_label.config(text=self._get_cmd_info())
            self.show_status("命令已保存", "success")
        else:
            self.show_status("保存失败", "error")
    
    def _save_cmd_replace_ip(self) -> None:
        """保存命令并替换本地IP"""
        cmd = self.cmd_entry.get("1.0", tk.END).strip()
        if not cmd:
            self.show_status("命令不能为空", "error")
            return
        
        if self.broadcast.save_cmd(cmd, replace_ip=True):
            self.info_label.config(text=self._get_cmd_info())
            self.show_status("命令已保存（IP已替换）", "success")
        else:
            self.show_status("保存失败", "error")
    
    def _generate_from_ip(self) -> None:
        """从教师机IP生成命令"""
        ip = self.ip_entry.get().strip()
        if not ip:
            self.show_status("请输入教师机IP", "error")
            return
        
        if self.broadcast.generate_cmd_from_teacher_ip(ip):
            # 更新输入框
            self.cmd_entry.delete("1.0", tk.END)
            self.cmd_entry.insert("1.0", self.broadcast.cmd)
            self.info_label.config(text=self._get_cmd_info())
            self.show_status(f"已根据IP {ip} 生成命令", "success")
        else:
            self.show_status("生成命令失败", "error")
    
    def _parse_log(self) -> None:
        """从日志解析命令"""
        success, cmds = self.broadcast.parse_log_file()
        if success and cmds:
            # 使用最后一条命令
            last_cmd = cmds[-1]
            self.broadcast.save_cmd(last_cmd, replace_ip=False)
            
            # 更新输入框
            self.cmd_entry.delete("1.0", tk.END)
            self.cmd_entry.insert("1.0", last_cmd)
            self.info_label.config(text=self._get_cmd_info())
            
            self.show_status(f"从日志提取到 {len(cmds)} 条命令", "success")
        else:
            self.show_status("未从日志中找到命令", "error")
    
    def _export_cmd(self) -> None:
        """导出命令到文件"""
        if not self.broadcast.cmd:
            self.show_status("没有可导出的命令", "error")
            return
        
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")],
            initialfile="command.txt"
        )
        
        if filepath:
            if self.broadcast.save_cmd_to_file(filepath):
                self.show_status(f"已导出到 {filepath}", "success")
            else:
                self.show_status("导出失败", "error")
    
    def _import_cmd(self) -> None:
        """从文件导入命令"""
        filepath = filedialog.askopenfilename(
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        
        if filepath:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    cmd = f.read().strip()
                
                self.cmd_entry.delete("1.0", tk.END)
                self.cmd_entry.insert("1.0", cmd)
                self.broadcast.save_cmd(cmd, replace_ip=False)
                self.info_label.config(text=self._get_cmd_info())
                self.show_status("命令已导入", "success")
            except Exception as e:
                self.show_status(f"导入失败: {e}", "error")
    
    def refresh(self) -> None:
        """刷新页面"""
        self.yiyan_label.config(text=self.app.get_random_yiyan())
        self.info_label.config(text=self._get_cmd_info())