# src/modules/patches/__init__.py
# VA 型 patch 目标注册表 —— 纯配置数据（无执行逻辑）
#
# 每个文件定义一个 VA_PatchTarget（含 files / patch_points）。
# 执行逻辑统一在 src/core/va_patch.py 的 VAPatchExecutor。
#
# 新增一个 VA 型 patch 工具时：
#   1. 在 src/modules/patches/<key>.py 里定义一个 VA_PatchTarget
#   2. 在下方 import 并加入 ALL_TARGETS
#   3. GUI 页面 / CLI 通过 get_va_target(key) 获取配置后交给执行器
#
# 注意：src/patches/（固定偏移型，PatchEngine 驱动）与本目录（VA 型）是两套机制，
#       本目录的目标不纳入 src/patches/ 注册表。

from src.modules.patches.duo_open import TARGET as DUO_OPEN
from src.modules.patches.screen_capture import TARGET as SCREEN_CAPTURE
from src.modules.patches.noshutdown import TARGET as NOSHUTDOWN

ALL_TARGETS = [
    DUO_OPEN,
    SCREEN_CAPTURE,
    NOSHUTDOWN,
]

_TARGET_MAP = {t.key: t for t in ALL_TARGETS}


def get_va_target(key: str):
    return _TARGET_MAP.get(key)


def va_target_keys():
    return list(_TARGET_MAP.keys())