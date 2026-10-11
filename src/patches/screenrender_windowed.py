# src/patches/screenrender_windowed.py
# 屏幕广播窗口化 —— ScreenRender.exe 固定偏移 patch 目标定义
#
# 逆向结论（见 docs/patches/）：
#   ScreenRenderApp 构造函数 FUN_0041c7d0 把 --fullscreen 参数值存入 this+0x844。
#   off 0x1BDA6 处 "mov eax,[ebp+0x58]" 读取参数值，紧随 off 0x1BDA9 的
#   "mov [edx+0x844],eax" 写入。patch 读取指令为 "xor eax,eax; nop" 强制 0（窗口）。
#
#   this+0x844: 1=全屏(WS_POPUP) / 0=窗口 / 2=窗口缩放
#   窗口化尺寸 = 屏宽 * 3/4

from src.core.patch_engine import PatchTarget, PatchPoint

SAMPLE_NAME = "ScreenRender.exe"
SAMPLE_MD5 = "76cfa20119b247685827d9341132570a"
SAMPLE_SIZE = 450048

TARGET = PatchTarget(
    key="screenrender_windowed",
    name="屏幕广播窗口化",
    sample_name=SAMPLE_NAME,
    md5=SAMPLE_MD5,
    size=SAMPLE_SIZE,
    description=(
        "patch ScreenRender.exe，强制 --fullscreen=0，使教师端屏幕广播始终以"
        "可拖拽/可缩放的窗口启动，而非默认全屏。广播功能保留、画面照常显示。"
    ),
    patches=[
        PatchPoint(
            label="fullscreen 赋值", offset=0x1BDA6,
            orig=bytes.fromhex("8b4558"),   # mov eax,[ebp+0x58]
            new=bytes.fromhex("31c090"),    # xor eax,eax; nop
            required=True,
            # 语义校验：紧随其后的 store 指令必须存在，确认 patch 点定位正确
            check=(0x1BDA9, bytes.fromhex("898244080000")),  # mov [edx+0x844],eax
        ),
    ],
)