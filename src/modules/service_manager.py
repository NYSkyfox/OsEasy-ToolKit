# src/modules/service_manager.py
# 服务管理与版本检测

import os
import time

import psutil

from src.core.runtime_config import toolbox_cfg
from src.core.helpers import check_give_file_path_is_excs, run_sigle_cmd


def try_guess_student_client_version() -> int:
    """尝试通过检测LissHeler.exe此类旧版本没有的程序
    来猜测学生端版本"""

    if not toolbox_cfg.oseasypath_have_been_modified:
        from src.modules.usb_network_unlock import TryGetStudentPath
        _, _2 = TryGetStudentPath()

    versions = {
        109: f"{toolbox_cfg.oseasy_path}LissHelper.exe",
        108: f"{toolbox_cfg.oseasy_path}MultiClient.exe",
        105: f"{toolbox_cfg.oseasy_path}MouseKeyBoradControl.exe",
    }

    for version, path in versions.items():
        if check_give_file_path_is_excs(path):
            print(f"[Student Ver Guess] maybe is v{version // 10}.{version % 10}")
            toolbox_cfg.running_student_client_ver = version
            toolbox_cfg.set_config_key_data("studentClientVer", version)
            return toolbox_cfg.running_student_client_ver

    print("[Student Ver Guess] 超出检测范围 学生端本体可能损坏或路径不正确")
    toolbox_cfg.running_student_client_ver = 0
    return toolbox_cfg.running_student_client_ver


def if_is_high_ver_client_auto_close_mmpc_helper():
    """检查学生端版本来决定
    需不需要关闭MMPC保护服务
    """
    if not toolbox_cfg.running_student_client_ver:
        _ = try_guess_student_client_version()

    if toolbox_cfg.running_student_client_ver >= 109:
        mpStatus = check_mmpc_status()
        if mpStatus:
            run_sigle_cmd("sc stop MMPC")
            time.sleep(1)


def if_is_high_ver_client_then_return_stop_cmd_line(IsStop = True):
    """检查学生端版本 返回根服务控制指令
    用于直接插入到脚本中
    """

    if not toolbox_cfg.running_student_client_ver:
        _ = try_guess_student_client_version()

    if toolbox_cfg.running_student_client_ver >= 109:
        if IsStop == True:
            return "sc stop MMPC\n"
        else:
            return "sc start MMPC\n"
    return ""


def check_mmpc_status() -> bool:
    """检查MMPC根服务状态
    返回True/False"""
    name = "MMPC"
    service = None
    try:
        service = psutil.win_service_get(name)
        service = service.as_dict()
    except Exception as ex:
        return False

    if service and service["status"] == "running":
        return True
    else:
        return False


def run_upto_admin() -> None:
    """用于在非管理员运行时尝试提权"""
    import ctypes
    import sys
    if ctypes.windll.shell32.IsUserAnAdmin() == 0:
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable, "".join(sys.argv), None, 1
        )
        sys.exit()


def handle_start_student_client(*e) -> None:
    os.startfile(f"{toolbox_cfg.oseasy_path}{toolbox_cfg.student_exe_name}")