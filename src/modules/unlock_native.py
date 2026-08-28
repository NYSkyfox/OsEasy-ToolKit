# src/modules/unlock_native.py
# 原生解锁实现 —— 完全脱离 bat / PowerShell
# 用 winreg 清理注册表过滤驱动、os.remove 删文件、原生服务/进程控制
# 保留 script_generator.py / script_templates.py 供其他用途（击杀脚本等）

import os
import winreg

from src.core.settings import toolkit_cfg
from src.utils.fs import file_exists
from src.modules.service_manager import stop_service, delete_service, query_service_state
from src.utils.process import kill_process, is_process_running

# 设备类 GUID
_KB_GUIDS = [
    "{4D36E96B-E325-11CE-BFC1-08002BE10318}",  # 键盘
    "{4D36E96F-E325-11CE-BFC1-08002BE10318}",  # 鼠标
    "{745a17a0-74d3-11d0-b6fe-00a0c90f57da}",  # HID
]
_USB_GUIDS = [
    "{36FC9E60-C465-11CF-8056-444553540000}",  # USB
    "{745a17a0-74d3-11d0-b6fe-00a0c90f57da}",  # HID
]

_CLASS_KEY = r"SYSTEM\CurrentControlSet\Control\Class"


# ══════════════════════════════════════════════════════════
# 底层工具函数
# ══════════════════════════════════════════════════════════

def _remove_filter_from_class(guid: str, target: str) -> list[str]:
    """从指定设备类 GUID 的 UpperFilters/LowerFilters 中移除目标驱动名。"""
    logs = []
    path = _CLASS_KEY + "\\" + guid
    try:
        key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, path, 0,
                             winreg.KEY_READ | winreg.KEY_WRITE)
    except OSError:
        return logs
    try:
        for value_name in ("UpperFilters", "LowerFilters"):
            try:
                value, _ = winreg.QueryValueEx(key, value_name)
            except OSError:
                continue
            if not isinstance(value, (list, tuple)):
                continue
            if target not in value:
                continue
            new_value = [v for v in value if v != target]
            if new_value:
                winreg.SetValueEx(key, value_name, 0, winreg.REG_MULTI_SZ, new_value)
                logs.append(f"注册表 {guid} {value_name}: 移除 {target}")
            else:
                winreg.DeleteValue(key, value_name)
                logs.append(f"注册表 {guid} {value_name}: 移除 {target} (已删除空值)")
    finally:
        winreg.CloseKey(key)
    return logs


def _delete_file(relpath: str) -> bool:
    """删除学生端目录下的文件（不存在则忽略），返回是否删除成功。"""
    path = os.path.join(toolkit_cfg.oseasy_path, relpath)
    if not file_exists(path):
        return False
    try:
        os.remove(path)
        return True
    except OSError:
        return False


def _delete_file_logged(relpath: str, on_output=None) -> None:
    """删除文件并如实输出日志：不存在则跳过；被占用则自动 kill 占用进程后重试。"""
    path = os.path.join(toolkit_cfg.oseasy_path, relpath)
    if not file_exists(path):
        return
    try:
        os.remove(path)
        _emit(f"已删除文件 {relpath}", on_output)
    except PermissionError:
        _emit(f"无法删除文件 {relpath} [拒绝访问，需管理员权限]", on_output)
    except OSError:
        # 查询占用进程 → kill → 重试
        owners = _find_file_locking_processes(path)
        if not owners:
            _emit(f"无法删除文件 {relpath}", on_output)
            return
        _emit(f"文件 {relpath} 被占用 [{', '.join(owners)}]，正在终止占用进程...", on_output)
        for name in set(owners):
            if kill_process(name):
                _emit(f"  已终止 {name}", on_output)
            else:
                _emit(f"  终止 {name} 失败", on_output)
        # 重试删除
        try:
            os.remove(path)
            _emit(f"已删除文件 {relpath}", on_output)
        except OSError:
            _emit(f"无法删除文件 {relpath} [终止占用进程后仍失败]", on_output)


