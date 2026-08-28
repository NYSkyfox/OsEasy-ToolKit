# src/utils/aumid.py
# 注册 AppUserModelID (AUMID)：在开始菜单创建带 AUMID 的快捷方式
# 用途：让 Toast 通知的来源正确显示为应用名/图标（纯 ctypes COM，零依赖）

import os
import sys
import ctypes
from ctypes import (
    Structure, POINTER, byref, c_void_p, c_ulong, c_ushort, c_ubyte,
    c_long, c_wchar_p, c_int, cast, CFUNCTYPE, create_unicode_buffer,
)

_ole32 = ctypes.windll.ole32
HRESULT = c_long

# ---------- GUID ----------
class GUID(Structure):
    _fields_ = [
        ("Data1", c_ulong),
        ("Data2", c_ushort),
        ("Data3", c_ushort),
        ("Data4", c_ubyte * 8),
    ]

def _guid(s: str) -> GUID:
    """解析 'XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX' 形式的 GUID"""
    s = s.strip("{}")
    return GUID(
        int(s[0:8], 16),
        int(s[9:13], 16),
        int(s[14:18], 16),
        (c_ubyte * 8).from_buffer_copy(bytes.fromhex(s[19:23] + s[24:])),
    )

# 常用 GUID
CLSID_ShellLink = _guid("00021401-0000-0000-C000-000000000046")
IID_IShellLinkW = _guid("000214F9-0000-0000-C000-000000000046")
IID_IPersistFile = _guid("0000010B-0000-0000-C000-000000000046")
IID_IPropertyStore = _guid("886D8EEB-8CF2-4446-8D02-CDBA1DBDCF99")
# PKEY_AppUserModel_ID 的 fmtid / pid
PKEY_AppUserModel_ID_fmtid = _guid("9F4C2855-9F79-4B39-A8D0-E1D42DE1D5F3")
PKEY_AppUserModel_ID_pid = 5

# ---------- IPropertyStore 相关结构 ----------
class PROPERTYKEY(Structure):
    _fields_ = [("fmtid", GUID), ("pid", c_ulong)]

class PROPVARIANT(Structure):
    # 仅需承载 VT_LPWSTR（vt 头 + 指针，8 字节偏移）
    _fields_ = [
        ("vt", c_ushort),
        ("wReserved1", c_ushort),
        ("wReserved2", c_ushort),
        ("wReserved3", c_ushort),
        ("pointerValue", c_void_p),
    ]


# ---------- 轻量 COM 调用助手 ----------
class _Com:
    """按虚表索引调用 COM 接口方法（this 指针自动传入）"""

    def __init__(self, ptr: int):
        self._ptr = ptr

    def _vtable(self):
        vtbl_addr = cast(self._ptr, POINTER(c_void_p)).contents.value
        return cast(vtbl_addr, POINTER(c_void_p))

    def _call(self, index, restype, argtypes, args):
        fn = cast(self._vtable()[index], CFUNCTYPE(restype, c_void_p, *argtypes))
        return fn(self._ptr, *args)

    def query_interface(self, iid: GUID) -> "_Com":
        out = c_void_p()
        hr = self._call(0, HRESULT, [POINTER(GUID), POINTER(c_void_p)],
                        [byref(iid), byref(out)])
        if hr != 0:
            raise OSError(f"QueryInterface 失败: HRESULT=0x{hr & 0xFFFFFFFF:08X}")
        return _Com(out.value)


