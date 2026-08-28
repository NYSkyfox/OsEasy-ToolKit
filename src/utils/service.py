# src/utils/service.py
# Windows 服务原生控制 —— 直接调用服务控制管理器(SCM) API
# 通过 ctypes 调用 advapi32，不依赖 sc.exe 子进程 / pywin32
# 支持：查询状态(运行/停止/不存在)、启动、停止、删除服务

import ctypes
from ctypes import wintypes

# ---- SCM / 服务句柄访问权限 ----
SC_MANAGER_CONNECT = 0x0001
SERVICE_QUERY_STATUS = 0x0004
SERVICE_START = 0x0010
SERVICE_STOP = 0x0020
SERVICE_DELETE = 0x00010000

# ---- 服务状态 ----
SERVICE_STOPPED = 1
SERVICE_START_PENDING = 2
SERVICE_STOP_PENDING = 3
SERVICE_RUNNING = 4

# ---- 控制码 ----
SERVICE_CONTROL_STOP = 0x00000001
# ---- 服务类型 ----
SERVICE_KERNEL_DRIVER = 0x00000001
SERVICE_FILE_SYSTEM_DRIVER = 0x00000002
# ---- 服务接受的控制码 ----
SERVICE_ACCEPT_STOP = 0x00000001

SC_HANDLE = wintypes.HANDLE
_advapi = ctypes.windll.advapi32


def _win_last_error() -> int:
    """获取最近一次 Win32 API 调用的错误码（ctypes.get_last_error 需 use_last_error 才有效，这里直接用 API）"""
    try:
        return ctypes.windll.kernel32.GetLastError()
    except Exception:
        return 0


class SERVICE_STATUS(ctypes.Structure):
    _fields_ = [
        ("dwServiceType", wintypes.DWORD),
        ("dwCurrentState", wintypes.DWORD),
        ("dwControlsAccepted", wintypes.DWORD),
        ("dwWin32ExitCode", wintypes.DWORD),
        ("dwServiceSpecificExitCode", wintypes.DWORD),
        ("dwCheckPoint", wintypes.DWORD),
        ("dwWaitHint", wintypes.DWORD),
    ]


# ---- 声明函数签名（必须在 SERVICE_STATUS 定义之后，避免 64 位句柄截断） ----
_advapi.OpenSCManagerW.restype = SC_HANDLE
_advapi.OpenSCManagerW.argtypes = [wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD]
_advapi.OpenServiceW.restype = SC_HANDLE
_advapi.OpenServiceW.argtypes = [SC_HANDLE, wintypes.LPCWSTR, wintypes.DWORD]
_advapi.CloseServiceHandle.restype = wintypes.BOOL
_advapi.CloseServiceHandle.argtypes = [SC_HANDLE]
_advapi.QueryServiceStatus.restype = wintypes.BOOL
_advapi.QueryServiceStatus.argtypes = [SC_HANDLE, ctypes.POINTER(SERVICE_STATUS)]
_advapi.StartServiceW.restype = wintypes.BOOL
_advapi.StartServiceW.argtypes = [SC_HANDLE, wintypes.DWORD, ctypes.POINTER(ctypes.c_wchar_p)]
_advapi.ControlService.restype = wintypes.BOOL
_advapi.ControlService.argtypes = [SC_HANDLE, wintypes.DWORD, ctypes.POINTER(SERVICE_STATUS)]
_advapi.DeleteService.restype = wintypes.BOOL
_advapi.DeleteService.argtypes = [SC_HANDLE]


def _open_sc_manager() -> SC_HANDLE | None:
    """打开服务控制管理器句柄，失败返回 None"""
    h = _advapi.OpenSCManagerW(None, None, SC_MANAGER_CONNECT)
    return h if h else None


def _open_service(scm: SC_HANDLE, name: str, access: int) -> SC_HANDLE | None:
    """打开指定服务的句柄，失败返回 None"""
    h = _advapi.OpenServiceW(scm, name, access)
    return h if h else None


