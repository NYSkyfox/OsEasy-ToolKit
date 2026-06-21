"""
广播管理服务 - 拦截、替换、运行广播命令
"""

import os
import re
import json
from typing import Optional, Tuple, List
from utils.helpers import (
    check_file_exists, run_cmd, write_bat_file, get_ipv4_address
)
import config


class BroadcastService:
    """广播服务类"""
    
    def __init__(self, student_service):
        """
        Args:
            student_service: StudentService 实例
        """
        self.student = student_service
        self._cmd: Optional[str] = None
        self._load_saved_cmd()
    
    def _load_saved_cmd(self) -> None:
        """从配置文件加载已保存的广播命令"""
        if check_file_exists(config.CONFIG_FILE_PATH):
            try:
                with open(config.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self._cmd = data.get("broadcast_cmd")
            except:
                pass
    
    def _save_cmd(self) -> None:
        """保存广播命令到配置文件"""
        data = {}
        if check_file_exists(config.CONFIG_FILE_PATH):
            try:
                with open(config.CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            except:
                pass
        
        data["broadcast_cmd"] = self._cmd
        
        try:
            with open(config.CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"保存广播命令失败: {e}")
    
    def is_replaced(self) -> bool:
        """
        检查是否已经替换了 ScreenRender
        
        Returns:
            True 表示已替换
        """
        return check_file_exists(self.student.get_screen_render_y_path())
    
    def replace_screen_render(self) -> Tuple[bool, str]:
        """
        替换 ScreenRender.exe 为拦截程序

        Returns:
            (是否成功, 信息)
        """
        helper_name = "ScreenRender_Helper.exe"
        helper_src = os.path.join(os.getcwd(), helper_name)

        if not check_file_exists(helper_src):
            return False, f"未找到 {helper_name}\n请确保它与工具在同一目录"

        try:
            # 重命名原程序（等待完成）
            ret = run_cmd(
                f'rename "{self.student.get_screen_render_path()}" '
                f'"ScreenRender_Y.exe"',
                wait=True
            )
            if ret != 0:
                return False, "重命名原 ScreenRender.exe 失败，可能正在使用中"

            # 复制 helper（等待完成）
            ret = run_cmd(
                f'copy "{helper_src}" "{self.student.path}" /Y',
                wait=True
            )
            if ret != 0:
                return False, "复制 ScreenRender_Helper.exe 失败"

            # 重命名为 ScreenRender.exe
            helper_dst = os.path.join(self.student.path, helper_name)
            run_cmd(
                f'rename "{helper_dst}" "ScreenRender.exe"',
                wait=True
            )

            return True, "替换成功！等待老师广播后即可拦截命令"
        except Exception as e:
            return False, f"替换失败: {e}"
    
    def restore_screen_render(self) -> Tuple[bool, str]:
        """
        恢复原始的 ScreenRender.exe
        
        Returns:
            (是否成功, 信息)
        """
        if not self.is_replaced():
            return False, "未检测到替换的备份文件"
        
        try:
            # 删除假的 ScreenRender
            fake_path = self.student.get_screen_render_path()
            if check_file_exists(fake_path):
                os.remove(fake_path)
            
            # 恢复原名
            run_cmd(
                f'rename "{self.student.get_screen_render_y_path()}" '
                f'"ScreenRender.exe"'
            )
            
            return True, "已恢复原始 ScreenRender"
        except Exception as e:
            return False, f"恢复失败: {e}"
    
    def read_intercepted_cmd(self) -> Tuple[bool, str]:
        """
        读取拦截到的广播命令
        
        Returns:
            (是否成功, 命令内容或错误信息)
        """
        if check_file_exists(config.INTERCEPT_CMD_SAVE_PATH):
            try:
                with open(config.INTERCEPT_CMD_SAVE_PATH, 'r', encoding='utf-8') as f:
                    cmd = f.read().strip()
                if cmd:
                    self._cmd = cmd
                    self._save_cmd()
                    return True, cmd
            except Exception as e:
                return False, f"读取失败: {e}"
        
        return False, "尚未拦截到广播命令"
    
    def save_cmd(self, cmd: str, replace_ip: bool = True) -> bool:
        """
        保存广播命令
        
        Args:
            cmd: 命令字符串
            replace_ip: 是否自动替换本地 IP
            
        Returns:
            是否成功
        """
        if not cmd:
            return False
        
        if replace_ip:
            local_ip = get_ipv4_address()
            if local_ip:
                cmd = re.sub(r"(#local#:)(#.*?#)", rf"\1#{local_ip}#", cmd)
        
        self._cmd = cmd
        self._save_cmd()
        return True
    
    def generate_cmd_from_teacher_ip(self, teacher_ip: str) -> bool:
        """
        根据教师机 IP 生成广播命令
        
        Args:
            teacher_ip: 教师机 IP 地址
            
        Returns:
            是否成功
        """
        local_ip = get_ipv4_address()
        if not local_ip:
            return False
        
        # 模板命令
        template = (
            "{#decoderName#:#h264#,#fullscreen#:0,"
            f"#local#:#{local_ip}#,#port#:7778,"
            f"#remote#:#{teacher_ip}#,#teacher_ip#:0,#verityPort#:7788" + "}"
        )
        
        self._cmd = template
        self._save_cmd()
        return True
    
    def build_run_cmd(self, fullscreen: bool = False) -> Optional[str]:
        """
        构建运行广播的命令
        
        Args:
            fullscreen: 是否全屏
            
        Returns:
            命令字符串，未设置广播命令返回 None
        """
        if not self._cmd:
            return None
        
        cmd = self._cmd
        if fullscreen:
            cmd = cmd.replace("#fullscreen#:0", "#fullscreen#:1")
        else:
            cmd = cmd.replace("#fullscreen#:1", "#fullscreen#:0")
        
        # 使用备份的原始程序或当前程序
        if self.is_replaced():
            exe_path = self.student.get_screen_render_y_path()
        else:
            exe_path = self.student.get_screen_render_path()
        
        return f'"{exe_path}" {cmd}'
    
    def run_broadcast(self, fullscreen: bool = False) -> Tuple[bool, str]:
        """
        运行广播命令
        
        Args:
            fullscreen: 是否全屏
            
        Returns:
            (是否成功, 信息)
        """
        cmd = self.build_run_cmd(fullscreen)
        if not cmd:
            return False, "未设置广播命令"
        
        run_cmd(cmd)
        mode = "全屏" if fullscreen else "窗口"
        return True, f"已运行{mode}广播"
    
    def kill_broadcast(self) -> bool:
        """
        杀死广播进程
        
        Returns:
            是否成功
        """
        run_cmd("taskkill /f /t /im ScreenRender.exe")
        run_cmd("taskkill /f /t /im ScreenRender_Y.exe")
        return True
    
    def parse_log_file(self) -> Tuple[bool, List[str]]:
        """
        从 ScreenRender.log 解析广播命令
        
        Returns:
            (是否成功, 命令列表)
        """
        appdata = os.getenv("APPDATA")
        if not appdata:
            return False, []
        
        log_path = os.path.join(appdata, "Mmc", "ScreenRender.log")
        if not check_file_exists(log_path):
            return False, []
        
        pattern = re.compile(r"\d{2}-\d{2} \d{2}:\d{2}:\d{2} (\{.*\})")
        results = []
        
        try:
            with open(log_path, 'r', encoding='gbk') as f:
                for line in f:
                    match = pattern.search(line)
                    if match:
                        cmd = match.group(1).replace('"', '#')
                        results.append(cmd)
        except Exception as e:
            print(f"解析日志失败: {e}")
            return False, []
        
        return len(results) > 0, results
    
    def save_cmd_to_file(self, filepath: str = None) -> bool:
        """
        保存当前广播命令到文件
        
        Args:
            filepath: 保存路径，默认当前目录 command.txt
            
        Returns:
            是否成功
        """
        if not self._cmd:
            return False
        
        if not filepath:
            filepath = os.path.join(os.getcwd(), "command.txt")
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(self._cmd)
            return True
        except Exception as e:
            print(f"保存文件失败: {e}")
            return False
    
    @property
    def cmd(self) -> Optional[str]:
        """当前保存的广播命令"""
        return self._cmd
    
    def extract_teacher_ip(self) -> Optional[str]:
        """
        从广播命令中提取教师机 IP
        
        Returns:
            IP 地址
        """
        if not self._cmd:
            return None
        
        pattern = r"#(\d{1,3}(?:\.\d{1,3}){3})#"
        ips = re.findall(pattern, self._cmd)
        
        # 第二个 IP 通常是教师机
        if len(ips) >= 2:
            return ips[1]
        return None