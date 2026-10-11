# src/modules/__init__.py
# 功能模块层 —— “PE+VA+shellcode”型工具（独立维护，不纳入 patches 注册表）
#
#   duo_open       双开教师端 / 学生端（OpenEventW 恒返回 0）
#   screen_capture 阻止 / 使用假屏幕截图（NOP / shellcode 替换 BitBlt）
#   noshutdown     拦截远程关机 / 重启（patch Student.exe FUN_004a9660 入口；文件版 + 内存版）