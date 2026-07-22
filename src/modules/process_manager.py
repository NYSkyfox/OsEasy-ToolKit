# src/modules/process_manager.py
# 进程管理工具

import os

import psutil
import pyautogui

from src.core.helpers import get_time_str


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
        try:
            for process in psutil.process_iter(["pid", "name"]):
                if process.info["name"] == process_name:
                    pid = process.info["pid"]

                    psutil.Process(pid).suspend() if option == "suspend" \
                    else psutil.Process(pid).resume()

                    print(f"Process {process_name} (PID {pid}) {option}.")
                    return True
            print(f"Process {process_name} not found.")
            return f"尝试{option}的进程未找到"
        except psutil.AccessDenied as e:
            print(f"Permission error: {e}")
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


def get_scshot() -> None:
    """保存一张屏幕截图到用户数据目录的 Screenshots/，并复制到剪贴板"""
    from src.core.constants import cmd_file_path
    savepath = os.path.join(cmd_file_path, "..", "Screenshots")
    os.makedirs(savepath, exist_ok=True)

    PMsize = pyautogui.size()
    print("DEBUG 屏幕尺寸 > ", PMsize)

    img = pyautogui.screenshot()

    mix_name = os.path.join(savepath, get_time_str() + ".jpg")
    img.save(mix_name, quality=95, optimize=True)
    print("DEBUG SavePath > ", mix_name)

    # 复制到剪贴板
    try:
        import io
        import win32clipboard
        from PIL import Image
        output = io.BytesIO()
        img.convert("RGB").save(output, format="BMP")
        data = output.getvalue()[14:]  # 去掉 BMP 文件头(14字节)
        output.close()
        win32clipboard.OpenClipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32clipboard.CF_DIB, data)
        win32clipboard.CloseClipboard()
        print("DEBUG 截图已复制到剪贴板")
    except Exception as e:
        print(f"DEBUG 复制到剪贴板失败: {e}")