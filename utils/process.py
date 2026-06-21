"""
进程操作工具类
封装 psutil 的进程管理功能
"""

import psutil
import os
from typing import Optional, List, Union


class ProcessManager:
    """进程管理器"""
    
    @staticmethod
    def find_process(name: str) -> Optional[psutil.Process]:
        """
        根据进程名查找进程
        
        Args:
            name: 进程名（如 'Student.exe'）
            
        Returns:
            找到的进程对象，未找到返回 None
        """
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['name'] == name:
                    return psutil.Process(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    @staticmethod
    def get_process_path(name: str) -> Optional[str]:
        """
        获取进程的可执行文件路径
        
        Args:
            name: 进程名
            
        Returns:
            进程路径，未找到返回 None
        """
        for proc in psutil.process_iter(['pid', 'name', 'exe']):
            try:
                if proc.info['name'] == name:
                    return proc.info['exe']
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        return None
    
    @staticmethod
    def kill_process(name: str) -> bool:
        """
        强制终止指定进程
        
        Args:
            name: 进程名
            
        Returns:
            是否成功终止
        """
        proc = ProcessManager.find_process(name)
        if proc:
            try:
                proc.kill()
                return True
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                return False
        return False
    
    @staticmethod
    def kill_processes(names: List[str]) -> dict:
        """
        批量终止多个进程
        
        Args:
            names: 进程名列表
            
        Returns:
            字典 {进程名: 是否成功}
        """
        results = {}
        for name in names:
            results[name] = ProcessManager.kill_process(name)
        return results
    
    @staticmethod
    def suspend_process(name: str) -> Union[bool, str]:
        """
        挂起（暂停）指定进程
        
        Args:
            name: 进程名
            
        Returns:
            True 表示成功，str 表示错误信息
        """
        proc = ProcessManager.find_process(name)
        if proc:
            try:
                proc.suspend()
                return True
            except psutil.AccessDenied:
                return f"挂起 {name} 失败：权限不足"
            except Exception as e:
                return f"挂起 {name} 失败：{e}"
        return f"未找到进程 {name}"
    
    @staticmethod
    def resume_process(name: str) -> Union[bool, str]:
        """
        恢复挂起的进程
        
        Args:
            name: 进程名
            
        Returns:
            True 表示成功，str 表示错误信息
        """
        proc = ProcessManager.find_process(name)
        if proc:
            try:
                proc.resume()
                return True
            except psutil.AccessDenied:
                return f"恢复 {name} 失败：权限不足"
            except Exception as e:
                return f"恢复 {name} 失败：{e}"
        return f"未找到进程 {name}"
    
    @staticmethod
    def is_process_running(name: str) -> bool:
        """
        检查进程是否正在运行
        
        Args:
            name: 进程名
            
        Returns:
            是否正在运行
        """
        return ProcessManager.find_process(name) is not None
    
    @staticmethod
    def get_pid(name: str) -> Optional[int]:
        """
        获取进程 PID
        
        Args:
            name: 进程名
            
        Returns:
            PID，未找到返回 None
        """
        proc = ProcessManager.find_process(name)
        return proc.pid if proc else None
