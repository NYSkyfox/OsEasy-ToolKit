# src/patches/__init__.py
# patch 目标注册表 —— 固定偏移 patch（引擎驱动）
#
# 新增一个固定偏移 patch 工具时：
#   1. 在 src/patches/<key>.py 里定义一个 PatchTarget（含 patches 列表）
#   2. 在下方 import 并加入 ALL_TARGETS
#   3. GUI 的 Patch 页下拉框会自动发现并渲染
#
# 注意：
#   - duo_open / screen_capture / noshutdown 属“PE+VA+shellcode”型，放在
#     src/modules/patches/ 单独维护，不纳入本注册表。
#   - multiclient_disable_behaviorcontrol 与 multiclient_disable_screenrender
#     作用于同一个 MultiClient.exe（共享文件级备份），但作为两个独立目标
#     便于分开启用 / 还原。

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