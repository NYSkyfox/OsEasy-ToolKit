# src/modules/process_manager.py
# 进程管理工具

import os

import psutil

from src.core.helpers import get_time_str

# 截图功能已移至 src/utils/system/screenshot.py，此处保持向后兼容
from src.utils.program.screenshot import get_scshot  # noqa: F401


class utils:
    @staticmethod
    def get_program_path(program_name) -> str | None:
        """
        获取指定程序的运行路径

        :param program_name: 程序名称，如 'exp.exe'

        :return: 程序的运行路径

        """
        for proc in psutil.process_iter(["pid", "name", "exe"]):
            try:
                if proc.info["name"] == program_name:
                    return proc.info["exe"]
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None

    @staticmethod
    def suspend_resume_process(process_name, option) -> str | bool:
        """挂起进程"""
        from src.utils.system.logger import debug as logger_debug
        try:
            for process in psutil.process_iter(["pid", "name"]):
                if process.info["name"] == process_name:
                    pid = process.info["pid"]

                    psutil.Process(pid).suspend() if option == "suspend" \
                    else psutil.Process(pid).resume()

                    logger_debug(f"Process {process_name} (PID {pid}) {option}.")
                    return True
            logger_debug(f"Process {process_name} not found.")
            return f"尝试{option}的进程未找到"
        except psutil.AccessDenied as e:
            logger_debug(f"Permission error: {e}")
            return "尝试挂起进程失败"

    @staticmethod
    def guaqi_process(process_name) -> str | bool:
        return utils.suspend_resume_process(process_name, "suspend")

    @staticmethod
    def huifu_process(process_name) -> str | bool:
        """恢复挂起进程"""
        return utils.suspend_resume_process(process_name, "resume")

    @staticmethod
    def is_process_suspended(process_name) -> bool:
        """检测指定进程是否处于挂起状态"""
        try:
            for process in psutil.process_iter(["pid", "name", "status"]):
                if process.info["name"] == process_name:
                    return process.info["status"] == psutil.STATUS_STOPPED
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
        return False


def get_proc_pid(name) -> int | None:
    """
    根据进程名获取进程pid
    未寻找到返回None
    """
    pids = psutil.process_iter()
    print("[" + name + "]'s pid is:")
    for pid in pids:
        if pid.name() == name:
            print(pid.pid)
            return pid.pid
    return None


