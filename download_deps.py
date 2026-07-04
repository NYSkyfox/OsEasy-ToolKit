# download_deps.py
# 把项目依赖下载为离线 whl 包，存到 vendor/ 目录
# 在有网的电脑上运行一次，之后把 vendor/ 一起带走

import subprocess
import sys
from pathlib import Path

VENDOR_DIR = Path("vendor")
REQUIREMENTS = "requirements.txt"


def main():
    VENDOR_DIR.mkdir(exist_ok=True)

    print("=== 下载离线依赖 whl 包 ===")
    print(f"输出目录: {VENDOR_DIR.resolve()}")
    print()

    # pip download 会下载当前 Python 版本的 wheel
    cmd = [
        sys.executable, "-m", "pip", "download",
        "--only-binary", ":all:",
        "-d", str(VENDOR_DIR),
        "-r", REQUIREMENTS,
    ]
    print(f"执行: {' '.join(cmd)}")
    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("\n✅ 下载完成，文件列表:")
        for f in sorted(VENDOR_DIR.iterdir()):
            size_mb = f.stat().st_size / (1024 * 1024)
            print(f"   {f.name} ({size_mb:.1f} MB)")
    else:
        print("\n❌ 下载失败")
        sys.exit(result.returncode)


if __name__ == "__main__":
    main()