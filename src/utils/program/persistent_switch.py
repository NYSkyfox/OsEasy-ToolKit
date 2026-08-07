# src/utils/program/persistent_switch.py
# 带自动持久化的 Switch 控件

import flet as ft
from typing import Callable

from src.core.runtime_config import toolkit_cfg


class PersistentSwitch(ft.Switch):
    """自动从/向 toolkit_cfg 读写状态的 Switch。

    支持三种模式：

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

    3. 运行时验证模式（传 verifier）：
        sw = PersistentSwitch(
            live_getter=lambda: is_foo_enabled(),
            verifier=lambda: is_foo_enabled(),
            on_toggle=some_callback,
            label="...",
        )
        开关切换后延迟 500ms 调用 verifier 回读真实状态，
        与期望值不匹配则自动弹回 + SnackBar 提示。
    """

    def __init__(
        self,
        config_key: str | None = None,
        live_getter: Callable | None = None,
        verifier: Callable | None = None,
        on_toggle=None,
        default_value: bool = False,
        **kwargs,
    ):
        self._config_key = config_key
        self._live_getter = live_getter
        self._verifier = verifier
        self._on_toggle = on_toggle

        # 初始化 value
        if config_key is not None:
            # 模式 1：配置文件
            saved = toolkit_cfg.get_config_key_data(config_key)
            if saved is not None:
                kwargs.setdefault("value", bool(saved))
            else:
                kwargs.setdefault("value", default_value)
        elif live_getter is not None:
            # 模式 2/3：实时查询
            kwargs.setdefault("value", live_getter())

        super().__init__(**kwargs)

        self.on_change = self._persist_and_callback

    def _persist_and_callback(self, e):
        from src.utils.system.logger import debug
        expected = self.value
        label = getattr(self, 'label', None) or self._config_key or '未知功能'
        debug(f"开关 [{label}] → {'开启' if expected else '关闭'}")
        if self._config_key is not None:
            toolkit_cfg.set_config_key_data(self._config_key, expected)
        if self._on_toggle is not None:
            self._on_toggle(e)
        # 运行时验证
        if self._verifier is not None:
            self._verify(expected)

    def _verify(self, expected: bool):
        """延迟回读真实状态，不匹配则弹回并提示"""
        import threading, time as _time
        def _check():
            _time.sleep(0.5)
            try:
                actual = self._verifier()
            except Exception:
                return
            if actual != expected:
                # 弹回开关
                self.value = actual
                if self._config_key is not None:
                    toolkit_cfg.set_config_key_data(self._config_key, actual)
                # 提示（通过 page 的 snack_bar，由于在子线程需通过 dispatch）
                try:
                    self.page.run_task(
                        lambda: self._show_verify_fail(expected, actual)
                    )
                except Exception:
                    pass
        threading.Thread(target=_check, daemon=True).start()

    def _show_verify_fail(self, expected: bool, actual: bool):
        """显示验证失败的提示"""
        label = getattr(self, 'label', '此功能') or '此功能'
        self.page.snack_bar = ft.SnackBar(
            ft.Text(f"⚠ {label} 未生效（可能权限不足或被拦截），已自动恢复"),
            duration=4000,
        )
        self.page.snack_bar.open = True
        self.update()
        self.page.update()