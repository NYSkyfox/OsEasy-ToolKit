@echo off
chcp 65001 >nul
title OsEasy 学生端卸载测试

:: 以管理员权限运行
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 请以管理员身份运行此脚本！
    pause
    exit /b 1
)

set "BASE=%~dp0"
echo 学生端套件目录: %BASE%

:: ============================================
:: 1. 停止并删除 MMPC 服务（多媒体广播协调器）
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
