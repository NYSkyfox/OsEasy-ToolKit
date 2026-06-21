"""
DLL 调用服务 - 封装 ctypes 调用噢易 DLL
"""

import ctypes
from ctypes import wintypes
from typing import Optional, Callable
from utils.helpers import show_message
import config


class DllService:
    """DLL 调用服务类"""
    
    def __init__(self, student_service):
        """
        Args:
            student_service: StudentService 实例
        """
        self.student = student_service
    
    def _load_dll(self, dll_name: str):
        """
        加载 DLL
        
        Args:
            dll_name: DLL 文件名（相对学生端路径）
            
        Returns:
            ctypes.WinDLL 对象
        """
        dll_path = self.student.path + dll_name
        return ctypes.WinDLL(dll_path)
    
    def _setup_function(self, dll, func_name: str, 
                       restype=ctypes.c_int, argtypes=None):
        """
        设置 DLL 函数参数和返回类型
        
        Args:
            dll: DLL 对象
            func_name: 函数名
            restype: 返回类型
            argtypes: 参数类型列表
            
        Returns:
            设置好的函数
        """
        func = getattr(dll, func_name)
        func.restype = restype
        func.argtypes = argtypes or []
        return func
    
    def _get_error_message(self, error_code: int) -> str:
        """
        获取 Windows 错误信息
        
        Args:
            error_code: 错误码
            
        Returns:
            错误信息字符串
        """
        msg_buffer = ctypes.create_unicode_buffer(256)
        ctypes.windll.kernel32.FormatMessageW(
            0x00001000,  # FORMAT_MESSAGE_FROM_SYSTEM
            None,
            error_code,
            0,
            msg_buffer,
            len(msg_buffer),
            None,
        )
        return msg_buffer.value
    
    def call_usb_function(self, func_key: str) -> str:
        """
        调用 USB 管控 DLL 函数
        
        Args:
            func_key: 功能键 (start, stop, status)
            
        Returns:
            结果信息
        """
        try:
            dll_cfg = config.DLL_CONFIG["usb_ctrl"]
            dll = self._load_dll(dll_cfg["path"])
            func_name = dll_cfg["functions"][func_key]
            
            if func_key == "status":
                # 查询状态需要输出参数
                out_buffer = wintypes.DWORD(0)
                func = self._setup_function(
                    dll, func_name, 
                    ctypes.c_int, 
                    [ctypes.POINTER(wintypes.DWORD)]
                )
                result = func(ctypes.byref(out_buffer))
                
                msg = f"USB 管控状态查询\n返回值: {result}\n状态: {out_buffer.value}"
                if result != 0:
                    msg += f"\n错误: {self._get_error_message(result)}"
                return msg
            else:
                func = self._setup_function(dll, func_name)
                result = func()
                
                action = "启动" if func_key == "start" else "停止"
                msg = f"USB 管控{action}\n返回值: {result}"
                if result != 0:
                    msg += f"\n错误: {self._get_error_message(result)}"
                return msg
                
        except Exception as e:
            return f"调用 USB DLL 失败: {e}"
    
    def call_net_function(self, func_key: str) -> str:
        """
        调用网络管控 DLL 函数
        
        Args:
            func_key: 功能键 (enable, disable)
            
        Returns:
            结果信息
        """
        try:
            dll_cfg = config.DLL_CONFIG["net_limit"]
            dll = self._load_dll(dll_cfg["path"])
            func_name = dll_cfg["functions"][func_key]
            
            func = self._setup_function(dll, func_name)
            result = func()
            
            action = "开启" if func_key == "enable" else "关闭"
            msg = f"网络管控{action}\n返回值: {result}"
            if result != 0:
                msg += f"\n错误: {self._get_error_message(result)}"
            return msg
            
        except Exception as e:
            return f"调用网络 DLL 失败: {e}"
    
    def usb_start(self) -> str:
        """启动 USB 管控"""
        return self.call_usb_function("start")
    
    def usb_stop(self) -> str:
        """停止 USB 管控"""
        return self.call_usb_function("stop")
    
    def usb_status(self) -> str:
        """查询 USB 管控状态"""
        return self.call_usb_function("status")
    
    def net_enable(self) -> str:
        """开启网络管控"""
        return self.call_net_function("enable")
    
    def net_disable(self) -> str:
        """关闭网络管控"""
        return self.call_net_function("disable")