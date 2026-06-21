"""
解锁服务 - 提供各种解锁方案
"""

import os
import time
from typing import Optional
from utils.helpers import (
    run_cmd, ensure_dir, write_bat_file, check_file_exists
)
from utils.process import ProcessManager
import config


class UnlockService:
    """解锁服务类"""
    
    def __init__(self, student_service):
        """
        Args:
            student_service: StudentService 实例
        """
        self.student = student_service
        ensure_dir(config.CMD_FILE_PATH)
        ensure_dir(config.BACKUP_FILE_PATH)
    
    def backup_files(self) -> bool:
        """
        备份噢易关键文件
        
        Returns:
            是否成功
        """
        try:
            for filename in config.BACKUP_FILE_LIST:
                src = os.path.join(self.student.path, filename)
                dst = os.path.join(config.BACKUP_FILE_PATH, filename)
                if check_file_exists(src):
                    run_cmd(f'copy "{src}" "{dst}" /Y')
            return True
        except Exception as e:
            print(f"备份失败: {e}")
            return False
    
    def restore_files(self) -> Tuple[bool, list]:
        """
        恢复备份的关键文件
        
        Returns:
            (是否全部成功, 失败文件列表)
        """
        failed = []
        
        for filename in config.BACKUP_FILE_LIST:
            src = os.path.join(config.BACKUP_FILE_PATH, filename)
            dst = os.path.join(self.student.path, filename)
            
            if check_file_exists(src):
                run_cmd(f'copy "{src}" "{dst}" /Y')
        
        # 等待复制完成并检查
        time.sleep(2)
        
        for filename in config.BACKUP_FILE_LIST:
            dst = os.path.join(self.student.path, filename)
            if not check_file_exists(dst):
                failed.append(filename)
        
        return len(failed) == 0, failed
    
    def restore_single_file(self, filename: str) -> bool:
        """
        恢复单个文件
        
        Args:
            filename: 文件名
            
        Returns:
            是否成功
        """
        src = os.path.join(config.BACKUP_FILE_PATH, filename)
        dst = os.path.join(self.student.path, filename)
        
        if check_file_exists(src):
            run_cmd(f'copy "{src}" "{dst}" /Y')
            time.sleep(1)
            return check_file_exists(dst)
        return False
    
    def generate_del_script(self, del_multiclient: bool = True, logout: bool = True) -> str:
        """
        生成删除关键文件的脚本内容
        
        Args:
            del_multiclient: 是否删除 MultiClient.exe
            logout: 执行后是否注销
            
        Returns:
            脚本内容
        """
        lines = [
            "@ECHO OFF",
            "title OsEasy-ToolKit-Unlock",
            f"cd /D {self.student.path}",
            "timeout 1",
            "del /F /S LockKeyboard.dll",
            "del /F /S LoadDriver.exe",
            "del /F /S BlackSlient.exe",
            "del /F /S oenetlimitx64.cat",
        ]
        
        if del_multiclient:
            lines.append("del /F /S MultiClient.exe")
        
        if logout:
            lines.extend(["timeout 5", "shutdown /l"])
        
        lines.append("exit")
        
        return "\n".join(lines)
    
    def generate_killer_script(self) -> str:
        """
        生成循环 kill 学生端的脚本内容
        
        Returns:
            脚本内容
        """
        mmpc_stop = ""
        if self.student.is_high_version():
            mmpc_stop = "sc stop MMPC\n"
        
        return f"""@ECHO OFF
title OsEasy-ToolKit-Killer
{mmpc_stop}taskkill /f /t /im MultiClient.exe
taskkill /f /t /im BlackSlient.exe
:a
taskkill /f /t /im {self.student.exe_name}
goto a
"""
    
    def generate_killer_v2_script(self) -> str:
        """
        生成 V2 版 kill 脚本（kill 更多进程）
        
        Returns:
            脚本内容
        """
        processes = ",".join(config.KILL_PROCESS_LIST)
        processes = processes.replace(self.student.exe_name, f"{self.student.exe_name}")
        
        return f"""@ECHO OFF
title OsEasy-ToolKit-KillerV2
:awa
for %p in ({processes}) do taskkill /f /IM %p
goto awa
"""
    
    def generate_unlock_net_script(self) -> str:
        """
        生成解锁网络脚本
        
        Returns:
            脚本内容
        """
        mmpc_stop = ""
        if self.student.is_high_version():
            mmpc_stop = "sc stop MMPC\n"
        
        return f"""@ECHO OFF
title OsEasy-ToolKit-UnlockNet
{mmpc_stop}:a
taskkill /f /t /im {self.student.exe_name}
taskkill /f /t /im DeviceControl_x64.exe
goto a
"""
    
    def run_unlock(self, del_multiclient: bool = True, logout: bool = True) -> bool:
        """
        执行解锁（删除关键文件）
        
        Args:
            del_multiclient: 是否删除控屏程序
            logout: 是否注销
            
        Returns:
            是否成功启动脚本
        """
        # 先备份
        self.backup_files()
        
        # 生成并运行 killer 脚本
        killer_content = self.generate_killer_script()
        killer_path = os.path.join(config.CMD_FILE_PATH, "killer.bat")
        write_bat_file(killer_path, killer_content)
        
        # 生成删除脚本
        del_content = self.generate_del_script(del_multiclient, logout)
        del_path = os.path.join(config.CMD_FILE_PATH, "unlock.bat")
        write_bat_file(del_path, del_content)
        
        # 运行 killer
        if check_file_exists(killer_path):
            os.startfile(killer_path)
        
        time.sleep(2)
        
        # 运行删除脚本
        if check_file_exists(del_path):
            os.startfile(del_path)
            return True
        
        return False
    
    def register_sticky_keys_backdoor(self) -> bool:
        """
        注册粘滞键后门（按5次Shift触发kill脚本）
        
        Returns:
            是否成功
        """
        killer_path = os.path.join(config.CMD_FILE_PATH, "killer.bat")
        
        # 确保 killer 脚本存在
        if not check_file_exists(killer_path):
            content = self.generate_killer_script()
            write_bat_file(killer_path, content)
        
        reg_cmd = (
            f'REG ADD "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\'
            f'Image File Execution Options\\sethc.exe" /v Debugger /t REG_SZ '
            f'/d "{killer_path}" /f'
        )
        
        run_cmd(reg_cmd)
        return True
    
    def remove_sticky_keys_backdoor(self) -> bool:
        """
        移除粘滞键后门
        
        Returns:
            是否成功
        """
        reg_cmd = (
            'REG DELETE "HKLM\\SOFTWARE\\Microsoft\\Windows NT\\CurrentVersion\\'
            'Image File Execution Options\\sethc.exe" /v Debugger /f'
        )
        run_cmd(reg_cmd)
        return True


# 导入 Tuple 用于类型注解
from typing import Tuple