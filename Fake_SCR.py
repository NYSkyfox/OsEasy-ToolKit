"""
Fake ScreenRender.exe - 假屏幕广播程序

将此文件打包为 ScreenRender_Helper.exe，
与 ToolKit 放在同一目录下，用于替换原始的 ScreenRender.exe

拦截到的广播命令会保存到指定路径，供 ToolKit 读取使用。
"""

import sys
import os

# 保存路径（当前用户的 ToolKitProd 目录）
SAVE_PATH = os.path.join(
    os.environ.get('USERPROFILE', r"C:\Users\Default"),
    "ToolKitProd",
    "SCCMD.txt"
)


def main():
    """主函数 - 处理传入的广播参数"""
    # 收集所有命令行参数
    args = sys.argv[1:]  # 排除程序本身路径
    
    if not args:
        print("未接收到广播参数")
        return
    
    # 合并参数（处理带空格的情况）
    full_cmd = " ".join(args)
    
    # 将全屏参数改为窗口化（fullscreen:1 -> fullscreen:0）
    # 这样学生端不会全屏被控，但命令参数已被记录
    processed_cmd = full_cmd.replace("#fullscreen#:1", "#fullscreen#:0")
    processed_cmd = processed_cmd.replace(" ", "")  # 去除空格
    
    # 确保保存目录存在
    os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)
    
    # 保存到文件
    try:
        with open(SAVE_PATH, 'w', encoding='utf-8') as f:
            f.write(processed_cmd)
        print("=" * 50)
        print("广播命令已拦截！")
        print("=" * 50)
        print(f"命令已保存到: {SAVE_PATH}")
        print("\n你现在可以使用 ToolKit 的广播管理功能了")
        print("按任意键退出...")
        input()
    except Exception as e:
        print(f"保存命令失败: {e}")
        input("按任意键退出...")


if __name__ == "__main__":
    main()