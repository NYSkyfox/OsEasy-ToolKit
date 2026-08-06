# src/modules/usb_network_unlock.py
# USB/网络解锁

import os
import subprocess
import time

from src.core.runtime_config import toolkit_cfg
from src.core.helpers import runbat, run_sigle_cmd
from src.modules.script_generator import script_gen
from config import UNLOCK_NET_BAT, UNLOCK_USB_BAT


def usb_unlock():
    """尝试解锁USB管控"""
    from src.core.helpers import show_snack
    show_snack("尝试关闭USB服务... 请稍等")
    script_gen.summon_unlocknet()
    script_gen.summon_unlock_usb()
    runbat(UNLOCK_NET_BAT)
    time.sleep(2)
    runbat(UNLOCK_USB_BAT)


def unlock_network() -> None:
    """停止网络管控服务（不可逆，服务不会自动恢复）。
    启动循环击杀脚本后通过 Popen.pid 精确追踪并杀进程，
    不依赖窗口标题，避免改名后杀错/杀不掉。"""
    from src.core.constants import cmd_file_path
    from src.core.helpers import show_snack

    script_gen.summon_unlocknet()
    show_snack("解锁网络锁定中 请稍等")

    # 用 Popen 启动脚本，记录 PID
    batpath = os.path.join(cmd_file_path, UNLOCK_NET_BAT)
    proc = subprocess.Popen(
        ["cmd.exe", "/c", batpath],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    pid = proc.pid

    time.sleep(2)
    run_sigle_cmd("sc stop OeNetlimit")
    time.sleep(1)

    # 通过 PID 精确杀掉脚本进程（含其子进程树）
    run_sigle_cmd(f"taskkill /f /t /pid {pid}")
    time.sleep(1)
    show_snack("执行完成 理论上网络已解锁")