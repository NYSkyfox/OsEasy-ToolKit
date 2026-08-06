# src/utils/web/network.py
# 网络工具

import socket
import webbrowser


def get_ipv4_address() -> str | None:
    """获取机器IPv4地址"""
    try:
        return socket.gethostbyname(socket.gethostname())
    except Exception as e:
        print(f"获取IPv4地址时出现错误: {e}")
        return None


def open_github_page(*e) -> None:
    """在浏览器打开github仓库页面"""
    from config import GITHUB_URL
    webbrowser.open(GITHUB_URL)