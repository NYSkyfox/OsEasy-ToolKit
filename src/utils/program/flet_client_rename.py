# src/utils/program/flet_client_rename.py
# flet 桌面客户端进程改名（规避部分设备的进程名黑名单）
#
# 背景：flet 桌面应用运行时，会派生一个独立的 Flutter 渲染进程 flet.exe
# （真正的窗口进程）。部分机房/管控设备有进程名黑名单，flet.exe 会被禁止运行。
#
# 原理：Windows 的进程名 = 可执行文件的文件名，无法在 Python 里运行时改名。
# 因此这里：
#   1. 把打包进来的客户端启动器 flet.exe 复制一份为 CLIENT_EXE_NAME；
#   2. 在 ft.app() 之前 monkeypatch flet_desktop 的定位函数，让它去启动改名后的副本。
# 不改动任何 flet / flet_desktop 源码，全部逻辑在本项目代码内完成。

import os
import shutil

import flet_desktop

# 自定义客户端进程名（在任务管理器里显示的名字）
CLIENT_EXE_NAME = "ToolKitClient.exe"

_ORIG_LOCATE = None
_APPLIED = False


def _renamed_client_path() -> str:
    """把打包的 flet 客户端启动器 flet.exe 复制为 CLIENT_EXE_NAME，返回新路径。

    保留原 flet.exe（flet 内部仍会按原路径查找它，避免触发在线下载），
    只是额外复制一份改名副本用于实际启动。复制的是启动器本身，体积很小。
    """
    src = os.path.join(flet_desktop.__path__[0], "app", "flet", "flet.exe")
    dst = os.path.join(os.path.dirname(src), CLIENT_EXE_NAME)
    if os.path.exists(src) and not os.path.exists(dst):
        try:
            shutil.copy2(src, dst)
        except OSError:
            return src  # 复制失败则退回原名字
    return dst if os.path.exists(dst) else src


def _patched_locate_flet_view(page_url, assets_dir, hidden):
    """调用原始定位逻辑，再把 Windows 客户端启动器换成改名后的副本。"""
    args, flet_env, pid_file = _ORIG_LOCATE(page_url, assets_dir, hidden)
    if os.name == "nt" and args and args[0].lower().endswith("flet.exe"):
        new_exe = _renamed_client_path()
        if new_exe.lower().endswith(CLIENT_EXE_NAME.lower()):
            args = [new_exe] + args[1:]
    return args, flet_env, pid_file


def apply_flet_client_rename():
    """在 ft.app() 之前调用：让 flet 桌面客户端以自定义进程名启动。"""
    global _ORIG_LOCATE, _APPLIED
    if _APPLIED:
        return
    _ORIG_LOCATE = flet_desktop.__locate_and_unpack_flet_view
    flet_desktop.__locate_and_unpack_flet_view = _patched_locate_flet_view
    _APPLIED = True
