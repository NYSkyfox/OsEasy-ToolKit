# src/core/helpers.py
# 通用工具函数 → 已迁移到 src/utils/__init__.py
# 此文件保留 UI 桥接和向后兼容的重新导出

from src.utils.__init__ import (
    get_time_str,
    file_exists,
    get_ipv4_address,
    open_github_page,
    run_sigle_cmd,
    use_bat_file_to_run_cmd,
    runbat,
    del_historyrem,
)

# ---- UI 桥接 ----

Ui_Class = None


def pass_ui_class(ui) -> None:
    """传递Ui类到此处让这里的函数可以调用主Ui的函数"""
    global Ui_Class
    Ui_Class = ui


def show_snack(*msg: tuple) -> None:
    """通过 Ui 实例弹出 SnackBar 消息（供非 UI 模块调用）"""
    mix = ""
    for i in msg:
        mix += str(i) + " "
    msg = mix.strip()
    Ui_Class.show_snakemessage(msg)