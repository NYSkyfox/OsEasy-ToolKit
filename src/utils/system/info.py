# src/utils/system/info.py
# 系统信息工具

import os
from datetime import datetime


def get_time_str() -> str:
    """返回一个时间字符串"""
    time_str = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
    return time_str


def file_exists(filePath) -> bool:
    """检查文件是否存在"""
    return os.path.isfile(filePath)