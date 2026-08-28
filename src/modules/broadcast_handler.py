# src/modules/broadcast_handler.py
# 广播/屏幕渲染处理 —— JSON 格式重写版

import json
import os
import re
import threading
import time
import urllib.request

from config import SOURCE_NAME
from src.core.settings import toolkit_cfg
from src.utils.cmd import run_sigle_cmd
from src.utils.fs import file_exists
from src.utils.network import get_ipv4_address
from src.modules.killer import ensure_killer_running


# ============================================================
#  日志路径 / 解析（真实格式为 JSON）
# ============================================================

def get_screenrender_log_path() -> str:
    """真实日志路径: %APPDATA%\\Mmc\\ScreenRender.log"""
    appdata = os.getenv("APPDATA")
    if not appdata:
        return ""
    return os.path.join(appdata, "Mmc", "ScreenRender.log")


def parse_screenrender_log():
    """
    读取 `%appdata%/Mmc/ScreenRender.log`，
    提取所有 JSON 广播命令（原始 JSON 字符串，不转 #）。

    `Returns`
        `(bool, list)`: (是否找到, JSON 命令列表)
    """
    from src.core.bridge import show_snack
    log_path = get_screenrender_log_path()
    if not log_path or not os.path.exists(log_path):
        show_snack(f"日志文件不存在: {log_path}")
        return False, []

    # 真实格式: 08-10 16:29:36 {"decoderName":"h264",...}
    pattern = re.compile(r"\d{2}-\d{2} \d{2}:\d{2}:\d{2} (\{.*\})")
    result = []

    try:
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                match = pattern.search(line)
                if match:
                    result.append(match.group(1))
    except Exception as e:
        show_snack(f"读取日志文件时发生错误: {e}")
        return False, []

    if not result:
        return False, []
    return True, result


def get_latest_broadcast_cmd() -> str | None:
    """读取日志中最近一条广播命令（原始 JSON 字符串）"""
    status, cmds = parse_screenrender_log()
    if not status:
        return None
    return cmds[-1]


def _parse_json_cmd(cmd) -> dict | None:
    """解析广播命令（JSON 字符串 或 dict），失败返回 None"""
    try:
        if isinstance(cmd, str):
            return json.loads(cmd)
        if isinstance(cmd, dict):
            return cmd
    except Exception:
        pass
    return None


def from_log_file_get_remote_cmd() -> str | None:
    """从配置读取保存的广播命令（JSON）"""
    return toolkit_cfg.get_config_key_data("broadcast_cmd")


# ============================================================
#  命令保存 / 生成（JSON）
# ============================================================

def handin_save_yc_cmd(save_cmd, replace_ip=True) -> None:
    """保存广播命令到配置（JSON 格式）。
    自动把 local 字段替换为本地 IP。"""
    from src.core.bridge import show_snack

    if replace_ip:
        data = _parse_json_cmd(save_cmd)
        if data:
            local_ip = get_ipv4_address()
            data["local"] = local_ip
            save_cmd = json.dumps(data, ensure_ascii=False)
            show_snack(f"已自动替换本地IP地址为{local_ip}")

    toolkit_cfg.set_config_key_data("broadcast_cmd", save_cmd)


def generate_remote_cmd_and_save(teacher_ip) -> None:
    """根据教师 IP 生成广播命令（JSON）并保存。
    组播地址映射: 教师 192.168.5.94 → remote 229.1.5.94"""
    from src.core.bridge import show_snack
    local_ip = get_ipv4_address()

    remote_ip = "229.1.0.0"
    if teacher_ip and re.match(r"^\d{1,3}(?:\.\d{1,3}){3}$", teacher_ip):
        parts = teacher_ip.split(".")
        remote_ip = f"229.1.{parts[2]}.{parts[3]}"

    data = {
        "decoderName": "h264",
        "fullscreen": 0,
        "local": local_ip,
        "port": 7778,
        "remote": remote_ip,
        "teacher_ip": 0,
        "verityPort": 7788,
    }
    save_cmd = json.dumps(data, ensure_ascii=False)
    toolkit_cfg.set_config_key_data("broadcast_cmd", save_cmd)

    print("[DEBUG]", save_cmd)
    show_snack("已按照模板生成广播命令（JSON）")


# ============================================================
#  执行命令构造
# ============================================================

