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
    """读取 Windows 系统已安装的可用中文字体，失败则返回 msyh.ttc"""
    # 按优先级尝试：微软雅黑（最可靠）→ 等线体 → 回退
    font_candidates = [
        r"C:\Windows\Fonts\msyh.ttc",       # 微软雅黑（Win7+ 全系预装）
        r"C:\Windows\Fonts\msyhbd.ttc",     # 微软雅黑粗体
        r"C:\Windows\Fonts\Deng.ttf",       # 等线体
        r"C:\Windows\Fonts\simsun.ttc",     # 宋体
        r"C:\Windows\Fonts\segoeui.ttf",    # Segoe UI
        r"C:\Windows\Fonts\seguisb.ttf",    # Segoe UI Semibold
        r"C:\Windows\Fonts\tahoma.ttf",     # Tahoma
    ]
    import os
    for fp in font_candidates:
        if os.path.isfile(fp):
            return fp
    return DEFAULT_FONT_PATH