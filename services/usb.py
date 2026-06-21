"""
USB 管控服务
"""

import os
from utils.helpers import run_cmd, check_file_exists
import config


class UsbService:
    """USB 管控服务类"""
    
    @staticmethod
    def unlock_usb() -> str:
        """
        解锁 USB 限制（删除驱动）
        
        Returns:
            结果信息
        """
        try:
            # 删除服务
            run_cmd(f"sc delete {config.SERVICES['usb_filter']}")
            
            # 删除驱动文件
            driver_path = r"C:\Windows\System32\drivers\easyusbflt.sys"
            if check_file_exists(driver_path):
                run_cmd(f'del "{driver_path}" /F')
            
            return "USB 解锁命令已执行，可能需要注销生效"
        except Exception as e:
            return f"USB 解锁失败: {e}"
    
    @staticmethod
    def is_driver_exists() -> bool:
        """
        检查 USB 驱动是否存在
        
        Returns:
            是否存在
        """
        driver_path = r"C:\Windows\System32\drivers\easyusbflt.sys"
        return check_file_exists(driver_path)