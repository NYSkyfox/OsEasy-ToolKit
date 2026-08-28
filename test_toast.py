# test_toast.py —— 独立测试：用 windows-toasts 发送一条标准 Windows 通知
# 运行: python test_toast.py

import os
import sys
import traceback

# 确保能找到项目根路径的 logo.png
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from pathlib import Path
from windows_toasts import (
    WindowsToaster,
    Toast,
    ToastDisplayImage,
)

APP_ID = "OsEasy-ToolKit"

def main():
    print("=== Windows Toast 独立测试 ===")
    print(f"Python: {sys.version}")
    print(f"App ID: {APP_ID}")

    # 1) 图标
    for name in ("logo.png", "logo.ico"):
        p = Path(name)
        print(f"  {name}: exists={p.exists()}  abs={p.resolve() if p.exists() else 'N/A'}")

    # 2) 创建 toaster（WindowsToaster 支持自定义来源名）
    print(f"\n 创建 WindowsToaster ...")
    from windows_toasts import WindowsToaster
    toaster = WindowsToaster(APP_ID)

    # 3) 构造 Toast
    text = ["OsEasy-ToolKit 测试", "如果你看到这条通知，说明库可用！"]
    images = []
    logo = Path("logo.png")
    if logo.exists():
        images.append(ToastDisplayImage.fromPath(
            str(logo),
            altText="OsEasy-ToolKit",
        ))
        print(f"  图标: {logo.resolve().as_uri()}")

    toast = Toast(text_fields=text, images=images)

    # 4) 失败/关闭回调
    def on_failed(e):
        print(f"  ❌ 通知失败: {e}")
    def on_dismissed(e):
        print(f"  ℹ 通知被关闭: reason={getattr(e, 'reason', None)}")
    toast.on_failed = on_failed
    toast.on_dismissed = on_dismissed

    # 5) 发送
    try:
        toaster.show_toast(toast)
        print("  ✓ show_toast() 返回（WinRT 调用完成）")
    except Exception:
        print("  ❌ 异常:")
        traceback.print_exc()
        return

    print("\n等待 5 秒收集回调...")
    import time
    time.sleep(5)
    print("=== 测试结束 ===")

if __name__ == "__main__":
    main()