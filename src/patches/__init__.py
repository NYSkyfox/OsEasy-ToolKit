# src/patches/__init__.py
# patch 目标注册表 —— 全部纯 patch 点配置（无执行逻辑），按驱动引擎分两组
#
# 本包平级存放 6 个配置文件，分属两套 patch 机制（仅执行引擎不同，配置形态一致）：
#   - 固定偏移型  → core.patch_engine.PatchEngine    （key: multiclient_* / screenrender_windowed）
#   - VA 型       → core.va_patch.VAPatchExecutor    （key: duo_open / screen_capture / noshutdown）
#
# 新增一个 patch 工具：
#   1. 在 src/patches/<key>.py 里定义目标（PatchTarget 或 VA_PatchTarget）
#   2. 按机制 import 并加入 ALL_TARGETS（固定偏移）或 VA_TARGETS（VA 型）
#   3. GUI 的 Patch 页下拉框会自动发现并渲染
#
# 注意：
#   - multiclient_disable_behaviorcontrol 与 multiclient_disable_screenrender
#     作用于同一个 MultiClient.exe（共享文件级备份），但作为两个独立目标
#     便于分开启用 / 还原。

# ── 固定偏移型（PatchEngine 驱动） ──────────────────────
from src.patches.multiclient_disable_behaviorcontrol import TARGET as MULTICLIENT_BEHAVIORCONTROL
from src.patches.multiclient_disable_screenrender import TARGET as MULTICLIENT_SCREENRENDER
from src.patches.screenrender_windowed import TARGET as SCREENRENDER_WINDOWED

ALL_TARGETS = [
    MULTICLIENT_BEHAVIORCONTROL,
    MULTICLIENT_SCREENRENDER,
    SCREENRENDER_WINDOWED,
]
_TARGET_MAP = {t.key: t for t in ALL_TARGETS}


def get_target(key: str):
    return _TARGET_MAP.get(key)


def target_keys() -> list:
    return list(_TARGET_MAP.keys())


# ── VA 型（VAPatchExecutor 驱动） ──────────────────────
from src.patches.duo_open import TARGET as DUO_OPEN
from src.patches.screen_capture import TARGET as SCREEN_CAPTURE
from src.patches.noshutdown import TARGET as NOSHUTDOWN

VA_TARGETS = [
    DUO_OPEN,
    SCREEN_CAPTURE,
    NOSHUTDOWN,
]
_VA_TARGET_MAP = {t.key: t for t in VA_TARGETS}


def get_va_target(key: str):
    return _VA_TARGET_MAP.get(key)


def va_target_keys() -> list:
    return list(_VA_TARGET_MAP.keys())