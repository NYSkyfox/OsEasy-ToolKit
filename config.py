# config.py
# OsEasy ManagerHelper 静态配置
#
# ManagerHelper 定位：以字节 patch 为核心的“管控解除 / 行为改造”工具集。
# 顶层只放全局常量与功能描述，业务逻辑全部下沉到 src/ 各层。

# ── 基础信息 ──────────────────────────────────────────────
APP_NAME = "OsEasy-ManagerHelper"
APP_VERSION = "0.1.0"
RELEASE_NAME = f"{APP_NAME} v{APP_VERSION}"
AUTHOR = "NyxFox"
GITHUB_URL = "https://github.com/NYSkyfox/OsEasy-ToolKit"

# ── 数据根目录（用户文件夹下，存放备份/日志/配置） ──────────
DATA_ROOT_TEMPLATE = "C:\\Users\\{username}\\OsEasy-ManagerHelper"
CONFIG_FILE_TEMPLATE = DATA_ROOT_TEMPLATE + "\\config.json"
LOG_DIR_TEMPLATE = DATA_ROOT_TEMPLATE + "\\log"
BACKUP_DIR_TEMPLATE = DATA_ROOT_TEMPLATE + "\\backups"

# ── Os-Easy 默认安装目录候选（按序探测） ──────────────────
OSEASY_INSTALL_CANDIDATES = [
    r"C:\Program Files (x86)\Os-Easy\os-easy multicast teaching system",
    r"C:\Program Files\Os-Easy\os-easy multicast teaching system",
    r"D:\Os-Easy\os-easy multicast teaching system",
]

# ── UI 主题色（墨绿，跟随系统可覆盖） ─────────────────────
ACCENT_COLOR = "#3B8A67"

# ── 各功能的人类可读描述（用于 GUI 概览 / tooltip） ────────
# 说明：3 个 VA 型功能 + 1 个教师端授权解除（dog_license）在此登记
# （overview「功能模块」区显示）。
# 3 个固定偏移目标（行为管控 / 屏幕广播 / 窗口化）由 overview「Patch 目标状态」
# 区直接遍历 src/patches 注册表展示，不在此重复。
FEATURE_DESC = {
    "duo_open": (
        "双开教师端 / 学生端",
        "patch Teacher.exe / Student.exe 的互斥检测原语（OpenEventW 恒返回 0），"
        "解除“检测到另一端已启动即退出”的限制，实现两端同时运行。",
    ),
    "screen_capture": (
        "阻止 / 使用假屏幕截图",
        "patch StudentLogic.dll：NOP 模式停止截屏发送（教师端画面定格、状态灯在线）；"
        "假截图模式用本地 BMP 替换 BitBlt 截屏（教师端显示固定假画面）。",
    ),
    "noshutdown": (
        "拦截远程关机 / 重启",
        "patch Student.exe 的 FUN_004a9660 入口，使教师端下发的 远程重启 / 远程关机 "
        "指令在学生机失效。一个点封两个动作，支持文件版（持久）与内存版（抗 ASLR）。",
    ),
    "dog_license": (
        "教师端 加密狗 / 点数限制 解除",
        "教师端授权解除组合工具（4 方案可多选）：解除学生机连接数上限[MainLogic.dll]、"
        "恒判有狗[Teacher.exe]、消除\"未找到加密狗\"弹窗[Teacher.exe]、改 core.conf /Limit/ 并重签。",
    ),
}
