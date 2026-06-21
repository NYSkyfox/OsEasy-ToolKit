"""
全局快捷键服务
基于 pynput 实现的快捷键管理中心，管理所有全局快捷键
"""

from collections import defaultdict
from typing import Callable, Dict, List
from pynput import keyboard


class HotkeyService:
    """
    全局快捷键服务

    支持动态注册/注销多组快捷键，
    每组快捷键可以绑定多个回调函数。
    """

    def __init__(self):
        self._hotkeys: Dict[frozenset, List[Callable]] = defaultdict(list)
        self._current_keys: set = set()
        self._listener: keyboard.Listener | None = None
        self._running: bool = False

    def register(self, keys: list, callback: Callable) -> None:
        """
        注册一组快捷键

        Args:
            keys: 键序列，混合 str 和 keyboard.Key，如 [keyboard.Key.alt_l, 'k']
            callback: 触发回调函数
        """
        normalized = frozenset(self._normalize_key(k) for k in keys)
        if callback not in self._hotkeys[normalized]:
            self._hotkeys[normalized].append(callback)
        self._start_listener()

    def unregister(self, keys: list, callback: Callable = None) -> None:
        """
        取消注册指定快捷键的回调函数

        Args:
            keys: 键序列
            callback: 要移除的回调函数。为 None 时移除该组合下的所有回调
        """
        normalized = frozenset(self._normalize_key(k) for k in keys)
        if normalized in self._hotkeys:
            if callback is None:
                # 移除该组合下的所有回调
                del self._hotkeys[normalized]
            else:
                while callback in self._hotkeys[normalized]:
                    self._hotkeys[normalized].remove(callback)
                if not self._hotkeys[normalized]:
                    del self._hotkeys[normalized]

    def toggle(self, enabled: bool, keys: list, callback: Callable) -> None:
        """
        便捷的开关方法：根据 bool 值注册或注销

        Args:
            enabled: True 注册，False 注销
            keys: 键序列
            callback: 回调函数
        """
        if enabled:
            self.register(keys, callback)
        else:
            self.unregister(keys, callback)

    def _normalize_key(self, key):
        """
        统一键的表示形式

        Args:
            key: str 或 keyboard.Key 或 keyboard.KeyCode

        Returns:
            标准化的键对象
        """
        if isinstance(key, str):
            return keyboard.KeyCode.from_char(key.lower())
        if isinstance(key, keyboard.KeyCode):
            # Python pynput 在接收 Alt+F 时，
            # F 键的 KeyCode 字符串表示为 '<70>'，
            # 映射回普通 'f' 以匹配注册时的 lower() 标准化
            if str(key) == '<70>':
                return 'f'
        return key

    def _on_press(self, key) -> None:
        """按键按下事件"""
        if key is None:
            return
        self._current_keys.add(self._normalize_key(key))
        self._check_hotkeys()

    def _on_release(self, key) -> None:
        """按键释放事件"""
        if key is None:
            return
        normalized = self._normalize_key(key)
        self._current_keys.discard(normalized)

    def _check_hotkeys(self) -> None:
        """检查当前按键组合是否命中已注册快捷键"""
        current = frozenset(self._current_keys)
        # 从长到短匹配（最长匹配优先）
        for key_combo in sorted(self._hotkeys.keys(), key=len, reverse=True):
            if key_combo.issubset(current):
                for callback in self._hotkeys[key_combo]:
                    try:
                        callback()
                    except Exception as e:
                        print(f"[HotkeyService] 快捷键回调异常: {e}")
                self._current_keys.clear()
                break

    def _start_listener(self) -> None:
        """启动键盘监听（如果尚未启动）"""
        if not self._listener or not self._listener.running:
            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.start()
            self._running = True

    def stop(self) -> None:
        """停止键盘监听"""
        if self._listener and self._listener.running:
            self._listener.stop()
            self._listener = None
            self._running = False

    @property
    def is_running(self) -> bool:
        """是否正在监听"""
        return self._running