# src/modules/script_generator.py
# 脚本生成器 —— 业务逻辑（模板在 script_templates.py）

from config import (
    KILLER_BAT, KILLER_V2_BAT, HELPER_BAT,
    UNLOCK_NET_BAT, UNLOCK_USB_BAT, UNLOCK_USB_PS1,
    UNLOCK_KB_BAT, UNLOCK_ALL_BAT,
)
from src.core.constants import cmd_file_path
from src.core.runtime_config import toolkit_cfg
from src.modules.script_templates import (
    tpl_unlock_network, tpl_unlock_usb_ps1, tpl_unlock_usb,
    tpl_unlock_keyboard, tpl_unlock_all,
    tpl_process_killer_student, tpl_process_killer_all, tpl_files_delete,
)


# ══════════════════════════════════════════════════════════
# 辅助
# ══════════════════════════════════════════════════════════

def _write(filename: str, content: str) -> None:
    path = cmd_file_path + "\\" + filename
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ══════════════════════════════════════════════════════════
# 对外接口 —— 生成脚本 + 执行 Python 端操作 + 运行批处理
# ══════════════════════════════════════════════════════════

from src.core.helpers import runbat, run_sigle_cmd


class script_gen:

    # ── A. 网络解锁 ──

    @staticmethod
    def summon_unlocknet() -> None:
        _write(UNLOCK_NET_BAT, tpl_unlock_network())

    @staticmethod
    def network_block():
        run_sigle_cmd("sc stop MMPC")
        run_sigle_cmd(f"taskkill /f /t /im {toolkit_cfg.student_exe_name}")
        run_sigle_cmd("taskkill /f /t /im DeviceControl_x64.exe")
        run_sigle_cmd("sc stop OeNetLimit")
        run_sigle_cmd("sc stop ProcFireWall")

    @staticmethod
    def network_unlock():
        script_gen.summon_unlocknet()
        script_gen.network_block()
        runbat(UNLOCK_NET_BAT)

    # ── B. USB 解锁 ──

    @staticmethod
    def summon_unlock_usb() -> None:
        _write(UNLOCK_USB_PS1, tpl_unlock_usb_ps1())
        _write(UNLOCK_USB_BAT, tpl_unlock_usb())

    @staticmethod
    def usb_block():
        run_sigle_cmd("sc stop MMPC")
        run_sigle_cmd(f"taskkill /f /t /im {toolkit_cfg.student_exe_name}")
        run_sigle_cmd("taskkill /f /t /im DeviceControl_x64.exe")
        run_sigle_cmd("sc stop easyusbflt")
        run_sigle_cmd("sc delete easyusbflt")
        run_sigle_cmd(f'del /f /q "{toolkit_cfg.oseasy_path}easyusbflt.sys"')

    @staticmethod
    def usb_unlock():
        script_gen.summon_unlock_usb()
        script_gen.usb_block()
        runbat(UNLOCK_USB_BAT)  # PS 注册表清理 + 注销

    # ── C. 键盘/鼠标解锁 ──

    @staticmethod
    def summon_unlock_kb() -> None:
        _write(UNLOCK_KB_BAT, tpl_unlock_keyboard())

    @staticmethod
    def keyboard_block():
        from src.modules.file_handler import backup_oe_files
        backup_oe_files(skip_existing=True)
        run_sigle_cmd("sc stop MMPC")
        run_sigle_cmd(f"taskkill /f /t /im {toolkit_cfg.student_exe_name}")
        run_sigle_cmd("taskkill /f /t /im BlackSlient.exe")
        run_sigle_cmd("sc stop KbFilter")
        run_sigle_cmd("sc stop ProcFireWall")
        run_sigle_cmd("sc delete KbFilter")
        run_sigle_cmd("sc delete ProcFireWall")
        for f in ("KbFilter.sys", "ProcFireWall.sys", "LockKeyboard.dll", "LoadDriver.exe", "KbDriver.exe"):
            run_sigle_cmd(f'del /f /q "{toolkit_cfg.oseasy_path}{f}"')

    @staticmethod
    def keyboard_unlock():
        script_gen.summon_unlock_kb()
        script_gen.keyboard_block()
        runbat(UNLOCK_KB_BAT)  # PS 注册表清理 + 注销

    # ── D. 控屏解锁 ──

    @staticmethod
    def screen_control_block():
        from src.modules.file_handler import backup_oe_files
        backup_oe_files(skip_existing=True)
        run_sigle_cmd("sc stop MMPC")
        for name in ("ScreenRender.exe", "ScreenRender_Y.exe", "MultiClient.exe"):
            run_sigle_cmd(f"taskkill /f /t /im {name}")
            run_sigle_cmd(f'del /f /q "{toolkit_cfg.oseasy_path}{name}"')

    @staticmethod
    def screen_control_unlock():
        script_gen.screen_control_block()

    # ── E. 黑屏解锁 ──

    @staticmethod
    def black_screen_block():
        from src.modules.file_handler import backup_oe_files
        backup_oe_files(skip_existing=True)
        run_sigle_cmd("sc stop MMPC")
        run_sigle_cmd("taskkill /f /t /im BlackSlient.exe")
        run_sigle_cmd(f'del /f /q "{toolkit_cfg.oseasy_path}BlackSlient.exe"')

    @staticmethod
    def black_screen_unlock():
        script_gen.black_screen_block()

    # ── F. 删文件 ──

    @staticmethod
    def summon_del_dll(delMtc: bool, shutdown: bool) -> None:
        from src.modules.file_handler import backup_oe_files
        backup_oe_files()
        _write(HELPER_BAT, tpl_files_delete(delMtc, shutdown))

    @staticmethod
    def delete_files_block():
        from src.modules.file_handler import backup_oe_files
        backup_oe_files()
        script_gen.summon_del_dll(delMtc=True, shutdown=False)
        runbat(HELPER_BAT)

    @staticmethod
    def delete_files_unlock():
        script_gen.delete_files_block()

    # ── 全部解锁 ──

    @staticmethod
    def summon_unlock_all() -> None:
        script_gen.summon_unlock_usb()
        script_gen.summon_unlock_kb()
        _write(UNLOCK_ALL_BAT, tpl_unlock_all())

    @staticmethod
    def unlock_all():
        script_gen.summon_unlock_all()
        script_gen.network_block()
        script_gen.usb_block()
        script_gen.keyboard_block()
        script_gen.screen_control_block()
        script_gen.black_screen_block()
        from src.modules.file_handler import backup_oe_files
        backup_oe_files()
        import subprocess, os
        batpath = os.path.join(cmd_file_path, UNLOCK_ALL_BAT)
        subprocess.Popen(["cmd.exe", "/c", batpath], creationflags=subprocess.CREATE_NEW_CONSOLE)

    # ── 击杀脚本 ──

    @staticmethod
    def summon_killer_v2() -> None:
        _write(KILLER_V2_BAT, tpl_process_killer_all())

    @staticmethod
    def summon_killer() -> None:
        _write(KILLER_BAT, tpl_process_killer_student())
