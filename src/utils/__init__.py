# src/utils/__init__.py
# 通用工具函数

import os
import sys
import socket
import webbrowser
from datetime import datetime


def get_time_str() -> str:
    """返回一个时间字符串"""
    time_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return time_str


def check_give_file_path_is_excs(filePath) -> bool:
    """检查文件是否存在"""
    return os.path.isfile(filePath)


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


def run_sigle_cmd(givecmd: str, *quiterun: bool) -> None:
    """运行指定的命令"""
    if not quiterun:
        os.popen(cmd=givecmd)
    elif quiterun == False:
        os.system(command=givecmd)
    elif quiterun == True:
        os.popen(cmd=givecmd)
    else:
        os.system(command=givecmd)


def use_bat_file_to_run_cmd(cmd: str) -> None:
    """生成一个临时cmd文件运行指定命令"""
    from src.core.constants import cmd_file_path
    mp = cmd_file_path + "\\temp.bat"
    fm = open(mp, "w")
    cmdtext = "@ECHO OFF\n"
    cmdtext += cmd
    cmdtext += "\nexit"
    fm.write(cmdtext)
    fm.close()
    run_sigle_cmd(f"start {mp}")


def runbat(batname: str) -> None:
    """运行指定名称的bat脚本"""
    from src.core.constants import cmd_file_path
    batp = os.path.join(cmd_file_path, batname)
    os.startfile(batp)


def get_god_potato_path():
    """获取神の土豆可执行文件路径"""
    # PyInstaller 提取的临时路径
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, "resources", "gp_net35.exe")
    # 开发环境路径
    return os.path.join("resources", "gp_net35.exe")


def run_cmd_with_god_potato(arguments: str):
    """
    使用神の土豆来运行命令
    参数：
    - arguments: 要运行的命令
    如：run_god_potato_cmd("net start MMPC")
    """
    ntsd_path = get_god_potato_path()
    if not os.path.exists(ntsd_path):
        raise FileNotFoundError(f"ntsd.exe not found at {ntsd_path}")

    cmd = f'"{ntsd_path}" -cmd "cmd /c {arguments}"'
    run_sigle_cmd(cmd, False)


def del_historyrem(*e) -> None:
    """删除保存的历史路径文件"""
    from src.core.runtime_config import toolbox_cfg
    neddel = ["fontPath", "bgPath", "yiyanPath"]
    for i in neddel:
        toolbox_cfg.set_config_key_data(i, None)