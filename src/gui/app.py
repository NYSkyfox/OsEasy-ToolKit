# src/gui/app.py
# 工具箱主 UI 类

import os
import time
import random
import ctypes
from ctypes import wintypes

import flet as ft
from pynput import keyboard

from config import APP_VERSION, DEFAULT_FONT_PATH, DEFAULT_YIYAN_LIST

from src.core.runtime_config import toolbox_cfg
from src.core.helpers import (
    pass_ui_class, del_historyrem, open_github_page, run_sigle_cmd,
)
from src.modules.service_manager import (
    check_mmpc_status, handle_start_student_client,
    try_guess_student_client_version, if_is_high_ver_client_auto_close_mmpc_helper,
)
from src.modules.process_manager import (
    utils, get_proc_pid, get_scshot,
)
from src.modules.killer import (
    register_killer_script, del_register_killer, killer_script_protect,
    del_locked_exe_then_logout, start_oseasy_self_toolbox,
)
from src.modules.file_handler import (
    restone_oe_backup_key_dll, restone_sigle_oe_backup_file,
    del_self_cmd_files,
)
from src.modules.usb_network_unlock import (
    usb_unlock, handle_run_old_unlock_net,
)
from src.modules.broadcast_handler import (
    replace_screen_render, restone_screen_render,
    check_replace_screen_render_status,
    from_log_file_get_remote_cmd, build_run_broadcast_cmd,
    save_now_broadcast_cmd, from_scr_log_cmd_get_yccmd,
    handin_save_yc_cmd, generate_remote_cmd_and_save,
)
from src.modules.dll_manager import run_easy_dll
from src.gui.hotkey_manager import hotkey_manager

fontpath = DEFAULT_FONT_PATH


