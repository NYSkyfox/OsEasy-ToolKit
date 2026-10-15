# src/patches/duo_open.py
# 双开教师端 / 学生端 —— 纯 patch 点配置（无执行逻辑）
#
# 逆向结论：
#   Teacher.exe / Student.exe 启动时用「命名事件存在性检测」OpenEventW 做互斥，
#   任一端"存在"即弹 5 秒倒计时警告框并退出。
#   把检测原语函数体最前 3 字节改 31 c0 c3 (xor eax,eax; ret) 使其恒返回 0。
#
#   检测原语经全局函数指针调用（call [abs ptr]，FF 15），sanity 校验确认。

from src.core.va_patch import VA_PatchTarget, VA_FileTarget, VA_PatchPoint

NOP = bytes.fromhex("31c0c3")      # xor eax,eax; ret
PROLOGUE = bytes.fromhex("558bec")  # push ebp; mov ebp,esp

TARGET = VA_PatchTarget(
    key="duo_open",
    name="双开教师端 / 学生端",
    description=(
        "patch Teacher.exe / Student.exe 的互斥检测原语（OpenEventW 恒返回 0），"
        "解除「检测到另一端已启动即退出」的限制，实现两端同时运行。"
    ),
    image_base=0x400000,
    files=[
        VA_FileTarget(
            role="teacher",
            sample_name="Teacher.exe",
            patch_points=[
                VA_PatchPoint(
                    label="互斥检测",
                    va=0x5b9420,
                    orig=PROLOGUE,
                    new=NOP,
                    sanity_window=0x40,
                    sanity_pattern=bytes.fromhex("ff15"),  # call [abs ptr]
                ),
            ],
        ),
        VA_FileTarget(
            role="student",
            sample_name="Student.exe",
            patch_points=[
                VA_PatchPoint(
                    label="互斥检测",
                    va=0x4bb0b0,
                    orig=PROLOGUE,
                    new=NOP,
                    sanity_window=0x40,
                    sanity_pattern=bytes.fromhex("ff15"),  # call [abs ptr]
                ),
            ],
        ),
    ],
    backup_ext=".duo_open.bak",
    newfile_suffix="_duo_open",
)
