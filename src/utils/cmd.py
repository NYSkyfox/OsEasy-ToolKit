# src/utils/cmd.py
# 命令行执行工具
#
# 脚本执行统一方案：
#   runbat(batname, on_output)  -> 后台静默执行 + 输出实时回调 + 写入日志
#   _start_killer_cmd()         -> cmd 守护进程专用（后台 + 频率限制）
#   run_single_cmd / run_sigle_cmd -> 同步命令（subprocess.run 捕获输出）

import os
import subprocess
import threading

from src.core.constants import cmd_file_path


def run_single_cmd(givecmd: str, quiet: bool = False) -> None:
    """运行指定的命令
    :param givecmd: 要执行的命令
    :param quiet: True=不弹窗口(asynchronous), False=等待完成(synchronous)
    """
    from src.utils.logger import debug
    debug(f"执行命令: {givecmd}")

    if quiet:
        os.popen(cmd=givecmd)
        return

    try:
        result = subprocess.run(
            givecmd, shell=True,
            capture_output=True, text=True,
            timeout=30,
        )
        out = result.stdout.strip()
        err = result.stderr.strip()
        if out:
            for line in out.splitlines():
                debug(f"  stdout: {line}")
        if err:
            for line in err.splitlines():
                debug(f"  stderr: {line}")
        if result.returncode != 0:
            debug(f"  命令退出码: {result.returncode}")
    except subprocess.TimeoutExpired:
        debug(f"  命令超时（30s）: {givecmd}")
    except Exception as _e:
        debug(f"  命令执行异常: {_e}")


# 兼容旧名
run_sigle_cmd = run_single_cmd


def use_bat_file_to_run_cmd(cmd: str) -> None:
    """生成一个临时cmd文件运行指定命令"""
    mp = cmd_file_path + "\\temp.bat"
    with open(mp, "w", encoding="gbk") as fm:
        fm.write("@ECHO OFF\n" + cmd + "\nexit")
    run_sigle_cmd(f"start {mp}")


def runbat(batname: str, on_output=None) -> None:
    """
    统一 bat 脚本静默执行入口。
    后台执行 bat，输出实时回调 on_output(line) + 追加到日志文件。
    不弹出控制台窗口。

    :param batname: 脚本文件名（位于 cmd_file_path 下）
    :param on_output: 可选回调，每行输出调用 on_output(line)
    """
    from src.utils.logger import debug, get_log_path

    batp = os.path.join(cmd_file_path, batname)
    debug(f"运行脚本: {batname}")

    def _run():
        log_path = get_log_path()
        collected_lines = []
        try:
            proc = subprocess.Popen(
                batp,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="gbk",
                errors="replace",
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            for line in proc.stdout:
                line = line.rstrip("\n\r")
                if line:
                    collected_lines.append(line)
                    if on_output:
                        try:
                            on_output(line)
                        except Exception:
                            pass
            proc.wait()

            # 追加到日志文件
            if log_path and collected_lines:
                try:
                    with open(log_path, "a", encoding="utf-8") as lf:
                        lf.write(f"\n--- {batname} 输出 ---\n")
                        for line in collected_lines:
                            lf.write(line + "\n")
                        lf.write(f"--- {batname} 结束 (exit={proc.returncode}) ---\n")
                except Exception:
                    pass

            if proc.returncode != 0:
                debug(f"脚本 {batname} 退出码: {proc.returncode}")
        except Exception as e:
            debug(f"脚本 {batname} 执行异常: {e}")
            if on_output:
                try:
                    on_output(f"[错误] {e}")
                except Exception:
                    pass

    threading.Thread(target=_run, daemon=True).start()