# src/gui/hotkey_manager.py
# 快捷键管理中心

from collections import defaultdict

from pynput import keyboard


class hotkey_manager:
    """快捷键管理中心"""
    def __init__(self):
        self.hotkeys = defaultdict(list)
        # 存储快捷键与回调的映射
        self.current_keys = set()
        # 当前按下的键集合
        self.listener = None

    def register_hotkey(self, keys, callback):
        """注册快捷键
        :param keys: 键序列（支持普通键和特殊键混合）
        :param callback: 触发回调函数
        """
        print(f"register {keys =}")
        normalized = frozenset(self._normalize_key(k) for k in keys)
        self.hotkeys[normalized].append(callback)

        self.start()

    def unregister_hotkey(self, keys, callback):
        """取消注册指定快捷键的回调函数
        :param keys: 要取消的键序列
        :param callback: 要移除的回调函数
        """
        print(f"unregister_hotkey {keys =}")
        normalized = frozenset(self._normalize_key(k) for k in keys)
        if normalized in self.hotkeys:
            callbacks = self.hotkeys[normalized]
            # 移除所有匹配的callback实例
            while callback in callbacks:
                callbacks.remove(callback)
            # 如果回调列表为空，删除该快捷键条目
            if not callbacks:
                del self.hotkeys[normalized]

    def switch_reg_helper(self, swc_value: bool, keys: list, callback):
        """帮助开关注册快捷键
        可以省去一堆函数
        """
        print(f"传入的开关值{swc_value =}")

        if swc_value == True:
            self.register_hotkey(keys=keys, callback=callback)
        else:
            self.unregister_hotkey(keys=keys, callback=callback)

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
                    callback()
                self.current_keys.clear()  # 触发后清空状态
                break

    def start(self):
        """启动监听"""
        print("start listen")
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