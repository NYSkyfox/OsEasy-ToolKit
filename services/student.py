"""
学生端服务 - 管理学生端路径探测、版本识别等
"""

import os
import json
from typing import Optional, Tuple
from utils.process import ProcessManager
from utils.helpers import check_file_exists, ensure_dir
import config


class StudentService:
    """学生端服务类"""
    
    def __init__(self):
        self._path: str = config.DEFAULT_OSEASY_PATH
        self._exe_name: str = "Student.exe"
        self._version: int = 0  # 108, 109, 105 等
        self._path_modified: bool = False
        self._load_config()
    
    def _load_config(self) -> None:
        """从配置文件加载学生端路径"""
        if check_file_exists(config.CONFIG_FILE_PATH):
            try:
                with open(config.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                saved_path = data.get("student_path")
                saved_exe = data.get("student_exe_name")
                saved_ver = data.get("student_version")
                
                if saved_path and os.path.exists(saved_path):
                    self._path = saved_path
                    self._path_modified = True
                
                if saved_exe:
                    self._exe_name = saved_exe
                
                if saved_ver:
                    self._version = saved_ver
                    
            except Exception as e:
                print(f"加载学生端配置失败: {e}")
    
    def _save_config(self) -> None:
        """保存学生端路径到配置文件"""
        data = {}
        if check_file_exists(config.CONFIG_FILE_PATH):
            try:
                with open(config.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                pass
        
        data["student_path"] = self._path
        data["student_exe_name"] = self._exe_name
        data["student_version"] = self._version
        data["student_path_modified"] = self._path_modified
        
        try:
            ensure_dir(os.path.dirname(config.CONFIG_FILE_PATH))
            with open(config.CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存学生端配置失败: {e}")
    
    def detect_path(self) -> Tuple[bool, str]:
        """
        探测学生端安装路径
        
        Returns:
            (是否成功, 信息)
        """
        # 尝试查找运行中的进程
        for exe_name in config.STUDENT_EXE_NAMES:
            path = ProcessManager.get_process_path(exe_name)
            if path:
                self._exe_name = exe_name
                self._path = os.path.dirname(path) + "\\"
                self._path_modified = True
                self._save_config()
                self.guess_version()
                return True, f"检测到运行中的学生端: {exe_name}\n路径: {self._path}"
        
        # 检查配置文件中的历史路径
        if self._path_modified and os.path.exists(self._path):
            self.guess_version()
            return True, f"使用历史路径: {self._path}"
        
        # 检查默认路径
        if os.path.exists(config.DEFAULT_OSEASY_PATH):
            self._path = config.DEFAULT_OSEASY_PATH
            self._path_modified = True
            self._save_config()
            self.guess_version()
            return True, f"使用默认路径: {self._path}"
        
        return False, "未找到学生端，请手动指定路径"
    
    def guess_version(self) -> int:
        """
        通过文件特征猜测学生端版本
        
        Returns:
            版本号 (109, 108, 105, 0)
        """
        version_files = {
            109: "LissHelper.exe",
            108: "MultiClient.exe",
            105: "MouseKeyBoradControl.exe",
        }
        
        for ver, filename in version_files.items():
            if check_file_exists(os.path.join(self._path, filename)):
                self._version = ver
                self._save_config()
                return ver
        
        self._version = 0
        return 0
    
    def is_high_version(self) -> bool:
        """是否是高版本（>= v10.9）"""
        return self._version >= 109
    
    @property
    def path(self) -> str:
        """学生端安装路径"""
        return self._path
    
    @property
    def exe_name(self) -> str:
        """学生端可执行文件名"""
        return self._exe_name
    
    @property
    def full_path(self) -> str:
        """学生端完整路径"""
        return os.path.join(self._path, self._exe_name)
    
    @property
    def version(self) -> int:
        """学生端版本号"""
        return self._version
    
    @property
    def is_running(self) -> bool:
        """学生端是否正在运行"""
        return ProcessManager.is_process_running(self._exe_name)
    
    def start(self) -> None:
        """启动学生端"""
        if os.path.exists(self.full_path):
            os.startfile(self.full_path)
    
    def get_screen_render_path(self) -> str:
        """获取 ScreenRender.exe 路径"""
        return os.path.join(self._path, "ScreenRender.exe")
    
    def get_screen_render_y_path(self) -> str:
        """获取备份的 ScreenRender_Y.exe 路径"""
        return os.path.join(self._path, "ScreenRender_Y.exe")