"""
OsEasy-ToolKit 全局配置
所有常量、路径、版本号集中管理
"""

# ==================== 版本信息 ====================
VERSION = "1.0.0"
APP_NAME = "OsEasy-ToolKit"
FULL_TITLE = f"{APP_NAME} v{VERSION}"

# ==================== 路径配置 ====================
# 学生端默认安装路径
DEFAULT_OSEASY_PATH = r"C:\Program Files (x86)\Os-Easy\os-easy multicast teaching system"

# 配置文件路径
CONFIG_FILE_PATH = r"C:\ToolKitConfig.json"

# 备份文件路径
BACKUP_FILE_PATH = r"C:\ToolKitBackups"

# 脚本文件生成路径（当前用户目录下）
import os
CMD_FILE_PATH = os.path.join(os.environ.get('USERPROFILE', r"C:\Users\Default"), "ToolKitProd")

# 拦截命令保存路径
INTERCEPT_CMD_SAVE_PATH = os.path.join(CMD_FILE_PATH, "SCCMD.txt")

# ==================== 学生端进程名 ====================
STUDENT_EXE_NAMES = ["Student.exe", "MmcStudent.exe"]

# ==================== 颜色配置（仅状态栏消息使用） ====================
COLORS = {
    "info": "#333333",
    "success": "#107c10",
    "warning": "#ffc107",
    "error": "#d13438",
    "fg": "#333333",
}

# ==================== 窗口尺寸 ====================
WINDOW_WIDTH = 500
WINDOW_HEIGHT = 650
WINDOW_MIN_WIDTH = 480
WINDOW_MIN_HEIGHT = 600

# ==================== 需要 kill 的进程列表 ====================
KILL_PROCESS_LIST = [
    "Ctsc_Multi.exe",
    "DeviceControl_x64.exe",
    "HRMon.exe",
    "MultiClient.exe",
    "OActiveII-Client.exe",
    "OEClient.exe",
    "OELogSystem.exe",
    "OEUpdate.exe",
    "OEProtect.exe",
    "ProcessProtect.exe",
    "RunClient.exe",
    "ServerOSS.exe",
    "wfilesvr.exe",
    "tvnserver.exe",
    "updatefilesvr.exe",
    "ScreenRender.exe",
]

# ==================== 需要备份的关键文件 ====================
BACKUP_FILE_LIST = [
    "MultiClient.exe",
    "LoadDriver.exe",
    "BlackSlient.exe",
    "LockKeyboard.dll",
    "oenetlimitx64.cat",
    "OeNetLimitSetup.exe",
    "OeNetLimit.sys",
    "OeNetLimit.inf",
]

# ==================== DLL 文件配置 ====================
DLL_CONFIG = {
    "usb_ctrl": {
        "path": r"\x64\easyusbctrl.dll",
        "functions": {
            "start": "EasyUsb_StartWorking",
            "stop": "EasyUsb_StopWorking",
            "status": "EasyUsb_IsWorking",
        }
    },
    "net_limit": {
        "path": r"\x64\OeNetlimit.dll",
        "functions": {
            "enable": "EnableNet",
            "disable": "DisableInternet",
        }
    }
}

# ==================== 服务名 ====================
SERVICES = {
    "mmpc": "MMPC",
    "net_limit": "OeNetlimit",
    "usb_filter": "easyusbflt",
}

# ==================== 仓库地址 ====================
GITHUB_REPO_URL = "https://github.com/NYSkyfox/OsEasy-ToolKit"

# ==================== 默认一言 ====================
DEFAULT_YIYAN = [
    "人生苦短，我用 Python",
    "亻尔 女子",
    "《机房课时间管理》",
    "就让你看看...这葫芦里卖的什么药！",
    "让我来摸个鱼吧~",
    "代码没写完，Bug 先写好了",
    "科技改变课堂",
    "噢易？噢，易如反掌~",
]