def _find_file_locking_processes(filepath: str) -> list[str]:
    """通过 psutil 遍历进程打开的文件句柄，查询占用指定文件的进程名。
    最多检查 3 个进程即返回，避免全量遍历耗时过长。"""
    import psutil
    filepath_lower = filepath.lower()
    owners = []
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            for f in proc.open_files():
                if f.path and f.path.lower() == filepath_lower:
                    owners.append(proc.info["name"])
                    if len(owners) >= 3:
                        return owners
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return owners


def _emit(msg: str, on_output=None) -> None:
    """输出带时间戳的操作日志。"""
    if on_output is None:
        return
    import time
    ts = time.strftime("%H:%M:%S")
    on_output(f"[{ts}] {msg}")


def _logout_if_needed(logout: bool, on_output=None) -> None:
    """操作完成后按需注销系统（shutdown /l，无黑框）。"""
    if not logout:
        return
    _emit("自动注销", on_output)
    import subprocess
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    subprocess.run(["shutdown", "/l"], creationflags=flags)


# ══════════════════════════════════════════════════════════
# 原子操作（每一项只做一件事，带状态感知）
# 签名: (on_output) -> None
# ══════════════════════════════════════════════════════════

def _a_backup(on_output=None):
    """备份关键文件"""
    from src.modules.file_handler import backup_oe_files
    backup_oe_files(skip_existing=True)
    _emit("已备份关键文件", on_output)


def _a_kill_student(on_output=None):
    _kill_logged(toolkit_cfg.student_exe_name, on_output)


def _a_kill_device_control(on_output=None):
    _kill_logged("DeviceControl_x64.exe", on_output)


def _a_kill_blacksilent(on_output=None):
    _kill_logged("BlackSlient.exe", on_output)


def _a_kill_screenrender(on_output=None):
    _kill_logged("ScreenRender.exe", on_output)


def _a_kill_screenrender_y(on_output=None):
    _kill_logged("ScreenRender_Y.exe", on_output)


def _a_kill_multiclient(on_output=None):
    _kill_logged("MultiClient.exe", on_output)


def _a_stop_mmpc(on_output=None):
    _stop_service_logged("MMPC", on_output)


def _a_stop_oenetlimit(on_output=None):
    _stop_service_logged("OeNetLimit", on_output)


def _a_stop_procfirewall(on_output=None):
    _stop_service_logged("ProcFireWall", on_output)


def _a_stop_delete_easyusbflt(on_output=None):
    _stop_delete_service_logged("easyusbflt", on_output)


def _a_stop_delete_kbfilter(on_output=None):
    _stop_delete_service_logged("KbFilter", on_output)


def _a_stop_delete_procfirewall(on_output=None):
    _stop_delete_service_logged("ProcFireWall", on_output)


def _a_stop_delete_fbdats(on_output=None):
    _stop_delete_service_logged("FbdATS", on_output)


def _a_delete_easyusbflt_sys(on_output=None):
    _delete_file_logged("easyusbflt.sys", on_output)


def _a_delete_kb_files(on_output=None):
    for f in ("KbFilter.sys", "ProcFireWall.sys", "LockKeyboard.dll", "LoadDriver.exe", "KbDriver.exe"):
        _delete_file_logged(f, on_output)


def _a_delete_screen_files(on_output=None):
    for name in ("ScreenRender.exe", "ScreenRender_Y.exe", "MultiClient.exe"):
        _delete_file_logged(name, on_output)


def _a_delete_blacksilent_file(on_output=None):
    _delete_file_logged("BlackSlient.exe", on_output)


def _a_clean_registry_usb(on_output=None):
    found = False
    for guid in _USB_GUIDS:
        for line in _remove_filter_from_class(guid, "easyusbflt"):
            _emit(line, on_output)
            found = True
    if not found:
        _emit("注册表: 未找到 easyusbflt 过滤驱动项，无需清理", on_output)


