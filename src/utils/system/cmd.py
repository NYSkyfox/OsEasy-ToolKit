# src/utils/system/cmd.py
# 命令行执行工具
#
# 脚本执行统一方案：
#   runbat(batname)           → 用户手动触发的 bat（可见窗口 + 输出进日志）
#   _start_killer_cmd()       → cmd 守护进程专用（后台 + 频率限制）
#   run_single_cmd / run_sigle_cmd → 同步命令（subprocess.run 捕获输出）

import os
import subprocess

from src.core.constants import cmd_file_path

# ── PowerShell 统一控制台颜色设置（灰白色，不出现红字吓人） ──
_PS_COLOR_SETUP = (
    "$Host.PrivateData.ErrorForegroundColor = 'Gray'; "
    "$Host.PrivateData.ErrorBackgroundColor = $Host.UI.RawUI.BackgroundColor; "
    "$Host.PrivateData.WarningForegroundColor = 'Gray'; "
    "$Host.PrivateData.WarningBackgroundColor = $Host.UI.RawUI.BackgroundColor;"
)


def run_single_cmd(givecmd: str, quiet: bool = False) -> None:
    """运行指定的命令
    :param givecmd: 要执行的命令
    :param quiet: True=不弹窗口(asynchronous), False=等待完成(synchronous)
    """
    from src.utils.system.logger import debug
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
    fm = open(mp, "w")
    cmdtext = "@ECHO OFF\n"
    cmdtext += cmd
    cmdtext += "\nexit"
    fm.write(cmdtext)
    fm.close()
    run_sigle_cmd(f"start {mp}")


def runbat(batname: str) -> None:
    """
    统一 bat 脚本执行入口。
    生成包装脚本：PowerShell 用 Tee-Object 执行目标 bat，
    输出同时显示在控制台窗口 + 追加进日志文件。
    控制台颜色统一为灰白色（PowerShell 原生错误红色改为灰色）。
    """
    import uuid
    from src.utils.system.logger import debug, get_log_path

    batp = os.path.join(cmd_file_path, batname)
    log_path = get_log_path()
    debug(f"运行脚本: {batname}")

    # 临时文件：包装脚本 + 输出暂存
    uid = uuid.uuid4().hex
    wrapper_path = os.path.join(cmd_file_path, f"runbat_wrapper_{uid}.bat")
    tmp_output = os.path.join(cmd_file_path, f"runbat_output_{uid}.log")

    lines = ["@ECHO OFF"]
    if log_path:
        # 一条 PowerShell：统一颜色 → 执行目标 bat + Tee 到临时文件 → 追加日志 → 删临时文件
        # 全部在同一个 PowerShell 进程内完成，窗口被 X 掉时只要 bat 跑完就已合并+清理
        lines.append(
            f"powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "
            f"\"{_PS_COLOR_SETUP} "
            f"& {{ & '{batp}' 2>&1 | Tee-Object -FilePath '{tmp_output}' }}; "
            f"Get-Content -Path '{tmp_output}' -Encoding UTF8 | Out-File -FilePath '{log_path}' -Encoding UTF8 -Append; "
            f"Remove-Item -Path '{tmp_output}' -Force\""
        )
    else:
        # 日志未初始化 → 纯 cmd 原生执行
        lines.append(f"call \"{batp}\"")

    # 统一的窗口交互
    lines.append("echo.")
    lines.append("echo ==============================")
    lines.append("echo 按任意键关闭此窗口...")
    lines.append("pause >nul")
    lines.append("del /f /q \"%~f0\" >nul 2>&1")

    with open(wrapper_path, "w", encoding="utf-8", newline="\r\n") as f:
        f.write("\r\n".join(lines) + "\r\n")

    cmdline = f'start "" "{wrapper_path}"'
    subprocess.Popen(
        cmdline,
        shell=True,
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )