# src/utils/__init__.py
# 通用工具函数 — 兼容 re-export（实际实现已拆分到子目录）

from src.utils.system.cmd import run_sigle_cmd, use_bat_file_to_run_cmd, runbat
from src.utils.system.info import get_time_str, file_exists
from src.utils.web.network import get_ipv4_address, open_github_page
from src.utils.program.config_tools import del_historyrem