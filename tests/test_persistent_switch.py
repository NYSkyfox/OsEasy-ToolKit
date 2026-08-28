import threading
import tkinter as tk

from src.gui.switch import PersistentSwitch


class DummyThread:
    def __init__(self, target, daemon=None):
        self._target = target
        self.daemon = daemon

    def start(self):
        self._target()


def test_stale_verification_is_ignored(monkeypatch):
    root = tk.Tk()
    root.withdraw()
    try:
        switch = PersistentSwitch(root, label="测试开关", verifier=lambda: False)
        switch._verify_generation = 7

        calls = []
        monkeypatch.setattr(threading, "Thread", DummyThread)
        monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)
        switch._show_verify_msg = lambda *args, **kwargs: calls.append((args, kwargs))

        switch._verify(expected=True, generation=1)

        assert calls == []
        assert switch._verify_generation == 7
    finally:
        root.destroy()


def test_verify_uses_current_value_not_stale_expected(monkeypatch):
    root = tk.Tk()
    root.withdraw()
    try:
        switch = PersistentSwitch(root, label="冲突取消", verifier=lambda: False)
        switch._var.set(False)
        switch._verify_generation = 1

        calls = []
        monkeypatch.setattr(threading, "Thread", DummyThread)
        monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)
        switch._show_verify_msg = lambda *args, **kwargs: calls.append((args, kwargs))

        switch._verify(expected=True, generation=1)

        assert calls == []
    finally:
        root.destroy()
