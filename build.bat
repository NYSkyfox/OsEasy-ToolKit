@echo off
chcp 65001 >nul
cd /d "%~dp0"

:: ============================================
:: OsEasy-ToolKit 一键打包脚本
:: 直接调用 build.py（不关心 venv / 全局 Python）
:: ============================================

echo.
echo ============================================
echo   OsEasy-ToolKit 打包脚本
echo ============================================
echo.

:: 1. 找可用的 Python
set PYTHON=
for %%p in (python python3 py) do (
    where %%p >nul 2>&1
    if not errorlevel 1 (
        set PYTHON=%%p
        goto :found_python
    )
)

echo [错误] 未找到 Python，请先安装 Python 3
echo        下载地址: https://www.python.org/downloads/
pause
exit /b 1

:found_python
echo [Python] %PYTHON%

:: 2. 确保 PyInstaller 已安装
%PYTHON% -m PyInstaller --version >nul 2>&1
if errorlevel 1 (
    echo [依赖] PyInstaller 未安装，正在安装...
    %PYTHON% -m pip install pyinstaller
    if errorlevel 1 (
        echo [错误] PyInstaller 安装失败
        pause
        exit /b 1
    )
) else (
    echo [依赖] PyInstaller 已安装
)

:: 3. 调用 build.py
echo.
echo [开始] 启动打包流程...
echo.
%PYTHON% build.py

:: 4. 结果
if errorlevel 1 (
    echo.
    echo [失败] 打包出错，查看上方日志。
    pause
    exit /b 1
)

echo.
echo [完成] 按任意键退出...
pause >nul