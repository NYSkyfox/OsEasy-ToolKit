# src/gui/switch.py
# 带自动持久化的 Checkbutton 控件（ttk 版）
# 原 flet 版 Switch 迁移至 ttk.Checkbutton

import tkinter as tk
from tkinter import ttk
from typing import Callable

from src.core.settings import toolkit_cfg


class PersistentSwitch(ttk.Frame):
    """自动从/向 toolkit_cfg 读写状态的 Checkbutton。

    支持三种模式：

    1. 配置文件模式（传 config_key）：
        sw = PersistentSwitch(config_key="hide_tbox_hotkey", label="...", on_toggle=...)

    2. 注册表/实时状态模式（不传 config_key，传 live_getter）：
        sw = PersistentSwitch(live_getter=lambda: is_sethc_hijacked(), on_toggle=..., label="...")

    3. 运行时验证模式（传 verifier）：
        sw = PersistentSwitch(live_getter=..., verifier=..., on_toggle=..., label="...")
    """

    def __init__(
        self,
        parent=None,
        config_key: str | None = None,
        live_getter: Callable | None = None,
        verifier: Callable | None = None,
        on_toggle=None,
        default_value: bool = False,
        label: str = "",
        **kwargs,
    ):
        super().__init__(parent, **kwargs)
        self._config_key = config_key
        self._live_getter = live_getter
        self._verifier = verifier
        self._on_toggle = on_toggle
        self._label_text = label
        self._verify_generation = 0

        # 初始化 value
        if config_key is not None:
            saved = toolkit_cfg.get_config_key_data(config_key)
            init_val = bool(saved) if saved is not None else default_value
        elif live_getter is not None:
            init_val = live_getter()
        else:
            init_val = default_value

        self._var = tk.BooleanVar(value=init_val)
        self._cb = ttk.Checkbutton(
            self, text=label, variable=self._var,
            command=self._on_change,
        )
        self._cb.pack(anchor=tk.W, fill=tk.X)

    @property
    def value(self) -> bool:
        return self._var.get()

    @value.setter
    def value(self, v: bool):
        self._var.set(v)

    @property
    def label(self) -> str:
        return self._label_text

    @label.setter
    def label(self, text: str):
        self._label_text = text
        self._cb.configure(text=text)

    def _on_change(self):
        expected = self.value
        self._verify_generation += 1
        generation = self._verify_generation
        from src.utils.logger import debug
        lbl = self._label_text or self._config_key or '未知功能'
        debug(f"开关 [{lbl}] → {'开启' if expected else '关闭'}")
        if self._config_key is not None:
            toolkit_cfg.set_config_key_data(self._config_key, expected)
        if self._on_toggle is not None:
            self._on_toggle(self)
        # 运行时验证
        if self._verifier is not None:
            self._verify(expected, generation=generation)

    def _verify(self, expected: bool, generation: int | None = None):
        import threading
        import time as _time

        if generation is None:
            generation = self._verify_generation

        def _check():
            _time.sleep(0.5)
            if generation != self._verify_generation:
                return
            try:
                actual = self._verifier()
            except Exception:
                return
            if actual != self.value:
                self._var.set(actual)
                if self._config_key is not None:
                    toolkit_cfg.set_config_key_data(self._config_key, actual)
                try:
                    self.after(0, lambda: self._show_verify_msg(expected, actual, self.value))
                except Exception:
                    pass

        threading.Thread(target=_check, daemon=True).start()

    def _show_verify_msg(self, expected, actual, current=None):
        from tkinter import messagebox
        lbl = self._label_text or self._config_key or '未知功能'
        # 如果 current 与 expected 不同，说明 on_toggle 已合法修改了状态，不再弹窗
        if current is not None and current != expected:
            return
        messagebox.showwarning(
            "操作未生效",
            f"「{lbl}」切换失败，已自动恢复。\n"
            f"期望: {'开启' if expected else '关闭'} → 实际: {'开启' if actual else '关闭'}"
        )