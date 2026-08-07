# src/utils/system/logger.py
# 工具箱日志系统 — 从启动到关闭全生命周期记录
# 设计要点：零外部依赖、UAC 提权前即可使用、线程安全

import os
import sys
import time
import threading
import traceback

# 日志文件路径，pre_init() 或 init() 中设置
_log_path: str | None = None
_log_lock = threading.Lock()
_initialized = False


def _timestamp() -> str:
    """返回格式化的时间戳"""
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())


def _ensure_dir() -> None:
    """确保日志目录存在"""
    if _log_path:
        d = os.path.dirname(_log_path)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)


_SESSION_MARKER_NAME = "ToolKit.startup.marker"


def _marker_file(log_folder: str) -> str:
    return os.path.join(log_folder, _SESSION_MARKER_NAME)


def _find_marker(log_folder: str) -> str | None:
    marker_path = _marker_file(log_folder)
    return marker_path if os.path.exists(marker_path) else None


def _write_session_marker(log_folder: str, log_path: str) -> None:
    try:
        marker_path = _marker_file(log_folder)
        existing = []
        if os.path.exists(marker_path):
            if time.time() - os.path.getmtime(marker_path) > _RECENT_WINDOW:
                existing = []
            else:
                with open(marker_path, "r", encoding="utf-8") as f:
                    existing = [line.strip() for line in f if line.strip()]
        if log_path not in existing:
            existing.append(log_path)
        with open(marker_path, "w", encoding="utf-8") as f:
            f.write("\n".join(existing))
    except Exception:
        pass


def _read_session_marker(log_folder: str) -> list[str] | None:
    marker_path = _marker_file(log_folder)
    if not os.path.exists(marker_path):
        return None
    if time.time() - os.path.getmtime(marker_path) > _RECENT_WINDOW:
        return None
    try:
        with open(marker_path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f if line.strip()]
        return lines if lines else None
    except Exception:
        return None


def _remove_session_marker(log_folder: str) -> None:
    try:
        marker_path = _marker_file(log_folder)
        if os.path.exists(marker_path):
            os.remove(marker_path)
    except Exception:
        pass


def _write(level: str, msg: str) -> None:
    """线程安全地写入一行日志"""
    global _log_path
    line = f"[{_timestamp()}] [{level}] {msg}\n"
    # 如果还没初始化，退化为 stderr
    if not _log_path:
        sys.stderr.write(line)
        sys.stderr.flush()
        return
    with _log_lock:
        try:
            with open(_log_path, "a", encoding="utf-8") as f:
                f.write(line)
                f.flush()
        except Exception:
            pass



def _log_filename() -> str:
    """生成带时间戳的日志文件名，如 ToolKit_2026-08-06_19-30-00.log"""
    return time.strftime("ToolKit_%Y-%m-%d_%H-%M-%S.log", time.localtime())


def pre_init(log_dir: str) -> None:
    """
    预初始化日志（UAC 提权前调用，提权后的管理员进程也会再调一次）。
    直接写一个带时间戳的日志文件，避免在提权阶段把日志追加到旧的客户端日志文件。
    提权完成后，正式 init() 会找到当前启动的最近日志文件并继续追加。
    """
    global _log_path, _initialized
    _log_path = os.path.join(log_dir, "log", _log_filename())
    _initialized = True
    try:
        _ensure_dir()
        _write_session_marker(os.path.join(log_dir, "log"), _log_path)
    except Exception:
        pass
    info(f"========== ToolKit 启动 ==========")
    info(f"Python: {sys.executable}")
    info(f"版本: {sys.version}")
    info(f"工作目录: {os.getcwd()}")
    info(f"命令行: {' '.join(sys.argv)}")
    info(f"是否管理员: {_is_admin_raw()}")


