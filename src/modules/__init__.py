# src/modules/__init__.py
# 功能模块层 —— VA 型 patch 的「纯配置」目录
#
# 结构（重构后）：
#   patches/  纯 patch 点配置文件（每个文件一个 VA_PatchTarget，无执行逻辑）
#       duo_open        双开教师端 / 学生端
#       screen_capture  阻止 / 使用假屏幕截图（nop + 假截图 shellcode）
#       noshutdown      拦截远程关机 / 重启（文件版 + 内存版）
#
# 执行逻辑统一在 src/core/va_patch.py（VAPatchExecutor），
# 读取上述配置后执行 dry_run / patch / restore / status / 内存操作。
#
# 注意：src/patches/（固定偏移型，PatchEngine 驱动）与本目录（VA 型）是两套机制。