# src/gui/pages/patch_panels/__init__.py
# 统一 Patch 页的下拉项注册表 —— 一个下拉项 = 一个面板文件
#
# 每条目：
#   id       下拉项唯一标识（= 面板文件名，供 goto_patch/select_key 跳转）
#   label    下拉显示名（中文）
#   kind     "fixed"（PatchEngine 驱动）/ "va"（VAPatchExecutor 驱动）
#   target   对应配置 target（供 overview 状态区 / 显示用）
#   factory  (ui, detail, log_text) -> 面板实例（须暴露 buttons() 与可选 _refresh()）
#
# 面板契约：__init__(ui, detail, log_text)，把控件 build 进 detail，日志写 log_text，
#           并提供 buttons() 返回 [(text, command)]。
#
# 新增 patch 目标：建一个面板文件 + 在此登记一条，下拉框自动出现，无需改框架。
#   - 固定偏移型：面板驱动 src/patches/<key>.py 的 PatchTarget
#   - VA 型     ：面板驱动 src/patches/<key>.py 的 VA_PatchTarget

from src.patches import get_target
from src.patches import get_va_target

from src.gui.pages.patch_panels.multiclient_disable_behaviorcontrol import MulticlientDisableBehaviorcontrol
from src.gui.pages.patch_panels.multiclient_disable_screenrender import MulticlientDisableScreenrender
from src.gui.pages.patch_panels.screenrender_windowed import ScreenrenderWindowed
from src.gui.pages.patch_panels.teacher_student_double_open import TeacherStudentDoubleOpen
from src.gui.pages.patch_panels.student_fake_screenshot import StudentFakeScreenshot
from src.gui.pages.patch_panels.fake_shutdown import FakeShutdown

REGISTRY = [
    {
        "id": "multiclient_disable_behaviorcontrol",
        "label": "禁用行为管控",
        "kind": "fixed",
        "target": get_target("multiclient_disable_behaviorcontrol"),
        "factory": lambda ui, d, lg: MulticlientDisableBehaviorcontrol(ui, d, lg),
    },
    {
        "id": "multiclient_disable_screenrender",
        "label": "禁用屏幕广播（含可选键鼠锁）",
        "kind": "fixed",
        "target": get_target("multiclient_disable_screenrender"),
        "factory": lambda ui, d, lg: MulticlientDisableScreenrender(ui, d, lg),
    },
    {
        "id": "screenrender_windowed",
        "label": "屏幕广播窗口化",
        "kind": "fixed",
        "target": get_target("screenrender_windowed"),
        "factory": lambda ui, d, lg: ScreenrenderWindowed(ui, d, lg),
    },
    {
        "id": "teacher_student_double_open",
        "label": "双开教师端 / 学生端",
        "kind": "va",
        "target": get_va_target("duo_open"),
        "factory": lambda ui, d, lg: TeacherStudentDoubleOpen(ui, d, lg),
    },
    {
        "id": "student_fake_screenshot",
        "label": "阻止 / 使用假屏幕截图",
        "kind": "va",
        "target": get_va_target("screen_capture"),
        "factory": lambda ui, d, lg: StudentFakeScreenshot(ui, d, lg),
    },
    {
        "id": "fake_shutdown",
        "label": "拦截远程关机 / 重启",
        "kind": "va",
        "target": get_va_target("noshutdown"),
        "factory": lambda ui, d, lg: FakeShutdown(ui, d, lg),
    },
]

# 便于按 id 跳转
KEY_INDEX = {e["id"]: i for i, e in enumerate(REGISTRY)}