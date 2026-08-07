# src/modules/service_manager.py
# 服务管理与版本检测

import os
import time

import psutil

from src.core.runtime_config import toolkit_cfg
from src.core.helpers import file_exists, run_sigle_cmd
from src.modules.process_manager import utils


def detect_student_path() -> tuple[str, str] | tuple[bool, None]:
    """检测学生端安装路径。优先从运行中进程获取（Student.exe/MmcStudent.exe），
    若未运行则回退读取配置文件中上次保存的路径。"""
    Spath = utils.get_program_path("Student.exe")
    Spath_2 = utils.get_program_path("MmcStudent.exe")
    # v10.9.1 学生端改名为 MmcStudent.exe

    if Spath is None and Spath_2 is None:
        print("[DEBUG] > 未找到运行中的学生端")

        isModed = toolkit_cfg.get_config_key_data("studentPath_have_been_modified")
        print(f"[DEBUG] 配置文件 > 学生端路径是否被修改：{isModed}")
        if not isModed:
            return False, None

        toolkit_cfg.oseasypath_have_been_modified = True

        toolkit_cfg.oseasy_path = toolkit_cfg.get_config_key_data("studentPath")
        toolkit_cfg.student_exe_name = toolkit_cfg.get_config_key_data("studentExeName")

        print(f"[DEBUG] 配置文件 > 学生端路径为：{toolkit_cfg.oseasy_path}")
        print(f"[DEBUG] 配置文件 > 学生端进程名为：{toolkit_cfg.student_exe_name}")

        toolkit_cfg.set_config_key_data("studentPath", toolkit_cfg.oseasy_path)
        toolkit_cfg.set_config_key_data("studentExeName", toolkit_cfg.student_exe_name)

        return toolkit_cfg.oseasy_path, toolkit_cfg.student_exe_name

    if Spath_2:
        Spath = Spath_2
        exe_name = "MmcStudent.exe"
    else:
        exe_name = "Student.exe"

    Spath = str(Spath).replace("/", "\\").removesuffix(exe_name)

    toolkit_cfg.oseasypath_have_been_modified = True
    toolkit_cfg.oseasy_path = Spath
    toolkit_cfg.student_exe_name = exe_name

    print(f"[DEBUG] 学生端路径为：{toolkit_cfg.oseasy_path}")
    print(f"[DEBUG] 学生端进程名为：{toolkit_cfg.student_exe_name}")

    toolkit_cfg.set_config_key_data("studentPath", toolkit_cfg.oseasy_path)
    toolkit_cfg.set_config_key_data("studentExeName", toolkit_cfg.student_exe_name)
    toolkit_cfg.set_config_key_data("studentPath_have_been_modified", True)

    return toolkit_cfg.oseasy_path, toolkit_cfg.student_exe_name


def detect_student_version() -> int:
    """通过检测特征文件推断学生端版本。
    不同版本附带不同的可执行文件：
    - v10.9.x → LissHelper.exe
    - v10.8.x → MultiClient.exe
    - v10.5.x → MouseKeyBoardControl.exe"""
    from src.utils.system.logger import debug

    if not toolkit_cfg.oseasypath_have_been_modified:
        _, _ = detect_student_path()

    versions = {
        109: f"{toolkit_cfg.oseasy_path}LissHelper.exe",
        108: f"{toolkit_cfg.oseasy_path}MultiClient.exe",
        105: f"{toolkit_cfg.oseasy_path}MouseKeyBoradControl.exe",
    }

    for version, path in versions.items():
        if file_exists(path):
            debug(f"学生端版本检测: v{version // 10}.{version % 10}")
            toolkit_cfg.student_version = version
            toolkit_cfg.set_config_key_data("studentClientVer", version)
            return toolkit_cfg.student_version

    debug("学生端版本检测: 超出检测范围或未安装")
    toolkit_cfg.student_version = 0
    return toolkit_cfg.student_version


def auto_stop_mmpc_if_needed():
    """v109+ 的学生端会启动 MMPC 根服务来保护进程，
    此函数检测版本并在需要时自动关闭该服务。"""
    if not toolkit_cfg.student_version:
        _ = detect_student_version()

    if toolkit_cfg.student_version >= 109:
        mpStatus = check_mmpc_status()
        if mpStatus:
            run_sigle_cmd("sc stop MMPC")
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


def check_mmpc_status() -> bool:
    """检查MMPC根服务状态
    返回True/False"""
    name = "MMPC"
    service = None
    try:
        service = psutil.win_service_get(name)
        service = service.as_dict()
    except Exception as ex:
        return False

    if service and service["status"] == "running":
        return True
    else:
        return False


def handle_start_student_client(*e) -> None:
    os.startfile(f"{toolkit_cfg.oseasy_path}{toolkit_cfg.student_exe_name}")