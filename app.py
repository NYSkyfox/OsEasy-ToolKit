"""
OsEasy-ToolKit 主应用类
负责窗口管理、服务初始化、页面切换
"""

import tkinter as tk
from tkinter import ttk, messagebox
import random
import os
import threading

import config
from utils.admin import ensure_admin
from utils.helpers import ensure_dir, run_cmd, write_bat_file, check_file_exists, take_screenshot
from utils.process import ProcessManager

from services.student import StudentService
from services.mmpc import MmpcService
from services.unlock import UnlockService
from services.broadcast import BroadcastService
from services.dll_utils import DllService
from services.network import NetworkService
from services.usb import UsbService
from services.hotkey_service import HotkeyService

from pages.process_page import ProcessPage
from pages.unlock_page import UnlockPage
from pages.broadcast_page import BroadcastPage
from pages.command_page import CommandPage
from pages.dll_page import DllPage
from pages.about_page import AboutPage


class ToolKitTk:
    """
    OsEasy-ToolKit 主应用

    使用 tkinter + ttk 构建 GUI
    """

    def __init__(self):
        # 确保管理员权限
        ensure_admin()

        # 确保必要目录存在
        ensure_dir(config.CMD_FILE_PATH)
        ensure_dir(config.BACKUP_FILE_PATH)

        # 初始化服务
        self._init_services()
        self._init_infrastructure()

        # 创建主窗口
        self.root = tk.Tk()
        self.root.title(config.FULL_TITLE)
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.minsize(config.WINDOW_MIN_WIDTH, config.WINDOW_MIN_HEIGHT)

        # 设置 ttk 主题（自动适配 Windows 版本）
        self._apply_ttk_theme()

        # 创建界面
        self._create_menu()
        self._create_main_layout()

        # 探测学生端
        self._detect_student()

        # 注册默认快捷键：CapsLock+Enter 隐藏/显示工具箱（默认启用）
        self._register_hide_show_hotkey(True)

        # 窗口关闭时清理
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _init_services(self) -> None:
        """初始化所有业务服务"""
        self.student_service = StudentService()
        self.mmpc_service = MmpcService()
        self.unlock_service = UnlockService(self.student_service)
        self.broadcast_service = BroadcastService(self.student_service)
        self.dll_service = DllService(self.student_service)
        self.network_service = NetworkService()
        self.usb_service = UsbService()

    def _init_infrastructure(self) -> None:
        """初始化基础设施（快捷键、守护进程等）"""
        self.hotkey_service = HotkeyService()
        self._killer_protect_running: bool = False
        self._killer_protect_thread: threading.Thread | None = None

    @staticmethod
    def _apply_ttk_theme() -> None:
        """
        设置 ttk 主题，完全跟随 Windows 系统当前视觉样式。
        无论系统是否加载了第三方主题，工具按钮外观都会和系统一致。
        """
        style = ttk.Style()
        # 可用主题列表：style.theme_names()
        available = style.theme_names()
        # "default" 是 ttk 的原生主题，直接反射系统视觉样式
        if "default" in available:
            style.theme_use("default")

    def _create_menu(self) -> None:
        """创建菜单栏"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="文件", menu=file_menu)
        file_menu.add_command(label="退出", command=self._on_close)

        # 帮助菜单
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="帮助", menu=help_menu)
        help_menu.add_command(label="关于", command=self._show_about)

    def _create_main_layout(self) -> None:
        """创建主界面布局"""
        # 主容器（使用 PanedWindow 或简单的 Frame）
        main_container = ttk.Frame(self.root)
        main_container.pack(fill="both", expand=True)

        # 左侧导航栏
        self.nav_frame = ttk.Frame(
            main_container,
            width=100
        )
        self.nav_frame.pack(side="left", fill="y")
        self.nav_frame.pack_propagate(False)

        # 导航按钮
        self.nav_buttons = []
        self.page_names = [
            ("进程管理", "process"),
            ("解锁管理", "unlock"),
            ("广播管理", "broadcast"),
            ("广播命令", "command"),
            ("DLL工具", "dll"),
            ("关于", "about"),
        ]

        for i, (name, key) in enumerate(self.page_names):
            btn = ttk.Button(
                self.nav_frame,
                text=name,
                command=lambda k=key: self._switch_page(k),
                width=12,
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons.append((btn, key))

        # 分隔线
        separator = ttk.Separator(
            main_container,
            orient="vertical"
        )
        separator.pack(side="left", fill="y", padx=2)

        # 右侧内容区域
        self.content_frame = ttk.Frame(
            main_container
        )
        self.content_frame.pack(side="left", fill="both", expand=True)

        # 创建页面实例
        self.pages = {}
        self._create_pages()

        # 默认显示第一个页面
        self.current_page_key = None
        self._switch_page("process")

        # 底部状态栏
        self.status_bar = ttk.Label(
            self.root,
            text="就绪",
            anchor="w",
            padding=(10, 2)
        )
        self.status_bar.pack(side="bottom", fill="x")

    def _create_pages(self) -> None:
        """创建所有页面实例"""
        self.pages["process"] = ProcessPage(self.content_frame, self)
        self.pages["unlock"] = UnlockPage(self.content_frame, self)
        self.pages["broadcast"] = BroadcastPage(self.content_frame, self)
        self.pages["command"] = CommandPage(self.content_frame, self)
        self.pages["dll"] = DllPage(self.content_frame, self)
        self.pages["about"] = AboutPage(self.content_frame, self)

        # 初始隐藏所有页面
        for page in self.pages.values():
            page.pack_forget()

    def _switch_page(self, key: str) -> None:
        """
        切换页面

        Args:
            key: 页面标识
        """
        # 离开广播页面时清理其注册的快捷键
        if self.current_page_key == "broadcast":
            self.pages["broadcast"].unregister_hotkeys()

        # 隐藏当前页面
        if self.current_page_key and self.current_page_key in self.pages:
            self.pages[self.current_page_key].pack_forget()

        # 显示新页面
        if key in self.pages:
            self.pages[key].pack(fill="both", expand=True)
            self.pages[key].refresh()
            self.current_page_key = key

        # 更新导航按钮样式（ttk 下无法动态改色，此处仅作为预留）
        for btn, btn_key in self.nav_buttons:
            if btn_key == key:
                btn.state(["pressed"])
            else:
                btn.state(["!pressed"])

    def _detect_student(self) -> None:
        """探测学生端"""
        success, msg = self.student_service.detect_path()
        if success:
            self.show_status(f"学生端已就绪: {self.student_service.exe_name}")
        else:
            self.show_status("未检测到学生端，请手动检查", "warning")
            messagebox.showwarning("警告", msg)

    def show_status(self, message: str, msg_type: str = "info") -> None:
        """
        显示状态消息

        Args:
            message: 消息内容
            msg_type: 类型 (info, success, warning, error)
        """
        clr = config.COLORS.get(msg_type, config.COLORS["fg"])

        self.status_bar.config(
            text=message,
            foreground=clr
        )

    def get_random_yiyan(self) -> str:
        """
        获取随机一言

        Returns:
            一言字符串
        """
        return random.choice(config.DEFAULT_YIYAN)

    def _show_about(self) -> None:
        """显示关于对话框"""
        messagebox.showinfo(
            "关于",
            f"{config.APP_NAME} v{config.VERSION}\n\n"
            "针对噢易多媒体教学系统的辅助工具\n"
            "愿我们的电脑课都不再无聊~"
        )

    # ---------- 快捷键相关 ----------

    def _register_hide_show_hotkey(self, enabled: bool) -> None:
        """注册/注销 CapsLock+Enter 隐藏/显示工具箱快捷键"""
        from pynput import keyboard as kb
        self.hotkey_service.toggle(
            enabled,
            [kb.Key.caps_lock, kb.Key.enter],
            self._toggle_window_visibility
        )

    def _toggle_window_visibility(self) -> None:
        """切换窗口的隐藏/显示状态"""
        try:
            if self.root.state() == "withdrawn":
                self.root.deiconify()
                self.show_status("工具箱已显示", "success")
            else:
                self.root.withdraw()
                self.show_status("工具箱已隐藏（CapsLock+Enter 恢复）", "info")
        except Exception as e:
            print(f"[Hide/Show] 切换窗口可见性失败: {e}")

    def toggle_hide_show_hotkey(self, enabled: bool) -> None:
        """供广播页面调用的快捷键开关方法"""
        self._register_hide_show_hotkey(enabled)
        status = "已开启" if enabled else "已关闭"
        self.show_status(f"CapsLock+Enter 隐藏/显示 {status}", "success")

    # ---------- 屏幕截图 ----------

    def do_screenshot(self) -> None:
        """执行屏幕截图（供快捷键和服务调用）"""
        try:
            filepath = take_screenshot()
            if filepath:
                self.show_status(f"截图已保存: {os.path.basename(filepath)}", "success")
            else:
                self.show_status("截图失败", "error")
        except Exception as e:
            self.show_status(f"截图出错: {e}", "error")

    # ---------- 守护进程（外部 cmd 守护） ----------

    def _generate_killer_bat(self) -> str:
        """
        生成循环 kill 学生端和 MultiClient 的批处理脚本

        Returns:
            bat 文件路径
        """
        student_exe = self.student_service.exe_name
        mmpc_stop = ""
        if self.student_service.is_high_version():
            mmpc_stop = "sc stop MMPC\n"

        content = f"""@ECHO OFF
