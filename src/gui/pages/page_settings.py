# src/gui/pages/page_settings.py
# 设置页（页面 5）

import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from src.utils.fs import del_historyrem
from src.gui.switch import PersistentSwitch


class PageSettings:

    def __init__(self, ui):
        self.ui = ui

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # 内容（可滚动）
        _, inner = ui.make_scrollable(frame)

        # 外观设置
        appear_frame = ttk.LabelFrame(inner, text="外观设置", padding=5)
        appear_frame.pack(fill=tk.X, pady=2)

        btn1 = ttk.Button(appear_frame, text="切换背景图片",
                   command=self._pick_bg)
        btn1.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn1, "FUNC_SET_BG")
        btn2 = ttk.Button(appear_frame, text="更换显示字体",
                   command=self._pick_font)
        btn2.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn2, "FUNC_SET_FONT")
        btn3 = ttk.Button(appear_frame, text="加载外部一言文件",
                   command=self._pick_yiyan)
        btn3.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn3, "FUNC_SET_YIYAN")

        ui.random_yiyan_swc = PersistentSwitch(
            appear_frame,
            config_key="random_yiyan_enabled",
            label="随机一言",
            on_toggle=ui.toggle_random_yiyan,
        )
        ui.random_yiyan_swc.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.random_yiyan_swc, "FUNC_SET_RANDOM_YIYAN")

        # 背景不透明度
        opacity_frame = ttk.LabelFrame(inner, text="背景不透明度", padding=5)
        opacity_frame.pack(fill=tk.X, padx=5, pady=2)

        ui.bgtmd_var = tk.DoubleVar(value=ui.bgtmd)
        opacity_scale = ttk.Scale(opacity_frame, from_=0, to=1.0, variable=ui.bgtmd_var,
                                   orient=tk.HORIZONTAL, command=self._on_opacity_change)
        opacity_scale.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(opacity_scale, "FUNC_SET_OPACITY")

        # 快捷键
        hk_frame = ttk.LabelFrame(inner, text="快捷键", padding=5)
        hk_frame.pack(fill=tk.X, padx=5, pady=2)

        from src.gui.hotkey import get_hotkey_label
        from src.utils.screenshot import get_scshot

        ui.hide_tbox_swc = PersistentSwitch(
            hk_frame,
            config_key="hide_tbox_hotkey",
            label=get_hotkey_label("hide_tbox") + " 隐&显工具箱",
            default_value=True,
            verifier=lambda: ui.hotkeyManager.is_registered_by_name("hide_tbox", ui.hide_toolkit_helper),
            on_toggle=lambda _: ui._on_hide_tbox_changed(),
        )
        ui.hide_tbox_swc.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.hide_tbox_swc, "FUNC_HK_HIDE_TOOLKIT")

        _screenshot_cb = lambda: ui._run_in_thread(get_scshot, "截图")
        ui._scshot_callback = _screenshot_cb
        ui.FastGetSC = PersistentSwitch(
            hk_frame,
            config_key="fast_screenshot_hotkey",
            label=get_hotkey_label("fast_screenshot") + " 屏幕截图",
            verifier=lambda: ui.hotkeyManager.is_registered_by_name("fast_screenshot", _screenshot_cb),
            on_toggle=lambda _: ui._on_fast_screenshot_changed(),
        )
        ui.FastGetSC.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.FastGetSC, "FUNC_FAST_SCREENSHOT")

        # 窗口
        win_frame = ttk.LabelFrame(inner, text="窗口", padding=5)
        win_frame.pack(fill=tk.X, padx=5, pady=2)

        ui.topmost_swc = PersistentSwitch(
            win_frame,
            config_key="topmost_enabled",
            label="置顶本窗口",
            on_toggle=ui._on_topmost_changed,
        )
        ui.topmost_swc.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.topmost_swc, "FUNC_SET_TOPMOST")

        # Toast 通知
        ui.toast_swc = PersistentSwitch(
            win_frame,
            config_key="toast_notification_enabled",
            label="Windows Toast 通知（部分操作时弹桌面通知）",
            on_toggle=self._on_toast_toggle,
        )
        ui.toast_swc.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.toast_swc, "FUNC_SET_TOAST")

        # 重置
        reset_frame = ttk.LabelFrame(inner, text="重置", padding=5)
        reset_frame.pack(fill=tk.X, padx=5, pady=2)

        btn_reset = ttk.Button(reset_frame, text="重置工具箱设置",
                   command=self._confirm_reset)
        btn_reset.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn_reset, "FUNC_SET_RESET")

        return frame

    def _on_toast_toggle(self, e=None):
        self.ui._toast_enabled = e.value

    def _pick_bg(self):
        path = filedialog.askopenfilename(
            title="选择背景图片",
            filetypes=[("图片文件", "*.png *.jpg *.jpeg *.bmp *.gif"), ("所有文件", "*.*")]
        )
        if path:
            self.ui.bgpath = path
            self.ui.loaded_bg = True
            from src.core.settings import toolkit_cfg
            toolkit_cfg.set_style_path("bgPath", path)
            self.ui.show_snakemessage("背景图片已设置")

    def _pick_font(self):
        path = filedialog.askopenfilename(
            title="选择字体文件",
            filetypes=[("TrueType 字体", "*.ttf"), ("所有文件", "*.*")]
        )
        if path:
            self.ui.zdy_fontpath = path
            from src.core.settings import toolkit_cfg
            toolkit_cfg.set_style_path("fontPath", path)
            self.ui.show_snakemessage("字体文件已加载（需重启生效）")

    def _pick_yiyan(self):
        path = filedialog.askopenfilename(
            title="选择一言文件",
            filetypes=[("文本文件", "*.txt"), ("所有文件", "*.*")]
        )
        if path:
            self.ui.yiyanfpath = path
            self.ui.from_file_load_yiyan()

    def _on_opacity_change(self, val):
        self.ui.bgtmd = float(val)
        from src.core.settings import toolkit_cfg
        toolkit_cfg.set_config_key_data("bg_opacity", self.ui.bgtmd)

    def _confirm_reset(self):
        if messagebox.askyesno(
            "重置工具箱设置",
            "将清除以下内容：\n"
            "  • 外观设置（背景/字体/一言）\n"
            "  • 配置文件 (config.json)\n"
            "  • IFEO 注册表劫持项\n"
            "  • 所有已生成的脚本 (.bat/.ps1)\n"
            "  • 所有日志文件 (.log)\n\n"
            "下次启动恢复默认设置。\n\n确认继续？"
        ):
            self._do_reset()

    def _do_reset(self):
        ui = self.ui
        del_historyrem()
        from src.core.settings import toolkit_cfg
        try:
            os.remove(toolkit_cfg.config_file_path)
        except FileNotFoundError:
            pass
        toolkit_cfg._data_cache = None
        from src.utils.ifeo import remove_ifeo_debugger
        for exe in ("sethc.exe", "shutdown.exe", "Student.exe"):
            remove_ifeo_debugger(exe)
        from src.modules.file_handler import del_self_cmd_files
        del_self_cmd_files()
        from src.core.constants import log_dir_path
        import glob
        for f in glob.glob(os.path.join(log_dir_path, "*.log")):
            try:
                os.remove(f)
            except OSError:
                pass
        ui.loaded_bg = False
        ui.bgtmd = 0.6
        ui.bgpath = ""
        ui.yiyanfpath = ""
        ui.zdy_fontpath = ""
        ui.font_loadtime = 1
        ui.random_yy_enabled = False
        ui.pick_a_random_yiyan()
        toolkit_cfg.set_config_key_data("theme_mode", "system")
        ui.show_snakemessage("工具箱已重置，设置已恢复默认值")