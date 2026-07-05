# src/core/helpers.py
# 通用工具函数 → 已迁移到 src/utils/__init__.py
# 此文件保留 UI 桥接和向后兼容的重新导出

from src.utils.__init__ import (
    get_time_str,
    check_give_file_path_is_excs,
    get_ipv4_address,
    open_github_page,
    run_sigle_cmd,
    use_bat_file_to_run_cmd,
    runbat,
    get_god_potato_path,
    run_cmd_with_god_potato,
    del_historyrem,
)

# ---- UI 桥接 ----

Ui_Class = None


def pass_ui_class(ui) -> None:
    """传递Ui类到此处让这里的函数可以调用主Ui的函数"""
    global Ui_Class
    Ui_Class = ui


def Ui_call_show_snake_message(*msg: tuple) -> None:
    """Ui类 显示底部弹窗"""
    mix = ""
    for i in msg:
        mix += str(i) + " "
    msg = mix.strip()
    Ui_Class.show_snakemessage(msg)