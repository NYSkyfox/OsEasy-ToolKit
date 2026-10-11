#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OsEasy ManagerHelper - 屏幕广播窗口化
======================================
patch ScreenRender.exe，使教师端屏幕广播始终以「窗口化」模式启动，
而非默认的全屏铺满。广播功能保留、画面照常显示，只是变成可拖拽/可缩放的窗口。

原理:
  ScreenRenderApp 构造函数 FUN_0041c7d0 会把命令行 --fullscreen 参数值
  写入 this+0x844。该字段 1=全屏 / 0=窗口 / 2=窗口(缩放)。
  本脚本 patch「读取参数值」的指令 (mov eax,[ebp+0x58] → xor eax,eax)，
  强制 fullscreen=0，使窗口创建走窗口化分支。

用法:
  python patch_windowed_broadcast.py                 # patch 窗口化
  python patch_windowed_broadcast.py --restore       # 还原
  python patch_windowed_broadcast.py --status        # 查看状态
  python patch_windowed_broadcast.py --path "D:\\xxx\\ScreenRender.exe"

安全: 修改前自动备份（*.bak），还原从备份恢复，字节级校验。
"""
import os, sys, struct, hashlib, argparse, shutil

# ─── 样本指纹 ────────────────────────────────────────────────────────────────
SAMPLE_NAME = "ScreenRender.exe"
SAMPLE_MD5 = "76cfa20119b247685827d9341132570a"
SAMPLE_SIZE = 450048

# ─── Patch 点 ────────────────────────────────────────────────────────────────
# "mov eax,[ebp+0x58]" → "xor eax,eax; nop"  (强制 fullscreen=0 窗口化)
PATCH = {
    "label": "fullscreen 赋值",
    "offset": 0x1BDA6,
    "orig":  bytes.fromhex("8b4558"),   # mov eax, [ebp+0x58]
    "new":   bytes.fromhex("31c090"),   # xor eax, eax; nop
    "check_store": (0x1BDA9, bytes.fromhex("898244080000")),  # mov [edx+0x844], eax (紧随其后)
}

# ─── 默认搜索路径 ────────────────────────────────────────────────────────────
DEFAULT_DIRS = [
    r"C:\Program Files (x86)\Os-Easy\os-easy multicast teaching system",
    r"C:\Program Files\Os-Easy\os-easy multicast teaching system",
    r"D:\Os-Easy\os-easy multicast teaching system",
]


def find_sample(explicit_path=None):
    if explicit_path:
        if os.path.isfile(explicit_path):
            return explicit_path
        print(f"[错误] 指定路径不存在: {explicit_path}")
        sys.exit(1)
    for d in DEFAULT_DIRS:
        p = os.path.join(d, SAMPLE_NAME)
        if os.path.isfile(p):
            return p
    print(f"[错误] 未找到 {SAMPLE_NAME}，请用 --path 指定路径")
    sys.exit(1)


def md5_of(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def state_of(data):
    off, orig, new = PATCH["offset"], PATCH["orig"], PATCH["new"]
    cur = data[off:off+len(orig)]
    if cur == new:
        return "已 patch (窗口化)"
    if cur == orig:
        return "未 patch (原始)"
    return f"异常: {cur.hex(' ')}"


def do_status(path):
    print(f"\n{'='*60}")
    print(f"  {SAMPLE_NAME} 状态")
    print(f"  路径: {path}")
    print(f"  大小: {os.path.getsize(path)}  (预期 {SAMPLE_SIZE})")
    md5 = md5_of(path)
    print(f"  MD5:  {md5}")
    print(f"  指纹: {'✓ 原始样本' if md5 == SAMPLE_MD5 else '⚠ 非原始（可能已 patch 或版本不同）'}")
    data = open(path, "rb").read()
    print(f"  窗口化: {state_of(data)}")
    print(f"{'='*60}\n")


def do_patch(path):
    print(f"\n[1/5] 校验样本...")
    if os.path.getsize(path) != SAMPLE_SIZE:
        print(f"  ✗ 文件大小不符: {os.path.getsize(path)} ≠ {SAMPLE_SIZE}")
        sys.exit(1)
    md5 = md5_of(path)
    data = bytearray(open(path, "rb").read())

    off, orig, new = PATCH["offset"], PATCH["orig"], PATCH["new"]
    cur = bytes(data[off:off+len(orig)])

    if md5 == SAMPLE_MD5:
        print(f"  ✓ MD5 = {md5}（原始样本）")
    else:
        print(f"  ⚠ MD5 不匹配（{md5}），可能版本不同，按 patch 点字节校验继续。")

    if cur == new:
        print(f"  ⚠ 已是窗口化状态，跳过（如需原始请 --restore）")
        return
    if cur != orig:
        print(f"  ✗ patch 点原字节不符: {cur.hex(' ')} ≠ {orig.hex(' ')}")
        print(f"    该文件可能已被修改或版本不同，中止。")
        sys.exit(1)

    # 校验紧随的 store 指令（确认 patch 点语义正确）
    soff, sbytes = PATCH["check_store"]
    scur = bytes(data[soff:soff+len(sbytes)])
    if scur != sbytes:
        print(f"  ✗ 语义校验失败: 紧随 store 不符 {scur.hex(' ')} ≠ {sbytes.hex(' ')}")
        print(f"    可能版本不匹配，中止。")
        sys.exit(1)
    print(f"  ✓ patch 点 + 语义校验通过")

    # 备份
    bak = path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        print(f"\n[3/5] 备份 → {os.path.basename(bak)}")
    else:
        print(f"\n[3/5] 备份已存在: {os.path.basename(bak)}（不覆盖）")

    # 写入
    print(f"\n[4/5] 写入 patch...")
    data[off:off+len(orig)] = new
    print(f"  ✓ {PATCH['label']:<14} off={off:#06x}  {orig.hex(' ')} → {new.hex(' ')}")
    with open(path, "wb") as f:
        f.write(data)

    # 验证
    print(f"\n[5/5] 验证...")
    back = open(path, "rb").read()
    if back[off:off+len(orig)] == new:
        print(f"  ✓ patch 验证通过")
        print(f"\n  完成！下次教师端发起屏幕广播时将以窗口模式显示。")
        print(f"  还原: python {os.path.basename(__file__)} --restore")
    else:
        print(f"\n  ✗ 验证失败！请立即 --restore")
        sys.exit(1)


def do_restore(path):
    bak = path + ".bak"
    if not os.path.exists(bak):
        print(f"\n[错误] 备份不存在: {bak}")
        sys.exit(1)
    bak_md5 = md5_of(bak)
    if bak_md5 == SAMPLE_MD5:
        print(f"\n  备份 MD5 = {bak_md5} ✓（原始样本）")
    else:
        print(f"\n  ⚠ 备份 MD5 = {bak_md5}（非原始指纹）")
        if input("  仍要还原? [y/N] ").lower() != "y":
            sys.exit(0)
    shutil.copy2(bak, path)
    print(f"  ✓ 已还原: {path}")
    new_md5 = md5_of(path)
    print(f"  还原后 MD5 = {new_md5}  {'✓ 原始' if new_md5 == SAMPLE_MD5 else '⚠ 非原始'}")
    print(f"\n  下次屏幕广播将恢复全屏。")


def main():
    ap = argparse.ArgumentParser(description="OsEasy - 屏幕广播窗口化 (ScreenRender.exe)")
    ap.add_argument("--path", help=f"{SAMPLE_NAME} 路径（默认自动搜索）")
    ap.add_argument("--restore", action="store_true", help="还原（从 .bak 备份恢复）")
    ap.add_argument("--status", action="store_true", help="查看当前状态")
    args = ap.parse_args()

    path = find_sample(args.path)
    if args.status:
        do_status(path)
    elif args.restore:
        do_restore(path)
    else:
        do_patch(path)


if __name__ == "__main__":
    main()