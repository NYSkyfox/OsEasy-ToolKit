# src/gui/pages/page_process.py
# 进程管理页（页面 1）

import tkinter as tk
from tkinter import ttk, messagebox
import os

from src.core.settings import toolkit_cfg
from src.modules.killer import (
    launch_oe_toolkit, is_sethc_hijacked, is_killer_protected,
)
from src.modules import power_control
from src.modules.service_manager import handle_start_student_client
from src.gui.switch import PersistentSwitch


class PageProcess:

    def __init__(self, ui):
        self.ui = ui

    # ─────────────────────── 远程重启/关机拦截 ───────────────────────

    def _open_power_dialog(self):
        """弹出"拦截远程重启/关机"对话框，可选择文件版或内存版。"""
        ui = self.ui
        dlg = tk.Toplevel(ui.root)
        dlg.title("拦截教师端远程重启/关机")
        dlg.geometry("520x420")
        dlg.resizable(False, False)
        dlg.transient(ui.root)
        dlg.grab_set()

        # ── 状态区 ──
        status_frame = ttk.LabelFrame(dlg, text="当前状态", padding=6)
        status_frame.pack(fill=tk.X, padx=8, pady=(8, 4))

        file_st = "已拦截" if power_control.is_file_patched() else "未拦截"
        try:
            found, mem_patched, mem_detail = power_control.is_memory_patched()
            mem_st = "已拦截" if (found and mem_patched) else ("未拦截" if found else "进程未运行")
        except Exception:
            mem_st = "未知"

        ttk.Label(status_frame, text=f"文件版: {file_st}    内存版: {mem_st}",
                  font=("", 10, "bold")).pack(anchor=tk.W)

        # ── 模式选择 ──
        mode_frame = ttk.LabelFrame(dlg, text="运行方式", padding=6)
        mode_frame.pack(fill=tk.X, padx=8, pady=4)
        mode_var = tk.StringVar(value="memory")  # 默认内存版
        rb_file = ttk.Radiobutton(mode_frame, text="文件版 —— 改磁盘 Student.exe（持久，需先结束学生端再重启）",
                                  variable=mode_var, value="file")
        rb_file.pack(anchor=tk.W, padx=2, pady=1)
        rb_mem = ttk.Radiobutton(mode_frame, text="内存版 —— 改运行中进程内存（即时生效，进程重启自动恢复，需管理员）",
                                 variable=mode_var, value="memory")
        rb_mem.pack(anchor=tk.W, padx=2, pady=1)

        # ── 按钮区 ──
        btn_frame = ttk.Frame(dlg, padding=(8, 4))
        btn_frame.pack(fill=tk.X)
        btn_patch = ttk.Button(btn_frame, text="执行拦截", command=lambda: _do("patch"))
        btn_patch.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        btn_restore = ttk.Button(btn_frame, text="执行还原", command=lambda: _do("restore"))
        btn_restore.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=2)
        ttk.Button(dlg, text="关闭", command=dlg.destroy).pack(pady=(4, 8))

        # ── 结果区 ──
        result_frame = ttk.LabelFrame(dlg, text="结果", padding=4)
        result_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=(0, 8))
        result_text = tk.Text(result_frame, height=8, background="#1e1e1e",
                              foreground="#d4d4d4", font=("Consolas", 9),
                              state=tk.DISABLED, wrap=tk.WORD)
        sb = ttk.Scrollbar(result_frame, command=result_text.yview)
        result_text.configure(yscrollcommand=sb.set)
        result_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        sb.pack(side=tk.RIGHT, fill=tk.Y)

        def _append(msg):
            result_text.configure(state=tk.NORMAL)
            result_text.insert(tk.END, msg + "\n")
            result_text.see(tk.END)
            result_text.configure(state=tk.DISABLED)

        def _do(action):
            mode = mode_var.get()
            btn_patch.config(state="disabled")
            btn_restore.config(state="disabled")
            _append(f"\n--- {action} ({mode}) ---")
            try:
                if action == "patch":
                    ok, msg = power_control.patch(mode)
                else:
                    ok, msg = power_control.restore(mode)
                _append(msg)
                _append("=> " + ("成功" if ok else "失败"))
                # 刷新状态
                file_st2 = "已拦截" if power_control.is_file_patched() else "未拦截"
                try:
                    f2, m2, _ = power_control.is_memory_patched()
                    mem_st2 = "已拦截" if (f2 and m2) else ("未拦截" if f2 else "进程未运行")
                except Exception:
                    mem_st2 = "未知"
            except Exception as e:
                _append(f"异常: {e!r}")
            finally:
                btn_patch.config(state="normal")
                btn_restore.config(state="normal")
                # 更新状态标签（重新读取）
                # 简单做法：直接关弹窗让用户重新打开看状态
                # 或者用 after 更新（这里用简单方案）

    # ─────────────────────── UI 构建 ───────────────────────

    def build(self):
        ui = self.ui
        frame = ttk.Frame(ui.notebook)

        # ---- 上部：控件（可滚动） ----
        _, ctrl_frame = ui.make_scrollable(frame)

        proc_frame = ttk.LabelFrame(ctrl_frame, text="进程操作", padding=5)
        proc_frame.pack(fill=tk.X, pady=2)
        btn1 = ttk.Button(proc_frame, text="重启学生端", command=handle_start_student_client)
        btn1.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn1, "FUNC_RESTART_STUDENT")
        btn2 = ttk.Button(proc_frame, text="重新获取学生端路径", command=ui.reflashStudentPath)
        btn2.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn2, "FUNC_REFRESH_STUDENT_PATH")

        switch_frame = ttk.LabelFrame(ctrl_frame, text="功能开关", padding=5)
        switch_frame.pack(fill=tk.X, pady=2)
        ui.sethc_swc = PersistentSwitch(switch_frame, live_getter=is_sethc_hijacked, verifier=is_sethc_hijacked,
                                         label="劫持粘滞键 (sethc.exe)", on_toggle=ui._on_sethc_toggle)
        ui.sethc_swc.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.sethc_swc, "FUNC_HIJACK_SETHC")
        ui.protect_swc = PersistentSwitch(switch_frame, config_key="protect_killer_enabled",
                                           label="循环杀死学生端", verifier=is_killer_protected,
                                           on_toggle=ui._on_protect_killer_changed)
        ui.protect_swc.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.protect_swc, "FUNC_PROTECT_KILLER")
        ui.guaqi_sw = PersistentSwitch(switch_frame, config_key="guaqi_enabled",
                                        label="挂起学生端", on_toggle=ui._on_guaqi_changed)
        ui.guaqi_sw.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(ui.guaqi_sw, "FUNC_SUSPEND_STUDENT")

        # 防护（从原"其他管理"页移入）
        protect_frame = ttk.LabelFrame(ctrl_frame, text="防护", padding=5)
        protect_frame.pack(fill=tk.X, pady=2)
        btn_power = ttk.Button(protect_frame, text="拦截教师端远程重启/关机",
                               command=self._open_power_dialog)
        btn_power.pack(fill=tk.X, padx=2, pady=1)
        ui.bind_tooltip(btn_power, "FUNC_BLOCK_REMOTE_POWER")

        quick_frame = ttk.LabelFrame(ctrl_frame, text="快捷操作", padding=5)
        quick_frame.pack(fill=tk.X, pady=2)
        btn3 = ttk.Button(quick_frame, text="打开噢易自带工具", command=launch_oe_toolkit)
        btn3.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn3, "FUNC_LAUNCH_OE_TOOLKIT")
        btn4 = ttk.Button(quick_frame, text="打开OsEasy安装目录", command=self.open_oseasy_dir)
        btn4.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn4, "FUNC_OPEN_OE_DIR")
        btn5 = ttk.Button(quick_frame, text="打开ToolKit数据文件夹", command=self.open_toolkit_data_dir)
        btn5.pack(fill=tk.X, padx=2, pady=2)
        ui.bind_tooltip(btn5, "FUNC_OPEN_DATA_DIR")

        # ---- 下部：输出区域（固定底部） ----
        output_frame = ttk.Frame(frame)
        output_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=2)
        self.output_text = ui.make_output_text(output_frame, height=5)

        return frame

    def open_oseasy_dir(self, *e):
        path = toolkit_cfg.oseasy_path
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.ui.show_snakemessage(f"目录不存在: {path}")

    def open_toolkit_data_dir(self, *e):
        from config import DATA_ROOT_TEMPLATE
        path = DATA_ROOT_TEMPLATE.format(username=os.environ.get('USERNAME', 'Default'))
        if os.path.exists(path):
            os.startfile(path)
        else:
            self.ui.show_snakemessage(f"目录不存在: {path}")