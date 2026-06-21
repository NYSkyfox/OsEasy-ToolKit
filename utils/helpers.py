"""
通用辅助工具函数
"""

import os
import time
import socket
import subprocess
from datetime import datetime
from tkinter import messagebox

import config


def get_time_str() -> str:
    """返回当前时间字符串，格式：2024_01_15_14_30_00"""
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")


def get_ipv4_address() -> Optional[str]:
    """
    获取本机 IPv4 地址

    Returns:
        IPv4 地址字符串，获取失败返回 None
    """
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        print(f"获取 IP 地址失败: {e}")
        return None


def check_file_exists(path: str) -> bool:
    """
    检查文件是否存在

    Args:
        path: 文件路径

    Returns:
        是否存在
    """
    return os.path.isfile(path)


def check_dir_exists(path: str) -> bool:
    """
    检查目录是否存在

    Args:
        path: 目录路径

    Returns:
        是否存在
    """
    return os.path.isdir(path)


def ensure_dir(path: str) -> None:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径
    """
    os.makedirs(path, exist_ok=True)


def run_cmd(command: str, wait: bool = False, capture_output: bool = False) -> Optional[int] | str:
    """
    运行系统命令

    Args:
        command: 命令字符串
        wait: 是否等待命令执行完成
        capture_output: 是否捕获输出（wait=True 时生效，返回 (code, stdout, stderr)）

    Returns:
        如果 wait=False 返回 None；
        如果 wait=True 且 capture_output=False 返回返回码；
        如果 wait=True 且 capture_output=True 返回格式化的输出字符串
    """
    try:
        if wait:
            result = subprocess.run(
                command, shell=True,
                capture_output=capture_output,
                text=True
            )
            if capture_output:
                output = result.stdout.strip()
                error = result.stderr.strip()
                msg = f"返回码: {result.returncode}"
                if output:
                    msg += f"\n输出: {output}"
                if error:
                    msg += f"\n错误: {error}"
                return msg
            return result.returncode
        else:
            subprocess.Popen(command, shell=True)
            return None
    except Exception as e:
        print(f"执行命令失败: {e}")
        return None


def run_bat(bat_path: str) -> None:
    """
    运行批处理文件

    Args:
        bat_path: bat 文件完整路径
    """
    if os.path.exists(bat_path):
        os.startfile(bat_path)
    else:
        print(f"批处理文件不存在: {bat_path}")


def show_message(title: str, message: str, msg_type: str = "info") -> None:
    """
    显示消息对话框

    Args:
        title: 标题
        message: 消息内容
        msg_type: 消息类型 (info, warning, error, yesno)
    """
    if msg_type == "info":
        messagebox.showinfo(title, message)
    elif msg_type == "warning":
        messagebox.showwarning(title, message)
    elif msg_type == "error":
        messagebox.showerror(title, message)
    elif msg_type == "yesno":
        return messagebox.askyesno(title, message)


def write_bat_file(path: str, content: str) -> bool:
    """
    写入批处理文件

    Args:
        path: 文件路径
        content: 文件内容

    Returns:
        是否成功
    """
    try:
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"写入 bat 文件失败: {e}")
        return False


def take_screenshot(save_dir: str = None) -> str | None:
    """
    使用 pyautogui 截取全屏并保存为 JPG 文件

    Args:
        save_dir: 保存目录，默认使用 ToolKitProd\\screenshots

    Returns:
        保存的文件路径，失败返回 None
    """
    try:
        import pyautogui

        if not save_dir:
            # 默认保存到 ToolKitProd\\screenshots
            save_dir = os.path.join(
                os.path.dirname(config.CMD_FILE_PATH) 
                if hasattr(config, 'CMD_FILE_PATH') and config.CMD_FILE_PATH 
                else os.getcwd(),
                "screenshots"
            )

        ensure_dir(save_dir)

        img = pyautogui.screenshot()
        filename = f"screenshot_{get_time_str()}.png"
        filepath = os.path.join(save_dir, filename)
        img.save(filepath)
        print(f"[Screenshot] 已保存: {filepath}")
        return filepath
    except ImportError:
        print("[Screenshot] pyautogui 未安装，无法截图")
        return None
    except Exception as e:
        print(f"[Screenshot] 截图失败: {e}")
        return None


# 导入 Optional 用于类型注解
from typing import Optional