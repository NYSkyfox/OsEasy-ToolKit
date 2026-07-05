# src/modules/file_handler.py
# 文件备份/恢复

import os
import time

from src.core.runtime_config import toolbox_cfg
from src.core.helpers import check_give_file_path_is_excs, run_sigle_cmd
from src.core.constants import backup_path, cmd_file_path


def backup_oe_files() -> None:
    """备份OE的关键文件"""
    print("[INFO] 尝试备份关键文件")
    namelist = [
        "MultiClient.exe",
        "MultiClient.exe",
        "LoadDriver.exe",
        "BlackSlient.exe",
        "\\x86\\LISSNetInfoSniffer.exe",
    ]
    for filename in namelist:
        oepath = toolbox_cfg.oseasy_path + filename
        needbkpath = backup_path + "\\" + filename
        run_sigle_cmd(f'copy "{oepath}" "{needbkpath}"')


def restone_sigle_oe_backup_file(filename: str) -> None:
    oepath = toolbox_cfg.oseasy_path + filename
    needbkpath = backup_path + "\\" + filename
    run_sigle_cmd(f'copy "{needbkpath}" "{oepath}"')


def restone_oe_backup_key_dll() -> None:
    """恢复OE关键文件"""
    from src.core.helpers import Ui_call_show_snake_message
    print("尝试还原关键文件")
    namelist = [
        "oenetlimitx64.cat",
        "OeNetLimitSetup.exe",
        "OeNetLimit.sys",
        "OeNetLimit.inf",
        "MultiClient.exe",
        "LoadDriver.exe",
        "BlackSlient.exe",
    ]

    faild_file_name = []

    for filename in namelist:
        oepath = toolbox_cfg.oseasy_path + filename
        needbkpath = backup_path + "\\" + filename
        run_sigle_cmd(f'copy "{needbkpath}" "{oepath}"')

    time.sleep(3)

    for filename in namelist:
        oepath = toolbox_cfg.oseasy_path + filename
        cSta = check_give_file_path_is_excs(oepath)
        print(f"filename {filename} 复制检测状态 > {cSta}")
        if not cSta:
            faild_file_name.append(filename)

    if len(faild_file_name) > 0:
        msg_mix = " , ".join(faild_file_name)
        Ui_call_show_snake_message(f"在恢复文件时检测到可能复制失败的文件有: \n{msg_mix}")
        return

    Ui_call_show_snake_message("恢复文件完成")


def del_self_cmd_files() -> None:
    """删除生成的脚本文件"""
    for filename in ["k.bat", "d.bat", "temp.bat", "kv2.bat", "net.bat", "usb.bat"]:
        try:
            os.remove(os.path.join(cmd_file_path, filename))
        except FileNotFoundError:
            continue