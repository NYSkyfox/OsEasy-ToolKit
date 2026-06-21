"""
OsEasy-ToolKit 入口文件

启动命令:
    python main.py

打包命令:
    python build.py
"""

import sys
import os
import subprocess
import importlib

# 所需依赖列表
REQUIRED_PACKAGES = [
    "psutil",
    "pyautogui",
    "pygetwindow",
    "pynput",
]


def check_dependencies() -> bool:
    """
    检查所有必需依赖是否已安装

    Returns:
        True 全部已安装，False 有缺失
    """
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
        except ImportError:
            missing.append(pkg)

    if missing:
        print("=" * 50)
        print("检测到以下依赖未安装：")
        for pkg in missing:
            print(f"  - {pkg}")
        print("=" * 50)
        return False
    return True


def install_dependencies() -> bool:
    """
    自动安装缺失的依赖

    Returns:
        是否全部安装成功
    """
    print("正在自动安装依赖...")
    print()

    success = True
    for pkg in REQUIRED_PACKAGES:
        try:
            importlib.import_module(pkg)
            continue  # 已安装，跳过
        except ImportError:
            pass

        print(f"正在安装 {pkg}...", end=" ")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg],
                capture_output=True,
                text=True,
                timeout=120,
            )
            if result.returncode == 0:
                print("✓")
            else:
                print("✗")
                print(f"  错误: {result.stderr.strip()}")
                success = False
        except subprocess.TimeoutExpired:
            print(f"✗ (安装超时)")
            success = False
        except Exception as e:
            print(f"✗ ({e})")
            success = False

    print()
    if success:
        print("所有依赖安装完成！")
    else:
        print("部分依赖安装失败，请手动执行: pip install " + " ".join(REQUIRED_PACKAGES))
    print("=" * 50)
    return success


def ensure_dependencies() -> bool:
    """
    确保所有依赖可用，缺失则自动安装

    Returns:
        是否可继续运行
    """
    if check_dependencies():
        return True

    print("正在尝试自动安装...")
    print()

    if not install_dependencies():
        return False

    # 安装后二次验证
    if not check_dependencies():
        print("依赖安装后仍然缺失，请手动安装。")
        return False

    return True


# 确保当前目录在路径中
if getattr(sys, 'frozen', False):
    # 打包后的环境
    BASE_DIR = os.path.dirname(sys.executable)
else:
    # 开发环境
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def main():
    """程序入口"""
    if not ensure_dependencies():
        input("按 Enter 键退出...")
        sys.exit(1)

    from app import main as app_main
    app_main()


if __name__ == "__main__":
    main()