# src/modules/student_detector.py
# 学生端检测：路径定位 + 版本识别

import json
import re

from src.core.settings import toolkit_cfg
from src.utils.fs import file_exists
from src.utils.process import get_program_path


def detect_student_path() -> tuple[str, str] | tuple[bool, None]:
    """检测学生端安装路径。优先从运行中进程获取（Student.exe/MmcStudent.exe），
    若未运行则回退读取配置文件中上次保存的路径。"""
    Spath = get_program_path("Student.exe")
    Spath_2 = get_program_path("MmcStudent.exe")
    # v10.9.5 学生端改名为 MmcStudent.exe

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


def read_version_file() -> str:
    """读取学生端安装目录下的 version 文件，返回精确版本字符串（如 "V10.9.1.5145"）。
    文件不存在、格式不合法或解析失败时返回空字符串。"""
    from src.utils.logger import debug
    try:
        vpath = f"{toolkit_cfg.oseasy_path}version"
        if not file_exists(vpath):
            return ""
        with open(vpath, "r", encoding="utf-8") as f:
            raw = f.read().strip()
        data = json.loads(raw)
        version = str(data.get("version", "")).strip()
        if version.startswith("V"):
            version = version[1:]
        debug(f"学生端版本文件: {raw} → {version}")
        return version
    except Exception:
        return ""


def _parse_version_tier(version_str: str) -> int:
    """将版本字符串（如 "10.9.1.5145"）转换为档位整数（如 105/108/109）。
    解析失败返回 0。"""
    m = re.match(r"(\d+)\.(\d+)", version_str or "")
    if not m:
        return 0
    return int(m.group(1)) * 10 + int(m.group(2))


def detect_student_version() -> int:
    """检测学生端版本档位。

    优先读取安装目录下的 version 文件（内容形如 {"version":"V10.9.1.5145"}），
    得到精确版本号并映射为档位（105/108/109）；
    若该文件不存在或解析失败，则回退到按特征文件推断：
    - v10.9.x → LissHelper.exe
    - v10.8.x → MultiClient.exe
    - v10.5.x → MouseKeyBoardControl.exe

    返回档位整数，无法识别时返回 0。"""
    from src.utils.logger import debug

    if not toolkit_cfg.oseasypath_have_been_modified:
        _, _ = detect_student_path()

    version_str = read_version_file()
    if version_str:
        tier = _parse_version_tier(version_str)
        if tier:
            debug(f"学生端版本检测(version文件): v{version_str} → {tier}")
            toolkit_cfg.student_version = tier
            toolkit_cfg.student_version_str = version_str
            toolkit_cfg.set_config_key_data("studentClientVer", tier)
            toolkit_cfg.set_config_key_data("studentClientVerStr", version_str)
            return tier

    versions = {
        109: f"{toolkit_cfg.oseasy_path}LissHelper.exe",
        108: f"{toolkit_cfg.oseasy_path}MultiClient.exe",
        105: f"{toolkit_cfg.oseasy_path}MouseKeyBoradControl.exe",
    }

    for version, path in versions.items():
        if file_exists(path):
            debug(f"学生端版本检测(特征文件): v{version // 10}.{version % 10}")
            toolkit_cfg.student_version = version
            toolkit_cfg.student_version_str = f"{version // 10}.{version % 10}"
            toolkit_cfg.set_config_key_data("studentClientVer", version)
            toolkit_cfg.set_config_key_data("studentClientVerStr", f"{version // 10}.{version % 10}")
            return toolkit_cfg.student_version

    debug("学生端版本检测: 超出检测范围或未安装")
    toolkit_cfg.student_version = 0
    toolkit_cfg.student_version_str = ""
    return toolkit_cfg.student_version
