# src/utils/fs.py
# 文件系统工具

import os
from datetime import datetime


def get_time_str() -> str:
    """返回一个时间字符串"""
    return datetime.now().strftime("%Y_%m_%d_%H_%M_%S")


def file_exists(filePath) -> bool:
    """检查文件是否存在"""
    return os.path.isfile(filePath)


def del_historyrem(*e) -> None:
    """删除保存的历史路径文件"""
    from src.core.settings import toolkit_cfg
    neddel = ["fontPath", "bgPath", "yiyanPath"]
    for i in neddel:
        toolkit_cfg.set_config_key_data(i, None)