def build_run_broadcast_cmd(YC_command) -> str:
    """构造执行显示命令（直接传 JSON 给 ScreenRender.exe）"""
    exe = f"{toolkit_cfg.oseasy_path}ScreenRender.exe"
    return f'"{exe}" {YC_command}'


def build_windowed_broadcast_cmd() -> str | None:
    """构造窗口化广播命令：JSON 中 fullscreen → 0"""
    cmd = from_log_file_get_remote_cmd()
    data = _parse_json_cmd(cmd)
    if not data:
        return None
    data["fullscreen"] = 0
    return build_run_broadcast_cmd(json.dumps(data, ensure_ascii=False))


def save_now_broadcast_cmd() -> bool | None:
    """保存当前广播命令到程序目录 command.txt"""
    savepath = os.path.join(os.getcwd(), "command.txt")
    cmd = from_log_file_get_remote_cmd()
    if not cmd:
        return False
    with open(savepath, "w") as f:
        f.write(cmd)
    return True


def try_get_teacher_ip() -> str | None:
    """从广播命令 JSON 中提取教师机 IP。
    优先用 remote 组播地址映射回 192.168.x.y。"""
    cmd = from_log_file_get_remote_cmd()
    data = _parse_json_cmd(cmd)
    if not data:
        return None

    remote = str(data.get("remote", ""))
    m = re.match(r"229\.1\.(\d{1,3})\.(\d{1,3})", remote)
    if m:
        return f"192.168.{m.group(1)}.{m.group(2)}"
    return None


def blow_teacher_client():
    from src.core.bridge import show_snack
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


# ============================================================
#  日志命令提取（兼容旧接口）
# ============================================================

def save_scr_log_cmd_to_file(log_list=None) -> None:
    """保存广播命令日志列表到 scr_log_cmd.txt"""
    if log_list == []:
        return
    elif log_list is None:
        status, log_list = parse_screenrender_log()
        if not status:
            return
        return save_scr_log_cmd_to_file(log_list)

    path = os.path.join(os.getcwd(), "scr_log_cmd.txt")
    with open(path, "w") as f:
        f.write("\n".join(log_list))


def extract_yc_cmd_from_log() -> None:
    """从 ScreenRender 日志中提取最近一条广播命令并保存（JSON）"""
    status, log_list = parse_screenrender_log()
    if not status:
        return
    save_scr_log_cmd_to_file(log_list)
    handin_save_yc_cmd(log_list[-1], replace_ip=False)


# ============================================================
#  旧的文件替换方案（保留以兼容广播管理页，已不推荐）
# ============================================================

def replace_screen_render() -> bool:
    """[已弃用] 替换 ScreenRender.exe 为 Helper 版本。
    真实参数通过共享内存传递且为 JSON，文件替换方案不可靠，
    请改用 日志监控 + 秒杀 + 窗口化重开 方案。"""
    from src.utils.logger import debug
    filename = "ScreenRender_Helper.exe"
    nowcurhelper = os.path.join(os.getcwd(), filename)
    copypath = os.path.join(toolkit_cfg.oseasy_path, filename)

    if not file_exists(nowcurhelper):
        debug("ScreenRender_Helper.exe 不存在，无法替换")
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
    """[已弃用] 还原原有的 ScreenRender.exe"""
    path = f"{toolkit_cfg.oseasy_path}ScreenRender.exe"
    if not check_replace_screen_render_status():
        return False
    try:
        os.remove(path)
    except FileNotFoundError:
        pass
    run_sigle_cmd(f'rename "{toolkit_cfg.oseasy_path}ScreenRender_Y.exe" "ScreenRender.exe"')
    return True


def check_replace_screen_render_status() -> bool:
    """通过检查 ScreenRender_Y.exe 是否存在判断是否已替换"""
    return file_exists(f"{toolkit_cfg.oseasy_path}ScreenRender_Y.exe")


# ============================================================
#  日志监控 + 秒杀 + 窗口化重开（推荐方案）
# ============================================================

_monitor_running = False
_monitor_thread = None
_monitor_seen_count = 0
_monitor_auto_windowed = True


