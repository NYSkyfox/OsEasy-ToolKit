# src/modules/script_generator.py
# 脚本生成器 —— 击杀/删文件/学生端安装测试脚本

from config import KILLER_BAT, KILLER_ALL_BAT, FILE_DEL_BAT, INSTALL_STUDENT_TEST_BAT, UNINSTALL_STUDENT_TEST_BAT
from src.core.constants import cmd_file_path
from src.core.settings import toolkit_cfg
from src.modules.script_templates import (
    tpl_process_killer_student, tpl_process_killer_all, tpl_files_delete,
    tpl_install_student_test, tpl_uninstall_student_test,
)


# ══════════════════════════════════════════════════════════
# 辅助
# ══════════════════════════════════════════════════════════

def _write(filename: str, content: str) -> None:
    path = cmd_file_path + "\\" + filename
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ══════════════════════════════════════════════════════════
# 对外接口
# ══════════════════════════════════════════════════════════

from src.utils.cmd import run_sigle_cmd, runbat
from src.modules.service_manager import stop_service, delete_service
from src.utils.process import kill_process


class script_gen:

    # ── 击杀脚本 ──

    @staticmethod
    def summon_killer() -> None:
        _write(KILLER_BAT, tpl_process_killer_student())

    @staticmethod
    def summon_killer_v2() -> None:
        _write(KILLER_ALL_BAT, tpl_process_killer_all())

    # ── 删文件 ──

    @staticmethod
    def summon_del_dll(delMtc: bool, shutdown: bool) -> None:
        from src.modules.file_handler import backup_oe_files
        backup_oe_files()
        _write(FILE_DEL_BAT, tpl_files_delete(delMtc, shutdown))

    # ── 学生端安装测试 ──

    @staticmethod
    def summon_install_student_test(base: str | None = None) -> str:
        """生成学生端轻量安装测试脚本到 scripts/ 目录。

        :param base: 学生端套件目录（含 MMPC.exe/DriverInstall.exe 等）；
                     默认取 toolkit_cfg.oseasy_path
        :return: 生成的 bat 完整路径
        """
        if not base:
            base = toolkit_cfg.oseasy_path
        base = base.rstrip("\\/") + "\\"
        _write(INSTALL_STUDENT_TEST_BAT, tpl_install_student_test(base))
        return cmd_file_path + "\\" + INSTALL_STUDENT_TEST_BAT

    @staticmethod
    def run_install_student_test(on_output=None) -> str:
        """生成并运行学生端安装测试脚本，返回 bat 路径。

        脚本需要管理员权限；工具箱本身提权运行，直接静默执行。
        """
        path = script_gen.summon_install_student_test()
        runbat(INSTALL_STUDENT_TEST_BAT, on_output=on_output)
        return path

    # ── 学生端卸载测试 ──

    @staticmethod
    def summon_uninstall_student_test(base: str | None = None) -> str:
        """生成学生端卸载测试脚本到 scripts/ 目录。

        :param base: 学生端套件目录（含 DriverInstall.exe）；
                     默认取 toolkit_cfg.oseasy_path
        :return: 生成的 bat 完整路径
        """
        if not base:
            base = toolkit_cfg.oseasy_path
        base = base.rstrip("\\/") + "\\"
        _write(UNINSTALL_STUDENT_TEST_BAT, tpl_uninstall_student_test(base))
        return cmd_file_path + "\\" + UNINSTALL_STUDENT_TEST_BAT

    @staticmethod
    def run_uninstall_student_test(on_output=None) -> str:
        """生成并运行学生端卸载测试脚本，返回 bat 路径。"""
        path = script_gen.summon_uninstall_student_test()
        runbat(UNINSTALL_STUDENT_TEST_BAT, on_output=on_output)
        return path