def _a_clean_registry_kb(on_output=None):
    found = False
    for guid in _KB_GUIDS:
        for line in _remove_filter_from_class(guid, "KbFilter"):
            _emit(line, on_output)
            found = True
    if not found:
        _emit("注册表: 未找到 KbFilter 过滤驱动项，无需清理", on_output)


# ══════════════════════════════════════════════════════════
# 带状态感知的日志辅助函数
# ══════════════════════════════════════════════════════════

def _kill_logged(process_name: str, on_output=None) -> None:
    if not is_process_running(process_name):
        _emit(f"进程 {process_name} 未运行，跳过", on_output)
        return
    if kill_process(process_name):
        _emit(f"已终止进程 {process_name}", on_output)
    else:
        _emit(f"终止进程 {process_name} 失败", on_output)


def _stop_service_logged(name: str, on_output=None) -> None:
    state = query_service_state(name)
    if state == "missing":
        _emit(f"服务 {name} 不存在，跳过", on_output)
        return
    if state == "stopped":
        _emit(f"服务 {name} 未运行，跳过", on_output)
        return
    if stop_service(name):
        _emit(f"已停止服务 {name}", on_output)
    else:
        _emit(f"停止服务 {name} 失败", on_output)


def _stop_delete_service_logged(name: str, on_output=None) -> None:
    """合并停止+删除：一次状态查询，避免重复日志。"""
    state = query_service_state(name)
    if state == "missing":
        _emit(f"服务 {name} 不存在，跳过", on_output)
        return
    if state == "running":
        if stop_service(name):
            _emit(f"已停止服务 {name}", on_output)
        else:
            _emit(f"停止服务 {name} 失败", on_output)
    if delete_service(name):
        _emit(f"已删除服务 {name}", on_output)
    else:
        _emit(f"删除服务 {name} 失败（可能仍在运行或被占用）", on_output)


# ══════════════════════════════════════════════════════════
# 解锁项定义（每个解锁项 = 若干原子操作的列表）
# ══════════════════════════════════════════════════════════

_NETWORK = [
    ("停止 MMPC",             _a_stop_mmpc),
    ("终止学生端进程",         _a_kill_student),
    ("终止 DeviceControl",    _a_kill_device_control),
    ("停止 OeNetLimit",       _a_stop_oenetlimit),
    ("停止 ProcFireWall",     _a_stop_procfirewall),
]

_USB = [
    ("备份关键文件",           _a_backup),
    ("停止 MMPC",             _a_stop_mmpc),
    ("终止学生端进程",         _a_kill_student),
    ("终止 DeviceControl",    _a_kill_device_control),
    ("停删 easyusbflt",       _a_stop_delete_easyusbflt),
    ("删除 easyusbflt.sys",   _a_delete_easyusbflt_sys),
    ("清理注册表 easyusbflt", _a_clean_registry_usb),
]

_KEYBOARD = [
    ("备份关键文件",           _a_backup),
    ("停止 MMPC",             _a_stop_mmpc),
    ("终止学生端进程",         _a_kill_student),
    ("终止 BlackSlient",      _a_kill_blacksilent),
    ("停删 KbFilter",         _a_stop_delete_kbfilter),
    ("停删 ProcFireWall",     _a_stop_delete_procfirewall),
    ("删除键盘驱动文件",       _a_delete_kb_files),
    ("清理注册表 KbFilter",   _a_clean_registry_kb),
]

_SCREEN_CONTROL = [
    ("备份关键文件",           _a_backup),
    ("停止 MMPC",             _a_stop_mmpc),
    ("终止 ScreenRender",     _a_kill_screenrender),
    ("终止 ScreenRender_Y",   _a_kill_screenrender_y),
    ("终止 MultiClient",      _a_kill_multiclient),
    ("删除控屏文件",           _a_delete_screen_files),
]

_BLACK_SCREEN = [
    ("备份关键文件",           _a_backup),
    ("停止 MMPC",             _a_stop_mmpc),
    ("终止 BlackSlient",      _a_kill_blacksilent),
    ("删除 BlackSlient",      _a_delete_blacksilent_file),
]

