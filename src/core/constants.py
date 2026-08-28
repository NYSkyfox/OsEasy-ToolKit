# src/core/constants.py
# 向后兼容 re-export（已拆分至 paths.py + state.py）

from src.core.paths import cmd_file_path, backup_path, log_dir_path, screenshot_path, ensure_dirs
from src.core.state import is_kit_killer_running, is_protect_killer_script_running