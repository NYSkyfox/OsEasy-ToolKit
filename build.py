# build.py
# OsEasy-ToolBox 打包脚本（自动下载 UPX + PyInstaller 压缩）
#
# 使用方法:
#   1. pip install pyinstaller
#   2. python build.py
#
# 脚本会自动下载 UPX 5.2.0 到 tools/ 目录进行压缩，
# 无需手动准备任何东西。

import os
import sys
import shutil
import subprocess
import zipfile
import urllib.request
from pathlib import Path

# ---- 配置 ----

APP_NAME = "OsEasy-ToolBox"
MAIN_SCRIPT = "main.py"
ICON_PATH = "logo.ico"              # 根目录下的图标文件
ONE_FILE = True
CONSOLE = False

# UPX 配置
UPX_VERSION = "5.2.0"
UPX_ZIP = f"upx-{UPX_VERSION}-win64.zip"
UPX_DIR = Path("tools")
UPX_EXE = UPX_DIR / f"upx-{UPX_VERSION}-win64" / "upx.exe"

# 多个下载源（GitHub + 镜像），按顺序尝试
UPX_URLS = [
    f"https://github.com/upx/upx/releases/download/v{UPX_VERSION}/{UPX_ZIP}",
    f"https://ghproxy.com/https://github.com/upx/upx/releases/download/v{UPX_VERSION}/{UPX_ZIP}",
    f"https://hub.fastgit.xyz/upx/upx/releases/download/v{UPX_VERSION}/{UPX_ZIP}",
    f"https://download.fastgit.org/upx/upx/releases/download/v{UPX_VERSION}/{UPX_ZIP}",
    f"https://mirror.ghproxy.com/https://github.com/upx/upx/releases/download/v{UPX_VERSION}/{UPX_ZIP}",
]

# ---- UPX 管理 ----

def find_upx():
    """查找 UPX，找不到则自动下载"""
    # 1. 已解压到 tools/
    if UPX_EXE.exists():
        return str(UPX_EXE)

    # 2. 系统 PATH
    for name in ["upx.exe", "upx"]:
        if shutil.which(name):
            return name

    # 3. 自动下载
    print(f"[UPX] 未找到，自动下载 UPX {UPX_VERSION}...")
    return download_upx()


def download_upx():
    """下载并解压 UPX"""
    UPX_DIR.mkdir(exist_ok=True)
    zip_path = UPX_DIR / UPX_ZIP

    # 尝试所有源下载
    last_error = None
    for url in UPX_URLS:
        if zip_path.exists():
            zip_path.unlink()

        try:
            print(f"[UPX] 尝试下载: {url}")
            urllib.request.urlretrieve(url, zip_path)
            break
        except Exception as e:
            last_error = e
            print(f"[UPX] 下载失败: {e}")
    else:
        raise RuntimeError(f"所有 UPX 下载源均失败，最后一个错误: {last_error}")

    # 解压
    print(f"[UPX] 解压到 {UPX_DIR}/")
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(UPX_DIR)

    # 删除 zip
    zip_path.unlink()

    if UPX_EXE.exists():
        print(f"[UPX] 就绪: {UPX_EXE}")
        return str(UPX_EXE)

    raise FileNotFoundError(f"解压后未找到 upx.exe，期望路径: {UPX_EXE}")

def install_dependencies():
    """从本地 vendor/ 安装依赖，没有就从 PyPI 下载"""
    print("[依赖] 安装项目依赖...")
    vendor_dir = Path("vendor")

    if vendor_dir.exists() and any(vendor_dir.iterdir()):
        print("[依赖] 使用本地离线包 (vendor/)")
        cmd = [sys.executable, "-m", "pip", "install", "--no-index", "--find-links", str(vendor_dir), "-r", "requirements.txt"]
    else:
        print("[依赖] 本地离线包不存在，从 PyPI 在线安装")
        cmd = [sys.executable, "-m", "pip", "install", "-r", "requirements.txt"]

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print("❌ 依赖安装失败")
        sys.exit(result.returncode)
    print("[依赖] 安装完成")


