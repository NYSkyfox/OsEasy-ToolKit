# src/patches/screen_capture.py
# 阻止 / 使用假屏幕截图 —— 纯 patch 点配置（无执行逻辑）
#
# 目标 StudentLogic.dll（PE32，ImageBase=0x10000000）
#
# 两种工作模式（对应 GUI 的 nop / fake 单选）：
#   nop   模式  —— patch pipeline 点（默认），截屏发送完全停止
#   fake  模式  —— patch fake_screen 点（shellcode），用本地 BMP 替换 BitBlt
#
# 标签（labels）：
#   pipeline    屏幕截图完整流水线（截屏→编码→BMP→WSASend）
#   bplt        BitBlt 全屏截图（备选，更精确）
#   screenrender ScreenRender 子进程启动（备选）
#   wsasend     WSASend 通用网络发送（备选，影响面大）
#   fake_screen 假截图 shellcode（替换 FUN_1008cb70 整个函数体 352B）
#
# shellcode IAT 地址（绝对 VA，ImageBase=0x10000000）

from src.core.va_patch import VA_PatchTarget, VA_FileTarget, VA_PatchPoint

NOP = bytes.fromhex("31c0c3")
PROLOGUE = bytes.fromhex("558bec")

# shellcode 布局参数
FUN_CB70_VA = 0x1008CB70
FUN_CB70_SIZE = 0x160  # 352 bytes
SC_FP_OFF = 0x100       # filepath 字符串在函数体内偏移
SC_RF_OFF = 0x118       # "ReadFile\0" 在函数体内偏移

TARGET = VA_PatchTarget(
    key="screen_capture",
    name="阻止 / 使用假屏幕截图",
    description=(
        "patch StudentLogic.dll：NOP 模式停止截屏发送（教师端画面定格、状态灯在线）；"
        "假截图模式用本地 BMP 替换 BitBlt（教师端显示固定假画面）。"
    ),
    image_base=0x10000000,
    files=[
        VA_FileTarget(
            role="default",
            sample_name="StudentLogic.dll",
            patch_points=[
                # ── NOP 模式点（按 label 选择执行） ──
                VA_PatchPoint(
                    label="pipeline",
                    va=0x1007D650,
                    orig=PROLOGUE,
                    new=NOP,
                    section_check=".text",
                ),
                VA_PatchPoint(
                    label="bplt",
                    va=0x1008CB70,
                    orig=PROLOGUE,
                    new=NOP,
                    section_check=".text",
                ),
                VA_PatchPoint(
                    label="screenrender",
                    va=0x10088CA0,
                    orig=PROLOGUE,
                    new=NOP,
                    section_check=".text",
                ),
                VA_PatchPoint(
                    label="wsasend",
                    va=0x1002A730,
                    orig=PROLOGUE,
                    new=NOP,
                    section_check=".text",
                ),
                # ── 假截图 shellcode 点 ──
                VA_PatchPoint(
                    label="fake_screen",
                    va=FUN_CB70_VA,
                    orig=PROLOGUE,
                    new=PROLOGUE,  # shellcode 模式下 new 被忽略
                    shellcode_mode=True,
                    func_size=FUN_CB70_SIZE,
                    section_check=".text",
                ),
            ],
        ),
    ],
    backup_ext=".bak",
    newfile_suffix="_fake",
    # ── shellcode 参数 ──
    shellcode_iat={
        "_func_base":      FUN_CB70_VA,
        "CreateFileA":     0x102340D8,
        "SetFilePointer":  0x102340F4,
        "CloseHandle":     0x102341E8,
        "GetModuleHandleA": 0x102341F8,
        "GetProcAddress":  0x1023411C,
    },
    shellcode_fp_off=SC_FP_OFF,
    shellcode_rf_off=SC_RF_OFF,
    shellcode_max_fp=SC_RF_OFF - SC_FP_OFF - 1,  # 23 chars
)