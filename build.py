# build.py
# ToolKit 打包脚本（自动下载 UPX + PyInstaller 压缩）
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

from datetime import datetime

from config import SOURCE_NAME

# ---- 配置 ----

APP_NAME = SOURCE_NAME
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
# 注意：ghproxy.com / fastgit 等老镜像已关停，仅保留仍可用的代理
UPX_URLS = [
    f"https://github.com/upx/upx/releases/download/v{UPX_VERSION}/{UPX_ZIP}",
    f"https://gh-proxy.com/https://github.com/upx/upx/releases/download/v{UPX_VERSION}/{UPX_ZIP}",
    f"https://ghfast.top/https://github.com/upx/upx/releases/download/v{UPX_VERSION}/{UPX_ZIP}",
    f"https://ghproxy.net/https://github.com/upx/upx/releases/download/v{UPX_VERSION}/{UPX_ZIP}",
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
    """安装缺失的项目依赖（已有则跳过）"""
    print("[依赖] 检查项目依赖...")
    vendor_dir = Path("vendor")
    use_offline = vendor_dir.exists() and any(vendor_dir.iterdir())

    if use_offline:
        print("[依赖] 使用本地离线包 (vendor/)")
    else:
        print("[依赖] 本地离线包不存在，从 PyPI 在线安装")

    # 解析 requirements.txt
    reqs = []
    with open("requirements.txt", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                reqs.append(line)

    # 用 importlib.metadata 检测已安装（一次查询所有包，比逐条 pip show 快很多）
    import importlib.metadata
    missing = []
    skipped = []
    for req in reqs:
        pkg_name = req.split("==")[0].split(">=")[0].split("<=")[0].split(">")[0].split("<")[0].strip()
        try:
            importlib.metadata.version(pkg_name)
            skipped.append(pkg_name)
        except importlib.metadata.PackageNotFoundError:
            missing.append(req)

    if skipped:
        print(f"[依赖] 已安装，跳过: {', '.join(skipped)}")

    if not missing:
        print("[依赖] 全部已安装，无需下载 ✓")
        return

    print(f"[依赖] 需要安装: {', '.join(missing)}")

    for req in missing:
        if use_offline:
            cmd = [sys.executable, "-m", "pip", "install", "--no-index", "--find-links", str(vendor_dir), req]
        else:
            cmd = [sys.executable, "-m", "pip", "install", req]
        result = subprocess.run(cmd)
        if result.returncode != 0:
            print(f"❌ 依赖安装失败: {req}")
            sys.exit(result.returncode)

    print("[依赖] 安装完成")


def build_args():
    args = [
        MAIN_SCRIPT,
        "--onefile",
        "--windowed",
        f"--name={APP_NAME}",
        "--manifest", "app.manifest",
        "--noconfirm",  # 输出已存在时不交互询问，直接覆盖
    ]

    # exe 文件图标（嵌入资源，任务栏/资源管理器显示 logo.ico）
    if Path(ICON_PATH).exists():
        args.extend(["--icon", ICON_PATH])
        print(f"[图标] 已嵌入 exe 图标: {ICON_PATH}")

    # UPX 不压缩这些模块（避免运行时解压失败）
    args.extend(["--upx-exclude", "email*"])
    args.extend(["--upx-exclude", "urllib*"])
    args.extend(["--upx-exclude", "ssl*"])
    args.extend(["--upx-exclude", "pdb*"])

    # 显式导入 email / urllib 全族
    email_mods = [
        "email", "email.mime", "email.mime.multipart",
        "email.mime.text", "email.mime.base",
    ]
    for m in email_mods:
        args.extend(["--hidden-import", m])
    args.extend(["--hidden-import", "urllib.request"])
    args.extend(["--hidden-import", "urllib.parse"])

    # ---- 添加数据文件（打包进 exe 的资源） ----
    args.extend(["--add-data", f"Fake_SCR.py{os.pathsep}."])
    args.extend(["--add-data", f"config.py{os.pathsep}."])

    # 窗口/任务栏图标
    if Path("logo.png").exists():
        args.extend(["--add-data", f"logo.png{os.pathsep}."])
        print("[图标] 已打包 logo.png")
    if Path("logo.ico").exists():
        args.extend(["--add-data", f"logo.ico{os.pathsep}."])
        print("[图标] 已打包 logo.ico")

    # ScreenRender_Helper.exe（如果存在）
    screen_helper = Path("ScreenRender_Helper.exe")
    if screen_helper.exists():
        args.extend(["--add-data", f"ScreenRender_Helper.exe{os.pathsep}."])

    # ---- 隐藏导入 ----
    extra_hidden = [
        "pynput.keyboard._win32", "pynput.mouse._win32",
        "ctypes.wintypes", "psutil", "webbrowser",
        "windows_toasts", "winrt.windows.data.xml.dom",
        "winrt.windows.foundation", "winrt.windows.foundation.collections",
        "winrt.windows.ui.notifications",
    ]
    for m in extra_hidden:
        args.extend(["--hidden-import", m])

    # ---- 排除不需要的大模块 ----
    exclude_modules = [
        "matplotlib", "numpy", "pandas", "PIL",
        "PyQt5", "PyQt6", "PySide2", "PySide6", "wx",
        "IPython", "jupyter", "notebook",
        "pydoc", "unittest", "test",
        "setuptools", "pip",
    ]
    for mod in exclude_modules:
        args.extend(["--exclude-module", mod])

    # ---- UPX 压缩 ----
    upx_path = find_upx()
    if upx_path:
        print(f"[UPX] 找到: {upx_path}")
        # 如果是本地 tools/ 目录下的 upx，传绝对路径给 PyInstaller
        # 如果在系统 PATH 里（返回的是 "upx.exe" 这种裸名），不传 --upx-dir
        upx_path_obj = Path(upx_path)
        if upx_path_obj.exists():
            args.extend(["--upx-dir", str(upx_path_obj.resolve().parent)])
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

    print()

    # ── 安装依赖 ──
    install_dependencies()

    # ── 注入构建日期（正则替换，幂等；打包后恢复源码，避免污染 config.py） ──
    import re
    print("[构建] 写入构建日期到 config.py ...")
    build_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    config_path = Path("config.py")
    original_cfg = config_path.read_text(encoding="utf-8")
    content = re.sub(
        r'BUILD_DATE = "[^"]*"',
        f'BUILD_DATE = "{build_date}"',
        original_cfg,
        count=1,
    )
    config_path.write_text(content, encoding="utf-8")
    print(f"[构建] 构建日期: {build_date}")

    try:
        # 构建命令
        args = build_args()

        # 删除旧的 .spec 文件（防止残留硬编码路径）
        spec_file = Path(f"{APP_NAME}.spec")
        if spec_file.exists():
            spec_file.unlink()
            print(f"[清理] 已删除旧 spec: {spec_file}")

        cmd = [sys.executable, "-m", "PyInstaller"] + args
        print(f"[执行] pyinstaller {' '.join(args[:5])} ...")
        print()

        result = subprocess.run(cmd, cwd=os.getcwd())
    finally:
        # 无论成败都恢复 config.py 源码（避免 BUILD_DATE 被持久修改）
        config_path.write_text(original_cfg, encoding="utf-8")

    if result.returncode == 0:
        dist_path = Path("dist") / (APP_NAME + (".exe" if ONE_FILE else ""))
        print()
        print(f"✅ 打包完成!")
        print(f"   输出: {dist_path.resolve()}")

        # ── 计算 SHA256 并重命名 ──
        import hashlib
        from config import APP_VERSION
        sha256 = hashlib.sha256()
        with open(dist_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        hash_short = sha256.hexdigest()[:7]
        version_str = APP_VERSION.replace(" ", "_")
        new_name = f"{APP_NAME}_v{version_str}_{hash_short}.exe"
        new_path = dist_path.parent / new_name
        dist_path.rename(new_path)
        size_mb = new_path.stat().st_size / (1024 * 1024)
        print(f"   重命名: {new_name}")
        print(f"   大小: {size_mb:.1f} MB")
        print(f"   SHA256: {sha256.hexdigest()}")
    else:
        print()
        print("❌ 打包失败，检查上方错误信息")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()