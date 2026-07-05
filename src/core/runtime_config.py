# src/core/runtime_config.py
# 运行时配置读写类

import json
import os
from config import CONFIG_FILE_PATH_TEMPLATE, DEFAULT_OSEASY_PATH, DEFAULT_STUDENT_EXE_NAME
from src.core.helpers import check_give_file_path_is_excs, get_time_str

_username = os.environ.get('USERNAME') or 'Default'


class RuntimeConfig:
    """运行时配置读写类"""

    def __init__(self):
        self.config_file_path = CONFIG_FILE_PATH_TEMPLATE.format(username=_username)
        self.running_student_client_ver = 0
        self.oseasypath_have_been_modified = False
        self.student_exe_name = DEFAULT_STUDENT_EXE_NAME
        self.oseasy_path = DEFAULT_OSEASY_PATH
        self.broadcast_cmd = None
        self._data_cache = None

    # ---- 缓存层 ----

    def _cache_load(self) -> dict:
        """从磁盘读取配置到内存缓存"""
        raw = self._read_config_raw()
        if raw == "{}":
            self._data_cache = {}
        else:
            self._data_cache = json.loads(raw)
        return self._data_cache

    def _cache_get(self) -> dict:
        """获取缓存数据，若未加载则从磁盘读取"""
        if self._data_cache is None:
            self._cache_load()
        return self._data_cache

    def _cache_write(self, data: dict) -> None:
        """写入缓存并同步到磁盘"""
        self._data_cache = data
        self._write_config_raw(data)

    # ---- 磁盘 I/O ----

    def _read_config_raw(self) -> str:
        """从配置文件读取原始字符串"""
        if check_give_file_path_is_excs(self.config_file_path):
            with open(self.config_file_path, "r", encoding="utf-8") as f:
                return f.read()
        else:
            self._write_config_raw({})
            return "{}"

    def _write_config_raw(self, datas: dict) -> None:
        """写入配置文件"""
        try:
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(datas, ensure_ascii=False, indent=4))
        except (FileNotFoundError, OSError):
            # 目录不存在，自动创建后重试
            os.makedirs(os.path.dirname(self.config_file_path), exist_ok=True)
            with open(self.config_file_path, "w", encoding="utf-8") as f:
                f.write(json.dumps(datas, ensure_ascii=False, indent=4))

    # ---- 公开方法 ----

    def first_launch_check(self) -> bool:
        """首次启动检查"""
        reads = self.get_config_key_data("first_launch_time")
        if not reads:
            self.write_first_launch_time()
            return True
        else:
            return False

    def write_first_launch_time(self) -> None:
        """写入首次启动时间"""
        self.set_config_key_data("first_launch_time", get_time_str())

    def read_config(self) -> str:
        """从配置文件中读取（兼容旧接口，返回 JSON 字符串）"""
        data = self._cache_get()
        if not data:
            return "{}"
        return json.dumps(data, ensure_ascii=False, indent=4)

    def write_config(self, datas: str | dict) -> None:
        """写入配置文件"""
        if isinstance(datas, str):
            datas = json.loads(datas) if datas != "{}" else {}
        self._cache_write(datas)

    def get_config_key_data(self, key) -> str | None:
        """获取配置文件中指定键的数据"""
        return self._cache_get().get(key)

    def set_config_key_data(self, key, value) -> None:
        """设置配置文件中的数据"""
        data = self._cache_get()
        data[key] = value
        self._cache_write(data)

    def clear_config_key_data(self, key) -> None:
        """清空配置文件中的数据"""
        data = self._cache_get()
        if key in data:
            data.pop(key)
        self._cache_write(data)

    def get_style_path(self, style_name: str) -> str | None:
        """获取自定义外观的路径
        style_name: ["yiyan","font","bg"]
        一言, 字体, 背景
        """
        return self._cache_get().get(style_name)

    def set_style_path(self, style_name: str, style_path: str) -> None:
        """设置自定义外观的路径
        style_name: ["yiyan","font","bg"]
        一言, 字体, 背景
        """
        data = self._cache_get()
        data[style_name] = style_path
        self._cache_write(data)


toolbox_cfg = RuntimeConfig()