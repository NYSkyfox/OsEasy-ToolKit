# src/modules/file_handler.py
# 文件备份/恢复 —— 统一清单，备份即恢复

import os
import time
import shutil

from src.core.settings import toolkit_cfg
from src.utils.cmd import run_sigle_cmd
from src.utils.fs import file_exists
from src.core.constants import backup_path, cmd_file_path
from config import BACKUP_FILES


def _copy_file(src: str, dst: str, overwrite: bool = True) -> str:
    """用 Python shutil 复制文件，返回结果状态字符串（捕获各类错误）。

    返回:
      "ok"           复制成功（dst 已存在时表示覆盖成功）
      "src_missing"  源文件不存在
      "dst_exists"   目标已存在且不覆盖
      "denied"       权限/访问被拒绝
      "error:xxx"    其他错误
    """
    if not file_exists(src):
        return "src_missing"
    if not overwrite and file_exists(dst):
        return "dst_exists"
    try:
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        return "ok"
    except PermissionError:
        return "denied"
    except OSError as e:
        return f"error:{e}"


def backup_oe_files(skip_existing: bool = True) -> dict:
    """增量备份关键文件到 backup_path

    优先使用动态检测到的学生端路径，若该路径下无任何待备份文件，
    则回退到默认安装路径。

    Args:
        skip_existing: True=已存在则跳过（增量），False=强制覆盖

    Returns:
        分类统计字典:
        {"backed": 新备份数, "skipped": 已有备份跳过的数,
         "missing": 源文件不存在的数, "failed": 失败数}
    """
    from src.utils.logger import info, warn
    from config import DEFAULT_OSEASY_PATH

    def _do_backup(source_dir: str) -> dict:
        stats = {"backed": 0, "skipped": 0, "missing": 0, "failed": 0}
        for name in BACKUP_FILES:
            src = os.path.join(source_dir, name)
            dst = os.path.join(backup_path, name)
            status = _copy_file(src, dst, overwrite=not skip_existing)
            if status == "ok":
                stats["backed"] += 1
            elif status == "dst_exists":
                stats["skipped"] += 1
            elif status == "src_missing":
                stats["missing"] += 1
            else:
                stats["failed"] += 1
                warn(f"备份失败 [{name}]: {status}")
        return stats

    source = toolkit_cfg.oseasy_path
    stats = _do_backup(source)

    # 动态路径下没找到任何文件 → 回退到默认路径
    if stats["backed"] == 0 and source != DEFAULT_OSEASY_PATH:
        warn(f"动态路径未找到可备份文件 ({source})，回退到默认路径")
        stats = _do_backup(DEFAULT_OSEASY_PATH)

    if stats["backed"] > 0:
        info(f"备份 {stats['backed']} 个文件")
    else:
        info("备份已完整（全部已有备份或源文件不存在）")
    return stats


def backup_oe_file(filename: str) -> str:
    """备份单个 OE 文件到备份目录。

    返回结果状态字符串，供 UI 精确反馈：
      "ok" / "src_missing" / "denied" / "dst_exists" / "error:xxx"
    """
    src = os.path.join(toolkit_cfg.oseasy_path, filename)
    dst = os.path.join(backup_path, filename)
    return _copy_file(src, dst, overwrite=True)


def restore_oe_file(filename: str) -> str:
    """从备份恢复单个 OE 文件到原路径。

    返回结果状态字符串，供 UI 精确反馈：
      "ok" / "src_missing"（无备份） / "denied" / "error:xxx"
    """
    src = os.path.join(backup_path, filename)
    dst = os.path.join(toolkit_cfg.oseasy_path, filename)
    return _copy_file(src, dst, overwrite=True)


def restore_oe_key_dlls() -> None:
    """批量恢复全部关键文件到 OE 目录"""
    from src.core.bridge import show_snack
    from src.utils.logger import info

    info("恢复关键文件...")
    failed = []
    for name in BACKUP_FILES:
        src = os.path.join(backup_path, name)
        dst = os.path.join(toolkit_cfg.oseasy_path, name)
        status = _copy_file(src, dst, overwrite=True)
        if status != "ok":
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