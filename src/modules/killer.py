# src/modules/killer.py
# 击杀脚本、粘滞键绑定、守护进程

import os
import subprocess
import threading
import time

import psutil

from src.core.constants import cmd_file_path, is_kit_killer_running, is_protect_killer_script_running
from src.core.helpers import runbat, run_sigle_cmd, use_bat_file_to_run_cmd
from src.core.runtime_config import toolkit_cfg
from src.modules.script_generator import script_gen
from src.utils.system.ifeo import (
    add_ifeo_debugger, remove_ifeo_debugger, query_ifeo_debugger,
)
from config import KILLER_BAT, KILLER_V2_BAT, HELPER_BAT

# 守护进程启动的 cmd PID（用于关闭时精确杀进程 / 检测存活）
_killer_protect_pid = None


def _start_killer_cmd():
    """启动击杀脚本 cmd 窗口，记录其 PID"""
    global _killer_protect_pid
    from src.utils.system.logger import debug
    batpath = os.path.join(cmd_file_path, KILLER_BAT)
    proc = subprocess.Popen(
        ["cmd.exe", "/c", batpath],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    _killer_protect_pid = proc.pid
    debug(f"守护进程已启动 (PID={_killer_protect_pid})")


def register_killer_script() -> None:
    """生成击杀脚本并绑定粘滞键"""
    from src.utils.system.logger import info
    info("绑定粘滞键劫持 → sethc.exe")
    script_gen.summon_killer()
    add_ifeo_debugger("sethc.exe", os.path.join(cmd_file_path, KILLER_BAT))


def del_register_killer() -> None:
    """清理绑定的粘滞键重定向"""
    from src.utils.system.logger import info
    info("解除粘滞键劫持")
    remove_ifeo_debugger("sethc.exe")


def is_sethc_hijacked() -> bool:
    """检测当前 sethc.exe 是否已被映像劫持"""
    return query_ifeo_debugger("sethc.exe") is not None


def is_killer_protected() -> bool:
    """检测外部cmd守护进程是否正在运行"""
    return is_protect_killer_script_running


def register_killer_v2_cmd() -> None:
    """生成击杀脚本V2并绑定粘滞键"""
    script_gen.summon_killer_v2()
    add_ifeo_debugger("sethc.exe", os.path.join(cmd_file_path, KILLER_V2_BAT))


def ensure_killer_running() -> None:
    """确保击杀脚本正在运行；PID 不存在则重新拉起。"""
    global _killer_protect_pid
    if _killer_protect_pid is not None and psutil.pid_exists(_killer_protect_pid):
        return
    script_gen.summon_killer()
    runbat(KILLER_BAT)


def start_killer_protect() -> None:
    """守护线程：检测 PID 对应进程是否存活，被杀后自动重新拉起。
    每次重新拉起会生成新的 PID，循环持续直到守护关闭。"""
    global is_protect_killer_script_running, _killer_protect_pid
    while is_protect_killer_script_running:
        if _killer_protect_pid is not None and psutil.pid_exists(_killer_protect_pid):
            time.sleep(0.5)
        else:
            _start_killer_cmd()
            time.sleep(1)


def start_inner_killer_loop() -> None:
    """内部击杀循环：持续 taskkill 学生端进程"""
    global is_kit_killer_running
    while is_kit_killer_running:
        os.system(f"taskkill /f /t /im {toolkit_cfg.student_exe_name}")
        time.sleep(0.2)


def killer_script_protect() -> None:
    from src.utils.system.logger import info
    global is_protect_killer_script_running, _killer_protect_pid
    if not is_protect_killer_script_running:
        info("启动 cmd 守护进程")
        is_protect_killer_script_running = True
        script_gen.summon_killer()
        threading.Thread(target=start_killer_protect, daemon=True).start()
    else:
        info("停止 cmd 守护进程")
        is_protect_killer_script_running = False
        if _killer_protect_pid is not None:
            run_sigle_cmd(f"taskkill /f /t /pid {_killer_protect_pid}")
            _killer_protect_pid = None


def selfunc_g1plus(*e) -> None:
    # 注册V2版本的替换击杀脚本
    register_killer_v2_cmd()


def delete_locked_and_logout(need_shutdown: bool) -> None:
    """击杀学生端、删除锁定 DLL 文件，可选注销"""
    script_gen.summon_killer()
    ensure_killer_running()
    script_gen.summon_del_dll(delMtc=True, shutdown=need_shutdown)
    time.sleep(2)
    runbat(HELPER_BAT)


def launch_oe_toolkit(*e) -> None:
    """启动噢易自带 AssistHelper 工具"""
    register_killer_script()
    ensure_killer_running()
    time.sleep(2)
    os.startfile(f"{toolkit_cfg.oseasy_path}AssistHelper.exe")