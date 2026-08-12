# src/modules/file_handler.py
# 文件备份/恢复 —— 统一清单，备份即恢复

import os
import time

from src.core.runtime_config import toolkit_cfg
from src.core.helpers import file_exists, run_sigle_cmd
from src.core.constants import backup_path, cmd_file_path
from config import BACKUP_FILES


def backup_oe_files(skip_existing: bool = True) -> int:
    """增量备份关键文件到 backup_path

    优先使用动态检测到的学生端路径，若该路径下无任何待备份文件，
    则回退到默认安装路径。

    Args:
        skip_existing: True=已存在则跳过（增量），False=强制覆盖

    Returns:
        本次实际备份的文件数
    """
    from src.utils.system.logger import info, warn
    from config import DEFAULT_OSEASY_PATH

    def _do_backup(source_dir: str) -> tuple[int, int]:
        backed = 0
        skipped = 0
        for name in BACKUP_FILES:
            src = os.path.join(source_dir, name)
            dst = os.path.join(backup_path, name)
            if not file_exists(src):
                continue
            if skip_existing and file_exists(dst):
                skipped += 1
                continue
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            run_sigle_cmd(f'copy "{src}" "{dst}"')
            backed += 1
        return backed, skipped

    source = toolkit_cfg.oseasy_path
    backed, skipped = _do_backup(source)

    # 动态路径下没找到任何文件 → 回退到默认路径
    if backed == 0 and source != DEFAULT_OSEASY_PATH:
        warn(f"动态路径未找到可备份文件 ({source})，回退到默认路径")
        backed, skipped = _do_backup(DEFAULT_OSEASY_PATH)

    if backed > 0:
        info(f"备份 {backed} 个文件" + (f"，跳过 {skipped} 个已有" if skipped else ""))
    else:
        info(f"备份已完整，跳过 {skipped} 个文件")
    return backed


def restore_oe_file(filename: str) -> None:
    """从备份恢复单个 OE 文件到原路径"""
    src = os.path.join(backup_path, filename)
    dst = os.path.join(toolkit_cfg.oseasy_path, filename)
    run_sigle_cmd(f'copy "{src}" "{dst}"')


def restore_oe_key_dlls() -> None:
    """批量恢复全部关键文件到 OE 目录"""
    from src.core.helpers import show_snack
    from src.utils.system.logger import info

    info("恢复关键文件...")
    failed = []
    for name in BACKUP_FILES:
        src = os.path.join(backup_path, name)
        dst = os.path.join(toolkit_cfg.oseasy_path, name)
        if file_exists(src):
            run_sigle_cmd(f'copy "{src}" "{dst}"')
        else:
            failed.append(name)

    time.sleep(2)
    for name in BACKUP_FILES:
        dst = os.path.join(toolkit_cfg.oseasy_path, name)
        if not file_exists(dst):
            failed.append(f"{name} (恢复失败，请先停止相关服务再试)")

    if failed:
        show_snack(f"部分文件恢复失败:\n{', '.join(failed)}")
    else:
        show_snack("全部关键文件恢复完成")


def del_self_cmd_files() -> None:
    """删除 scripts 文件夹下的所有文件"""
    for filename in os.listdir(cmd_file_path):
        filepath = os.path.join(cmd_file_path, filename)
        try:
            if os.path.isfile(filepath):
                os.remove(filepath)
        except OSError:
            continue