"""
进程管理页面
"""

import tkinter as tk
from tkinter import ttk
from pages.base_page import BasePage
from utils.process import ProcessManager


class ProcessPage(BasePage):
    """进程管理页面"""

    def __init__(self, parent, app):
        self.mmpc = app.mmpc_service
        self._guaqi_status = False
        self._killer_protect_var = None
        super().__init__(parent, app)

    def create_widgets(self) -> None:
        """创建进程管理页面控件"""
        # 一言
        self.yiyan_label = self.create_label(
            self, self.app.get_random_yiyan(),
            font_size=10, bold=True
        )
        self.yiyan_label.pack(pady=(15, 10), padx=20)

        # 分隔线
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=5)

        # 学生端状态卡片
        status_card = self.create_card(self, "学生端状态")
        status_card.pack(fill="x", padx=20, pady=10)

        self.status_label = self.create_label(
            status_card,
            f"路径: {self.student.path}\n"
            f"进程: {self.student.exe_name}\n"
            f"版本: v{self.student.version / 10 if self.student.version else '未知'}\n"
            f"运行中: {'是' if self.student.is_running else '否'}",
            font_size=9
        )
        self.status_label.pack(anchor="w")

        # MMPC 状态
        self.mmpc_label = self.create_label(
            status_card,
            f"MMPC 服务: {self.mmpc.get_status_text()}",
            font_size=9
        )
        self.mmpc_label.pack(anchor="w", pady=(5, 0))

        # 刷新状态按钮
        refresh_btn = self.create_button(
            status_card, "刷新状态",
            self._refresh_status, "primary", 20
        )
        refresh_btn.pack(pady=8)

        # 操作卡片
        action_card = self.create_card(self, "进程操作")
        action_card.pack(fill="x", padx=20, pady=10)

        # 挂起/恢复开关
        guaqi_frame = ttk.Frame(action_card)
        guaqi_frame.pack(fill="x", pady=5)

        guaqi_label = self.create_label(guaqi_frame, "挂起学生端进程")
        guaqi_label.pack(side="left")

        self.guaqi_var = tk.BooleanVar(value=False)
        self.guaqi_switch = ttk.Checkbutton(
            guaqi_frame,
            variable=self.guaqi_var,
            command=self._toggle_guaqi
        )
        self.guaqi_switch.pack(side="right")

        # 守护进程开关
        protect_frame = ttk.Frame(action_card)
        protect_frame.pack(fill="x", pady=5)

        protect_label = self.create_label(protect_frame, "外部cmd守护进程")
        protect_label.pack(side="left")

        self._killer_protect_var = tk.BooleanVar(value=False)
        protect_switch = ttk.Checkbutton(
            protect_frame,
            variable=self._killer_protect_var,
            command=self._toggle_killer_protect
        )
        protect_switch.pack(side="right")

        # 按钮区域
        btn_frame = ttk.Frame(action_card)
        btn_frame.pack(fill="x", pady=8)

        # MMPC 控制
        mmpc_btn = self.create_button(
            btn_frame, "切换 MMPC 服务",
            self._toggle_mmpc, "primary", 20
        )
        mmpc_btn.pack(pady=3)

        # 重启学生端
        restart_btn = self.create_button(
            btn_frame, "重启学生端",
            self._restart_student, "primary", 20
        )
        restart_btn.pack(pady=3)

        # 粘滞键后门
        sticky_frame = ttk.Frame(btn_frame)
        sticky_frame.pack(fill="x", pady=5)

        sticky_reg_btn = self.create_button(
            sticky_frame, "注册粘滞键后门",
            self._register_sticky, "primary", 18
        )
        sticky_reg_btn.pack(side="left", padx=2)

        sticky_del_btn = self.create_button(
            sticky_frame, "移除",
            self._remove_sticky, "primary", 8
        )
        sticky_del_btn.pack(side="right", padx=2)

        # 打开自带工具
        tool_btn = self.create_button(
            btn_frame, "打开噢易自带工具",
            self._open_oseasy_tool, "primary", 20
        )
        tool_btn.pack(pady=3)
    
    def _refresh_status(self) -> None:
        """刷新状态显示"""
        self.student.detect_path()
        self.status_label.config(
            text=f"路径: {self.student.path}\n"
                 f"进程: {self.student.exe_name}\n"
                 f"版本: v{self.student.version / 10 if self.student.version else '未知'}\n"
                 f"运行中: {'是' if self.student.is_running else '否'}"
        )
        self.mmpc_label.config(
            text=f"MMPC 服务: {self.mmpc.get_status_text()}"
        )
        self.show_status("状态已刷新")
    
    def _toggle_guaqi(self) -> None:
        """切换挂起状态"""
        if self.guaqi_var.get():
            # 挂起前先隐藏工具箱，防止被学生端检测
            self.app.root.withdraw()
            self.app.root.update()

            result = ProcessManager.suspend_process(self.student.exe_name)
            if result is True:
                # 同时挂起 MultiClient（忽略失败——某些版本不存在此进程）
                ProcessManager.suspend_process("MultiClient.exe")
                self._guaqi_status = True
                self.show_status("已挂起学生端进程（0.8秒后恢复窗口）", "success")
                # 短暂隐藏后自动恢复显示（不阻塞主线程）
                self.app.root.after(800, self._restore_window_after_guaqi)
            else:
                self.guaqi_var.set(False)
                # 挂起失败也要恢复窗口
                self.app.root.deiconify()
                self.show_status(str(result), "error")
        else:
            result = ProcessManager.resume_process(self.student.exe_name)
            if result is True:
                ProcessManager.resume_process("MultiClient.exe")
                self._guaqi_status = False
                self.show_status("已恢复学生端进程", "success")
            else:
                self.guaqi_var.set(True)
                self.show_status(str(result), "error")

    def _restore_window_after_guaqi(self) -> None:
        """挂起后延迟恢复显示工具箱"""
        try:
            self.app.root.deiconify()
            self.show_status("已挂起学生端进程", "success")
        except Exception:
            pass
    
    def _toggle_killer_protect(self) -> None:
        """切换外部cmd守护进程"""
        self.app.toggle_killer_protect(self._killer_protect_var.get())
    
    def _toggle_mmpc(self) -> None:
        """切换 MMPC 服务"""
        result = self.mmpc.toggle()
        self.mmpc_label.config(
            text=f"MMPC 服务: {self.mmpc.get_status_text()}"
        )
        self.show_status(result)
    
    def _restart_student(self) -> None:
        """重启学生端"""
        if self.student.is_running:
            ProcessManager.kill_process(self.student.exe_name)
        self.student.start()
        self.show_status("学生端已重启", "success")
    
    def _register_sticky(self) -> None:
        """注册粘滞键后门"""
        self.unlock.register_sticky_keys_backdoor()
        self.show_status("粘滞键后门已注册（按5次Shift触发）", "success")
    
    def _remove_sticky(self) -> None:
        """移除粘滞键后门"""
        self.unlock.remove_sticky_keys_backdoor()
        self.show_status("粘滞键后门已移除", "success")
    
    def _open_oseasy_tool(self) -> None:
        """打开噢易自带工具"""
        import os
        tool_path = os.path.join(self.student.path, "AssistHelper.exe")
        if os.path.exists(tool_path):
            os.startfile(tool_path)
            self.show_status("已打开噢易自带工具")
        else:
            self.show_status("未找到 AssistHelper.exe", "error")
    
    def refresh(self) -> None:
        """刷新页面"""
        self.yiyan_label.config(text=self.app.get_random_yiyan())
        self._refresh_status()