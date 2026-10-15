# src/patches/noshutdown.py
# 拦截远程关机 / 重启 —— 纯 patch 点配置（无执行逻辑）
#
# 目标 Student.exe（PE32，i386，ImageBase=0x400000）
#
# 逆向结论：
#   远程重启与远程关机共用同一函数 FUN_004a9660：
#       if (param == 0)   ExitWindowsEx(6, 0);   // REBOOT|FORCE
#       else              ExitWindowsEx(0xd, 0); // SHUTDOWN|FORCE|POWEROFF
#   先 AdjustTokenPrivileges 启用 SeShutdownPrivilege 再 ExitWindowsEx。
#   把入口 3 字节 55 8b ec 改 31 c0 c3 即函数进入即返回，一个点封两个动作。
#   StudentLogic.dll 不参与；Student.exe 内无 shutdown.exe 字符串（红鲱鱼）。
#
# 支持文件版 + 内存版（supports_memory=True）。

from src.core.va_patch import VA_PatchTarget, VA_FileTarget, VA_PatchPoint

NOP = bytes.fromhex("31c0c3")
PROLOGUE = bytes.fromhex("558bec")

TARGET = VA_PatchTarget(
    key="noshutdown",
    name="拦截远程关机 / 重启",
    description=(
        "patch Student.exe 的 FUN_004a9660 入口，使教师端下发的 远程重启 / 远程关机 "
        "指令在学生机失效。一个点封两个动作，支持文件版（持久）与内存版（抗 ASLR）。"
    ),
    image_base=0x400000,
    files=[
        VA_FileTarget(
            role="default",
            sample_name="Student.exe",
            patch_points=[
                VA_PatchPoint(
                    label="shutdown_reboot",
                    va=0x4A9660,
                    orig=PROLOGUE,
                    new=NOP,
                ),
            ],
        ),
    ],
    known_md5={
        "326a77edb4b5d03eaeeb7dafa2d9e08e": "Student.exe 原版",
        "aa2e24bc4912e8f57a3dd2b3df6cb6e1": "Student_duo_open.exe 双开版",
    },
    supports_memory=True,
    backup_ext=".noshutdown.bak",
    newfile_suffix=".noshutdown",
)