# 一键全部（去重：MMPC 只停一次，备份只做一次，相同进程只杀一次）
_ALL = [
    ("备份关键文件",           _a_backup),
    ("停止 MMPC",             _a_stop_mmpc),
    ("终止学生端进程",         _a_kill_student),
    ("终止 DeviceControl",    _a_kill_device_control),
    ("停止 OeNetLimit",       _a_stop_oenetlimit),
    ("停止 ProcFireWall",     _a_stop_procfirewall),
    ("停删 easyusbflt",       _a_stop_delete_easyusbflt),
    ("删除 easyusbflt.sys",   _a_delete_easyusbflt_sys),
    ("清理注册表 easyusbflt", _a_clean_registry_usb),
    ("终止 BlackSlient",      _a_kill_blacksilent),
    ("停删 KbFilter",         _a_stop_delete_kbfilter),
    ("停删 ProcFireWall",     _a_stop_delete_procfirewall),
    ("删除键盘驱动文件",       _a_delete_kb_files),
    ("清理注册表 KbFilter",   _a_clean_registry_kb),
    ("终止 ScreenRender",     _a_kill_screenrender),
    ("终止 ScreenRender_Y",   _a_kill_screenrender_y),
    ("终止 MultiClient",      _a_kill_multiclient),
    ("删除控屏文件",           _a_delete_screen_files),
    ("删除 BlackSlient",      _a_delete_blacksilent_file),
    ("停删 FbdATS",           _a_stop_delete_fbdats),
]


# ══════════════════════════════════════════════════════════
# 对外接口
# ══════════════════════════════════════════════════════════

def _run_items(items, label, logout, on_output):
    _emit(f"开始: {label}", on_output)
    for desc, fn in items:
        fn(on_output)
    _emit(f"完成: {label}", on_output)
    _logout_if_needed(logout, on_output)


def network_block(logout: bool = False, on_output=None) -> None:
    _run_items(_NETWORK, "解锁网络", logout, on_output)


def usb_block(logout: bool = False, on_output=None) -> None:
    _run_items(_USB, "解锁 USB", logout, on_output)


def keyboard_block(logout: bool = False, on_output=None) -> None:
    _run_items(_KEYBOARD, "解锁键盘鼠标", logout, on_output)


def screen_control_block(logout: bool = False, on_output=None) -> None:
    _run_items(_SCREEN_CONTROL, "解除控屏", logout, on_output)


def black_screen_block(logout: bool = False, on_output=None) -> None:
    _run_items(_BLACK_SCREEN, "移除黑屏肃静", logout, on_output)


def unlock_all(logout: bool = False, on_output=None) -> None:
    _run_items(_ALL, "一键脱离管控", logout, on_output)


# ══════════════════════════════════════════════════════════
# Toast 包装（供 UI 页面直接调用）
# ══════════════════════════════════════════════════════════

from src.core.bridge import show_snack


def network_unlock(logout=False, on_output=None):
    show_snack("解锁网络中...")
    network_block(logout=logout, on_output=on_output)
    show_snack("网络已解锁")


def usb_unlock(logout=False, on_output=None):
    show_snack("解锁USB中...")
    usb_block(logout=logout, on_output=on_output)
    show_snack("USB 已解锁")


def keyboard_unlock(logout=False, on_output=None):
    show_snack("解锁键盘鼠标中...")
    keyboard_block(logout=logout, on_output=on_output)
    show_snack("键盘鼠标已解锁")


def screen_control_unlock(logout=False, on_output=None):
    show_snack("解除控屏...")
    screen_control_block(logout=logout, on_output=on_output)
    show_snack("控屏已解除")


def black_screen_unlock(logout=False, on_output=None):
    show_snack("移除黑屏肃静...")
    black_screen_block(logout=logout, on_output=on_output)
    show_snack("黑屏肃静已移除")
