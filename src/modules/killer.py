# src/modules/killer.py
# 击杀脚本、粘滞键绑定、守护进程

import os
import threading
import time

import pygetwindow as gw

from src.core.constants import cmd_file_path, is_box_killer_running, is_protect_killer_script_running
from src.core.helpers import runbat, run_sigle_cmd, use_bat_file_to_run_cmd
from src.core.runtime_config import toolbox_cfg
from src.modules.script_generator import script_gen


def register_killer_script() -> None:
    """生成击杀脚本并绑定粘滞键"""
    script_gen.summon_killer()
    run_sigle_cmd(
        f'REG ADD "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\sethc.exe" /v Debugger /t REG_SZ /d "{cmd_file_path}\\k.bat"'
    )


def del_register_killer() -> None:
    """清理绑定的粘滞键重定向"""
    run_sigle_cmd(
        'REG DELETE "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\sethc.exe" /v Debugger /f'
    )


def register_killer_v2_cmd() -> None:
    """生成击杀脚本V2并绑定粘滞键"""
    script_gen.summon_killer_v2()
    run_sigle_cmd(
        f'REG ADD "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\Image File Execution Options\\sethc.exe" /v Debugger /t REG_SZ /d "{cmd_file_path}\\kv2.bat"'
    )


def check_killer_script_is_alreay_start() -> None:
    """检测是否开启了击杀脚本
    若未开启则帮助启动一次
    已经开启则忽略"""
    try:
        window = gw.getWindowsWithTitle("OsEasyToolBoxKiller")[0]
    except:
        script_gen.summon_killer()
        runbat("k.bat")


def start_killer_protect() -> None:
    """启动守护进程"""
    global is_protect_killer_script_running
    ptct = 0
    while is_protect_killer_script_running == True:
        try:
            window = gw.getWindowsWithTitle("OsEasyToolBoxKiller")[0]
            time.sleep(0.5)
        except:
            runbat("k.bat")
            ptct += 1
            time.sleep(1)


def run_inner_toolbox_killer_loop() -> None:
    global is_box_killer_running
    while is_box_killer_running == True:
        opt = os.system(f"taskkill /f /t /im {toolbox_cfg.student_exe_name}")
        time.sleep(0.2)


def killer_script_protect() -> None:
    global is_protect_killer_script_running
    if is_protect_killer_script_running == False:
        is_protect_killer_script_running = True
        script_gen.summon_killer()
        threading.Thread(target=start_killer_protect, daemon=True).start()
    elif is_protect_killer_script_running == True:
        is_protect_killer_script_running = False
        use_bat_file_to_run_cmd(
            'taskkill /f /t /fi "imagename eq cmd.exe" /fi "windowtitle eq 管理员:  OsEasyToolBoxKiller"'
        )


def selfunc_g1plus(*e) -> None:
    # 注册V2版本的替换击杀脚本
    register_killer_v2_cmd()


def del_locked_exe_then_logout(need_shutdown: bool) -> None:
    script_gen.summon_killer()
    check_killer_script_is_alreay_start()
    script_gen.summon_del_dll(delMtc=True, shutdown=need_shutdown)
    time.sleep(2)
    runbat("d.bat")


def start_oseasy_self_toolbox(*e) -> None:
    register_killer_script()
    check_killer_script_is_alreay_start()
    time.sleep(2)
    os.startfile(f"{toolbox_cfg.oseasy_path}AssistHelper.exe")