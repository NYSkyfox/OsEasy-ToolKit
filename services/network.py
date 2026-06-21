"""
网络管控服务
"""

import time
from utils.helpers import run_cmd
from utils.process import ProcessManager
import config


class NetworkService:
    """网络管控服务类"""
    
    @staticmethod
    def unlock_network(student_service) -> str:
        """
        解锁网络限制
        
        Args:
            student_service: StudentService 实例
            
        Returns:
            结果信息
        """
        from services.unlock import UnlockService
        
        unlock = UnlockService(student_service)
        
        # 生成解锁网络脚本
        content = unlock.generate_unlock_net_script()
        net_bat = f"{config.CMD_FILE_PATH}\\unlock_net.bat"
        
        from utils.helpers import write_bat_file
        write_bat_file(net_bat, content)
        
        # 运行脚本
        from utils.helpers import run_bat
        run_bat(net_bat)
        
        time.sleep(2)
        
        # 停止网络限制服务
        run_cmd(f"sc stop {config.SERVICES['net_limit']}")
        
        time.sleep(1)
        
        return "网络解锁命令已执行"
    
    @staticmethod
    def stop_netlimit_service() -> bool:
        """
        停止网络限制服务
        
        Returns:
            是否成功
        """
        try:
            run_cmd(f"sc stop {config.SERVICES['net_limit']}")
            return True
        except Exception as e:
            print(f"停止网络服务失败: {e}")
            return False
    
    @staticmethod
    def start_netlimit_service() -> bool:
        """
        启动网络限制服务
        
        Returns:
            是否成功
        """
        try:
            run_cmd(f"sc start {config.SERVICES['net_limit']}")
            return True
        except Exception as e:
            print(f"启动网络服务失败: {e}")
            return False