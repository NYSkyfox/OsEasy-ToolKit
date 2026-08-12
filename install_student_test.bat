@echo off
chcp 65001 >nul
title OsEasy 学生端轻量安装

:: 以管理员权限运行
>nul 2>&1 "%SYSTEMROOT%\system32\cacls.exe" "%SYSTEMROOT%\system32\config\system"
if '%errorlevel%' NEQ '0' (
    echo 请以管理员身份运行此脚本！
    pause
    exit /b 1
)

set "BASE=%~dp0"
echo 安装目录: %BASE%

:: ============================================
:: 1. 注册并启动 MMPC 服务（多媒体广播协调器）
:: ============================================
echo [1/4] 注册 MMPC 服务...
sc query MMPC >nul 2>&1
if %errorlevel% EQU 0 (
    echo   MMPC 服务已存在，跳过创建
) else (
    sc create MMPC binPath= "\"%BASE%MMPC.exe\"" start= auto DisplayName= "OsEasy MMPC Service"
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
