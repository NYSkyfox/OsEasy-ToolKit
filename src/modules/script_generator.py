# src/modules/script_generator.py
# 脚本生成器

from config import SOURCE_NAME, KILLER_BAT, KILLER_V2_BAT, HELPER_BAT, UNLOCK_NET_BAT, UNLOCK_USB_BAT
from src.core.constants import cmd_file_path
from src.core.runtime_config import toolkit_cfg
from src.modules.service_manager import get_mmpc_cmd

class script_gen:
    @staticmethod
    def summon_unlocknet() -> None:
        """生成解锁网络锁定脚本"""
        mp = cmd_file_path + "\\" + UNLOCK_NET_BAT
        cmdtext = f"""@ECHO OFF\n
        title {SOURCE_NAME}-UnlockNetHeler\n
        {get_mmpc_cmd(True)}
        :a\n
        taskkill /f /t /im {toolkit_cfg.student_exe_name}\n
        taskkill /f /t /im DeviceControl_x64.exe\n
        goto a
        """
        with open(mp, "w") as f:
            f.write(cmdtext)

    @staticmethod
    def summon_unlock_usb() -> None:
        """生成解锁USB脚本"""
        mp = cmd_file_path + "\\" + UNLOCK_USB_BAT
        cmdtext = f"""@ECHO OFF\n
        title {SOURCE_NAME}-UnlockUSBHeler\n

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
        mp = cmd_file_path + "\\" + KILLER_V2_BAT
        cmdtext = f"@ECHO OFF\ntitle {SOURCE_NAME}-KillerV2\n:awa\nfor %%p in (Ctsc_Multi.exe,DeviceControl_x64.exe,HRMon.exe,MultiClient.exe,OActiveII-Client.exe,OEClient.exe,OELogSystem.exe,OEUpdate.exe,OEProtect.exe,ProcessProtect.exe,RunClient.exe,RunClient.exe,ServerOSS.exe,{toolkit_cfg.student_exe_name},wfilesvr.exe,tvnserver.exe,updatefilesvr.exe,ScreenRender.exe) do taskkill /f /IM %%p\ngoto awa\n"
        with open(mp, "w") as f:
            f.write(cmdtext)

    @staticmethod
    def summon_killer() -> None:
        """生成击杀脚本"""
        mp = cmd_file_path + "\\" + KILLER_BAT
        cmdtext = f"""@ECHO OFF\n
        title {SOURCE_NAME}-Killer\n
        
        {get_mmpc_cmd(True)}

        taskkill /f /t /im MultiClient.exe\n
        taskkill /f /t /im MultiClient.exe\n
        taskkill /f /t /im BlackSlient.exe\n
        :a\n
        taskkill /f /t /im {toolkit_cfg.student_exe_name}\n
        goto a"""
        with open(mp, "w") as f:
            f.write(cmdtext)

    @staticmethod
    def summon_del_dll(delMtc: bool, shutdown: bool) -> None:
        """生成删除关键文件脚本"""
        from src.modules.file_handler import backup_oe_files  # 懒导入，避免循环依赖
        backup_oe_files()

        mp = cmd_file_path + "\\" + HELPER_BAT
        cmdtext = f"@ECHO OFF\ntitle {SOURCE_NAME}-Helper\ncd /D {toolkit_cfg.oseasy_path}\ntimeout 1\ndel /F /S LockKeyboard.dll\ndel /F /S LoadDriver.exe\ndel /F /S LoadDriver.exe\ndel /F /S oenetlimitx64.cat\ndel /F /S BlackSlient.exe\ncd x86\ndel /F /S LISSNetInfoSniffer.exe\ncd .."
        if delMtc == True:
            cmdtext += "\ndel /F /S MultiClient.exe"
        if shutdown == False:
            pass
        elif shutdown == True:
            cmdtext += "\ntimeout 5\nshutdown /l"
        cmdtext += "\nexit"
        with open(mp, "w") as f:
            f.write(cmdtext)