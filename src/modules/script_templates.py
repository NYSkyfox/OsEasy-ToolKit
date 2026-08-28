# src/modules/script_templates.py
# 击杀/删文件脚本模板（解锁已迁移至 unlock_native.py）

from src.core.settings import toolkit_cfg
from src.modules.service_manager import get_mmpc_cmd


def _mmcp_stop():
    return get_mmpc_cmd(True)


# ══════════════════════════════════════════════════════════
# 脚本模板
# ══════════════════════════════════════════════════════════

def tpl_process_killer_all() -> str:
    return (
        f"@ECHO OFF\n"
        f"title Process-Killer_All\n"
        f":awa\n"
        f"for %%p in (Ctsc_Multi.exe,DeviceControl_x64.exe,HRMon.exe,"
        f"MultiClient.exe,OActiveII-Client.exe,OEClient.exe,OELogSystem.exe,"
        f"OEUpdate.exe,OEProtect.exe,ProcessProtect.exe,RunClient.exe,"
        f"ServerOSS.exe,{toolkit_cfg.student_exe_name},wfilesvr.exe,"
        f"tvnserver.exe,updatefilesvr.exe,ScreenRender.exe) "
        f"do taskkill /f /IM %%p\n"
        f"goto awa\n"
    )


def tpl_process_killer_student() -> str:
    return f"""@ECHO OFF
title Process-Killer_Student

{_mmcp_stop()}

taskkill /f /t /im MultiClient.exe
taskkill /f /t /im BlackSlient.exe
:a
taskkill /f /t /im {toolkit_cfg.student_exe_name}
goto a
"""


def tpl_files_delete(delMtc: bool, shutdown: bool) -> str:
    lines = [
        f"@ECHO OFF",
        f"title Files-Delete",
        f"cd /D {toolkit_cfg.oseasy_path}",
        f"timeout 1",
        f"del /F /S LockKeyboard.dll",
        f"del /F /S LoadDriver.exe",
        f"del /F /S oenetlimitx64.cat",
        f"del /F /S BlackSlient.exe",
        f"cd x86",
        f"del /F /S LISSNetInfoSniffer.exe",
        f"cd ..",
    ]
    if delMtc:
        lines.append("del /F /S MultiClient.exe")
    if shutdown:
        lines.append("timeout 5")
        lines.append("shutdown /l")
    lines.append("exit")
    return "\n".join(lines)


def tpl_install_student_test(base: str) -> str:
    """学生端轻量安装测试脚本模板。

    在指定目录(base)下注册 MMPC 服务、安装管控驱动、添加防火墙规则。
    base 应指向包含 MMPC.exe / DriverInstall.exe / KbDriver.exe / Student.exe
    的学生端套件目录（默认取 toolkit_cfg.oseasy_path）。
    """
    return f"""@echo off
chcp 65001 >nul
title OsEasy 学生端轻量安装

:: 以管理员权限运行
>nul 2>&1 "%SYSTEMROOT%\\system32\\cacls.exe" "%SYSTEMROOT%\\system32\\config\\system"
if '%errorlevel%' NEQ '0' (
    echo 请以管理员身份运行此脚本！
    pause
    exit /b 1
)

set "BASE={base}"
echo 安装目录: %BASE%

:: ============================================
:: 1. 注册并启动 MMPC 服务（多媒体广播协调器）
:: ============================================
echo [1/4] 注册 MMPC 服务...
sc query MMPC >nul 2>&1
if %errorlevel% EQU 0 (
    echo   MMPC 服务已存在，跳过创建
) else (
    sc create MMPC binPath= "\\"%BASE%MMPC.exe\\"" start= auto DisplayName= "OsEasy MMPC Service"
    if %errorlevel% NEQ 0 (
        echo   MMPC 服务创建失败！尝试直接启动进程...
    ) else (
        echo   MMPC 服务创建成功
    )
)

echo [2/4] 启动 MMPC 服务...
sc start MMPC >nul 2>&1
if %errorlevel% EQU 0 (
    echo   MMPC 服务已启动
) else (
    echo   MMPC 服务启动失败，尝试直接运行进程...
    start "" "%BASE%MMPC.exe"
    echo   MMPC 已作为普通进程启动
)

:: ============================================
:: 2. 安装内核驱动（可选，用于测试管控功能）
:: ============================================
echo [3/4] 安装管控驱动...

if exist "%BASE%DriverInstall.exe" (
    echo   正在安装 FbdATS + easyusbflt + ProcFireWall + OeNetLimit...
    "%BASE%DriverInstall.exe" /S /DIR="%BASE%" /OPT=install /d1=FbdATS /d2=easyusbflt /d3=ProcFireWall /d4=OeNetLimit
)

if exist "%BASE%KbDriver.exe" (
    echo   正在安装 KbFilter（键盘过滤驱动）...
    "%BASE%KbDriver.exe" /install
)

:: ============================================
:: 3. 防火墙放行
:: ============================================
echo [4/4] 添加防火墙规则...
netsh advfirewall firewall add rule name="OsEasy Student" dir=in program="%BASE%Student.exe" action=allow >nul 2>&1
netsh advfirewall firewall add rule name="OsEasy MMPC" dir=in program="%BASE%MMPC.exe" action=allow >nul 2>&1
netsh advfirewall firewall add rule name="OsEasy MultiClient" dir=in program="%BASE%MultiClient.exe" action=allow >nul 2>&1
netsh advfirewall firewall add rule name="OsEasy Ports 7778-7788" dir=in protocol=udp localport=7778-7788 action=allow >nul 2>&1
echo   防火墙规则已添加

:: ============================================
:: 完成
:: ============================================
echo.
echo ========================================
echo   安装完成！
echo.
echo   MMPC 状态:
sc query MMPC | findstr STATE
echo.
echo   下一步:
echo   1. 运行 Student.exe 启动学生端
echo   2. 如需重启使驱动生效，运行: shutdown -r -t 0
echo ========================================
pause
"""


