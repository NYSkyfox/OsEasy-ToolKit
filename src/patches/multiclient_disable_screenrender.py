# src/patches/multiclient_disable_screenrender.py
# 禁用屏幕广播（含可选键鼠锁） —— MultiClient.exe 固定偏移 patch 目标定义
#
# 逆向结论（见 docs/patches/）：
#   屏幕广播入口 FUN_0042f970 @ off 0x2ED70，MSVC SEH 序言 55 8b ec → 31 c0 c3。
#   键鼠锁       FUN_0041ae10 @ off 0x1A210，解析 lock 字段 JSON → 31 c0 c3。
#
#   屏幕广播为必选点；键鼠锁作为可勾选的附加选项（默认勾选），
#   勾选后一并封禁教师端下发的键鼠锁指令。
#   独立成一个目标，便于与「禁用行为管控」分开启用 / 还原
#   （同一 MultiClient.exe，共享文件级备份：还原本目标会恢复整个 MultiClient.exe）。
#
#   屏幕广播入口 FUN_0042f970 @ 0x42f970  off 0x2ED70
#   键鼠锁指令   FUN_0041ae10 @ 0x41ae10  off 0x1A210

from src.core.patch_engine import PatchTarget, PatchPoint

SAMPLE_NAME = "MultiClient.exe"
SAMPLE_MD5 = "b8bb9b809e8f45918f6759d4cb51f5b0"
SAMPLE_SIZE = 1189376

_NOP = bytes.fromhex("31c0c3")      # xor eax,eax; ret
_PROLOGUE = bytes.fromhex("558bec")  # push ebp; mov ebp,esp

TARGET = PatchTarget(
    key="multiclient_disable_screenrender",
    name="禁用屏幕广播",
    sample_name=SAMPLE_NAME,
    md5=SAMPLE_MD5,
    size=SAMPLE_SIZE,
    description=(
        "patch MultiClient.exe 的屏幕广播入口，使教师端屏幕广播指令失效"
        "（画面不再被截取 / 广播）。可勾选一并封禁键鼠锁。"
        "行为管控保留（见「禁用行为管控」）。"
    ),
    patches=[
        PatchPoint(
            label="屏幕广播入口", offset=0x2ED70,
            orig=_PROLOGUE, new=_NOP, required=True,
        ),
        PatchPoint(
            label="键鼠锁指令", offset=0x1A210,
            orig=_PROLOGUE, new=_NOP, required=False,
            toggle_key="keyboard",   # 可勾选选项，默认启用
        ),
    ],
)