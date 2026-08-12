# src/utils/program/screenshot.py
# 截图工具 —— 纯 GDI 截屏，零第三方依赖，保存 PNG + 写剪贴板 + 系统通知

import os
import ctypes
import struct
import zlib
from ctypes import wintypes

from src.core.helpers import get_time_str


def get_scshot() -> None:
    """保存一张屏幕截图到用户数据目录的 Screenshots/，并复制到剪贴板（纯 GDI，零依赖）"""
    from src.core.constants import screenshot_path
    from src.utils.system.logger import debug

    user32 = ctypes.windll.user32
    gdi32 = ctypes.windll.gdi32
    kernel32 = ctypes.windll.kernel32

    hdc_screen = hdc_mem = hbmp = old_bmp = None
    hmem = None
    clipboard_open = False
    clip_msg = "图片已保存"

    # 获取屏幕尺寸
    SW = user32.GetSystemMetrics(0)   # SM_CXSCREEN
    SH = user32.GetSystemMetrics(1)   # SM_CYSCREEN
    debug(f"截图开始，屏幕尺寸 {SW}x{SH}")

    # GDI 截屏
    try:
        hdc_screen = user32.GetDC(0)
        hdc_mem = gdi32.CreateCompatibleDC(hdc_screen)
        hbmp = gdi32.CreateCompatibleBitmap(hdc_screen, SW, SH)
        old_bmp = gdi32.SelectObject(hdc_mem, hbmp)
        debug("GDI 上下文已创建，执行 BitBlt...")
        if not gdi32.BitBlt(hdc_mem, 0, 0, SW, SH, hdc_screen, 0, 0, 0x00CC0020):
            raise OSError("BitBlt 失败")
        debug("BitBlt 完成")

        # ---- 保存为 PNG（纯标准库 zlib + struct，零额外依赖）----
        savepath = screenshot_path
        os.makedirs(savepath, exist_ok=True)
        mix_name = os.path.join(savepath, get_time_str() + ".png")

        # 分配像素缓冲区（GetDIBits 返回 BMP 格式：底部在上、BGR、行补齐到 4 字节）
        bmp_row_size = ((SW * 24 + 31) // 32) * 4
        pixel_buf_size = bmp_row_size * SH
        pixel_buf = (ctypes.c_ubyte * pixel_buf_size)()

        debug("执行 GetDIBits...")
        if not gdi32.GetDIBits(hdc_mem, hbmp, 0, SH, pixel_buf,
                               ctypes.byref(BITMAPINFO(SW, SH)), 0):
            raise OSError("GetDIBits 失败")
        debug("GetDIBits 完成")

        # 将 BMP 像素转为 PNG 原始数据：翻转行序 + BGR→RGB + 去补齐 + 每行加 filter byte=0
        png_row_size = SW * 3
        raw_lines = []
        for y in range(SH - 1, -1, -1):  # 从底部向上（BMP 倒序 → PNG 正序）
            row_start = y * bmp_row_size
            row = bytearray(pixel_buf[row_start:row_start + png_row_size])
            # BGR → RGB：交换每像素的 B 和 R 通道
            for x in range(0, png_row_size, 3):
                row[x], row[x + 2] = row[x + 2], row[x]
            raw_lines.append(b'\x00' + bytes(row))  # filter byte = 0 (None)

        raw = b''.join(raw_lines)
        idat = zlib.compress(raw)

        def _png_chunk(ctype, data):
            chunk = ctype + data
            return struct.pack('>I', len(data)) + chunk + struct.pack('>I', zlib.crc32(chunk) & 0xFFFFFFFF)

        png_sig = b'\x89PNG\r\n\x1a\n'
        ihdr = struct.pack('>IIBBBBB', SW, SH, 8, 2, 0, 0, 0)  # 8bit, RGB, 无压缩/隔行/alpha

        with open(mix_name, "wb") as f:
            f.write(png_sig)
            f.write(_png_chunk(b'IHDR', ihdr))
            f.write(_png_chunk(b'IDAT', idat))
            f.write(_png_chunk(b'IEND', b''))
        debug(f"PNG 已保存: {mix_name}")

        # ---- 复制到剪贴板（纯 Win32 API，零 PowerShell/.NET 依赖）----
        debug("写入剪贴板...")
        try:
            # 检查剪贴板是否被其他进程占用（避免管理员模式下跨权限潜在死锁）
            if user32.GetOpenClipboardWindow():
                clip_msg = "剪贴板被占用，未能复制"
                debug(clip_msg)
            else:
                # 构造完整 DIB：BITMAPINFOHEADER(40B) + 像素数据（BGR、底部在上、行补齐）
                dib_header = struct.pack('<IiiHHIIiiII',
                    40, SW, SH, 1, 24, 0, pixel_buf_size, 0, 0, 0, 0)
                dib_size = len(dib_header) + pixel_buf_size

                GMEM_MOVEABLE = 0x0002
                CF_DIB = 8

                # 关键：必须声明 argtypes，否则 64 位句柄按默认 c_int 传参会溢出
                kernel32.GlobalAlloc.restype = wintypes.HGLOBAL
                kernel32.GlobalAlloc.argtypes = (wintypes.UINT, ctypes.c_size_t)
                kernel32.GlobalLock.restype = wintypes.LPVOID
                kernel32.GlobalLock.argtypes = (wintypes.HGLOBAL,)
                kernel32.GlobalUnlock.argtypes = (wintypes.HGLOBAL,)
                kernel32.GlobalFree.argtypes = (wintypes.HGLOBAL,)
                user32.OpenClipboard.argtypes = (wintypes.HWND,)
                user32.SetClipboardData.argtypes = (wintypes.UINT, wintypes.HANDLE)

                hmem = kernel32.GlobalAlloc(GMEM_MOVEABLE, dib_size)
                if not hmem:
                    clip_msg = "内存分配失败，未能复制"
                    debug(clip_msg)
                else:
                    ptr = kernel32.GlobalLock(hmem)
                    if not ptr:
                        clip_msg = "内存锁定失败，未能复制"
                        debug(clip_msg)
                    else:
                        ctypes.memmove(ptr, dib_header, len(dib_header))
                        ctypes.memmove(ptr + len(dib_header), pixel_buf, pixel_buf_size)
                        kernel32.GlobalUnlock(hmem)

                        if not user32.OpenClipboard(0):
                            clip_msg = "打开剪贴板失败，未能复制"
                            debug(clip_msg)
                        else:
                            clipboard_open = True
                            user32.EmptyClipboard()
                            if user32.SetClipboardData(CF_DIB, hmem):
                                hmem = 0  # 内存已移交给系统，不再释放
                                clip_msg = "已复制到剪贴板"
                            else:
                                clip_msg = "写入剪贴板失败"
                            user32.CloseClipboard()
                            clipboard_open = False
                            debug(clip_msg)
        except Exception as _e:
            clip_msg = f"剪贴板写入异常: {_e}"
            debug(clip_msg)
        finally:
            if clipboard_open:
                user32.CloseClipboard()
            if hmem:
                kernel32.GlobalFree(hmem)

        # ---- 系统通知（Windows 原生 Toast，右上角弹出）----
        try:
            from winotify import Notification
            toast = Notification(
                app_id="OsEasy-ToolKit",
                title="截图已保存",
                msg=clip_msg or "图片已保存",
                duration="short",
            )
            toast.show()
            debug("系统通知已发送")
        except Exception as _e:
            debug(f"通知发送失败: {_e}")

    finally:
        if hdc_mem:
            if old_bmp:
                gdi32.SelectObject(hdc_mem, old_bmp)
            gdi32.DeleteDC(hdc_mem)
        if hbmp:
            gdi32.DeleteObject(hbmp)
        if hdc_screen:
            user32.ReleaseDC(0, hdc_screen)
        debug("截图流程结束，GDI 资源已释放")


# ---- GDI 辅助结构 ----

class BITMAPINFOHEADER(ctypes.Structure):
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


class BITMAPINFO(ctypes.Structure):
    _fields_ = [
        ("bmiHeader", BITMAPINFOHEADER),
    ]

    def __init__(self, width, height):
        super().__init__()
        self.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        self.bmiHeader.biWidth = width
        self.bmiHeader.biHeight = height
        self.bmiHeader.biPlanes = 1
        self.bmiHeader.biBitCount = 24
