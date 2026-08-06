# src/utils/program/config_tools.py
# 配置工具

def del_historyrem(*e) -> None:
    """删除保存的历史路径文件"""
    from src.core.runtime_config import toolkit_cfg
    neddel = ["fontPath", "bgPath", "yiyanPath"]
    for i in neddel:
        toolkit_cfg.set_config_key_data(i, None)