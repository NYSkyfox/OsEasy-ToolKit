# src/utils/program/hotkey_manager.py
# 快捷键管理中心

import threading
from collections import defaultdict

from pynput import keyboard

from src.utils.system.logger import debug

# ══════════════════════════════════════════════════════════
# 快捷键定义注册表 —— 所有热键在此集中管理
# ══════════════════════════════════════════════════════════

HOTKEY_DEFS = {
    "hide_tbox": {
        "keys": [keyboard.Key.caps_lock, keyboard.Key.enter],
        "label": "caps+enter 显示/隐藏工具箱",
    },
    "fast_screenshot": {
        "keys": [keyboard.Key.alt_l, 'x'],
        "label": "Alt+X 截图",
    },
    "run_window_broadcast": {
        "keys": [keyboard.Key.alt_l, 'u'],
        "label": "Alt+U 窗口广播",
    },
    "kill_screen_render": {
        "keys": [keyboard.Key.alt_l, 'k'],
        "label": "Alt+K 杀广播进程",
    },
    "run_fullscreen_broadcast": {
        "keys": [keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_vk(70)],
        "label": "Ctrl+Alt+F 全屏广播",
    },
}


def get_hotkey_keys(name: str) -> list:
    """获取指定热键的键位列表"""
    return HOTKEY_DEFS[name]["keys"]


def get_hotkey_label(name: str) -> str:
    """获取指定热键的标签"""
    return HOTKEY_DEFS[name]["label"]


class hotkey_manager:
    """快捷键管理中心"""
    def __init__(self):
        self.hotkeys = defaultdict(list)
        # 存储快捷键与回调的映射
        self.current_keys = set()
        # 当前按下的键集合
        self.listener = None

    def register_hotkey(self, keys, callback, label: str = ""):
        """注册快捷键
        :param keys: 键序列（支持普通键和特殊键混合）
        :param callback: 触发回调函数
        :param label: 功能名称，用于日志
        """
        label_str = f" [{label}]" if label else ""
        debug(f"注册快捷键{label_str}: {self._keys_to_str(keys)}")
        normalized = frozenset(self._normalize_key(k) for k in keys)
        callbacks = self.hotkeys[normalized]
        if callback not in callbacks:
            callbacks.append(callback)
        self.start()

    def unregister_hotkey(self, keys, callback, label: str = ""):
        """取消注册指定快捷键的回调函数
        :param keys: 要取消的键序列
        :param callback: 要移除的回调函数
        :param label: 功能名称，用于日志
        """
        label_str = f" [{label}]" if label else ""
        debug(f"注销快捷键{label_str}: {self._keys_to_str(keys)}")
        normalized = frozenset(self._normalize_key(k) for k in keys)
        if normalized in self.hotkeys:
            callbacks = self.hotkeys[normalized]
            while callback in callbacks:
                callbacks.remove(callback)
            if not callbacks:
                del self.hotkeys[normalized]

    def switch_reg_helper(self, swc_value: bool, keys: list, callback, label: str = ""):
        """帮助开关注册快捷键
        :param swc_value: 开关状态（True=注册, False=注销）
        :param keys: 键序列
        :param callback: 回调函数
        :param label: 功能名称，用于日志
        """
        action = "启用" if swc_value else "禁用"
        label_str = f" [{label}]" if label else ""
        debug(f"快捷键{action}{label_str}")

        if swc_value:
            self.register_hotkey(keys=keys, callback=callback)
        else:
            self.unregister_hotkey(keys=keys, callback=callback)

    def switch_by_name(self, name: str, enabled: bool, callback):
        """按名称开关注册快捷键（从 HOTKEY_DEFS 取 keys + label）
        :param name:   HOTKEY_DEFS 中的键名
        :param enabled: True=注册, False=注销
        :param callback: 回调函数
        """
        d = HOTKEY_DEFS[name]
        self.switch_reg_helper(enabled, d["keys"], callback, d["label"])

    @staticmethod
    def _keys_to_str(keys) -> str:
        """将键序列转为可读字符串"""
        parts = []
        for k in keys:
            if isinstance(k, keyboard.Key):
                parts.append(k.name)
            elif isinstance(k, keyboard.KeyCode):
                parts.append(f"vk({k.vk})")
            else:
                parts.append(str(k))
        return "+".join(parts)

    def _normalize_key(self, key):
        """统一键的表示形式"""
        if isinstance(key, str):
            return keyboard.KeyCode.from_char(key.lower())
        elif isinstance(key, keyboard.KeyCode):
            if str(key) == '<70>':
                return 'f'
        return key

    def _on_press(self, key):
        """处理按键事件"""

        self.current_keys.add(self._normalize_key(key))
        self._check_hotkeys()

    def _on_release(self, key):
        """处理释放事件"""
        normalized = self._normalize_key(key)
        if normalized in self.current_keys:
            self.current_keys.remove(normalized)

    def _check_hotkeys(self):
        """检查当前按键组合"""
        current = frozenset(self.current_keys)

        # 查找匹配的快捷键（支持最长匹配原则）
        for key_combo in sorted(self.hotkeys.keys(), key=len, reverse=True):
            if key_combo.issubset(current):
                for callback in self.hotkeys[key_combo]:
                    threading.Thread(target=callback, daemon=True).start()
                self.current_keys.clear()  # 触发后清空状态
                break

    def start(self):
        """启动监听"""
        debug("start listen")
        if not self.listener or not self.listener.running:
            self.listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self.listener.start()

    def stop(self):
        """停止监听"""
        if self.listener and self.listener.running:
            self.listener.stop()

    def is_registered(self, keys, callback) -> bool:
        """检查指定快捷键+回调是否已注册"""
        normalized = frozenset(self._normalize_key(k) for k in keys)
        callbacks = self.hotkeys.get(normalized)
        return callbacks is not None and callback in callbacks

    def is_registered_by_name(self, name: str, callback) -> bool:
        """按名称检查快捷键+回调是否已注册"""
        return self.is_registered(HOTKEY_DEFS[name]["keys"], callback)
