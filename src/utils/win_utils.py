# src/utils/win_utils.py
# Windows 系统工具函数

from config import DEFAULT_ACCENT_COLOR, DEFAULT_FONT_PATH


def get_windows_accent_color() -> str:
    """读取 Windows 系统主题色，失败则返回默认墨绿色"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\DWM"
        )
        accent_raw, _ = winreg.QueryValueEx(key, "AccentColor")
        winreg.CloseKey(key)
        # AccentColor 格式为 0xAABBGGRR（ABGR），跳过 alpha 取后三字节
        if isinstance(accent_raw, int):
            b = (accent_raw >> 16) & 0xFF
            g = (accent_raw >> 8) & 0xFF
            r = accent_raw & 0xFF
            return f"#{r:02X}{g:02X}{b:02X}"
    except Exception:
        pass
    return DEFAULT_ACCENT_COLOR


def get_windows_default_font() -> str:
    """读取 Windows 系统默认字体，失败则返回 Deng.ttf"""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"Software\Microsoft\Windows NT\CurrentVersion\Fonts"
        )
        # 尝试读取 Segoe UI (Win10/11 默认)
        import ctypes
        # 方式一：读取注册表中已安装字体的路径
        # "Segoe UI (TrueType)" 或 "Microsoft Sans Serif (TrueType)"
        font_names = [
            "Segoe UI (TrueType)",
            "Microsoft Sans Serif (TrueType)",
            "Tahoma (TrueType)",
        ]
        for font_name in font_names:
            try:
                font_file, _ = winreg.QueryValueEx(key, font_name)
                winreg.CloseKey(key)
                if font_file:
                    return f"C:\\Windows\\Fonts\\{font_file}"
            except FileNotFoundError:
                continue
        winreg.CloseKey(key)
    except Exception:
        pass
    return DEFAULT_FONT_PATH