# src/modules/script_generator.py
# 脚本生成器

from src.core.constants import cmd_file_path
from src.core.runtime_config import toolbox_cfg
from src.modules.file_handler import backup_oe_files
from src.modules.service_manager import if_is_high_ver_client_then_return_stop_cmd_line


class script_gen:
    @staticmethod
    def summon_unlocknet() -> None:
        """生成解锁网络锁定脚本"""
        mp = cmd_file_path + "\\net.bat"
        cmdtext = f"""@ECHO OFF\n
        title OsEasyToolBoxUnlockNetHeler\n
        {if_is_high_ver_client_then_return_stop_cmd_line(True)}
        :a\n
        taskkill /f /t /im {toolbox_cfg.student_exe_name}\n
        taskkill /f /t /im DeviceControl_x64.exe\n
        goto a
        """
        with open(mp, "w") as f:
            f.write(cmdtext)

    @staticmethod
    def summon_unlock_usb() -> None:
        """生成解锁USB脚本"""
        mp = cmd_file_path + "\\usb.bat"
        cmdtext = """@ECHO OFF\n
        title OsEasyToolBoxUnlockUSBHeler\n

        sc delete easyusbflt\n
        sc delete easyusbflt\n
        timeout 1\n
        
        del C:\\Windows\\System32\\drivers\\easyusbflt.sys\n
        timeout 5\n
        shutdown /l
        """
        with open(mp, "w") as f:
            f.write(cmdtext)

    @staticmethod
    def summon_killer_v2() -> None:
        """生成V2击杀脚本"""
        mp = cmd_file_path + "\\kv2.bat"
        cmdtext = f"@ECHO OFF\ntitle OsEasyToolBoxKillerV2\n:awa\nfor %%p in (Ctsc_Multi.exe,DeviceControl_x64.exe,HRMon.exe,MultiClient.exe,OActiveII-Client.exe,OEClient.exe,OELogSystem.exe,OEUpdate.exe,OEProtect.exe,ProcessProtect.exe,RunClient.exe,RunClient.exe,ServerOSS.exe,{toolbox_cfg.student_exe_name},wfilesvr.exe,tvnserver.exe,updatefilesvr.exe,ScreenRender.exe) do taskkill /f /IM %%p\ngoto awa\n"
        with open(mp, "w") as f:
            f.write(cmdtext)

    @staticmethod
    def summon_killer() -> None:
        """生成击杀脚本"""
        mp = cmd_file_path + "\\k.bat"
        cmdtext = f"""@ECHO OFF\n
        title OsEasyToolBoxKiller\n
        
        {if_is_high_ver_client_then_return_stop_cmd_line(True)}
        
        taskkill /f /t /im MultiClient.exe\n
        taskkill /f /t /im MultiClient.exe\n
        taskkill /f /t /im BlackSlient.exe\n
        :a\n
        taskkill /f /t /im {toolbox_cfg.student_exe_name}\n
        goto a"""
        with open(mp, "w") as f:
            f.write(cmdtext)

    @staticmethod
    def summon_del_dll(delMtc: bool, shutdown: bool) -> None:
        """生成删除关键文件脚本"""
        backup_oe_files()

        mp = cmd_file_path + "\\d.bat"
        cmdtext = f"@ECHO OFF\ntitle OsEasyToolBox-Helper\ncd /D {toolbox_cfg.oseasy_path}\ntimeout 1\ndel /F /S LockKeyboard.dll\ndel /F /S LoadDriver.exe\ndel /F /S LoadDriver.exe\ndel /F /S oenetlimitx64.cat\ndel /F /S BlackSlient.exe\ncd x86\ndel /F /S LISSNetInfoSniffer.exe\ncd .."
        if delMtc == True:
            cmdtext += "\ndel /F /S MultiClient.exe"
        if shutdown == False:
            pass
        elif shutdown == True:
            cmdtext += "\ntimeout 5\nshutdown /l"
        cmdtext += "\nexit"
        with open(mp, "w") as f:
            f.write(cmdtext)