def build_args():
    args = [
        MAIN_SCRIPT,
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
    ]

    # UPX 不压缩这些模块（避免运行时解压失败）
    args.extend(["--upx-exclude", "email*"])
    args.extend(["--upx-exclude", "urllib*"])
    args.extend(["--upx-exclude", "ssl*"])

    # 显式导入 email / urllib 全族
    email_mods = [
        "email", "email.mime", "email.mime.multipart",
        "email.mime.text", "email.mime.base",
    ]
    for m in email_mods:
        args.extend(["--hidden-import", m])
    args.extend(["--hidden-import", "urllib.request"])
    args.extend(["--hidden-import", "urllib.parse"])

    # 收集 flet 全部资源
    args.extend(["--collect-all", "flet"])

    if ICON_PATH and Path(ICON_PATH).exists():
        args.extend(["--icon", ICON_PATH])

    # ---- 添加数据文件（打包进 exe 的资源） ----
    args.extend(["--add-data", f"Fake_SCR.py{os.pathsep}."])
    args.extend(["--add-data", f"config.py{os.pathsep}."])

    # ScreenRender_Helper.exe（如果存在）
    screen_helper = Path("ScreenRender_Helper.exe")
    if screen_helper.exists():
        args.extend(["--add-data", f"ScreenRender_Helper.exe{os.pathsep}."])

    # resources/gp_net35.exe（神の土豆，如果存在）
    gp_potato = Path("resources") / "gp_net35.exe"
    if gp_potato.exists():
        args.extend(["--add-data", f"resources/gp_net35.exe{os.pathsep}resources"])

    # ---- 其他隐藏导入 ----
    extra_hidden = [
        "flet_core", "flet_desktop", "flet_runtime",
        "pynput.keyboard._win32", "pynput.mouse._win32",
        "httpx", "ctypes.wintypes", "pygetwindow", "psutil", "pyautogui", "webbrowser",
    ]
    for m in extra_hidden:
        args.extend(["--hidden-import", m])

    # ---- 排除不需要的大模块 ----
    # 注意：email / urllib / ssl 不能排除，flet 依赖它们
    exclude_modules = [
        "tkinter", "tcl", "tk",
        "matplotlib", "numpy", "pandas", "PIL",
        "PyQt5", "PyQt6", "PySide2", "PySide6", "wx",
        "IPython", "jupyter", "notebook",
        "pydoc", "unittest", "test",
        "setuptools", "pip",
        # "email",      # ❌ flet runtime 需要
        # "html",       # 可能 urllib 依赖
        # "xml", "xmlrpc", "distutils", "lib2to3",
    ]
    for mod in exclude_modules:
        args.extend(["--exclude-module", mod])

    # ---- UPX 压缩 ----
    upx_path = find_upx()
    if upx_path:
        print(f"[UPX] 找到: {upx_path}")
        args.extend(["--upx-dir", str(Path(upx_path).parent)])
    else:
        print("[UPX] 未找到 UPX，跳过压缩（exe 会大一些）")
        print("[UPX] 下载: https://upx.github.io/")

    # ---- 清理上次构建 ----
    args.append("--clean")

    # ---- 路径 ----
    args.extend(["--paths", "."])

    return args


# ---- 执行 ----

def main():
    print(f"=== {APP_NAME} 打包脚本 ===")
    print(f"模式: {'单文件' if ONE_FILE else '文件夹'}")
    print()

    # 确保必要的资源存在
    print("[检查] 必要文件...")
    required = {
        "main.py": "入口文件",
        "config.py": "配置文件",
        "Fake_SCR.py": "假SCR脚本",
    }
    for fname, desc in required.items():
        if not Path(fname).exists():
            print(f"  ❌ 缺少 {desc}: {fname}")
            sys.exit(1)
        print(f"  ✓ {fname}")

    # ScreenRender_Helper.exe
    if Path("ScreenRender_Helper.exe").exists():
        print(f"  ✓ ScreenRender_Helper.exe（将打包进 exe）")
    else:
        print(f"  ⚠ ScreenRender_Helper.exe 未找到（运行时需手动放置在工具箱同目录）")

    # gp_net35.exe
    gp_path = Path("resources") / "gp_net35.exe"
    if gp_path.exists():
        print(f"  ✓ resources/gp_net35.exe（将打包进 exe）")
    else:
        print(f"  ⚠ resources/gp_net35.exe 未找到（神の土豆功能不可用）")

    print()

    # ── 安装依赖 ──
    install_dependencies()

    # 构建命令
    args = build_args()
    cmd = [sys.executable, "-m", "PyInstaller"] + args
    print(f"[执行] pyinstaller {' '.join(args[:5])} ...")
    print()

    result = subprocess.run(cmd, cwd=os.getcwd())

    if result.returncode == 0:
        dist_path = Path("dist") / (APP_NAME + (".exe" if ONE_FILE else ""))
        print()
        print(f"✅ 打包完成!")
        print(f"   输出: {dist_path.resolve()}")
        if dist_path.exists():
            size_mb = dist_path.stat().st_size / (1024 * 1024)
            print(f"   大小: {size_mb:.1f} MB")
    else:
        print()
        print("❌ 打包失败，检查上方错误信息")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()