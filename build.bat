@echo off
chcp 65001 >nul
cd /d "%~dp0"

python -m PyInstaller ^
    --onefile ^
    --noconsole ^
    --icon=logo.ico ^
    --name=OsEasy-ToolBox ^
    --manifest app.manifest ^
    --add-data "venv\Lib\site-packages\flet;flet" ^
    --add-data "venv\Lib\site-packages\flet_desktop;flet_desktop" ^
    --hidden-import=flet ^
    --hidden-import=flet_desktop ^
    --hidden-import=pdb ^
    --hidden-import=doctest ^
    --hidden-import=inspect ^
    --hidden-import=traceback ^
    --hidden-import=pyrect ^
    --hidden-import=win32clipboard ^
    --hidden-import=email ^
    --hidden-import=email.mime ^
    --hidden-import=email.mime.multipart ^
    --hidden-import=email.mime.text ^
    --hidden-import=email.mime.base ^
    --hidden-import=urllib.request ^
    --hidden-import=urllib.parse ^
    --upx-dir "tools\upx-5.2.0-win64" ^
    --upx-exclude "email*" ^
    --upx-exclude "urllib*" ^
    --upx-exclude "ssl*" ^
    --add-data "Fake_SCR.py;." ^
    --add-data "config.py;." ^
    main.py