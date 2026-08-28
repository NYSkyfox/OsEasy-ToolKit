# src/core/__init__.py
# 核心层统一导出

from src.core.settings import RuntimeConfig, toolkit_cfg
from src.core.bridge import pass_ui_class, show_snack
from src.core.paths import cmd_file_path, backup_path, log_dir_path, screenshot_path, ensure_dirs
from src.core.state import is_kit_killer_running, is_protect_killer_script_running