# src/modules/file_handler.py
# 文件备份/恢复

import os
import time

from src.core.runtime_config import toolkit_cfg
from src.core.helpers import file_exists, run_sigle_cmd
from src.core.constants import backup_path, cmd_file_path
from config import ALL_SCRIPT_FILES


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
        oepath = toolkit_cfg.oseasy_path + filename
        needbkpath = backup_path + "\\" + filename
        run_sigle_cmd(f'copy "{oepath}" "{needbkpath}"')


def restore_oe_file(filename: str) -> None:
    """从备份恢复单个 OE 文件到原路径"""
    oepath = toolkit_cfg.oseasy_path + filename
    needbkpath = backup_path + "\\" + filename
    run_sigle_cmd(f'copy "{needbkpath}" "{oepath}"')


def restore_oe_key_dlls() -> None:
    """批量恢复 OE 关键 DLL/驱动文件，并验证复制结果"""
    from src.core.helpers import show_snack
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
        oepath = toolkit_cfg.oseasy_path + filename
        needbkpath = backup_path + "\\" + filename
        run_sigle_cmd(f'copy "{needbkpath}" "{oepath}"')

    time.sleep(3)

    for filename in namelist:
        oepath = toolkit_cfg.oseasy_path + filename
        cSta = file_exists(oepath)
        print(f"filename {filename} 复制检测状态 > {cSta}")
        if not cSta:
            faild_file_name.append(filename)

    if len(faild_file_name) > 0:
        msg_mix = " , ".join(faild_file_name)
        show_snack(f"在恢复文件时检测到可能复制失败的文件有: \n{msg_mix}")
        return

    show_snack("恢复文件完成")


def del_self_cmd_files() -> None:
    """删除生成的脚本文件"""
    for filename in ALL_SCRIPT_FILES:
        try:
            os.remove(os.path.join(cmd_file_path, filename))
        except FileNotFoundError:
            continue