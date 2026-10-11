# src/patches/multiclient_disable.py
# 禁用教学管控 —— MultiClient.exe 固定偏移 patch 目标定义
#
# 逆向结论（见 docs/patches/）：
#   三个功能指令入口各只有一个函数，入口均为 MSVC SEH 序言 55 8b ec。
#   patch 为 31 c0 c3 (xor eax,eax; ret) 即让函数直接返回。
#
#   屏幕广播  FUN_0042f970 @ 0x42f970  off 0x2ED70   （可选：窗口化时不封）
#   键鼠锁    FUN_0041ae10 @ 0x41ae10  off 0x1A210   （解析 lock 字段 JSON）
#   行为管控  FUN_004197a0 @ 0x4197a0  off 0x18BA0   （→127.0.0.1 转发）

from src.core.patch_engine import PatchTarget, PatchPoint

SAMPLE_NAME = "MultiClient.exe"
SAMPLE_MD5 = "b8bb9b809e8f45918f6759d4cb51f5b0"
SAMPLE_SIZE = 1189376

_NOP = bytes.fromhex("31c0c3")      # xor eax,eax; ret
_PROLOGUE = bytes.fromhex("558bec")  # push ebp; mov ebp,esp

TARGET = PatchTarget(
    key="multiclient_disable",
    name="禁用教学管控",
    sample_name=SAMPLE_NAME,
    md5=SAMPLE_MD5,
    size=SAMPLE_SIZE,
    description=(
        "patch MultiClient.exe，使教师端下发的 键鼠锁 / 行为管控（网络·USB·程序）"
        "指令在学生机失效。屏幕广播点默认启用，取消勾选则保留广播（配合窗口化使用）。"
    ),
    patches=[
        PatchPoint(
            label="屏幕广播入口", offset=0x2ED70,
            orig=_PROLOGUE, new=_NOP,
            required=False, toggle_key="screen",
        ),
        PatchPoint(
            label="键鼠锁指令", offset=0x1A210,
            orig=_PROLOGUE, new=_NOP,
            required=True,
        ),
        PatchPoint(
            label="行为管控转发", offset=0x18BA0,
            orig=_PROLOGUE, new=_NOP,
            required=True,
        ),
    ],
)