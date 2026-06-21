"""
一键构建脚本

使用 PyInstaller 打包为可执行文件

依赖安装:
    pip install pyinstaller psutil pyautogui pygetwindow

使用方法:
    python build.py
"""

import os
import sys
import subprocess
import shutil


def clean_build():
    """清理构建目录"""
    dirs_to_remove = ["build", "dist"]
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            print(f"清理 {dir_name}...")
            shutil.rmtree(dir_name)
    
    # 删除 spec 文件
    for file in os.listdir("."):
        if file.endswith(".spec"):
            print(f"删除 {file}...")
            os.remove(file)
    
    print("清理完成")


def build():
    """执行构建"""
    print("=" * 50)
    print("OsEasy-ToolKit 构建脚本")
    print("=" * 50)
    
    # 检查 PyInstaller
    try:
        import PyInstaller
        print("✓ PyInstaller 已安装")
    except ImportError:
        print("✗ PyInstaller 未安装，正在安装...")
        subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # 清理旧构建
    clean_build()
    
    # 构建命令
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "OsEasy-ToolKit",
        "--onefile",           # 打包为单个文件
        "--windowed",          # 不显示控制台窗口
        "--icon", "NONE",      # 无图标（可自行指定 .ico 文件）
        "--add-data", "config.py;.",  # 包含配置文件
        "--clean",             # 清理临时文件
        "main.py"
    ]
    
    print("\n开始构建...")
    print(" ".join(cmd))
    print()
    
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n" + "=" * 50)
        print("构建成功！")
        print("=" * 50)
        print(f"输出目录: {os.path.abspath('dist')}")
        print("可执行文件: dist/OsEasy-ToolKit.exe")
        
        # 复制 Fake_SCR.py 到 dist
        if os.path.exists("Fake_SCR.py"):
            shutil.copy("Fake_SCR.py", "dist/")
            print("已复制 Fake_SCR.py 到 dist 目录")
    else:
        print("\n构建失败！")
        sys.exit(1)


def build_with_console():
    """构建带控制台的版本（用于调试）"""
    print("=" * 50)
    print("OsEasy-ToolKit 调试版本构建")
    print("=" * 50)
    
    clean_build()
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--name", "OsEasy-ToolKit-Debug",
        "--onefile",
        "--console",           # 显示控制台（调试用）
        "--icon", "NONE",
        "--add-data", "config.py;.",
        "--clean",
        "main.py"
    ]
    
    print("\n开始构建调试版本...")
    result = subprocess.run(cmd)
    
    if result.returncode == 0:
        print("\n调试版本构建成功！")
        print(f"输出: dist/OsEasy-ToolKit-Debug.exe")
    else:
        print("\n构建失败！")
        sys.exit(1)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="OsEasy-ToolKit 构建脚本")
    parser.add_argument(
        "--debug", 
        action="store_true",
        help="构建带控制台的调试版本"
    )
    parser.add_argument(
        "--clean",
        action="store_true", 
        help="仅清理构建文件"
    )
    
    args = parser.parse_args()
    
    if args.clean:
        clean_build()
    elif args.debug:
        build_with_console()
    else:
        build()