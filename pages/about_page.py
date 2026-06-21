"""
关于页面
"""

import tkinter as tk
from tkinter import ttk
import webbrowser
from pages.base_page import BasePage
import config


class AboutPage(BasePage):
    """关于页面"""

    def create_widgets(self) -> None:
        """创建关于页面控件"""
        # 标题
        title = self.create_label(
            self, config.APP_NAME,
            font_size=20, bold=True
        )
        title.pack(pady=(30, 5))

        # 版本号
        version = self.create_label(
            self, f"版本: v{config.VERSION}",
            font_size=12
        )
        version.pack(pady=5)

        # 分隔线
        ttk.Separator(self, orient="horizontal").pack(fill="x", padx=40, pady=15)

        # 描述
        desc = self.create_label(
            self,
            "OsEasy-ToolKit 是一款针对噢易多媒体教学系统的\n"
            "辅助工具，提供进程管理、广播拦截、系统解锁等功能。\n\n"
            "使用本工具需要管理员权限。\n"
            "请在合法合规的前提下使用。",
            font_size=10
        )
        desc.pack(pady=10)

        # 功能列表
        features_card = self.create_card(self, "主要功能")
        features_card.pack(fill="x", padx=40, pady=10)

        features = self.create_label(
            features_card,
            "• 进程挂起/恢复 - 暂停学生端进程\n"
            "• 广播拦截 - 替换 ScreenRender 拦截命令\n"
            "• 窗口化/全屏广播 - 自由控制广播显示\n"
            "• 键盘锁解除 - 删除锁定文件\n"
            "• 网络/USB 解锁 - 解除系统限制\n"
            "• DLL 直接调用 - 底层管控操作",
            font_size=9
        )
        features.pack(anchor="w")

        # 链接按钮
        link_frame = ttk.Frame(self)
        link_frame.pack(pady=20)

        github_btn = self.create_button(
            link_frame, "GitHub 仓库",
            self._open_github, "primary", 20
        )
        github_btn.pack(pady=5)

        # 底部信息
        footer = self.create_label(
            self,
            "愿我们的电脑课都不再无聊~ 🥳",
            font_size=10
        )
        footer.pack(pady=20)
    
    def _open_github(self) -> None:
        """打开 GitHub 页面"""
        webbrowser.open(config.GITHUB_REPO_URL)
        self.show_status("已打开 GitHub 页面")
    
    def refresh(self) -> None:
        """刷新页面"""
        pass  # 关于页面不需要刷新一言