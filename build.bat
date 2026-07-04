@echo off
chcp 65001 >nul
cd /d "%~dp0"

python -m PyInstaller ^
    --onefile ^
    --windowed ^
    --name OsEasyToolBox ^
    --icon logo.ico ^
    --upx-dir tools\upx-5.2.0-win64 ^
    --upx-exclude "email*" ^
    --upx-exclude "urllib*" ^
    --upx-exclude "ssl*" ^
    --hidden-import email ^
    --hidden-import email.mime ^
    --hidden-import email.mime.multipart ^
    --hidden-import email.mime.text ^
    --hidden-import email.mime.base ^
    --hidden-import urllib.request ^
    --hidden-import urllib.parse ^
    --collect-all flet ^
    --add-data "Fake_SCR.py;." ^
    --add-data "config.py;." ^
    main.py