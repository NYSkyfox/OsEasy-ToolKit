# src/gui/pages/patch_panels/__init__.py
# 统一 Patch 页的目标注册表 —— 把两套 patch 机制合并为一个可遍历列表
#
# 每条目：key / kind("fixed"|"va") / target / label(下拉显示名) / factory
#   factory(ui, detail, log_text) -> 面板实例（须暴露 buttons() 与可选 _refresh()）
#
# 新增 patch 目标：
#   - 固定偏移型：在 src/patches/ 注册，本表自动经 _fixed_entries 发现
#   - VA 型     ：在 src/modules/patches/ 注册，本表自动经 _va_entries 发现
# 无需改 GUI 框架，下拉框会自动出现新目标。

from src.patches import ALL_TARGETS as _FIXED_TARGETS
from src.modules.patches import ALL_TARGETS as _VA_TARGETS

from src.gui.pages.patch_panels.fixed_panel import FixedPanel
from src.gui.pages.patch_panels.duo_panel import DuoPanel
from src.gui.pages.patch_panels.capture_panel import CapturePanel
from src.gui.pages.patch_panels.noshutdown_panel import NoshutdownPanel


def _fixed_entries():
    out = []
    for t in _FIXED_TARGETS:
        out.append({
            "key": "fixed:" + t.key,
            "kind": "fixed",
            "target": t,
            "label": t.name,
            "factory": lambda ui, d, lg, t=t: FixedPanel(ui, d, lg, t),
        })
    return out


def _va_entries():
    # VA 型目标的面板工厂按 key 映射
    factories = {
        "duo_open": DuoPanel,
        "screen_capture": CapturePanel,
        "noshutdown": NoshutdownPanel,
    }
    out = []
    for t in _VA_TARGETS:
        cls = factories.get(t.key)
        if cls is None:
            continue
        out.append({
            "key": "va:" + t.key,
            "kind": "va",
            "target": t,
            "label": t.name,
            "factory": lambda ui, d, lg, c=cls: c(ui, d, lg),
        })
    return out


REGISTRY = _fixed_entries() + _va_entries()

# 便于主页快捷入口按 key 跳转
KEY_INDEX = {e["key"]: i for i, e in enumerate(REGISTRY)}