# src/core/constants.py
# 全局常量与状态

import os
from config import BACKUP_PATH_TEMPLATE, CMD_FILE_PATH_TEMPLATE

_username = os.environ.get('USERNAME') or 'Default'

cmd_file_path = CMD_FILE_PATH_TEMPLATE.format(username=_username)
backup_path = BACKUP_PATH_TEMPLATE.format(username=_username)

# 创建脚本目录和备份目录
try:
    os.makedirs(cmd_file_path, mode=0o777, exist_ok=True)
    os.makedirs(backup_path, mode=0o777, exist_ok=True)
except PermissionError:
    raise Exception("权限不足: 请右键使用管理员身份运行")
except (FileNotFoundError, OSError):
    # 若父目录不存在导致失败，确保父目录存在后重试
    for p in (cmd_file_path, backup_path):
        parent = os.path.dirname(p)
        if parent and not os.path.exists(parent):
            os.makedirs(parent, mode=0o777, exist_ok=True)
        os.makedirs(p, mode=0o777, exist_ok=True)

# 运行时状态标志
is_box_killer_running = False
is_protect_killer_script_running = False