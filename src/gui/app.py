# src/gui/app.py
# 工具箱主 UI 类 — 框架 + 通用方法（ttk 版）

import os
import time
import random
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from config import APP_VERSION, RELEASE_NAME, DEFAULT_YIYAN_LIST, DEFAULT_SHOW_YIYAN

from src.core.settings import toolkit_cfg
from src.core.bridge import pass_ui_class

from src.gui.hotkey import hotkey_manager, get_hotkey_label
from src.gui.switch import PersistentSwitch
from src.gui.widgets import make_scrollable, make_output_text, append_text, clear_text
from src.gui.pages import (
    PageOverview, PageProcess, PageService, PageUnlock, PageBackup, PageBroadcast,
    PageDll, PageSettings, PageAbout, PageAdvanced,
)
from src.utils.display import resource_path


class Ui:

    def __init__(self) -> None:
        self.ver = APP_VERSION
        self.release_name = RELEASE_NAME
        self.hotkeyManager = hotkey_manager()
        self.guaqi_runstatus = False
        self.bgtmd = 0.6
        self.defult_yy = True
        self.random_yy_enabled = False
        self.NowSelIndex = 0
        self.loaded_bg = False
        self.bgpath = ""
        self.yiyanfpath = ""
        self.zdy_fontpath = ""
        self.font_loadtime = 1
        self._toast_enabled = False  # 是否启用 Windows Toast 通知

        # tkinter 根窗口（延迟创建）
        self.root = None
        self.notebook = None
        self.status_var = None
        self._pages = []

    # ============================================================
    #  页面无关的通用回调
    # ============================================================

    def direct_run_fullscreen_broadcast_cmd(self):
        if self._swc('KillSCR_swc') is None:
            self.show_snakemessage("请先打开广播管理页再使用此功能")
            return
        if self.KillSCR_swc.value:
            from src.modules.broadcast_handler import force_screenrender_fullscreen
            if force_screenrender_fullscreen():
                self.show_snakemessage("已恢复全屏模式")
            else:
                self.show_snakemessage("未找到广播窗口")
        else:
            self.show_snakemessage("警告！ 未开启快捷键杀广播进程\n尝试运行的操作已拦截....")

    def direct_kill_screen_render(self, *e):
        from src.utils.process import kill_process
        kill_process("ScreenRender_Y.exe")
        kill_process("ScreenRender.exe")

    def hide_toolkit_helper(self):
        if self.root:
            if self.root.winfo_viewable():
                self.root.withdraw()
            else:
                self.root.deiconify()

    def _swc(self, name: str):
        """获取页面挂载到 ui 上的开关控件，不存在返回 None"""
        return getattr(self, name, None)

    def _on_hotkey_switch(self, hotkey_name: str, swc_name: str, callback):
        """通用快捷键开关回调"""
        swc = self._swc(swc_name)
        if swc is None:
            return
        self.hotkeyManager.switch_by_name(hotkey_name, swc.value, callback)

    def _on_hide_tbox_changed(self, e=None):
        self._on_hotkey_switch("hide_tbox", "hide_tbox_swc", self.hide_toolkit_helper)

    def _on_fast_screenshot_changed(self, e=None):
        self._on_hotkey_switch("fast_screenshot", "FastGetSC", self._scshot_callback)

    def _on_run_window_broadcast_changed(self, e=None):
        page = self._get_broadcast_page()
        self._on_hotkey_switch("run_window_broadcast", "runwindows_swc",
                               page.run_win_gbcmd_loj if page else None)

    def _on_kill_screen_render_changed(self, e=None):
        self._on_hotkey_switch("kill_screen_render", "KillSCR_swc", self.direct_kill_screen_render)

    def _on_run_fullscreen_broadcast_changed(self, e=None):
        self._on_hotkey_switch("run_fullscreen_broadcast", "RunFullSC_swc",
                               self.direct_run_fullscreen_broadcast_cmd)

    def _on_topmost_changed(self, e=None):
        if self.root:
            self.root.attributes("-topmost", bool(self._swc("topmost_swc").value if self._swc("topmost_swc") else False))

    # ============================================================
    #  主入口
    # ============================================================

    def main(self):
        self.root = tk.Tk()
        self.root.title(self.release_name)
        self.root.geometry("520x750")
        self.root.minsize(420, 600)
        # 全局关闭控件点击后的虚线焦点框
        self.root.option_add("*Button.highlightThickness", 0)
        self.root.option_add("*Checkbutton.highlightThickness", 0)

        # 窗口图标
        try:
            icon_path = resource_path("logo.png")
            if os.path.exists(icon_path):
                # tkinter 在 Windows 上支持 .ico，不支持 .png
                pass
        except Exception:
            pass

        # 尝试设置图标（使用 logo.ico 如果存在）
        try:
            ico_path = resource_path("logo.ico")
            if os.path.exists(ico_path):
                self.root.iconbitmap(ico_path)
        except Exception:
            pass

        # 绑定关闭事件
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

        # ---- 状态栏 ----
        status_frame = ttk.Frame(self.root)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        self.status_var = tk.StringVar(value="")
        self.status_label = ttk.Label(status_frame, textvariable=self.status_var,
                                      relief=tk.SUNKEN, anchor=tk.W,
                                      wraplength=500, justify=tk.LEFT)
        self.status_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2, pady=1)

        # ---- 一言显示 ----
        self.yiyan_var = tk.StringVar(value=DEFAULT_SHOW_YIYAN)
        yiyan_frame = ttk.Frame(self.root)
        yiyan_frame.pack(fill=tk.X, padx=5, pady=(5, 0))
        self.yiyan_label = ttk.Label(yiyan_frame, textvariable=self.yiyan_var, font=("", 10), foreground="gray")
        self.yiyan_label.pack(anchor=tk.W)

        # ---- 标签页导航 ----
        style = ttk.Style()
        style.configure("TNotebook.Tab", padding=[8, 2])
        # 去掉按钮/复选框点击后的虚线焦点框
        style.configure("TButton", focuscolor="none")
        style.configure("TCheckbutton", focuscolor="none")
        # 去掉顶栏标签点击后的虚线焦点框（移除 Notebook.focus 元素）
        style.layout("TNotebook.Tab", [
            ("Notebook.tab", {"sticky": "nswe", "children": [
                ("Notebook.padding", {"side": "top", "sticky": "nswe", "children": [
                    ("Notebook.label", {"side": "top", "sticky": ""}),
                ]}),
            ]}),
        ])
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # ---- 构建页面 ----
        self._pages = [
            PageOverview(self),
            PageProcess(self),
            PageService(self),
            PageUnlock(self),
            PageBroadcast(self),
            PageDll(self),
            PageBackup(self),
            PageSettings(self),
            PageAbout(self),
            PageAdvanced(self),
        ]

        tab_labels = [
            "概览", "进程", "服务", "解锁", "广播",
            "DLL", "文件", "设置", "关于", "高级",
        ]

        for i, page_cls in enumerate(self._pages):
            page_frame = page_cls.build()
            self.notebook.add(page_frame, text=tab_labels[i])

        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

        # ---- 全局去掉控件的焦点虚线框（按钮/复选框等非输入控件不再抢占焦点）----
        self._disable_widget_focus(self.root)

        # ---- 为输入框统一绑定右键菜单（剪切/复制/粘贴/全选）----
        self._setup_input_context_menu()

        # ---- 启动初始化 ----
        self.pick_a_random_yiyan()
        self.try_restore_settings()
        self.reflashStudentPath(silent=True)
        pass_ui_class(self)

        self.root.mainloop()

    def _disable_widget_focus(self, widget):
        """递归关闭所有非输入控件的焦点（去掉点击后的虚线焦点框）"""
        try:
            if widget.winfo_class() in ("TButton", "TCheckbutton", "TRadiobutton",
                                        "Button", "Checkbutton", "Radiobutton",
                                        "TSpinbox", "Combobox", "TCombobox",
                                        "TNotebook"):
                try:
                    widget.configure(takefocus=0)
                except Exception:
                    pass
        except Exception:
            pass
        try:
            for child in widget.winfo_children():
                self._disable_widget_focus(child)
        except Exception:
            pass

    def _setup_input_context_menu(self):
        """为所有输入框（Entry/Text/Spinbox）统一绑定 Windows 原生右键菜单。

        通过 bind_class 全局绑定，覆盖当前及后续创建的所有输入控件。
        菜单由系统绘制（原生 Windows 主题风格）。
        """
        try:
            from src.gui.widgets import show_native_context_menu

            def _popup(event):
                self._ctx_widget = event.widget
                # 临时把光标改为箭头，避免菜单上显示输入光标(I-beam)
                prev_root = prev_widget = None
                try:
                    prev_root = self.root.cget("cursor")
                    self.root.configure(cursor="arrow")
                except Exception:
                    pass
                try:
                    prev_widget = event.widget.cget("cursor")
                    event.widget.configure(cursor="arrow")
                except Exception:
                    pass
                try:
                    hwnd = self.root.winfo_id()
                except Exception:
                    hwnd = 0
                try:
                    show_native_context_menu(hwnd, event.x_root, event.y_root, [
                        ("剪切", self._ctx_cut),
                        ("复制", self._ctx_copy),
                        ("粘贴", self._ctx_paste),
                        None,
                        ("全选", self._ctx_select_all),
                    ])
                finally:
                    try:
                        self.root.configure(cursor=prev_root or "")
                    except Exception:
                        pass
                    try:
                        event.widget.configure(cursor=prev_widget or "")
                    except Exception:
                        pass

            # ttk 与 tk 输入控件的 class 名
            for cls in ("TEntry", "Entry", "Text", "TSpinbox", "Spinbox"):
                try:
                    self.root.bind_class(cls, "<Button-3>", _popup)
                except Exception:
                    pass
        except Exception:
            pass

    def _ctx_target(self):
        """返回右键菜单的目标控件（若已销毁则返回 None）"""
        w = getattr(self, "_ctx_widget", None)
        if w is not None:
            try:
                w.winfo_exists()
                return w
            except Exception:
                return None
        return None

    def _ctx_cut(self):
        w = self._ctx_target()
        if w:
            try:
                w.event_generate("<<Cut>>")
            except Exception:
                pass

    def _ctx_copy(self):
        w = self._ctx_target()
        if w:
            try:
                w.event_generate("<<Copy>>")
            except Exception:
                pass

    def _ctx_paste(self):
        w = self._ctx_target()
        if w:
            try:
                w.event_generate("<<Paste>>")
            except Exception:
                pass

    def _ctx_select_all(self):
        w = self._ctx_target()
        if w:
            try:
                w.event_generate("<<SelectAll>>")
            except Exception:
                pass

    def _on_close(self):
        """窗口关闭时的清理"""
        try:
            # 取消各页面的定时器（如概览页 3 秒自动刷新），避免残留回调
            for page in self._pages:
                after_id = getattr(page, "_after_id", None)
                if after_id:
                    try:
                        self.root.after_cancel(after_id)
                    except Exception:
                        pass
            self.root.destroy()
        except Exception:
            pass

    def _on_tab_changed(self, event=None):
        if self.notebook:
            self.NowSelIndex = self.notebook.index(self.notebook.select())
            self.pick_a_random_yiyan()
            # 切换到概览页时立即刷新其状态
            if self.NowSelIndex == 0 and self._pages:
                overview = self._pages[0]
                if hasattr(overview, "_refresh"):
                    try:
                        overview._refresh()
                    except Exception:
                        pass

    # ============================================================
    #  学生端相关
    # ============================================================

    def reflashStudentPath(self, *e, silent: bool = False):
        """重新检测学生端路径/进程名/版本。

        silent=True 时不弹窗、不写状态栏，仅更新内部状态，
        结果由概览页（工具箱状态）展示。
        """
        from src.modules.student_detector import detect_student_version
        _ = detect_student_version()
        if toolkit_cfg.oseasypath_have_been_modified:
            ver = toolkit_cfg.student_version
            ver_str = toolkit_cfg.student_version_str
            if ver_str:
                guess_msg = f"学生端版本:V{ver_str}"
            elif ver != 0:
                guess_msg = f"猜测的学生端版本 v{ver / 10}"
            else:
                guess_msg = '检测学生端版本特征失败'
            if not silent:
                self.show_snakemessage(f"更新学生端路径成功\n{toolkit_cfg.oseasy_path}\n学生端进程名:{toolkit_cfg.student_exe_name}\n{guess_msg}")
            # 通知概览页刷新学生端信息
            self._refresh_overview_student_info()
        else:
            if not silent:
                self.show_snakemessage("更新路径失败\n也许是学生端未运行??")

    def _refresh_overview_student_info(self):
        """刷新概览页“工具箱状态”中的学生端信息（若概览页已构建）"""
        overview = self._pages[0] if self._pages else None
        if overview is not None and hasattr(overview, "update_student_info"):
            overview.update_student_info()

    def _on_guaqi_changed(self, e=None):
        self.guaqi_chufa()

    def _on_protect_killer_changed(self, e=None):
        from src.modules.killer import killer_script_protect
        from src.utils.process import is_process_running
        if e.value:
            if not is_process_running(toolkit_cfg.student_exe_name):
                self.show_snakemessage(f"学生端进程 {toolkit_cfg.student_exe_name} 不存在，无法启动循环杀死")
                if self._swc('protect_swc'):
                    self._swc('protect_swc').value = False
                # 已写入 config 的 True 需要回退
                toolkit_cfg.set_config_key_data("protect_killer_enabled", False)
                return
        killer_script_protect()

    def _on_sethc_toggle(self, e=None):
        from src.modules.killer import register_killer_script, del_register_killer
        if self.sethc_swc.value:
            register_killer_script()
        else:
            del_register_killer()

    def guaqi_chufa(self, *e):
        from src.utils.process import suspend_process, resume_process, is_process_running
        if not self.guaqi_runstatus:
            # 挂起前检查进程是否存在，避免 withdraw/deiconify 导致的窗口闪烁
            if not is_process_running(toolkit_cfg.student_exe_name):
                self.show_snakemessage(f"学生端进程 {toolkit_cfg.student_exe_name} 不存在，挂起失败")
                self.guaqi_runstatus = False
                toolkit_cfg.set_config_key_data("guaqi_enabled", False)
                if self._swc('guaqi_sw'):
                    self._swc('guaqi_sw').value = False
                return
            self.root.withdraw()
            status = suspend_process(toolkit_cfg.student_exe_name)
            suspend_process("MultiClient.exe")
            if status is True:
                self.guaqi_runstatus = True
                time.sleep(0.8)
                self.root.deiconify()
            else:
                self.root.deiconify()
                self.guaqi_runstatus = False
                toolkit_cfg.set_config_key_data("guaqi_enabled", False)
                if self._swc('guaqi_sw'):
                    self._swc('guaqi_sw').value = False
                self.show_snakemessage(status)
        else:
            status = resume_process(toolkit_cfg.student_exe_name)
            resume_process("MultiClient.exe")
            if status is True:
                self.guaqi_runstatus = False
                toolkit_cfg.set_config_key_data("guaqi_enabled", False)
            else:
                self.guaqi_runstatus = True
                toolkit_cfg.set_config_key_data("guaqi_enabled", True)
                if self._swc('guaqi_sw'):
                    self._swc('guaqi_sw').value = True
                self.show_snakemessage(status)

    # ============================================================
    #  外观 / 一言
    # ============================================================

    def toggle_random_yiyan(self, e=None):
        if e is not None:
            self.random_yy_enabled = e.value
        self.pick_a_random_yiyan()

    def try_restore_settings(self):
        """从配置文件恢复用户设置状态"""
        from src.utils.logger import debug, exception as _log_exc
        try:
            self._try_restore_settings_impl()
        except Exception:
            _log_exc("恢复设置时出现异常")

    def _try_restore_settings_impl(self):
        # 随机一言
        saved_yy = toolkit_cfg.get_config_key_data("random_yiyan_enabled")
        if saved_yy is not None:
            self.random_yy_enabled = bool(saved_yy)
            self.pick_a_random_yiyan()

        # 背景不透明度
        saved_opacity = toolkit_cfg.get_config_key_data("bg_opacity")
        if saved_opacity is not None:
            try:
                self.bgtmd = float(saved_opacity)
            except (TypeError, ValueError):
                pass

        # 挂起学生端状态
        saved_guaqi = toolkit_cfg.get_config_key_data("guaqi_enabled")
        if saved_guaqi is not None:
            self.guaqi_runstatus = bool(saved_guaqi)
            # 启动时若已挂起但进程不存在，重置状态
            if self.guaqi_runstatus:
                from src.utils.process import is_process_running
                if not is_process_running(toolkit_cfg.student_exe_name):
                    self.guaqi_runstatus = False
                    toolkit_cfg.set_config_key_data("guaqi_enabled", False)

        # 置顶窗口
        saved_topmost = toolkit_cfg.get_config_key_data("topmost_enabled")
        if saved_topmost is not None and self.root:
            self.root.attributes("-topmost", bool(saved_topmost))

        # 恢复背景路径
        bgPath = toolkit_cfg.get_style_path("bgPath")
        if bgPath:
            self.bgpath = bgPath
            self.loaded_bg = True

        # 恢复一言路径
        yiyanPath = toolkit_cfg.get_style_path("yiyanPath")
        if yiyanPath:
            self.yiyanfpath = yiyanPath
            self.from_file_load_yiyan()

        # 初始注册快捷键
        self.hotkeyManager.switch_by_name("hide_tbox", self.hide_tbox_swc.value, self.hide_toolkit_helper)
        self.hotkeyManager.switch_by_name("fast_screenshot", self.FastGetSC.value, self._scshot_callback)

        # 启动时若循环杀死开关为 ON 但进程不存在，自动关掉
        from src.utils.process import is_process_running
        if (self._swc('protect_swc') and self._swc('protect_swc').value
                and not is_process_running(toolkit_cfg.student_exe_name)):
            self._swc('protect_swc').value = False
            toolkit_cfg.set_config_key_data("protect_killer_enabled", False)

        # 恢复 Toast 通知设置
        saved_toast = toolkit_cfg.get_config_key_data("toast_notification_enabled")
        if saved_toast is not None:
            self._toast_enabled = bool(saved_toast)

    def _restore_broadcast_hotkeys(self):
        """广播页快捷键初始注册"""
        if getattr(self, '_broadcast_hotkeys_restored', False):
            return
        self._broadcast_hotkeys_restored = True
        self.hotkeyManager.switch_by_name("run_window_broadcast", self.runwindows_swc.value, self._get_broadcast_page().run_win_gbcmd_loj)
        self.hotkeyManager.switch_by_name("kill_screen_render", self.KillSCR_swc.value, self.direct_kill_screen_render)
        self.hotkeyManager.switch_by_name("run_fullscreen_broadcast", self.RunFullSC_swc.value, self.direct_run_fullscreen_broadcast_cmd)

    def _get_broadcast_page(self):
        """按类型查找广播页实例（不依赖固定索引，避免页面增删导致偏移）"""
        from src.gui.pages.page_broadcast import PageBroadcast
        for page in self._pages:
            if isinstance(page, PageBroadcast):
                return page
        return None

    def pick_a_random_yiyan(self, *e):
        if self.random_yy_enabled:
            if hasattr(self, "yiyanlist") and self.yiyanlist:
                pickindex = random.randint(0, len(self.yiyanlist) - 1)
                text = self.yiyanlist[pickindex]
            else:
                pickindex = random.randint(0, len(DEFAULT_YIYAN_LIST) - 1)
                text = DEFAULT_YIYAN_LIST[pickindex]
        else:
            text = DEFAULT_SHOW_YIYAN
        self.yiyan_var.set(text)

    def from_file_load_yiyan(self):
        toolkit_cfg.set_style_path("yiyanPath", self.yiyanfpath)
        try:
            with open(self.yiyanfpath, "r", encoding="utf-8") as fm:
                list_get = fm.read().split("^")
            self.ex_fullindex = len(list_get)
            self.yiyanlist = list_get
            self.defult_yy = False
            self.show_snakemessage("成功加载外部一言库")
        except Exception as e:
            self.show_snakemessage(f"加载外部一言时出现{e}异常")

    # ============================================================
    #  通用工具（委托到 widgets.py）
    # ============================================================

    make_scrollable = staticmethod(make_scrollable)
    make_output_text = staticmethod(make_output_text)
    append_text = staticmethod(append_text)
    clear_text = staticmethod(clear_text)

    def _run_in_thread(self, func, label: str = "操作"):
        """在后台线程执行函数，避免阻塞 UI"""
        from src.utils.logger import debug, exception
        def _wrapper():
            debug(f"[线程] {label} 开始")
            try:
                func()
            except Exception:
                exception(f"{label} 异常")
            debug(f"[线程] {label} 结束")
        threading.Thread(target=_wrapper, daemon=True).start()

    def show_snakemessage(self, showtext: str):
        """显示消息到状态栏（3 秒后自动消失）；若 toast 开关打开，同步发 Windows 通知"""
        if self.status_var:
            self.status_var.set(showtext)
        if self.root:
            self.root.after(3000, lambda: self.status_var.set("") if self.status_var else None)
        if self._toast_enabled:
            self.show_toast("OsEasy-ToolKit", showtext)

    def show_toast(self, title: str, msg: str):
        """发送标准 Windows Toast 通知（ToastGeneric 模板，第一行小图标+标题、第二行内容）"""
        if not self._toast_enabled:
            return
        from src.utils.toast import send_toast
        send_toast(title=title, msg=msg)

    def bind_tooltip(self, widget, tooltip_id: str, **fmt_kwargs):
        """为控件绑定悬停提示：鼠标移入时在状态栏显示说明，移出时清空"""
        from config import TOOLTIPS
        from src.core.settings import toolkit_cfg
        description = TOOLTIPS.get(tooltip_id, tooltip_id)
        # 自动注入路径占位符（若文案中引用了它们）
        data_dir = os.path.dirname(toolkit_cfg.config_file_path)
        if "{data_dir}" in description:
            fmt_kwargs.setdefault("data_dir", data_dir)
        if "{student_dir}" in description:
            fmt_kwargs.setdefault("student_dir", toolkit_cfg.oseasy_path)
        if "{backup_dir}" in description:
            fmt_kwargs.setdefault("backup_dir", os.path.join(data_dir, "backups"))
        if fmt_kwargs:
            description = description.format(**fmt_kwargs)
        def _enter(_e):
            if self.status_var:
                self.status_var.set(description)
        def _leave(_e):
            if self.status_var:
                self.status_var.set("")
        widget.bind("<Enter>", _enter)
        widget.bind("<Leave>", _leave)


ToolKit = Ui()