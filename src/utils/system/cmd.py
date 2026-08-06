# src/utils/system/cmd.py
# 命令行执行工具

import os

from src.core.constants import cmd_file_path


def run_sigle_cmd(givecmd: str, quiet: bool = False) -> None:
    """运行指定的命令
    :param givecmd: 要执行的命令
    :param quiet: True=不弹窗口(asynchronous), False=等待完成(synchronous)
    """
    if quiet:
        os.popen(cmd=givecmd)
    else:
        os.system(command=givecmd)


def use_bat_file_to_run_cmd(cmd: str) -> None:
    """生成一个临时cmd文件运行指定命令"""
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
    batp = os.path.join(cmd_file_path, batname)
    os.startfile(batp)