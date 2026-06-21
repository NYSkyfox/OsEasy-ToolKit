"""
广播管理页面
"""

import tkinter as tk
from tkinter import ttk
from pages.base_page import BasePage
from pynput import keyboard as kb


class BroadcastPage(BasePage):
    """广播管理页面"""

    # 所有可能的快捷键组合（供清理用）
    _ALL_HOTKEYS = [
        ([kb.Key.alt_l, 'k'], "_do_kill_broadcast"),
        ([kb.Key.alt_l, 'u'], "_do_run_window_broadcast"),
        ([kb.Key.ctrl_l, kb.Key.alt_l, 'f'], "_do_run_fullscreen_broadcast"),
        ([kb.Key.alt_l, 'x'], "app.do_screenshot"),
        ([kb.Key.caps_lock, kb.Key.enter], "app._toggle_window_visibility"),
    ]

    def create_widgets(self) -> None:
        """创建广播管理页面控件"""
        # 一言
        self.yiyan_label = self.create_label(
            self, self.app.get_random_yiyan(),
            font_size=10, bold=True
        )
        self.yiyan_label.pack(pady=(15, 10), padx=20)

        # 分隔线
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=20, pady=5)

        # 使用说明
        help_card = self.create_card(self, "使用说明")
        help_card.pack(fill="x", padx=20, pady=10)

        help_text = self.create_label(
            help_card,
            "1. 点击'替换拦截程序'替换 ScreenRender.exe\n"
            "2. 等待老师广播一次，命令会被自动拦截\n"
            "3. 使用下方按钮运行窗口化或全屏广播\n"
            "4. 可以随时杀死广播进程恢复自由",
            font_size=9
        )
        help_text.pack(anchor="w")

        # 替换状态卡片
        status_card = self.create_card(self, "替换状态")
        status_card.pack(fill="x", padx=20, pady=10)

        self.replace_status = self.create_label(
            status_card,
            f"替换状态: {'已替换' if self.broadcast.is_replaced() else '未替换'}",
            font_size=10, bold=True
        )
        self.replace_status.pack(anchor="w")

        # 替换/恢复按钮
        btn_frame = ttk.Frame(status_card)
        btn_frame.pack(fill="x", pady=8)

        replace_btn = self.create_button(
            btn_frame, "替换拦截程序",
            self._replace_scr, "primary", 18
        )
        replace_btn.pack(side="left", padx=2)

        restore_btn = self.create_button(
            btn_frame, "恢复原始程序",
            self._restore_scr, "primary", 18
        )
        restore_btn.pack(side="right", padx=2)

        # 广播命令卡片
        cmd_card = self.create_card(self, "广播命令")
        cmd_card.pack(fill="x", padx=20, pady=10)

        self.cmd_label = self.create_label(
            cmd_card,
            f"已保存命令: {'是' if self.broadcast.cmd else '否'}",
            font_size=9
        )
        self.cmd_label.pack(anchor="w")

        # 读取拦截命令
        read_btn = self.create_button(
            cmd_card, "读取拦截的命令",
            self._read_cmd, "primary", 25
        )
        read_btn.pack(pady=5)

        # 广播操作按钮
        action_frame = ttk.Frame(cmd_card)
        action_frame.pack(fill="x", pady=5)

        window_btn = self.create_button(
            action_frame, "窗口广播",
            self._run_window_broadcast, "primary", 15
        )
        window_btn.pack(side="left", padx=2)

        fullscreen_btn = self.create_button(
            action_frame, "全屏广播",
            self._run_fullscreen_broadcast, "primary", 15
        )
        fullscreen_btn.pack(side="right", padx=2)

        # 杀死广播
        kill_btn = self.create_button(
            cmd_card, "杀死广播进程",
            self._kill_broadcast, "primary", 25
        )
        kill_btn.pack(pady=5)

        # 快捷键开关卡片
        hotkey_card = self.create_card(self, "快捷键（开关即生效）")
        hotkey_card.pack(fill="x", padx=20, pady=10)

        # Alt+K 杀广播
        kill_frame = ttk.Frame(hotkey_card)
        kill_frame.pack(fill="x", pady=3)

        kill_label = self.create_label(kill_frame, "Alt+K 杀广播进程")
        kill_label.pack(side="left")

        self.kill_hotkey_var = tk.BooleanVar(value=False)
        kill_check = ttk.Checkbutton(
            kill_frame,
            variable=self.kill_hotkey_var,
            command=self._toggle_kill_hotkey
        )
        kill_check.pack(side="right")

        # Alt+U 窗口广播
        win_frame = ttk.Frame(hotkey_card)
        win_frame.pack(fill="x", pady=3)

        win_label = self.create_label(win_frame, "Alt+U 窗口广播")
        win_label.pack(side="left")

        self.win_hotkey_var = tk.BooleanVar(value=False)
        win_check = ttk.Checkbutton(
            win_frame,
            variable=self.win_hotkey_var,
            command=self._toggle_window_hotkey
        )
        win_check.pack(side="right")

        # Ctrl+Alt+F 全屏广播
        full_frame = ttk.Frame(hotkey_card)
        full_frame.pack(fill="x", pady=3)

        full_label = self.create_label(full_frame, "Ctrl+Alt+F 全屏广播")
        full_label.pack(side="left")

        self.full_hotkey_var = tk.BooleanVar(value=False)
        full_check = ttk.Checkbutton(
            full_frame,
            variable=self.full_hotkey_var,
            command=self._toggle_fullscreen_hotkey
        )
        full_check.pack(side="right")

        # Alt+X 截图
        sc_frame = ttk.Frame(hotkey_card)
        sc_frame.pack(fill="x", pady=3)

        sc_label = self.create_label(sc_frame, "Alt+X 屏幕截图")
        sc_label.pack(side="left")

        self.sc_hotkey_var = tk.BooleanVar(value=False)
        sc_check = ttk.Checkbutton(
            sc_frame,
            variable=self.sc_hotkey_var,
            command=self._toggle_screenshot_hotkey
        )
        sc_check.pack(side="right")

        # CapsLock+Enter 隐藏工具箱
        hide_frame = ttk.Frame(hotkey_card)
        hide_frame.pack(fill="x", pady=3)

        hide_label = self.create_label(hide_frame, "CapsLock+Enter 隐/显工具箱")
        hide_label.pack(side="left")

        self.hide_hotkey_var = tk.BooleanVar(value=True)
        hide_check = ttk.Checkbutton(
            hide_frame,
            variable=self.hide_hotkey_var,
            command=self._toggle_hide_hotkey
        )
        hide_check.pack(side="right")

    # ---- 替换/恢复 ----

    def _replace_scr(self) -> None:
        """替换 ScreenRender"""
        success, msg = self.broadcast.replace_screen_render()
        if success:
            self.replace_status.config(text="替换状态: 已替换")
            self.show_status(msg, "success")
        else:
            self.show_status(msg, "error")

    def _restore_scr(self) -> None:
        """恢复 ScreenRender"""
        success, msg = self.broadcast.restore_screen_render()
        if success:
            self.replace_status.config(text="替换状态: 未替换")
            self.show_status(msg, "success")
        else:
            self.show_status(msg, "error")

    def _read_cmd(self) -> None:
        """读取拦截的命令"""
        success, result = self.broadcast.read_intercepted_cmd()
        if success:
            self.cmd_label.config(text=f"已保存命令: 是")
            self.show_status("广播命令已读取并保存", "success")
            self.broadcast.save_cmd_to_file()
        else:
            self.show_status(result, "error")

    # ---- 广播运行（供快捷键和按钮共同调用） ----

    def _do_run_window_broadcast(self) -> None:
        """执行窗口广播"""
        success, msg = self.broadcast.run_broadcast(fullscreen=False)
        if success:
            self.show_status(msg, "success")

    def _do_run_fullscreen_broadcast(self) -> None:
        """执行全屏广播"""
        success, msg = self.broadcast.run_broadcast(fullscreen=True)
        if success:
            self.show_status(msg, "success")

    def _do_kill_broadcast(self) -> None:
        """执行杀死广播进程"""
        self.broadcast.kill_broadcast()
        self.show_status("广播进程已杀死", "success")

    def _run_window_broadcast(self) -> None:
        """运行窗口广播（按钮回调）"""
        self._do_run_window_broadcast()

    def _run_fullscreen_broadcast(self) -> None:
        """运行全屏广播（按钮回调）"""
        self._do_run_fullscreen_broadcast()

    def _kill_broadcast(self) -> None:
        """杀死广播进程（按钮回调）"""
        self._do_kill_broadcast()

    # ---- 快捷键开关（真正生效） ----

    def _toggle_kill_hotkey(self) -> None:
        """切换 Alt+K 杀广播快捷键"""
        self.app.hotkey_service.toggle(
            self.kill_hotkey_var.get(),
            [kb.Key.alt_l, 'k'],
            self._do_kill_broadcast
        )
        status = "已开启" if self.kill_hotkey_var.get() else "已关闭"
        self.show_status(f"Alt+K 快捷键 {status}", "success")

    def _toggle_window_hotkey(self) -> None:
        """切换 Alt+U 窗口广播快捷键"""
        self.app.hotkey_service.toggle(
            self.win_hotkey_var.get(),
            [kb.Key.alt_l, 'u'],
            self._do_run_window_broadcast
        )
        status = "已开启" if self.win_hotkey_var.get() else "已关闭"
        self.show_status(f"Alt+U 快捷键 {status}", "success")

    def _toggle_fullscreen_hotkey(self) -> None:
        """切换 Ctrl+Alt+F 全屏广播快捷键"""
        self.app.hotkey_service.toggle(
            self.full_hotkey_var.get(),
            [kb.Key.ctrl_l, kb.Key.alt_l, 'f'],
            self._do_run_fullscreen_broadcast
        )
        status = "已开启" if self.full_hotkey_var.get() else "已关闭"
        self.show_status(f"Ctrl+Alt+F 快捷键 {status}", "success")

    def _toggle_screenshot_hotkey(self) -> None:
        """切换 Alt+X 截图快捷键"""
        self.app.hotkey_service.toggle(
            self.sc_hotkey_var.get(),
            [kb.Key.alt_l, 'x'],
            self.app.do_screenshot
        )
        status = "已开启" if self.sc_hotkey_var.get() else "已关闭"
        self.show_status(f"Alt+X 截图快捷键 {status}", "success")

    def _toggle_hide_hotkey(self) -> None:
        """切换 CapsLock+Enter 隐藏工具箱快捷键"""
        self.app.toggle_hide_show_hotkey(self.hide_hotkey_var.get())

    # ---- 快捷键清理 ----

    def unregister_hotkeys(self) -> None:
        """清理所有快捷键注册（页面切换时调用）"""
        hs = self.app.hotkey_service
        # 隐藏工具箱快捷键是通过 app 单独管理的，不注销
        for keys, _ in self._ALL_HOTKEYS:
            # 排除 CapsLock+Enter 这个全局快捷键
            if keys == [kb.Key.caps_lock, kb.Key.enter]:
                continue
            hs.unregister(keys, None)

    # ---- 刷新 ----

    def refresh(self) -> None:
        """刷新页面"""
        self.yiyan_label.config(text=self.app.get_random_yiyan())
        self.replace_status.config(
            text=f"替换状态: {'已替换' if self.broadcast.is_replaced() else '未替换'}"
        )
        self.cmd_label.config(
            text=f"已保存命令: {'是' if self.broadcast.cmd else '否'}"
        )