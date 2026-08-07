# src/modules/usb_network_unlock.py
# USB/网络解锁

import os
import time

from src.core.runtime_config import toolkit_cfg
from src.core.helpers import runbat, run_sigle_cmd
from src.modules.script_generator import script_gen
from config import UNLOCK_NET_BAT, UNLOCK_USB_BAT


def usb_unlock():
    """尝试解锁USB管控"""
    from src.core.helpers import show_snack
    from src.utils.system.logger import info
    info("开始 USB 解锁流程")
    show_snack("尝试关闭USB服务... 请稍等")
    script_gen.summon_unlocknet()
    script_gen.summon_unlock_usb()
    runbat(UNLOCK_NET_BAT)
    time.sleep(2)
    runbat(UNLOCK_USB_BAT)
    info("USB 解锁脚本已执行")


def unlock_network() -> None:
    """停止网络管控服务（不可逆，服务不会自动恢复）。
    用 Popen 启动循环击杀脚本获取精确 PID，完成后 taskkill 杀进程。"""
    import subprocess
    from src.core.constants import cmd_file_path
    from src.core.helpers import show_snack
    from src.utils.system.logger import info

    script_gen.summon_unlocknet()
    info("开始网络解锁流程")
    show_snack("解锁网络锁定中 请稍等")

    batpath = os.path.join(cmd_file_path, UNLOCK_NET_BAT)
    info(f"启动网络解锁脚本: {batpath}")
    proc = subprocess.Popen(
        ["cmd.exe", "/c", batpath],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )
    pid = proc.pid
    info(f"网络解锁脚本 PID={pid}")

    time.sleep(2)
    run_sigle_cmd("sc stop OeNetlimit")
    time.sleep(1)

    run_sigle_cmd(f"taskkill /f /t /pid {pid}")
    time.sleep(1)
    info("网络解锁流程完成")
    show_snack("执行完成 理论上网络已解锁")