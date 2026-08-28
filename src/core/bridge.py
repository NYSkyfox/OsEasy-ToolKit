# src/core/helpers.py
# UI 回调桥接（供非 UI 模块调用 UI 方法）

Ui_Class = None


def pass_ui_class(ui) -> None:
    """传递Ui类到此处让这里的函数可以调用主Ui的函数"""
    global Ui_Class
    Ui_Class = ui


def show_snack(*msg: tuple) -> None:
    """通过 Ui 实例弹出消息提示（供非 UI 模块调用）"""
    mix = ""
    for i in msg:
        mix += str(i) + " "
    msg = mix.strip()
    Ui_Class.show_snakemessage(msg)