# ---------- 主要逻辑 ----------
def register_aumid(
    app_id: str = "OsEasy-ToolKit",
    exe: str | None = None,
    args: str = "",
    workdir: str | None = None,
    icon: str = "",
    lnk_path: str | None = None,
) -> str:
    """创建/更新开始菜单快捷方式并设置 AUMID，返回快捷方式路径。

    :param app_id: AppUserModelID（Toast 来源标识）
    :param exe: 快捷方式指向的可执行文件（默认当前 python.exe）
    :param args: 命令行参数（如 'main.py'）
    :param workdir: 工作目录
    :param icon: 图标路径（.ico）
    :param lnk_path: .lnk 保存路径（默认开始菜单 Programs 下）
    """
    from src.utils.logger import debug

    if exe is None:
        exe = sys.executable
    if workdir is None:
        workdir = os.path.dirname(exe)
    if lnk_path is None:
        start_menu = os.path.join(
            os.environ.get("APPDATA", ""),
            "Microsoft", "Windows", "Start Menu", "Programs",
        )
        os.makedirs(start_menu, exist_ok=True)
        lnk_path = os.path.join(start_menu, f"{app_id}.lnk")

    _ole32.CoInitializeEx.argtypes = [c_void_p, c_ulong]
    _ole32.CoInitializeEx.restype = HRESULT
    _ole32.CoCreateInstance.argtypes = [POINTER(GUID), c_void_p, c_ulong,
                                        POINTER(GUID), POINTER(c_void_p)]
    _ole32.CoCreateInstance.restype = HRESULT
    _ole32.CoUninitialize.argtypes = []
    _ole32.CoUninitialize.restype = None

    _ole32.CoInitializeEx(None, 0)  # COINIT_MULTITHREADED
    try:
        # 1) 创建 IShellLinkW 并设置属性
        obj = c_void_p()
        hr = _ole32.CoCreateInstance(byref(CLSID_ShellLink), None, 1,
                                     byref(IID_IShellLinkW), byref(obj))
        if hr != 0:
            raise OSError(f"CoCreateInstance 失败: HRESULT=0x{hr & 0xFFFFFFFF:08X}")
        sl = _Com(obj.value)

        # IShellLinkW 虚表索引：7=SetDescription 9=SetWorkingDirectory
        # 11=SetArguments 17=SetIconLocation 20=SetPath
        sl._call(7, HRESULT, [c_wchar_p], [app_id])                    # SetDescription
        sl._call(9, HRESULT, [c_wchar_p], [workdir])                   # SetWorkingDirectory
        if args:
            sl._call(11, HRESULT, [c_wchar_p], [args])                 # SetArguments
        if icon:
            sl._call(17, HRESULT, [c_wchar_p, c_int], [icon, 0])       # SetIconLocation
        sl._call(20, HRESULT, [c_wchar_p], [exe])                      # SetPath

        # 2) IPersistFile::Save 写出 .lnk（索引 6=Save）
        pf = sl.query_interface(IID_IPersistFile)
        hr = pf._call(6, HRESULT, [c_wchar_p, c_int], [lnk_path, 1])
        if hr != 0:
            raise OSError(f"保存快捷方式失败: HRESULT=0x{hr & 0xFFFFFFFF:08X}")

        # 3) IPropertyStore 设置 System.AppUserModel.ID（6=SetValue 7=Commit）
        store = sl.query_interface(IID_IPropertyStore)
        key = PROPERTYKEY(fmtid=PKEY_AppUserModel_ID_fmtid, pid=PKEY_AppUserModel_ID_pid)
        pv = PROPVARIANT()
        pv.vt = 31  # VT_LPWSTR
        buf = create_unicode_buffer(app_id)
        pv.pointerValue = cast(buf, c_void_p)
        hr = store._call(6, HRESULT, [POINTER(PROPERTYKEY), POINTER(PROPVARIANT)],
                         [byref(key), byref(pv)])
        if hr != 0:
            raise OSError(f"设置 AUMID 失败: HRESULT=0x{hr & 0xFFFFFFFF:08X}")
        store._call(7, HRESULT, [], [])  # Commit

        debug(f"AUMID 注册完成: {lnk_path} (AppUserModelID={app_id})")
        return lnk_path
    finally:
        _ole32.CoUninitialize()


if __name__ == "__main__":
    _root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    _script = os.path.join(_root, "main.py")
    _logo = os.path.join(_root, "logo.ico")
    register_aumid(
        app_id="OsEasy-ToolKit",
        args=f'"{_script}"',
        workdir=_root,
        icon=_logo,
    )
    print("OK: AUMID 注册完成")
