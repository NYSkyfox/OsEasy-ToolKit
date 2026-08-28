# src/utils/ifeo.py
# IFEO（Image File Execution Options）映像劫持工具函数

import subprocess

from src.utils.cmd import run_sigle_cmd

# IFEO 注册表父键路径
IFEO_BASE_KEY = r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Image File Execution Options"


def add_ifeo_debugger(exe_name: str, debugger_path: str) -> None:
    """为指定 exe 添加 IFEO Debugger 映像劫持
    Args:
        exe_name: 目标可执行文件名，如 "sethc.exe"、"shutdown.exe"
        debugger_path: 替代程序路径（bat/exe 等）
    """
    cmd = (
        f'REG ADD "{IFEO_BASE_KEY}\\{exe_name}" '
        f'/v Debugger /t REG_SZ /d "{debugger_path}" /f'
    )
    run_sigle_cmd(cmd)


def remove_ifeo_debugger(exe_name: str) -> None:
    """移除指定 exe 的 IFEO Debugger 键值
    Args:
        exe_name: 目标可执行文件名
    """
    cmd = f'REG DELETE "{IFEO_BASE_KEY}\\{exe_name}" /v Debugger /f'
    run_sigle_cmd(cmd)


def query_ifeo_debugger(exe_name: str) -> str | None:
    """查询指定 exe 的 IFEO Debugger 键值
    Returns:
        Debugger 指向的路径字符串；不存在或查询失败返回 None
    """
    try:
        result = subprocess.run(
            f'reg query "{IFEO_BASE_KEY}\\{exe_name}" /v Debugger',
            shell=True,
            capture_output=True,
            text=True,
            # 不弹控制台窗口（避免打包为无控制台 exe 时闪现黑框）
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if "Debugger" not in result.stdout:
            return None
        # 解析 reg query 输出，提取 REG_SZ 值
        # 典型输出：    Debugger    REG_SZ    C:\path\to\file
        for line in result.stdout.splitlines():
            if "Debugger" in line and "REG_SZ" in line:
                parts = line.split("REG_SZ", 1)
                if len(parts) == 2:
                    return parts[1].strip()
        return None
    except Exception:
        return None