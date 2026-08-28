# src/modules/service_manager.py
# 服务管理（MMPC 根服务等）

import os
import time

from src.core.settings import toolkit_cfg
from src.utils.cmd import run_sigle_cmd
from src.modules.student_detector import detect_student_version
from src.utils.service import (
    service_state as _svc_state,
    start_service as _svc_start,
    stop_service as _svc_stop,
    stop_service_detailed as _svc_stop_detailed,
    delete_service as _svc_delete,
    get_service_info as _svc_info,
)

# 设备过滤驱动 → 对应的设备类 GUID（用于清理注册表过滤项）
# 与 unlock_native.py 中的定义保持一致
_DRIVER_FILTER_GUIDS = {
    "{4D36E96B-E325-11CE-BFC1-08002BE10318}": ["KbFilter"],   # 键盘
    "{4D36E96F-E325-11CE-BFC1-08002BE10318}": ["KbFilter"],   # 鼠标
    "{36FC9E60-C465-11CF-8056-444553540000}": ["easyusbflt"], # USB
    "{745a17a0-74d3-11d0-b6fe-00a0c90f57da}": ["easyusbflt", "KbFilter"],  # HID
}


def auto_stop_mmpc_if_needed():
    """v109+ 的学生端会启动 MMPC 根服务来保护进程，
    此函数检测版本并在需要时自动关闭该服务。"""
    if not toolkit_cfg.student_version:
        _ = detect_student_version()

    if toolkit_cfg.student_version >= 109:
        mpStatus = check_mmpc_status()
        if mpStatus:
            _svc_stop("MMPC")
            time.sleep(1)


def get_mmpc_cmd(stop: bool = True) -> str:
    """返回 MMPC 根服务的控制命令字符串（用于嵌入 bat 脚本）。
    v109+ 的学生端引用了该保护服务，需先停止才能击杀。
    stop=True → "sc stop MMPC", stop=False → "sc start MMPC"。
    非 v109+ 版本返回空字符串。"""

    if not toolkit_cfg.student_version:
        _ = detect_student_version()

    if toolkit_cfg.student_version >= 109:
        if stop:
            return "sc stop MMPC\n"
        else:
            return "sc start MMPC\n"
    return ""


def query_service_state(name: str) -> str:
    """查询服务/驱动的状态，返回三态字符串：
    - "running"  服务存在且运行中
    - "stopped"  服务存在但未运行
    - "missing"  服务不存在（未安装）
    使用原生 SCM API（ctypes），不弹窗口、无子进程。"""
    try:
        return _svc_state(name)
    except Exception:
        return "missing"


# 供其他模块直接使用的原生服务控制封装（避免重复 import win_service）
def start_service(name: str) -> bool:
    """启动服务"""
    return _svc_start(name)


def stop_service(name: str) -> bool:
    """停止服务"""
    return _svc_stop(name)


def stop_service_detailed(name: str) -> tuple[bool, str]:
    """停止服务，返回 (是否成功, 结果描述)"""
    return _svc_stop_detailed(name)


def get_service_info(name: str) -> dict:
    """查询服务类型/状态/是否接受停止控制"""
    return _svc_info(name)


def force_stop_driver(name: str, clean_filters: bool = True) -> list[str]:
    """强制卸载内核驱动（不重启）：
    1. 尝试普通停止
    2. 删除驱动服务注册
    3. （可选）清理设备类注册表 UpperFilters/LowerFilters 过滤项

    返回操作日志列表。适用于 easyusbflt / KbFilter 等不接受停止控制的设备过滤驱动。
    """
    logs = []
    try:
        info = _svc_info(name)
        if not info.get("exists"):
            logs.append(f"驱动 {name} 不存在，跳过")
            return logs
        if info.get("type") not in ("kernel_driver", "file_system_driver"):
            logs.append(f"{name} 不是内核驱动，请使用普通停止")
            return logs
    except Exception as e:
        logs.append(f"查询驱动信息失败: {e}")

    # 1) 普通停止（能停则停）
    ok, msg = _svc_stop_detailed(name)
    if ok:
        logs.append(f"已停止驱动 {name}")
    else:
        logs.append(f"普通停止失败：{msg}")

    # 2) 删除驱动服务注册
    try:
        if _svc_delete(name):
            logs.append(f"已删除驱动服务 {name}（重启后彻底卸载内核模块）")
        else:
            logs.append(f"删除驱动服务 {name} 失败（可能仍在运行或被占用）")
    except Exception as e:
        logs.append(f"删除驱动服务异常: {e}")

    # 3) 清理设备类过滤注册表
    if clean_filters:
        try:
            from src.modules.unlock_native import _remove_filter_from_class
            for guid, targets in _DRIVER_FILTER_GUIDS.items():
                if name.lower() not in [t.lower() for t in targets]:
                    continue
                for line in _remove_filter_from_class(guid, name):
                    logs.append(line)
        except Exception as e:
            logs.append(f"清理过滤注册表异常: {e}")

    return logs


def delete_service(name: str) -> bool:
    """删除服务"""
    return _svc_delete(name)


def check_service_status(name: str) -> bool:
    """检查 Windows 服务/驱动是否正在运行。存在且运行中返回 True。"""
    return query_service_state(name) == "running"


def check_mmpc_status() -> bool:
    """检查MMPC根服务状态
    返回True/False"""
    return check_service_status("MMPC")


def _kill_student_process() -> None:
    """结束学生端进程（兼容新旧版本进程名），忽略未找到的情况"""
    from src.utils.logger import debug, exception
    from src.utils.process import kill_process
    for exe_name in ("Student.exe", "MmcStudent.exe"):
        try:
            kill_process(exe_name)
            debug(f"已结束学生端进程: {exe_name}")
        except Exception:
            exception(f"结束学生端进程失败: {exe_name}")


def handle_start_student_client(*e) -> None:
    # 先结束学生端进程，再重新启动
    _kill_student_process()
    os.startfile(f"{toolkit_cfg.oseasy_path}{toolkit_cfg.student_exe_name}")