# src/utils/program/persistent_switch.py
# 带自动持久化的 Switch 控件

import flet as ft
from typing import Callable

from src.core.runtime_config import toolkit_cfg


class PersistentSwitch(ft.Switch):
    """自动从/向 toolkit_cfg 读写状态的 Switch。

    支持两种模式：

    1. 配置文件模式（传 config_key）：
        sw = PersistentSwitch(
            config_key="hide_tbox_hotkey",
            label="...",
            on_toggle=some_callback,
        )

    2. 注册表/实时状态模式（不传 config_key，传 live_getter）：
        sw = PersistentSwitch(
            live_getter=lambda: is_sethc_hijacked(),
            on_toggle=some_callback,
            label="...",
        )

    两种模式互斥：传了 config_key 就忽略 live_getter。
    """

    def __init__(
        self,
        config_key: str | None = None,
        live_getter: Callable | None = None,
        on_toggle=None,
        **kwargs,
    ):
        self._config_key = config_key
        self._live_getter = live_getter
        self._on_toggle = on_toggle

        # 初始化 value
        if config_key is not None:
            # 模式 1：配置文件
            saved = toolkit_cfg.get_config_key_data(config_key)
            if saved is not None:
                kwargs.setdefault("value", bool(saved))
        elif live_getter is not None:
            # 模式 2：实时查询
            kwargs.setdefault("value", live_getter())

        super().__init__(**kwargs)

        self._orig_on_change = self.on_change
        self.on_change = self._persist_and_callback

    def _persist_and_callback(self, e):
        if self._config_key is not None:
            # 模式 1：写入配置
            toolkit_cfg.set_config_key_data(self._config_key, self.value)
        if self._on_toggle is not None:
            self._on_toggle(e)