def tpl_uninstall_student_test(base: str) -> str:
    """学生端卸载测试脚本模板（与安装脚本互为反向）。

    在指定目录(base)下停止/删除 MMPC 服务、卸载管控驱动、删除防火墙规则。
    base 应指向包含 DriverInstall.exe 的学生端套件目录。
    """
    return f"""@echo off
chcp 65001 >nul
title OsEasy 学生端卸载测试

:: 以管理员权限运行
>nul 2>&1 "%SYSTEMROOT%\\system32\\cacls.exe" "%SYSTEMROOT%\\system32\\config\\system"
if '%errorlevel%' NEQ '0' (
    echo 请以管理员身份运行此脚本！
    pause
    exit /b 1
)

set "BASE={base}"
echo 学生端套件目录: %BASE%

:: ============================================
:: 1. 停止并删除 MMPC 服务
:: ============================================
echo [1/4] 停止并删除 MMPC 服务...
sc stop MMPC >nul 2>&1
sc delete MMPC >nul 2>&1
sc query MMPC >nul 2>&1
if %errorlevel% NEQ 0 (
    echo   MMPC 服务已删除
) else (
    echo   MMPC 服务仍存在（可能被占用，请重启后再试）
)

:: ============================================
:: 2. 停止并删除管控驱动服务
:: ============================================
echo [2/4] 停止并删除管控驱动...

for %%d in (OeNetLimit ProcFireWall easyusbflt FbdATS KbFilter) do (
    sc stop %%d >nul 2>&1
    sc delete %%d >nul 2>&1
)
echo   已尝试停止/删除: OeNetLimit ProcFireWall easyusbflt FbdATS KbFilter

:: ============================================
:: 3. 用 DriverInstall.exe 卸载驱动（如果存在）
:: ============================================
echo [3/4] 调用 DriverInstall.exe 卸载驱动...

if exist "%BASE%DriverInstall.exe" (
    "%BASE%DriverInstall.exe" /S /DIR="%BASE%" /OPT=uninst /d1=FbdATS /d2=easyusbflt /d3=ProcFireWall /d4=OeNetLimit
    "%BASE%DriverInstall.exe" /S /DIR="%BASE%" /OPT=uninst /d1=KbFilter
    echo   DriverInstall.exe 卸载完成
) else (
    echo   未找到 DriverInstall.exe，跳过（服务已通过 sc delete 清理）
)

:: ============================================
:: 4. 删除防火墙规则
:: ============================================
echo [4/4] 删除防火墙规则...
netsh advfirewall firewall delete rule name="OsEasy Student" >nul 2>&1
netsh advfirewall firewall delete rule name="OsEasy MMPC" >nul 2>&1
netsh advfirewall firewall delete rule name="OsEasy MultiClient" >nul 2>&1
netsh advfirewall firewall delete rule name="OsEasy Ports 7778-7788" >nul 2>&1
echo   防火墙规则已删除

:: ============================================
:: 完成
:: ============================================
echo.
echo ========================================
echo   卸载完成！
echo.
echo   注意:
echo   - 正在运行的内核驱动模块需重启后才彻底卸载
echo   - 如需彻底清理，运行: shutdown -r -t 0
echo ========================================
pause
"""
