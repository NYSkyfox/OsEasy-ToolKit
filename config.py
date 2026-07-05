# config.py
# 工具箱静态配置信息

# 基础信息
APP_NAME = "OsEasy-ToolBox"
APP_VERSION = "OsEasy-ToolBox v1.8 Beta4"
AUTHOR = "ZiHaoSaMa66"
GITHUB_URL = "https://github.com/NYSkyfox/OsEasy-ToolKit"

# 默认字体
DEFAULT_FONT_PATH = "C:\\Windows\\Fonts\\Deng.ttf"

# 工具箱数据根目录（用户文件夹下）
DATA_ROOT_TEMPLATE = "C:\\Users\\{username}\\OsEasy-ToolBox"

# 配置文件路径
CONFIG_FILE_PATH_TEMPLATE = DATA_ROOT_TEMPLATE + "\\ToolBoxConfig.json"

# 备份文件路径
BACKUP_PATH_TEMPLATE = DATA_ROOT_TEMPLATE + "\\Backups"

# 生成的脚本文件夹路径
CMD_FILE_PATH_TEMPLATE = DATA_ROOT_TEMPLATE + "\\Scripts"

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
DEFAULT_ACCENT_COLOR = "#2E7D32"  # 墨绿

# 各控件的颜色键名（存入 ToolBoxConfig.json）
# 注：目前通过 Ui.accent_color 统一控制所有开关颜色，此映射表为未来独立颜色配置预留
SWITCH_COLOR_KEYS = {
    "亮色主题":        "color_theme_switch",
    "外部cmd守护进程":   "color_protect_switch",
    "挂起学生端":       "color_guaqi_switch",
    "Alt+X 截图":      "color_screenshot_switch",
    "Ctrl+Alt+F 全屏": "color_fullscreen_switch",
    "Alt+K 杀广播":    "color_kill_switch",
    "Alt+U 窗口广播":  "color_window_switch",
    "CapsLock+Enter":  "color_hide_switch",
    "随机一言":         "color_random_switch",
}