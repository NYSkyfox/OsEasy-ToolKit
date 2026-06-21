"""
管理员权限检测与提权工具
"""

import ctypes
import sys
import os


def check_admin() -> bool:
    """
    检查当前是否以管理员权限运行
    
    Returns:
        bool: True 表示有管理员权限，False 表示没有
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def run_as_admin() -> None:
    """
    尝试以管理员权限重新启动自身
    如果当前没有管理员权限，则提权并退出当前进程
    """
    if not check_admin():
        try:
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, " ".join(sys.argv), None, 1
            )
        except Exception as e:
            print(f"提权失败: {e}")
        finally:
            sys.exit(0)


def ensure_admin() -> None:
    """
    确保以管理员权限运行，如果没有则自动提权
    """
    if not check_admin():
        print("需要管理员权限，正在尝试提权...")
        run_as_admin()
