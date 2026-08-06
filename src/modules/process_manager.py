# src/modules/process_manager.py
# 进程管理工具

import os
import ctypes
import struct
from ctypes import wintypes

import psutil

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
    """保存一张屏幕截图到用户数据目录的 Screenshots/，并复制到剪贴板（纯 GDI，零依赖）"""
    from src.core.constants import cmd_file_path

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    kernel32 = ctypes.windll.kernel32

    # 获取屏幕尺寸
    SW = user32.GetSystemMetrics(0)   # SM_CXSCREEN
    SH = user32.GetSystemMetrics(1)   # SM_CYSCREEN
    print("DEBUG 屏幕尺寸 > ", SW, "x", SH)

    # GDI 截屏
    hdc_screen = user32.GetDC(0)
    hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, SW, SH)
    gdi32.SelectObject(hdc_mem, hbmp)
    gdi32.BitBlt(hdc_mem, 0, 0, SW, SH, hdc_screen, 0, 0, 0x00CC0020)  # SRCCOPY

    # ---- 保存为 BMP ----
    savepath = os.path.join(cmd_file_path, "..", "Screenshots")
    os.makedirs(savepath, exist_ok=True)
    mix_name = os.path.join(savepath, get_time_str() + ".bmp")

    # 构造 BMP 文件头 + DIB 数据
    bmp_header_size = 14
    dib_header_size = 40
    row_size = ((SW * 24 + 31) // 32) * 4  # 每行对齐到4字节
    image_size = row_size * SH
    file_size = bmp_header_size + dib_header_size + image_size

    bmp_data = bytearray(file_size)
    # BMP 文件头 (14 bytes)
    bmp_data[0:2] = b'BM'
    struct.pack_into('<I', bmp_data, 2, file_size)
    struct.pack_into('<I', bmp_data, 10, bmp_header_size + dib_header_size)
    # DIB 头 (40 bytes)
    struct.pack_into('<I', bmp_data, 14, dib_header_size)
    struct.pack_into('<i', bmp_data, 18, SW)
    struct.pack_into('<i', bmp_data, 22, SH)
    struct.pack_into('<H', bmp_data, 26, 1)       # planes
    struct.pack_into('<H', bmp_data, 28, 24)       # bits per pixel
    struct.pack_into('<I', bmp_data, 34, image_size)

    # 读像素到 BMP buffer
    offset = bmp_header_size + dib_header_size
    buf = (ctypes.c_ubyte * image_size).from_buffer(bmp_data, offset)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, SH, buf,
                    ctypes.byref(_BITMAPINFO(SW, SH)), 0)  # DIB_RGB_COLORS=0

    with open(mix_name, "wb") as f:
        f.write(bmp_data)
    print("DEBUG SavePath > ", mix_name)

    # ---- 复制到剪贴板 ----
    # DIB 数据 = 去掉 BMP 文件头的部分
    dib_data = bytes(bmp_data[bmp_header_size:file_size])

    GMEM_MOVEABLE = 0x0002
    CF_DIB = 8
    size = len(dib_data)
    hmem = kernel32.GlobalAlloc(GMEM_MOVEABLE, size)
    if hmem:
        ptr = kernel32.GlobalLock(hmem)
        buf2 = (ctypes.c_char * size).from_address(ptr)
        buf2[:] = dib_data
        kernel32.GlobalUnlock(hmem)

        if user32.OpenClipboard(0):
            user32.EmptyClipboard()
            user32.SetClipboardData(CF_DIB, hmem)
            user32.CloseClipboard()
            print("DEBUG 截图已复制到剪贴板")
        else:
            kernel32.GlobalFree(hmem)
            print("DEBUG 打开剪贴板失败")

    # 清理
    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(0, hdc_screen)


# ---- GDI 辅助结构 ----

class _BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]

class _BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", _BITMAPINFOHEADER),
    ]

    def __init__(self, width, height):
        super().__init__()
        self.bmiHeader.biSize = ctypes.sizeof(_BITMAPINFOHEADER)
        self.bmiHeader.biWidth = width
        self.bmiHeader.biHeight = height
        self.bmiHeader.biPlanes = 1
        self.bmiHeader.biBitCount = 24