# src/utils/process.py
# 进程原生控制与查询 —— 基于 psutil（Windows 底层 Win32 API 的封装）+ 原生 API
# 统一提供进程的枚举、路径、状态、挂起/恢复、终止等操作，
# 不再依赖 taskkill 子进程（避免打包为无控制台 exe 时闪现黑框）

import psutil

# ---- 进程枚举 / 查询 ----

def get_program_path(program_name) -> str | None:
    """获取指定名称进程的完整路径，未找到返回 None"""
    for proc in psutil.process_iter(["pid", "name", "exe"]):
        try:
            if proc.info["name"] == program_name:
                return proc.info["exe"]
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return None


def is_process_running(process_name) -> bool:
    """检测指定名称的进程是否正在运行"""
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] == process_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return False


def get_proc_pid(name) -> int | None:
    """根据进程名获取 pid，未找到返回 None"""
    try:
        for proc in psutil.process_iter(["pid", "name"]):
            try:
                if proc.info["name"] == name:
                    return proc.info["pid"]
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
    except Exception:
        pass
    return None


def is_process_suspended(process_name) -> bool:
    """检测指定名称的进程是否处于挂起（暂停）状态"""
    try:
        for process in psutil.process_iter(["pid", "name", "status"]):
            if process.info["name"] == process_name:
                return process.info["status"] == psutil.STATUS_STOPPED
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
    return False


# ---- 挂起 / 恢复 ----

def suspend_process(process_name) -> str | bool:
    """挂起指定名称的所有进程。
    返回 True=成功；字符串表示失败原因（进程未找到 / 权限不足）。"""
    from src.utils.logger import debug as logger_debug
    try:
        found = False
        for process in psutil.process_iter(["pid", "name"]):
            if process.info["name"] == process_name:
                found = True
                pid = process.info["pid"]
                try:
                    psutil.Process(pid).suspend()
                    logger_debug(f"挂起进程 {process_name} (PID {pid})")
                except psutil.AccessDenied:
                    return "挂起进程失败（权限不足）"
        if not found:
            logger_debug(f"尝试挂起的进程未找到: {process_name}")
            return f"尝试挂起的进程未找到: {process_name}"
        return True
    except Exception as e:
        logger_debug(f"挂起进程异常: {e}")
        return "挂起进程失败"


def resume_process(process_name) -> str | bool:
    """恢复指定名称的所有进程。返回 True=成功；字符串表示失败原因。"""
    from src.utils.logger import debug as logger_debug
    try:
        found = False
        for process in psutil.process_iter(["pid", "name"]):
            if process.info["name"] == process_name:
                found = True
                pid = process.info["pid"]
                try:
                    psutil.Process(pid).resume()
                    logger_debug(f"恢复进程 {process_name} (PID {pid})")
                except psutil.AccessDenied:
                    return "恢复进程失败（权限不足）"
        if not found:
            logger_debug(f"尝试恢复的进程未找到: {process_name}")
            return f"尝试恢复的进程未找到: {process_name}"
        return True
    except Exception as e:
        logger_debug(f"恢复进程异常: {e}")
        return "恢复进程失败"


def suspend_resume_process(process_name, option) -> str | bool:
    """挂起/恢复进程（兼容旧接口：option='suspend'/'resume'）"""
    if option == "suspend":
        return suspend_process(process_name)
    return resume_process(process_name)


# ---- 终止进程（替代 taskkill，无黑框） ----

def kill_process(process_name) -> bool:
    """终止指定名称的所有进程（含子进程树），无黑框、无子进程。
    返回 True 表示所有找到的进程均已发出终止请求。"""
    from src.utils.logger import debug
    killed_any = False
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            if proc.info["name"] == process_name:
                killed_any = True
                try:
                    proc.terminate()          # 先优雅终止
                except psutil.AccessDenied:
                    proc.kill()               # 权限不足则强制
                debug(f"已终止进程 {process_name} (PID {proc.info['pid']})")
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            continue
    return killed_any


def kill_process_by_pid(pid: int) -> bool:
    """按 PID 终止进程（含子进程树），无黑框。
    返回 True 表示已发出终止请求；进程不存在返回 False。"""
    from src.utils.logger import debug
    try:
        proc = psutil.Process(pid)
        children = proc.children(recursive=True)
        for child in children:
            try:
                child.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                try:
                    child.kill()
                except Exception:
                    pass
        try:
            proc.terminate()
        except psutil.AccessDenied:
            proc.kill()
        debug(f"已按 PID 终止进程 {pid}")
        return True
    except psutil.NoSuchProcess:
        return False
    except Exception as e:
        debug(f"按 PID 终止进程失败: {e}")
        return False