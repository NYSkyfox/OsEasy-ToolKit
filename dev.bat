@echo off
chcp 65001 >nul

:: ============================================
:: OsEasy-ToolBox 虚拟环境启动脚本
:: 双击即可进入带虚拟环境的命令行
:: ============================================

if not exist "%~dp0venv\Scripts\activate.bat" (
    echo [错误] 未找到虚拟环境，请先运行：
    echo   python -m venv venv
    echo   然后安装依赖：
    echo   venv\Scripts\pip install -r requirements.txt
    pause
    exit /b 1
)

call "%~dp0venv\Scripts\activate.bat"
echo.
echo ============================================
echo   OsEasy-ToolBox 开发环境已就绪
echo   虚拟环境: %VIRTUAL_ENV%
echo   输入 python main.py 启动项目
echo   输入 exit   退出虚拟环境
echo ============================================
echo.
cmd /k
