"""
解锁管理 —— 对外 UI 接口
所有解锁逻辑集中在 script_generator.py，本文件仅负责 toast + 委托
"""
from src.core.helpers import show_snack
from src.modules.script_generator import script_gen


def _toast(msg: str):
    show_snack(msg)


# ── A. 网络解锁 ──

def network_block():
    script_gen.network_block()

def network_unlock():
    _toast("解锁网络中...")
    script_gen.network_unlock()
    _toast("网络已解锁")


# ── B. USB 解锁 ──

def usb_block():
    script_gen.usb_block()

def usb_unlock():
    _toast("解锁USB中...")
    script_gen.usb_unlock()
    _toast("USB 已解锁")


# ── C. 键盘/鼠标解锁 ──

def keyboard_block():
    script_gen.keyboard_block()

def keyboard_unlock():
    _toast("解锁键盘鼠标中，稍后注销...")
    script_gen.keyboard_unlock()


# ── D. 控屏解锁 ──

def screen_control_block():
    script_gen.screen_control_block()

def screen_control_unlock():
    _toast("解除控屏...")
    script_gen.screen_control_unlock()
    _toast("控屏已解除")


# ── E. 黑屏解锁 ──

def black_screen_block():
    script_gen.black_screen_block()

def black_screen_unlock():
    _toast("移除黑屏肃静...")
    script_gen.black_screen_unlock()
    _toast("黑屏肃静已移除")


# ── F. 删文件 ──

def delete_files_block():
    script_gen.delete_files_block()

def delete_files_unlock():
    _toast("删除关键文件中...")
    script_gen.delete_files_unlock()
    _toast("已删除 (LockKeyboard.dll/BlackSlient/MultiClient)")


# ── 全部解锁 ──

def unlock_all():
    _toast("一键脱离管控，稍后注销...")
    script_gen.unlock_all()
    _toast("脱离管控已启动，完成后将自动注销")