title OsEasyToolKitKiller
{mmpc_stop}taskkill /f /t /im MultiClient.exe
taskkill /f /t /im BlackSlient.exe
:a
taskkill /f /t /im {student_exe}
goto a
"""
        killer_path = os.path.join(config.CMD_FILE_PATH, "killer.bat")
        write_bat_file(killer_path, content)
        return killer_path

    def _killer_protect_loop(self) -> None:
        """
        守护线程：循环检查 killer.bat 窗口是否存活，
        若被杀则重新拉起
        """
        try:
            import pygetwindow as gw
        except ImportError:
            print("[守护进程] pygetwindow 未安装，无法检测窗口")
            return

        restart_count = 0
        killer_path = self._generate_killer_bat()

        # 先启动一次
        os.startfile(killer_path)

        while self._killer_protect_running:
            try:
                windows = gw.getWindowsWithTitle("OsEasyToolKitKiller")
                if not windows:
                    os.startfile(killer_path)
                    restart_count += 1
                # 每 0.5 秒检查一次
                import time
                time.sleep(0.5)
            except Exception as e:
                print(f"[守护进程] 检测异常: {e}")
                import time
                time.sleep(1)

        print(f"[守护进程] 已停止，共重启 {restart_count} 次")

    def start_killer_protect(self) -> None:
        """启动外部 cmd 守护进程"""
        if self._killer_protect_running:
            return

        self._killer_protect_running = True
        self._killer_protect_thread = threading.Thread(
            target=self._killer_protect_loop,
            daemon=True,
            name="killer-protect"
        )
        self._killer_protect_thread.start()
        self.show_status("外部cmd守护进程已启动", "success")

    def stop_killer_protect(self) -> None:
        """停止外部 cmd 守护进程"""
        self._killer_protect_running = False
        # 杀掉现有 killer 窗口
        run_cmd("taskkill /f /t /im cmd.exe /fi \"WINDOWTITLE eq OsEasyToolKitKiller\"")
        self.show_status("外部cmd守护进程已停止", "info")

    def toggle_killer_protect(self, enabled: bool) -> None:
        """切换守护进程开关"""
        if enabled:
            self.start_killer_protect()
        else:
            self.stop_killer_protect()

    # ---------- 生命周期 ----------

    def _on_close(self) -> None:
        """关闭窗口前的清理"""
        self.stop_killer_protect()
        self.hotkey_service.stop()
        self.root.destroy()

    def run(self) -> None:
        """运行应用"""
        self.root.mainloop()


def main():
    """应用入口"""
    app = ToolKitTk()
    app.run()


if __name__ == "__main__":
    main()