def _select_main_log_path(log_folder: str, recent: list[str]) -> tuple[str, list[str]]:
    marker_logs = _read_session_marker(log_folder) or []
    if marker_logs:
        current_paths: list[tuple[float, str]] = []
        now = time.time()
        for path in marker_logs:
            if not os.path.exists(path):
                continue
            try:
                m = os.path.getmtime(path)
            except Exception:
                continue
            if now - m <= _RECENT_WINDOW:
                current_paths.append((m, path))
        if current_paths:
            current_paths.sort(key=lambda x: x[0], reverse=True)
            main_path = current_paths[0][1]
            return main_path, [p for _, p in current_paths[1:]]
    # 如果 marker 无效或过期，则不合并旧日志，直接使用最新最近文件作为本次启动主日志
    if recent:
        return recent[0], []
    return os.path.join(log_folder, _log_filename()), []


def _remove_session_marker(log_folder: str) -> None:
    try:
        marker_path = _find_marker(log_folder)
        if marker_path and os.path.exists(marker_path):
            os.remove(marker_path)
    except Exception:
        pass


def init(log_dir: str) -> None:
    """
    正式初始化（UI 启动后，管理员进程调用）。

    核心思路：不新建日志文件，而是扫描日志目录，用**文件系统 mtime**（不看文件名）
    找到"本次启动"产生的最近日志文件，并把其余同次启动的旧日志合并进这个文件。
    """
    global _log_path, _initialized
    log_folder = os.path.join(log_dir, "log")
    os.makedirs(log_folder, exist_ok=True)

    recent = _recent_logs(log_folder)
    main_path, merge_paths = _select_main_log_path(log_folder, recent)
    for t in merge_paths:
        _append_file_into(main_path, t)
    _remove_session_marker(log_folder)
    _log_path = main_path

    _initialized = True
    _ensure_dir()
    info("日志系统正式初始化完成")


def _recent_logs(log_folder: str):
    """
    返回 mtime 在最近 _RECENT_WINDOW 秒内被修改过的所有 .log 文件路径，
    按 mtime 从新到旧排序。只看文件系统时间、不看文件名，
    避免把很久以前的旧日志误当作本次启动。
    """
    import glob

    now = time.time()
    recent = []
    for f in glob.glob(os.path.join(log_folder, "*.log")):
        try:
            m = os.path.getmtime(f)
        except Exception:
            continue
        if now - m <= _RECENT_WINDOW:
            recent.append((m, f))
    recent.sort(key=lambda x: x[0], reverse=True)  # 新的在前
    return [f for _, f in recent]


def _append_file_into(target_path: str, src_path: str) -> None:
    """把 src 文件内容追加到 target 文件末尾，然后删除 src"""
    try:
        with open(src_path, "r", encoding="utf-8") as f:
            content = f.read()
        if content:
            with open(target_path, "a", encoding="utf-8") as tf:
                if not content.endswith("\n"):
                    content += "\n"
                tf.write(content)
        os.remove(src_path)
    except Exception:
        pass


# 判定某个日志文件是否为"本次启动刚写入"的时间窗（秒）。
# 提权前后进程间隔通常仅 1~2 秒，窗口取 120 秒足够覆盖正常及较慢的启动。
_RECENT_WINDOW = 120


def _is_admin_raw() -> bool:
    """原始的管理员检测（不依赖任何模块）"""
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


# ---- 公开 API ----

def info(msg: str) -> None:
    _write("INFO", msg)


def warn(msg: str) -> None:
    _write("WARN", msg)


def error(msg: str) -> None:
    _write("ERROR", msg)


def exception(msg: str = "") -> None:
    """记录异常，附带完整 traceback"""
    tb = traceback.format_exc().strip()
    if msg:
        _write("ERROR", f"{msg}\n{tb}")
    else:
        _write("ERROR", tb)


def debug(msg: str) -> None:
    _write("DEBUG", msg)


def get_log_path() -> str | None:
    """返回当前日志文件路径，若日志未初始化则返回 None。"""
    return _log_path