class Ui:

    def __init__(self) -> None:

        self.ver = APP_VERSION
        self.hotkeyManager = hotkey_manager()
        self.guaqi_runstatus = False
        self.bgtmd = 0.6
        self.defult_yy = True
        self.font_loadtime = 1
        self.NowSelIndex = "0"
        self.yiyanshowtext = ft.Text("", size=16)
        self.yiyanshowtext2 = ft.Text("", size=16)
        self.loaded_bg = False

    def direct_run_fullscreen_boradcast_cmd(self):
        """按钮点击直接运行全屏广播指令"""
        status = from_log_file_get_remote_cmd()
        if self.KillSCR_swc.value == True:
            if status == None:
                self.show_snakemessage("未拦截到控制命令参数")
            else:
                cmd = status.replace("#fullscreen#:0", "#fullscreen#:1")
                builded = build_run_broadcast_cmd(cmd)
                print("DEBUG with build cmd", builded)
                run_sigle_cmd(builded)
        else:
            self.show_snakemessage(
                "警告！ 未开启快捷键杀广播进程\n尝试运行的操作已拦截...."
            )

    def direct_kill_screen_render(self, *e):
        """点击按钮直接杀屏幕广播进程"""
        run_sigle_cmd("taskkill /f /t /im ScreenRender_Y.exe")
        run_sigle_cmd("taskkill /f /t /im ScreenRender.exe")

    def theme_changed(self, *e):
        self.page.theme_mode = (
            ft.ThemeMode.DARK
            if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT
        )
        self.ztqhb.label = (
            "亮色主题" if self.page.theme_mode == ft.ThemeMode.LIGHT else "暗色主题"
        )
        self.page.update()

    def try_get_history_path(self):
        """尝试获取历史路径"""
        fstst = toolbox_cfg.first_launch_check()
        if fstst != True:
            bgPath = toolbox_cfg.get_style_path("bgPath")
            if bgPath:
                self.bgpath = bgPath
                self.bgtmdb.disabled = False
                self.loaded_bg = True
                self.reflash_ui_bg()
            yiyanPath = toolbox_cfg.get_style_path("yiyanPath")
            if yiyanPath:
                self.yiyanfpath = yiyanPath
                self.from_file_load_yiyan()
            fontPath = toolbox_cfg.get_style_path("fontPath")
            if fontPath:
                self.zdy_fontpath = fontPath
                self.setup_zidingyi_font()

    def enable_usb(self):
        pass

    def close_askdel_dlg(self, xueze):
        self.unlock_func_askdlg.open = False
        self.page.update()
        if xueze == None:
            self.show_snakemessage("取消解锁了")
        else:
            del_locked_exe_then_logout(xueze)

    def open_askdel_dlg(self, *e):
        self.page.dialog = self.unlock_func_askdlg
        self.unlock_func_askdlg.open = True
        self.page.update()

    def close_col_readme_dlg(self):
        self.col_readme_dlg.open = False
        self.show_snakemessage("Have Fun")
        self.page.update()

    def open_col_readme_dlg(self, *e):
        self.page.dialog = self.col_readme_dlg
        self.col_readme_dlg.open = True
        self.page.update()

    def main(self, bruh: ft.Page):
        self.page = bruh
        self.page.title = self.ver
        self.page.fonts = {"ht": fontpath}
        self.page.theme = ft.Theme(font_family="ht")
        self.page.update()
        self.page.window_height = 635
        self.page.window_width = 450
        self.page.window_max_height = 2000
        self.page.window_max_width = 455
        self.page.window_min_height = 620
        self.page.window_min_width = 449
        self.page.update()

        self.unlock_func_askdlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("解锁选项"),
            content=ft.Text(
                "选择适合你的选项\n三者一起: 删除黑屏安静+解除键盘锁+删除控屏锁定程序 (需要注销)\n仅控屏: 仅删除控屏锁定程序"
            ),
            actions=[
                ft.TextButton("三者一起", on_click=lambda _: self.close_askdel_dlg(xueze=True)),
                ft.TextButton("仅控屏锁定程序", on_click=lambda _: self.close_askdel_dlg(xueze=False)),
                ft.TextButton("取消", on_click=lambda _: self.close_askdel_dlg(xueze=None)),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )

        self.col_readme_dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("控屏管理页使用说明"),
            content=ft.Text(
                "在使用前请先使用解锁键盘锁&删除控制锁定软件功能\n点击替换拦截程序后再恢复控屏软件\n等待老师控制屏幕后即完成拦截远程命令\n完成替换后即可重新删除控屏软件\n此时当老师处于控制状态时你可以主动运行命令弹出窗口化共享屏幕\n实现自由的同时不影响听课!!\n当老师来时你可以使用快捷键启动全屏参数的控制\n等待老师走后再用快捷键清理进程"
            ),
            actions=[
                ft.TextButton("晓得了", on_click=lambda _: self.close_col_readme_dlg()),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
            on_dismiss=lambda _: self.close_col_readme_dlg(),
        )

        self.pick_files_dialog = ft.FilePicker(on_result=self.pick_files_result)
        self.yiyan_pick_files_dialog = ft.FilePicker(on_result=self.yiyan_pick_files_result)
        self.font_pick_files_dialog = ft.FilePicker(on_result=self.font_pick_files_result)

        self.bgfilepick = ft.ElevatedButton(
            "切换背景图片",
            icon=ft.icons.UPLOAD_FILE,
            on_click=lambda _: self.pick_files_dialog.pick_files(
                allow_multiple=False, file_type="IMAGE"
            ),
        )

        self.ztqhb = ft.Switch(label="亮色主题", on_change=self.theme_changed, value=True)
        self.bgtmd_text = ft.Text("滑动以调整背景图片不透明度")
        self.bgtmdb = ft.Slider(min=0.0, max=1.0, divisions=0.1, value=0.6, on_change_end=self.change_bg_btmd, disabled=True)
        self.yiyanbtn = ft.ElevatedButton(
            "加载外部一言文件",
            icon=ft.icons.UPLOAD_SHARP,
            on_click=lambda _: self.yiyan_pick_files_dialog.pick_files(allow_multiple=False, allowed_extensions=["txt"]),
        )
        self.zitibtn = ft.ElevatedButton(
            "更换显示字体",
            icon=ft.icons.UPLOAD_SHARP,
            on_click=lambda _: self.font_pick_files_dialog.pick_files(allow_multiple=False, allowed_extensions=["ttf"]),
        )
        self.remove_rem = ft.ElevatedButton("清除历史路径记忆", icon=ft.icons.DELETE_OUTLINE, on_click=del_historyrem)

        self.list_all_pickdialog = [self.pick_files_dialog, self.yiyan_pick_files_dialog, self.font_pick_files_dialog]

        self.guaqi_sw = ft.Switch(label="挂起学生端", active_color="pink", on_change=self.guaqi_chufa)
        self.mmpc_sw = ft.FilledTonalButton(
            text="长按开&关学生端根服务",
            icon=ft.icons.BACK_HAND_OUTLINED,
            on_long_press=lambda _: run_sigle_cmd("sc stop MMPC") if check_mmpc_status() else run_sigle_cmd("sc start MMPC"),
            on_hover=self.only_update_MMPC_status,
        )
        self.mmpc_Stext = ft.TextField(
            label="根服务状态", value="未知 (点我更新状态)", read_only=True,
            on_focus=self.only_update_MMPC_status, text_align=ft.TextAlign.CENTER,
        )

        self.FastGetSC = ft.Switch(
            label="Alt+X 快捷键屏幕截图",
            on_change=lambda _: self.hotkeyManager.switch_reg_helper(self.FastGetSC.value, [keyboard.Key.alt_l, 'x'], get_scshot)
        )

        self.funcTab_Stuff = ft.Column(controls=[
            self.yiyanshowtext, ft.Divider(height=1),
            self.mmpc_Stext, self.mmpc_sw,
            ft.FilledTonalButton(text="长按重启学生端", icon=ft.icons.RESTORE, on_long_press=handle_start_student_client),
            ft.FilledTonalButton(text="重新获取学生端路径", icon=ft.icons.REFRESH, on_click=self.reflashStudentPath),
            ft.FilledTonalButton(text="注册粘滞键替换", icon=ft.icons.FILE_COPY_ROUNDED, on_click=lambda _: register_killer_script()),
            ft.FilledTonalButton(text="还原粘滞键", icon=ft.icons.FILE_COPY_ROUNDED, on_click=lambda _: del_register_killer()),
            ft.Switch(label="外部cmd守护进程", active_color="green", on_change=lambda _: killer_script_protect()),
            self.guaqi_sw,
            ft.FilledTonalButton(text="打开噢易自带工具", icon=ft.icons.OPEN_IN_NEW, on_click=start_oseasy_self_toolbox),
        ])

        self.func_SecondTab_Stuff = ft.Column(controls=[
            self.yiyanshowtext, ft.Divider(height=1),
            ft.FilledTonalButton(text="长按以删除脚本文件", icon=ft.icons.CLEANING_SERVICES_OUTLINED, on_long_press=lambda _: del_self_cmd_files()),
            ft.FilledTonalButton(text="删除键盘锁驱动&控屏锁定程序", icon=ft.icons.KEYBOARD_SHARP, on_click=self.open_askdel_dlg),
            ft.FilledTonalButton(text="长按恢复所有备份文件", icon=ft.icons.RESTORE, on_long_press=lambda _: restone_oe_backup_key_dll()),
            ft.FilledTonalButton(text="长按以恢复黑屏安静程序", icon=ft.icons.ACCOUNT_BOX, on_long_press=lambda _: restone_sigle_oe_backup_file("BlackSlient.exe")),
            ft.FilledTonalButton(text="长按以仅恢复控屏锁定程序", icon=ft.icons.SCREEN_SHARE_SHARP, on_long_press=lambda _: restone_sigle_oe_backup_file("MultiClient.exe")),
            ft.FilledTonalButton(text="停止网络管控服务(不可逆)", icon=ft.icons.WIFI_PASSWORD_SHARP, on_click=lambda _: handle_run_old_unlock_net()),
            ft.FilledTonalButton(text="[无法正常工作] 关闭USB管控服务", icon=ft.icons.USB_SHARP, on_click=lambda _: usb_unlock()),
            self.FastGetSC,
        ])

        self.teachIp_input = ft.TextField(label="输入教师机IP地址")
        self.auto_gennerate_cmd = ft.FilledTonalButton(text="由教师机IP生成远程命令", icon=ft.icons.DRAW, on_click=lambda _: generate_remote_cmd_and_save(self.teachIp_input.value))
        self.conl_save_ycCmd_input = ft.TextField(label="键入完整的远程广播命令")
        self.conl_ycCmd_update_with_replace_ip = ft.FilledTonalButton("自动替换本地IP并更新命令", on_click=lambda _: handin_save_yc_cmd(self.conl_save_ycCmd_input.value, True), icon=ft.icons.DRAW)
        self.conl_ycCmd_update = ft.FilledTonalButton("手动更新完整远程广播命令", on_click=lambda _: handin_save_yc_cmd(self.conl_save_ycCmd_input.value, False), icon=ft.icons.MODE_EDIT_SHARP)
        self.conl_from_log_get_cmd = ft.FilledTonalButton(text="从日志文件获取远程命令", icon=ft.icons.BOOK, on_click=lambda _: from_scr_log_cmd_get_yccmd())
        self.conl_getyccmd_btn = ft.FilledTonalButton(text="读取已拦截的广播命令", icon=ft.icons.BOOK, on_click=self.dev_read_lj_cmd_loj)
        self.col_readme_dig = ft.FilledButton("点我查看此页面的使用说明", on_click=self.open_col_readme_dlg)
        self.RunFullSC_btn = ft.FilledTonalButton("长按运行全屏广播命令", on_long_press=lambda _: self.direct_run_fullscreen_boradcast_cmd(), icon=ft.icons.FULLSCREEN)
        self.restone_scr = ft.FilledTonalButton(text="恢复原有屏幕广播程序", on_click=self.restone_SCR_loj, icon=ft.icons.RESTORE_PAGE)
        self.tihuan_scr = ft.FilledTonalButton(text="替换拦截命令程序", on_click=self.replace_SCR_loj, icon=ft.icons.FIND_REPLACE)
        self.RunFullSC_swc = ft.Switch(label="Ctrl+Alt+F 以全屏运行广播命令", on_change=lambda _: self.hotkeyManager.switch_reg_helper(self.RunFullSC_swc.value, [keyboard.Key.ctrl_l, keyboard.Key.alt_l, keyboard.KeyCode.from_vk(70)], ToolBox.direct_run_fullscreen_boradcast_cmd), active_color="pink")
        self.KillSCR_btn = ft.FilledTonalButton("手动杀屏幕广播进程", icon=ft.icons.BACK_HAND_OUTLINED, on_click=self.direct_kill_screen_render)
        self.KillSCR_swc = ft.Switch(label="Alt+K 杀屏幕广播进程", on_change=lambda _: self.hotkeyManager.switch_reg_helper(self.KillSCR_swc.value, [keyboard.Key.alt_l, 'k'], ToolBox.direct_kill_screen_render), active_color="pink")
        self.runwindows_swc = ft.Switch(label="Alt+U 运行窗口屏幕广播", on_change=lambda _: self.hotkeyManager.switch_reg_helper(self.runwindows_swc.value, [keyboard.Key.alt_l, 'u'], ToolBox.run_win_gbcmd_loj), active_color="pink")
        self.try_read_sharecmd = ft.FilledTonalButton(text="运行窗口化广播命令", on_click=self.run_win_gbcmd_loj, icon=ft.icons.WINDOW_SHARP)
        self.hide_tbox_swc = ft.Switch(label="capsLock + enter 隐&显工具箱", on_change=lambda _: self.hotkeyManager.switch_reg_helper(self.hide_tbox_swc.value, [keyboard.Key.caps_lock, keyboard.Key.enter], ToolBox.hide_toolbox_helper), value=True)

        self.waiguanTab_Stuff = ft.Column(controls=[
            self.yiyanshowtext, ft.Divider(height=1), self.ztqhb, self.remove_rem,
            self.zitibtn, self.bgfilepick, self.bgtmd_text, self.bgtmdb, self.yiyanbtn,
        ])

        self.MyRail = ft.NavigationRail(
            selected_index=0, label_type="ALL", min_width=30, min_extended_width=30,
            group_alignment=-0.8, expand=False,
            destinations=[
                ft.NavigationRailDestination(icon_content=ft.Icon(ft.icons.AUTO_FIX_HIGH_OUTLINED), selected_icon_content=ft.Icon(ft.icons.AUTO_FIX_HIGH), label="进程管理"),
                ft.NavigationRailDestination(icon=ft.icons.INTEGRATION_INSTRUCTIONS_OUTLINED, selected_icon_content=ft.Icon(ft.icons.INTEGRATION_INSTRUCTIONS), label_content=ft.Text("其他管理")),
                ft.NavigationRailDestination(icon=ft.icons.SCREEN_SHARE_OUTLINED, selected_icon_content=ft.Icon(ft.icons.SCREEN_SHARE_SHARP), label_content=ft.Text("广播管理")),
                ft.NavigationRailDestination(icon=ft.icons.VPN_KEY_OUTLINED, selected_icon_content=ft.Icon(ft.icons.VPN_KEY), label="广播命令"),
                ft.NavigationRailDestination(icon=ft.icons.KEYBOARD_OPTION_KEY_OUTLINED, selected_icon_content=ft.Icon(ft.icons.KEYBOARD_OPTION_KEY), label="DLL工具"),
                ft.NavigationRailDestination(icon=ft.icons.STYLE_OUTLINED, selected_icon_content=ft.Icon(ft.icons.STYLE), label_content=ft.Text("外观")),
                ft.NavigationRailDestination(icon=ft.icons.FAVORITE_BORDER_OUTLINED, selected_icon_content=ft.Icon(ft.icons.FAVORITE, color="red"), label="关于"),
            ],
            on_change=lambda e: self.selPages_Helper(e.control.selected_index),
        )

        self.pick_a_random_yiyan()
        self.switch_main_page_0()
        self.added_pickdialog()
        self.try_get_history_path()
        self.reflashStudentPath()
        pass_ui_class(self)
        self.hotkeyManager.switch_reg_helper(self.hide_tbox_swc.value, [keyboard.Key.caps_lock, keyboard.Key.enter], ToolBox.hide_toolbox_helper)

    def reflashStudentPath(self, *e):
        """重新获取学生端路径"""
        _ = try_guess_student_client_version()
        if toolbox_cfg.oseasypath_have_been_modified != False:
            guess_msg = f"猜测的学生端版本 v{_ / 10}" if _ != 0 else '检测学生端版本特征失败'
            self.show_snakemessage(f"更新学生端路径成功\n{toolbox_cfg.oseasy_path}\n学生端进程名:{toolbox_cfg.student_exe_name}\n{guess_msg}")
        else:
            self.show_snakemessage(f"更新路径失败\n也许是学生端未运行??")

    def selPages_Helper(self, index):
        self.NowSelIndex = str(index)
        self.pick_a_random_yiyan()
        {
            0: self.switch_main_page_0,
            1: self.switch_main_page_1,
            2: self.switch_main_page_2,
            3: self.switch_main_page_3,
            4: self.switch_main_page_4,
            5: self.switch_main_page_5,
            6: self.switch_main_page_6,
        }.get(index, lambda: None)()

    def apply_bg_to_ui(self, needLoad_Stuff_list: list):
        if self.loaded_bg == True:
            bgb = ft.Stack(controls=[self.col_imgbg, needLoad_Stuff_list])
            nedadd = ft.Row([self.MyRail, ft.VerticalDivider(width=0), bgb], height=self.page.window_height, width=self.page.window_width)
            self.page.clean()
            self.page.update()
            self.page.add(nedadd)
            self.page.update()
        else:
            nedadd = ft.Row([self.MyRail, ft.VerticalDivider(width=1), needLoad_Stuff_list], height=self.page.window_height, width=self.page.window_width)
            self.page.clean()
            self.page.update()
            self.page.add(nedadd)
            self.page.update()

    def switch_main_page_0(self):
        self.mmpc_Stext.value = "未知 (随时都可以点我更新状态)"
        self.apply_bg_to_ui(needLoad_Stuff_list=self.funcTab_Stuff)

    def switch_main_page_1(self):
        self.apply_bg_to_ui(needLoad_Stuff_list=self.func_SecondTab_Stuff)

    def run_win_gbcmd_loj(self, *e):
        get = from_log_file_get_remote_cmd()
        if get == None:
            self.show_snakemessage("未拦截到控制命令参数")
        else:
            bcmd = build_run_broadcast_cmd(YC_command=get)
            bcmd = bcmd.replace("#fullscreen#:1","#fullscreen#:0")
            run_sigle_cmd(bcmd)

    def replace_SCR_loj(self, *e):
        if_is_high_ver_client_auto_close_mmpc_helper()
        time.sleep(1)
        self.show_snakemessage("开始替换程序 请稍等...\n这大约需要6秒左右")
        status = replace_screen_render()
        if status == False:
            self.show_snakemessage("替换拦截程序失败 未检测到可替换程序\n请确保ScreenRender_Helper.exe\n与工具箱处在同一目录")
        else:
            self.show_snakemessage("理论上已经成功替换拦截程序\n可自行检查替换结果")

    def restone_SCR_loj(self, *e):
        if_is_high_ver_client_auto_close_mmpc_helper()
        time.sleep(1)
        self.show_snakemessage("开始还原替换程序 请稍等...")
        status = restone_screen_render()
        if status == False:
            self.show_snakemessage("尝试恢复拦截程序时失败\n未检测到被重命名的ScreenRender.exe")
        else:
            self.show_snakemessage("理论上已经成功恢复原有程序")

    def dev_read_lj_cmd_loj(self, *e):
        status = save_now_broadcast_cmd()
        if status == None:
            self.show_snakemessage("未拦截到控制命令参数")
        else:
            self.show_snakemessage("保存拦截命令成功")

    def update_replace_status(self, *e):
        if check_replace_screen_render_status():
            self.show_snakemessage("检测到目录下已有ScreenRender_Y.exe")
            self.replace_status.value = "已替换"
        else:
            self.show_snakemessage("未检测到ScreenRender_Y.exe\n也许未执行替换或替换过程被打断")
            self.replace_status.value = "未替换"
        self.page.update()

    def switch_main_page_2(self):
        self.replace_status = ft.TextField(label="替换程序状态", value="未知 (点我更新状态)", read_only=True, on_focus=self.update_replace_status, text_align=ft.TextAlign.CENTER)
        self.ConlTab_Stuff = ft.Column([self.yiyanshowtext, ft.Divider(height=1), self.col_readme_dig, self.replace_status, self.tihuan_scr, self.try_read_sharecmd, self.RunFullSC_btn, self.KillSCR_btn, self.restone_scr, self.runwindows_swc, self.KillSCR_swc, self.RunFullSC_swc])
        self.apply_bg_to_ui(needLoad_Stuff_list=self.ConlTab_Stuff)

    def switch_main_page_3(self):
        self.gbCommandStuff = ft.Column(controls=[self.yiyanshowtext, ft.Divider(height=1), self.conl_save_ycCmd_input, self.conl_ycCmd_update, self.conl_ycCmd_update_with_replace_ip, self.teachIp_input, self.auto_gennerate_cmd, self.conl_from_log_get_cmd, self.conl_getyccmd_btn])
        self.apply_bg_to_ui(needLoad_Stuff_list=self.gbCommandStuff)

    def switch_main_page_5(self):
        self.apply_bg_to_ui(needLoad_Stuff_list=self.waiguanTab_Stuff)
        self.added_pickdialog()

    def switch_main_page_6(self):
        self.AboutTab_Stuff = ft.Column(controls=[ft.Text("此工具箱在Github上发布", size=22), ft.Text("愿我们的电脑课都不再无聊~🥳", size=22), ft.ElevatedButton("点我打开工具箱Github页", on_click=open_github_page), self.hide_tbox_swc])
        self.apply_bg_to_ui(needLoad_Stuff_list=self.AboutTab_Stuff)

    def switch_main_page_4(self):
        self.dll_usb_1 = ft.FilledTonalButton(text="执行:关闭USB管控", on_click=lambda _: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_StopWorking", ctypes.c_int, [], None), icon=ft.icons.USB)
        self.dll_usb_2 = ft.FilledTonalButton(text="执行:启动USB管控", on_click=lambda _: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_StartWorking", ctypes.c_int, [], None), icon=ft.icons.USB_OFF)
        self.dll_usb_3 = ft.FilledTonalButton(text="执行:查询USB管控状态", on_click=lambda _: run_easy_dll("\\x64\\easyusbctrl.dll", "EasyUsb_IsWorking", ctypes.c_int, [ctypes.POINTER(wintypes.DWORD)], wintypes.DWORD(0)), icon=ft.icons.CODE)
        self.dll_net_1 = ft.FilledTonalButton(text="执行:开启网络管控", on_click=lambda _: run_easy_dll("\\x64\\OeNetlimit.dll", "DisableInternet", ctypes.c_int, [], None), icon=ft.icons.SIGNAL_WIFI_CONNECTED_NO_INTERNET_4)
        self.dll_net_2 = ft.FilledTonalButton(text="执行:关闭网络管控", on_click=lambda _: run_easy_dll("\\x64\\OeNetlimit.dll", "EnableNet", ctypes.c_int, [], None), icon=ft.icons.SIGNAL_WIFI_4_BAR)
        self.dllTab_Stuff = ft.Column(controls=[self.yiyanshowtext, ft.Divider(height=1), self.dll_usb_1, self.dll_usb_2, self.dll_usb_3, self.dll_net_1, self.dll_net_2])
        self.apply_bg_to_ui(needLoad_Stuff_list=self.dllTab_Stuff)

    def added_pickdialog(self):
        for idlg in self.list_all_pickdialog:
            self.page.add(idlg)
            self.page.update()

    def reflash_ui_bg(self):
        toolbox_cfg.set_style_path("bgPath", self.bgpath)
        self.loaded_bg = True
        self.col_imgbg = ft.Image(src=f"{self.bgpath}", height=self.page.window_height, width=self.page.window_width - 100, opacity=self.bgtmd, fit=ft.ImageFit.SCALE_DOWN)
        exc = {
            0: self.switch_main_page_0,
            1: self.switch_main_page_1,
            2: self.switch_main_page_2,
            3: self.switch_main_page_3,
            4: self.switch_main_page_4,
            5: self.switch_main_page_5,
            6: self.switch_main_page_6,
        }.get(int(self.NowSelIndex), lambda: None)()

    def hide_toolbox_helper(self):
        self.page.window_visible = False if self.page.window_visible else True
        self.page.update()

    def guaqi_chufa(self, *e):
        if self.guaqi_runstatus == False:
            self.page.window_visible = False
            self.page.update()
            status = utils.guaqi_process(toolbox_cfg.student_exe_name)
            status_ = utils.guaqi_process("MultiClient.exe")
            if status == True:
                self.guaqi_runstatus = True
                time.sleep(0.8)
                self.page.window_visible = True
                self.page.update()
            else:
                self.page.window_visible = True
                self.guaqi_sw.value = False
                self.page.update()
                self.show_snakemessage(status)
        else:
            status = utils.huifu_process(toolbox_cfg.student_exe_name)
            status_ = utils.huifu_process("MultiClient.exe")
            if status == True:
                self.guaqi_runstatus = False
            else:
                self.guaqi_sw.value = False
                self.page.update()
                self.show_snakemessage(status)

    def pick_a_random_yiyan(self, *e):
        if self.defult_yy == False:
            pickindex = random.randint(0, self.ex_fullindex - 1)
            self.yiyanshowtext.value = self.yiyanlist[pickindex]
            self.yiyanshowtext2.value = self.yiyanlist[pickindex]
            self.page.update()
        elif self.defult_yy == True:
            deft_pickindex = random.randint(0, len(DEFAULT_YIYAN_LIST) - 1)
            self.yiyanshowtext.value = DEFAULT_YIYAN_LIST[deft_pickindex]
            self.yiyanshowtext2.value = DEFAULT_YIYAN_LIST[deft_pickindex]
            self.page.update()

    def show_snakemessage(self, showtext: str):
        self.page.snack_bar = ft.SnackBar(ft.Text(showtext))
        self.page.snack_bar.open = True
        self.page.update()

    def from_file_load_yiyan(self):
        toolbox_cfg.set_style_path("yiyanPath", self.yiyanfpath)
        try:
            fm = open(self.yiyanfpath, "r", encoding="utf-8")
            get = fm.read()
            fm.close()
            list_get = get.split("^")
            self.ex_fullindex = len(list_get)
            self.yiyanlist = list_get
            self.defult_yy = False
            self.show_snakemessage("成功加载外部一言库")
        except Exception as e:
            self.show_snakemessage(f"加载外部一言时出现{e}异常")

    def change_bg_btmd(self, e):
        self.bgtmd = e.control.value
        self.reflash_ui_bg()

    def yiyan_pick_files_result(self, e: ft.FilePickerResultEvent):
        try:
            _yiyanfpath = e.files[0]
            self.yiyanfpath = os.path.join(_yiyanfpath.path)
            self.from_file_load_yiyan()
        except TypeError:
            self.show_snakemessage("未选择一言文件")

    def setup_zidingyi_font(self):
        toolbox_cfg.set_style_path("fontPath", self.zdy_fontpath)
        self.font_loadtime += 1
        print("[DEBUG] font_loadtime var = ", self.font_loadtime)
        if 10 >= self.font_loadtime > 2:
            self.old_zidyingy_time = self.font_loadtime - 1
            del self.page.fonts[f"zidingyi{self.old_zidyingy_time}"]
        elif self.font_loadtime > 10:
            self.old_zidyingy_time = self.font_loadtime - 1
            del self.page.fonts[f"zidingyi{self.old_zidyingy_time}"]
            self.font_loadtime = 3
        self.page.fonts.update({f"zidingyi{self.font_loadtime}": self.zdy_fontpath})
        self.page.theme = ft.Theme(font_family=f"zidingyi{self.font_loadtime}")
        self.page.update()
        if self.loaded_bg == True:
            self.reflash_ui_bg()

    def font_pick_files_result(self, e: ft.FilePickerResultEvent):
        try:
            _fontfpath = e.files[0]
            self.zdy_fontpath = os.path.join(_fontfpath.path)
            self.setup_zidingyi_font()
        except TypeError:
            self.show_snakemessage("未选择字体文件")

    def pick_files_result(self, e: ft.FilePickerResultEvent):
        try:
            _bgpath = e.files[0]
            self.bgpath = os.path.join(_bgpath.path)
            self.bgtmdb.disabled = False
            self.reflash_ui_bg()
        except TypeError:
            self.show_snakemessage("未选择背景图片")

    def only_update_MMPC_status(self, *e):
        st = check_mmpc_status()
        self.show_snakemessage(f"根服务状态: {st}")
        if st == True:
            self.mmpc_Stext.value = "正在运行"
            self.page.update()
        elif st == False:
            self.mmpc_Stext.value = "未运行"
            self.page.update()


ToolBox = Ui()