def service_state(name: str) -> str:
    """查询服务/驱动的状态（不弹任何窗口，无子进程）：
    - "running"  服务存在且运行中
    - "stopped"  服务存在但未运行（含启动/停止中）
    - "missing"  服务不存在（未安装）
    """
    scm = _open_sc_manager()
    if not scm:
        return "missing"
    try:
        hsvc = _open_service(scm, name, SERVICE_QUERY_STATUS)
        if not hsvc:
            return "missing"
        try:
            status = SERVICE_STATUS()
            if not _advapi.QueryServiceStatus(hsvc, ctypes.byref(status)):
                return "missing"
            if status.dwCurrentState in (SERVICE_RUNNING,):
                return "running"
            return "stopped"
        finally:
            _advapi.CloseServiceHandle(hsvc)
    finally:
        _advapi.CloseServiceHandle(scm)


def start_service(name: str) -> bool:
    """启动服务，成功返回 True"""
    scm = _open_sc_manager()
    if not scm:
        return False
    try:
        hsvc = _open_service(scm, name, SERVICE_START)
        if not hsvc:
            return False
        try:
            # 第 2、3 参数仅在传递启动参数时使用，此处启动默认参数
            return bool(_advapi.StartServiceW(hsvc, 0, None))
        finally:
            _advapi.CloseServiceHandle(hsvc)
    finally:
        _advapi.CloseServiceHandle(scm)


def stop_service(name: str) -> bool:
    """停止服务，成功返回 True"""
    ok, _ = stop_service_detailed(name)
    return ok


def stop_service_detailed(name: str) -> tuple[bool, str]:
    """停止服务，返回 (是否成功, 结果描述)。

    对不接受停止控制的内核驱动（返回 1051 ERROR_SERVICE_CANNOT_ACCEPT_CTRL），
    结果描述会明确标注，方便 UI 提示用户改用“强制卸载”。
    """
    scm = _open_sc_manager()
    if not scm:
        return False, "无法打开服务控制管理器"
    try:
        hsvc = _open_service(scm, name, SERVICE_STOP)
        if not hsvc:
            err = _win_last_error()
            return False, f"无法打开服务(错误码 {err})"
        try:
            status = SERVICE_STATUS()
            if _advapi.ControlService(hsvc, SERVICE_CONTROL_STOP, ctypes.byref(status)):
                return True, "已停止"
            err = _win_last_error()
            # 1051: 服务/驱动不接受停止控制码（内核驱动常见）
            if err == 1051:
                return False, "内核驱动不接受停止控制(1051)，请用强制卸载"
            return False, f"停止失败(错误码 {err})"
        finally:
            _advapi.CloseServiceHandle(hsvc)
    finally:
        _advapi.CloseServiceHandle(scm)


def get_service_info(name: str) -> dict:
    """查询服务信息：类型、当前状态、是否接受停止控制。

    返回 {"type": ..., "state": ..., "accepts_stop": bool, "exists": bool}
    type 含义: "kernel_driver"(内核驱动) / "file_system_driver"(文件系统驱动) /
               "win32"(用户态服务) / "unknown"
    """
    scm = _open_sc_manager()
    if not scm:
        return {"exists": False}
    try:
        hsvc = _open_service(scm, name, SERVICE_QUERY_STATUS)
        if not hsvc:
            return {"exists": False}
        try:
            status = SERVICE_STATUS()
            if not _advapi.QueryServiceStatus(hsvc, ctypes.byref(status)):
                return {"exists": False}

            svc_type = status.dwServiceType
            if svc_type & 0x00000008:      # SERVICE_FILE_SYSTEM_DRIVER
                type_name = "file_system_driver"
            elif svc_type & 0x00000001:    # SERVICE_KERNEL_DRIVER
                type_name = "kernel_driver"
            elif svc_type & 0x00000010:    # SERVICE_WIN32_OWN_PROCESS
                type_name = "win32"
            else:
                type_name = "unknown"

            return {
                "exists": True,
                "type": type_name,
                "state": status.dwCurrentState,
                "accepts_stop": bool(status.dwControlsAccepted & SERVICE_ACCEPT_STOP),
            }
        finally:
            _advapi.CloseServiceHandle(hsvc)
    finally:
        _advapi.CloseServiceHandle(scm)


def delete_service(name: str) -> bool:
    """删除服务（需先停止），成功返回 True"""
    scm = _open_sc_manager()
    if not scm:
        return False
    try:
        hsvc = _open_service(scm, name, SERVICE_DELETE)
        if not hsvc:
            return False
        try:
            return bool(_advapi.DeleteService(hsvc))
        finally:
            _advapi.CloseServiceHandle(hsvc)
    finally:
        _advapi.CloseServiceHandle(scm)