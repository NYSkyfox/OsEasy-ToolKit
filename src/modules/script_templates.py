# src/modules/script_templates.py
# 击杀/删文件脚本模板（解锁已迁移至 unlock_native.py）

from src.core.settings import toolkit_cfg
from src.modules.service_manager import get_mmpc_cmd


def _mmcp_stop():
    return get_mmpc_cmd(True)


# ══════════════════════════════════════════════════════════
# 脚本模板
# ══════════════════════════════════════════════════════════

def tpl_process_killer_all() -> str:
    return (
        f"@ECHO OFF\n"
        f"title Process-Killer_All\n"
        f":awa\n"
        f"for %%p in (Ctsc_Multi.exe,DeviceControl_x64.exe,HRMon.exe,"
        f"MultiClient.exe,OActiveII-Client.exe,OEClient.exe,OELogSystem.exe,"
        f"OEUpdate.exe,OEProtect.exe,ProcessProtect.exe,RunClient.exe,"
        f"ServerOSS.exe,{toolkit_cfg.student_exe_name},wfilesvr.exe,"
        f"tvnserver.exe,updatefilesvr.exe,ScreenRender.exe) "
        f"do taskkill /f /IM %%p\n"
        f"goto awa\n"
    )


def tpl_process_killer_student() -> str:
    return f"""@ECHO OFF
title Process-Killer_Student

{_mmcp_stop()}

taskkill /f /t /im MultiClient.exe
taskkill /f /t /im BlackSlient.exe
:a
taskkill /f /t /im {toolkit_cfg.student_exe_name}
goto a
"""


def tpl_files_delete(delMtc: bool, shutdown: bool) -> str:
    lines = [
        f"@ECHO OFF",
        f"title Files-Delete",
        f"cd /D {toolkit_cfg.oseasy_path}",
        f"timeout 1",
        f"del /F /S LockKeyboard.dll",
        f"del /F /S LoadDriver.exe",
        f"del /F /S oenetlimitx64.cat",
        f"del /F /S BlackSlient.exe",
        f"cd x86",
        f"del /F /S LISSNetInfoSniffer.exe",
        f"cd ..",
    ]
    if delMtc:
        lines.append("del /F /S MultiClient.exe")
    if shutdown:
        lines.append("timeout 5")
        lines.append("shutdown /l")
    lines.append("exit")
    return "\n".join(lines)