def _monitor_loop():
    """后台轮询 ScreenRender.log。
    发现新广播命令 → 若 fullscreen=1 且开启窗口化 → 杀进程重开窗口化。"""
    global _monitor_seen_count

    while _monitor_running:
        try:
            log_path = get_screenrender_log_path()
            if log_path and os.path.exists(log_path):
                status, cmds = parse_screenrender_log()
                if status and len(cmds) > _monitor_seen_count:
                    # 有新命令
                    new_cmd = cmds[-1]
                    _monitor_seen_count = len(cmds)

                    data = _parse_json_cmd(new_cmd)
                    if data and data.get("fullscreen") == 1:
                        # 保存命令到配置
                        toolkit_cfg.set_config_key_data("broadcast_cmd", new_cmd)
                        if _monitor_auto_windowed:
                            _force_windowed()
        except Exception:
            pass
        time.sleep(0.5)


def force_screenrender_windowed() -> bool:
    """将当前 ScreenRender 窗口强制切换为窗口模式（不杀进程）。
    返回 True 表示成功找到窗口并切换。"""
    import ctypes
    from src.utils.logger import info

    user32 = ctypes.windll.user32
    GWL_STYLE = -16
    WS_POPUP = 0x80000000
    WS_OVERLAPPEDWINDOW = 0x00CF0000
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020

    hwnd = user32.FindWindowW("MultiRenderWindowClass", None)
    if not hwnd:
        info("force_screenrender_windowed: 未找到窗口")
        return False

    info("将 ScreenRender 切换为窗口模式...")
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    new_style = (style & ~WS_POPUP) | WS_OVERLAPPEDWINDOW
    user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
    user32.SetWindowPos(hwnd, 0, 0, 0, 0, 0, SWP_NOZORDER | SWP_FRAMECHANGED)
    # 重新设置大小：屏幕 80%
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    ww, wh = int(sw * 0.8), int(sh * 0.8)
    user32.SetWindowPos(hwnd, 0, (sw - ww) // 2, (sh - wh) // 2, ww, wh, SWP_NOZORDER | SWP_FRAMECHANGED)
    user32.ShowWindow(hwnd, 5)
    info("窗口模式切换完成")
    return True


# 监控线程内部调用 force_screenrender_windowed 的快捷别名
_force_windowed = force_screenrender_windowed


def force_screenrender_fullscreen() -> bool:
    """将当前 ScreenRender 窗口恢复全屏模式（去窗口装饰 + 覆盖屏幕）。"""
    import ctypes
    from src.utils.logger import info

    user32 = ctypes.windll.user32
    GWL_STYLE = -16
    WS_POPUP = 0x80000000
    WS_OVERLAPPEDWINDOW = 0x00CF0000
    SWP_NOZORDER = 0x0004
    SWP_FRAMECHANGED = 0x0020
    HWND_TOP = 0

    hwnd = user32.FindWindowW("MultiRenderWindowClass", None)
    if not hwnd:
        info("force_screenrender_fullscreen: 未找到窗口")
        return False

    info("将 ScreenRender 恢复全屏模式...")
    style = user32.GetWindowLongW(hwnd, GWL_STYLE)
    new_style = (style & ~WS_OVERLAPPEDWINDOW) | WS_POPUP
    sw = user32.GetSystemMetrics(0)
    sh = user32.GetSystemMetrics(1)
    user32.SetWindowLongW(hwnd, GWL_STYLE, new_style)
    user32.SetWindowPos(hwnd, HWND_TOP, 0, 0, sw, sh, SWP_NOZORDER | SWP_FRAMECHANGED)
    user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
    info("全屏模式恢复完成")
    return True


def start_log_monitor(auto_windowed: bool = True) -> None:
    """启动广播日志监控线程。
    auto_windowed=True 时，检测到全屏广播自动切换窗口化。"""
    global _monitor_running, _monitor_thread, _monitor_seen_count, _monitor_auto_windowed
    if _monitor_running:
        return

    # 记录已见过的命令数，避免重复处理历史命令
    _, cmds = parse_screenrender_log()
    _monitor_seen_count = len(cmds) if cmds else 0
    _monitor_auto_windowed = auto_windowed
    _monitor_running = True
    _monitor_thread = threading.Thread(target=_monitor_loop, daemon=True)
    _monitor_thread.start()


def stop_log_monitor() -> None:
    """停止广播日志监控线程。"""
    global _monitor_running
    _monitor_running = False


def is_log_monitor_running() -> bool:
    """监控线程是否在运行。"""
    return _monitor_running