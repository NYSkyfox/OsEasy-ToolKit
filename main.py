#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OsEasy ManagerHelper 入口
=========================
启动 GUI（tkinter + ttk，vista 主题，顶部导航栏 + 下部内容区）。

    python main.py

仅依赖 Python 3.8+ 标准库，无需 pip 安装任何第三方包。
"""

import os
import sys


def _ensure_project_root() -> None:
    """把项目根加入 sys.path，保证 `src` / `config` 可导入。"""
    root = os.path.dirname(os.path.abspath(__file__))
    if root not in sys.path:
        sys.path.insert(0, root)


def main() -> None:
    _ensure_project_root()

    from src.core import ensure_dirs
    from src.gui.app import app

    # 创建数据目录（备份/日志/配置）
    try:
        ensure_dirs()
    except Exception as e:
        print(f"[警告] 创建数据目录失败：{e}")

    # 顶层异常捕获
    try:
        app.main()
    except SystemExit:
        raise
    except BaseException as e:
        # GUI 启动阶段的致命错误，打印到控制台便于排查
        import traceback
        traceback.print_exc()
        print(f"\n[致命错误] {e}")
        # 尝试弹窗提示（若 GUI 已初始化）
        try:
            import tkinter as tk
            from tkinter import messagebox
            messagebox.showerror("OsEasy-ManagerHelper 启动失败", str(e))
        except Exception:
            pass
        raise


if __name__ == "__main__":
    main()