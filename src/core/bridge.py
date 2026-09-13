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


def notify_student_killed() -> None:
    """工具箱内部结束了学生端进程后回调（Ui 未就绪时静默忽略）。

    仅用于“工具箱自己”发起的结束操作；外部（任务管理器等）结束
    不会走这里，因此不构成对学生端的外部监听。
    """
    if Ui_Class is not None and hasattr(Ui_Class, "on_student_killed_by_toolkit"):
        try:
            Ui_Class.on_student_killed_by_toolkit()
        except Exception:
            pass