# src/modules/script_generator.py
# 脚本生成器 —— 仅保留击杀/删文件脚本（解锁已迁移至 unlock_native.py）

from config import KILLER_BAT, KILLER_ALL_BAT, FILE_DEL_BAT
from src.core.constants import cmd_file_path
from src.core.settings import toolkit_cfg
from src.modules.script_templates import (
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
