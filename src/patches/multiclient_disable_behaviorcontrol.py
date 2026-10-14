# src/patches/multiclient_disable_behaviorcontrol.py
# 禁用行为管控 —— MultiClient.exe 固定偏移 patch 目标定义
#
# 逆向结论（见 docs/patches/）：
#   行为管控 只有一个函数入口，入口均为 MSVC SEH 序言 55 8b ec。
#   patch 为 31 c0 c3 (xor eax,eax; ret) 即让函数直接返回。
#
#   本目标封「行为管控」点（网络·USB·程序 管控 → 127.0.0.1 转发）。
#   屏幕广播 / 键鼠锁 独立为 multiclient_disable_screenrender（同一 MultiClient.exe，
#   共享文件级备份）。
#
#   行为管控   FUN_004197a0 @ 0x4197a0  off 0x18BA0  （→127.0.0.1 转发）

from src.core.patch_engine import PatchTarget, PatchPoint

SAMPLE_NAME = "MultiClient.exe"
SAMPLE_MD5 = "b8bb9b809e8f45918f6759d4cb51f5b0"
SAMPLE_SIZE = 1189376

_NOP = bytes.fromhex("31c0c3")      # xor eax,eax; ret
_PROLOGUE = bytes.fromhex("558bec")  # push ebp; mov ebp,esp

TARGET = PatchTarget(
    key="multiclient_disable_behaviorcontrol",
    name="禁用行为管控",
    sample_name=SAMPLE_NAME,
    md5=SAMPLE_MD5,
    size=SAMPLE_SIZE,
    description=(
        "patch MultiClient.exe 的行为管控（网络·USB·程序）指令入口，"
        "使教师端下发的行为管控指令在学生机失效。屏幕广播 / 键鼠锁保留"
        "（见「禁用屏幕广播」）。"
    ),
    patches=[
        PatchPoint(
            label="行为管控转发", offset=0x18BA0,
            orig=_PROLOGUE, new=_NOP, required=True,
        ),
    ],
)