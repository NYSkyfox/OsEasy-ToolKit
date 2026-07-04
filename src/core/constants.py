# src/core/constants.py
# 全局常量与状态

import os
from config import BACKUP_PATH, CMD_FILE_PATH_TEMPLATE


cmd_file_path = CMD_FILE_PATH_TEMPLATE.format(username=os.environ.get('USERNAME'))

# 创建脚本目录和备份目录
try:
    os.makedirs(cmd_file_path, mode=0o777, exist_ok=True)
    os.makedirs(BACKUP_PATH, mode=0o777, exist_ok=True)
except PermissionError:
    raise Exception("权限不足: 请右键使用管理员身份运行")

# 运行时状态标志
is_box_killer_running = False
is_protect_killer_script_running = False