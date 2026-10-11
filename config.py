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
FEATURE_DESC = {
    "multiclient_disable": (
        "禁用教学管控",
        "patch MultiClient.exe，使教师端下发的 键鼠锁 / 行为管控（网络·USB·程序）"
        "指令在学生机失效。屏幕广播默认保留，可用 --no-screen 一并禁用。",
    ),
    "screenrender_windowed": (
        "屏幕广播窗口化",
        "patch ScreenRender.exe，强制 --fullscreen=0，使教师端屏幕广播始终以"
        "可拖拽/可缩放的窗口启动，而非默认全屏。广播功能保留。",
    ),
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
}
