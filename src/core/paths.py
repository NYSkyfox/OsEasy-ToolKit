# src/core/paths.py
# 路径常量 —— 纯计算，零副作用

import os
from config import (
    BACKUP_PATH_TEMPLATE, CMD_FILE_PATH_TEMPLATE,
    LOG_DIR_TEMPLATE, SCREENSHOT_PATH_TEMPLATE,
)

_username = os.environ.get('USERNAME') or 'Default'

cmd_file_path = CMD_FILE_PATH_TEMPLATE.format(username=_username)
backup_path = BACKUP_PATH_TEMPLATE.format(username=_username)
log_dir_path = LOG_DIR_TEMPLATE.format(username=_username)
screenshot_path = SCREENSHOT_PATH_TEMPLATE.format(username=_username)


def ensure_dirs() -> None:
    """创建所有需要的目录（应在 main.py 中显式调用）"""
    for p in (cmd_file_path, backup_path, log_dir_path, screenshot_path):
        os.makedirs(p, mode=0o777, exist_ok=True)