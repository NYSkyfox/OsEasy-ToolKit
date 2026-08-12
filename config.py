# config.py
# 工具箱静态配置信息

# 基础信息
APP_NAME = "OsEasy-ToolKit"
APP_VERSION = "1.8.1-Alpha"
RELEASE_NAME = f"{APP_NAME} v{APP_VERSION}"
SOURCE_NAME = "ToolKit"
AUTHOR = "NyxFox"
GITHUB_URL = "https://github.com/NYSkyfox/OsEasy-ToolKit"

# 构建日期（打包时由 build.py 写入）
BUILD_DATE = "2026-08-10 16:45:13"

# 默认字体（回退值，实际会按优先级探测可用字体）
DEFAULT_FONT_PATH = "C:\\Windows\\Fonts\\msyh.ttc"

# 工具箱数据根目录（用户文件夹下）
DATA_ROOT_TEMPLATE = "C:\\Users\\{username}\\OsEasy-ToolKit"

# 配置文件路径
CONFIG_FILE_PATH_TEMPLATE = DATA_ROOT_TEMPLATE + "\\config.json"

# 备份文件路径
BACKUP_PATH_TEMPLATE = DATA_ROOT_TEMPLATE + "\\backups"

# 生成的脚本文件夹路径
CMD_FILE_PATH_TEMPLATE = DATA_ROOT_TEMPLATE + "\\scripts"

# 日志文件夹路径
LOG_DIR_TEMPLATE = DATA_ROOT_TEMPLATE + "\\log"

# 截图保存路径
SCREENSHOT_PATH_TEMPLATE = DATA_ROOT_TEMPLATE + "\\screenshots"

# 默认学生端路径
DEFAULT_OSEASY_PATH = "C:\\Program Files (x86)\\Os-Easy\\os-easy multicast teaching system\\"

# 默认学生端进程名
DEFAULT_STUDENT_EXE_NAME = "Student.exe"

# 默认一言列表
DEFAULT_YIYAN_LIST = [
    "人生苦短,我用Python",
    "亻尔 女子",
    "《机房课时间管理》",
    "就让你看看...这葫芦里卖的什么药！",
    "让我来摸个鱼吧~",
    "代码没写完,Bug先写好了",
    "科技改变课堂"
]

# 默认显示的一言
DEFAULT_SHOW_YIYAN = "希君生羽翼，一化北溟鱼"

# ---- UI 主题色 ----
# 默认主题色（墨绿色），会在启动时尝试读取 Windows 系统主题色覆盖
DEFAULT_ACCENT_COLOR = "#3B8a67"

# ---- 脚本文件名 ----
KILLER_BAT = "Process-Killer_Student.bat"
KILLER_ALL_BAT = "Process-Killer_All.bat"
FILE_DEL_BAT = "Files-Delete.bat"
UNLOCK_NET_BAT = "Unlock-Network.bat"
UNLOCK_USB_BAT = "Unlock-USB.bat"
UNLOCK_USB_PS1 = "Unlock-USB.ps1"
UNLOCK_KB_BAT = "Unlock-Keyboard.bat"
UNLOCK_ALL_BAT = "Unlock-All.bat"

# ---- 备份文件清单（相对于 OE 安装目录） ----
BACKUP_FILES = [
    # 锁定相关
    "LockKeyboard.dll",
    "LoadDriver.exe",
    "KbDriver.exe",
    # 黑屏/控屏
    "BlackSlient.exe",
    "MultiClient.exe",
    # 网络/USB
    "OeNetLimit.sys",
    "OeNetLimitSetup.exe",
    "oenetlimitx64.cat",
    "easyusbflt.sys",
    "ProcFireWall.sys",
    # 嗅探
    "x86\\LISSNetInfoSniffer.exe",
]