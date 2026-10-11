# src/core/__init__.py
# 核心层统一导出
from src.core.paths import (
    ensure_dirs, find_oseasy_dir, resolve_target,
    data_root, config_file, log_dir, backup_dir,
)
from src.core.fingerprint import md5_of, size_of, describe
from src.core.patch_engine import (
    PatchPoint, PatchTarget, PatchEngine,
    ST_NONE, ST_DONE, ST_BAD, ST_SKIP,
)