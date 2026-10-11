# src/core/paths.py
# 路径与安装目录探测 —— 纯计算，零副作用
#
# 职责：
#   1. 定位 Os-Easy 学生端安装目录（按候选顺序探测）
#   2. 解析各目标组件的可执行文件路径
#   3. 计算并创建 ManagerHelper 自身的数据目录（备份/日志/配置）

import os
from typing import Optional

from config import (
    DATA_ROOT_TEMPLATE, CONFIG_FILE_TEMPLATE,
    LOG_DIR_TEMPLATE, BACKUP_DIR_TEMPLATE,
    OSEASY_INSTALL_CANDIDATES,
)

_username = os.environ.get("USERNAME") or "Default"

# ── ManagerHelper 自身数据目录 ────────────────────────────
data_root = DATA_ROOT_TEMPLATE.format(username=_username)
config_file = CONFIG_FILE_TEMPLATE.format(username=_username)
log_dir = LOG_DIR_TEMPLATE.format(username=_username)
backup_dir = BACKUP_DIR_TEMPLATE.format(username=_username)

# ── Os-Easy 安装目录（探测结果缓存） ──────────────────────
_oseasy_dir_cache = None


def ensure_dirs() -> None:
    """创建 ManagerHelper 自身数据目录（应在入口显式调用）。"""
    for p in (data_root, log_dir, backup_dir):
        os.makedirs(p, mode=0o777, exist_ok=True)


def find_oseasy_dir() -> Optional[str]:
    """按候选顺序探测 Os-Easy 安装目录，命中返回路径，否则 None。

    命中判定：目录下存在任一标志性组件 exe。
    """
    global _oseasy_dir_cache
    if _oseasy_dir_cache:
        return _oseasy_dir_cache
    markers = ("MultiClient.exe", "ScreenRender.exe", "Student.exe",
               "Teacher.exe", "StudentLogic.dll")
    for d in OSEASY_INSTALL_CANDIDATES:
        if not os.path.isdir(d):
            continue
        for m in markers:
            if os.path.isfile(os.path.join(d, m)):
                _oseasy_dir_cache = d
                return d
    return None


def resolve_target(name: str, explicit_dir: Optional[str] = None) -> Optional[str]:
    """解析某个组件的可执行文件绝对路径。

    :param name: 组件文件名（如 MultiClient.exe）
    :param explicit_dir: 若提供且有效则优先在其下查找
    :return: 绝对路径；找不到返回 None
    """
    dirs = []
    if explicit_dir and os.path.isdir(explicit_dir):
        dirs.append(explicit_dir)
    d = find_oseasy_dir()
    if d and d not in dirs:
        dirs.append(d)
    dirs.extend(OSEASY_INSTALL_CANDIDATES)

    for d in dirs:
        p = os.path.join(d, name)
        if os.path.isfile(p):
            return p
    return None
