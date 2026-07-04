# src/modules/usb_network_unlock.py
# USB/网络解锁

import os
import time

from src.core.runtime_config import toolbox_cfg
from src.core.helpers import runbat, run_sigle_cmd, use_bat_file_to_run_cmd
from src.modules.process_manager import utils
from src.modules.script_generator import script_gen


def TryGetStudentPath() -> tuple[str, str] | tuple[bool, None]:
    """尝试获取学生端路径 并更新全局变量"""

    Spath = utils.get_program_path("Student.exe")
    Spath_2 = utils.get_program_path("MmcStudent.exe")
    # v10.9.1 学生端改名为MmcStudent.exe

    if Spath == None and Spath_2 == None:
        print("[DEBUG] > 未找到运行中的学生端")

        isModed = toolbox_cfg.get_config_key_data("studentPath_have_been_modified")
        print(f"[DEBUG] 配置文件 > 学生端路径是否被修改：{isModed}")
        if not isModed:
            return False, None

        toolbox_cfg.oseasypath_have_been_modified = True

        toolbox_cfg.oseasy_path = toolbox_cfg.get_config_key_data("studentPath")
        toolbox_cfg.student_exe_name = toolbox_cfg.get_config_key_data("studentExeName")

        print(f"[DEBUG] 配置文件 > 学生端路径为：{toolbox_cfg.oseasy_path}")
        print(f"[DEBUG] 配置文件 > 学生端进程名为：{toolbox_cfg.student_exe_name}")

        toolbox_cfg.set_config_key_data("studentPath", toolbox_cfg.oseasy_path)
        toolbox_cfg.set_config_key_data("studentExeName", toolbox_cfg.student_exe_name)

        return toolbox_cfg.oseasy_path, toolbox_cfg.student_exe_name

    if Spath_2:
        Spath = Spath_2
        exe_name = "MmcStudent.exe"
    else:
        exe_name = "Student.exe"

    Spath = str(Spath).replace("/", "\\").removesuffix(exe_name)

    toolbox_cfg.oseasypath_have_been_modified = True
    toolbox_cfg.oseasy_path = Spath
    toolbox_cfg.student_exe_name = exe_name

    print(f"[DEBUG] 学生端路径为：{toolbox_cfg.oseasy_path}")
    print(f"[DEBUG] 学生端进程名为：{toolbox_cfg.student_exe_name}")

    toolbox_cfg.set_config_key_data("studentPath", toolbox_cfg.oseasy_path)
    toolbox_cfg.set_config_key_data("studentExeName", toolbox_cfg.student_exe_name)
    toolbox_cfg.set_config_key_data("studentPath_have_been_modified", True)

    return toolbox_cfg.oseasy_path, toolbox_cfg.student_exe_name


def usb_unlock():
    """尝试解锁USB管控"""
    from src.core.helpers import Ui_call_show_snake_message
    Ui_call_show_snake_message("尝试关闭USB服务... 请稍等")
    script_gen.summon_unlocknet()
    script_gen.summon_unlock_usb()
    runbat("net.bat")
    time.sleep(2)
    runbat("usb.bat")


def handle_run_old_unlock_net() -> None:
    from src.core.helpers import Ui_call_show_snake_message
    script_gen.summon_unlocknet()
    runbat("net.bat")
    Ui_call_show_snake_message("解锁网络锁定中 请稍等")
    time.sleep(2)
    run_sigle_cmd("sc stop OeNetlimit")
    time.sleep(1)
    use_bat_file_to_run_cmd(
        'taskkill /f /t /fi "imagename eq cmd.exe" /fi "windowtitle eq 管理员:  OsEasyToolBoxUnlockNetHeler"'
    )
    time.sleep(1)
    Ui_call_show_snake_message("执行完成 理论上网络已解锁")