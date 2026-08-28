# src/utils/toast.py
# Windows Toast 通知的统一入口

import os

from src.utils.display import resource_path

_APP_ID = "OsEasy-ToolKit"
_toaster = None


def _get_toaster():
    global _toaster
    if _toaster is None:
        from windows_toasts import WindowsToaster
        _toaster = WindowsToaster("OsEasy-ToolKit")
    return _toaster

def send_toast(title: str, msg: str, duration: str = "short", launch: str = "") -> bool:
    """发送 Windows Toast 通知。

    :param title: 通知标题
    :param msg: 通知正文
    :param duration: "short" | "long"
    :param launch: 点击通知后打开的 URL（如 file:///C:/pic.png），空串则不响应点击
    """
    try:
        from windows_toasts import Toast, ToastDisplayImage, ToastDuration

        text = [title, msg]
        images = []
        icon_path = resource_path("logo.png")
        if os.path.exists(icon_path):
            images.append(ToastDisplayImage.fromPath(
                icon_path,
                altText="OsEasy-ToolKit",
            ))

        toast = Toast(text_fields=text, images=images)
        if duration == "long":
            toast.duration = ToastDuration.Long
        elif duration == "short":
            toast.duration = ToastDuration.Short
        if launch:
            toast.launch_action = launch
        _get_toaster().show_toast(toast)
        return True
    except Exception:
        return False