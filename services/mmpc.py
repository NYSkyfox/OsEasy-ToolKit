"""
MMPC 服务管理
"""

import psutil
import time
from utils.helpers import run_cmd
import config


class MmpcService:
    """MMPC 根服务管理类"""
    
    SERVICE_NAME = config.SERVICES["mmpc"]
    
    @staticmethod
    def is_running() -> bool:
        """
        检查 MMPC 服务是否正在运行
        
        Returns:
            bool
        """
        try:
            service = psutil.win_service_get(MmpcService.SERVICE_NAME)
            return service.as_dict().get("status") == "running"
        except Exception:
            return False
    
    @staticmethod
    def start() -> bool:
        """
        启动 MMPC 服务
        
        Returns:
            是否成功
        """
        try:
            run_cmd(f"sc start {MmpcService.SERVICE_NAME}")
            return True
        except Exception as e:
            print(f"启动 MMPC 失败: {e}")
            return False
    
    @staticmethod
    def stop() -> bool:
        """
        停止 MMPC 服务
        
        Returns:
            是否成功
        """
        try:
            run_cmd(f"sc stop {MmpcService.SERVICE_NAME}")
            return True
        except Exception as e:
            print(f"停止 MMPC 失败: {e}")
            return False
    
    @staticmethod
    def toggle() -> str:
        """
        切换 MMPC 服务状态
        
        Returns:
            操作结果描述
        """
        if MmpcService.is_running():
            MmpcService.stop()
            time.sleep(1)
            return "MMPC 服务已停止"
        else:
            MmpcService.start()
            time.sleep(1)
            return "MMPC 服务已启动"
    
    @staticmethod
    def get_status_text() -> str:
        """
        获取状态文本
        
        Returns:
            状态描述
        """
        return "正在运行" if MmpcService.is_running() else "未运行"
    
    @staticmethod
    def auto_stop_for_high_version(student_service) -> None:
        """
        如果学生端是高版本，自动停止 MMPC 服务
        
        Args:
            student_service: StudentService 实例
        """
        if student_service.is_high_version() and MmpcService.is_running():
            MmpcService.stop()
            time.sleep(1)