#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
OsEasy ManagerHelper - 禁用教学管控
====================================
patch MultiClient.exe，使以下教师端管控指令在学生机无效：
  1. 屏幕广播（可选）  2. 键鼠锁  3. 行为管控（网络/USB/程序）

用法:
  python patch_disable_control.py                     # 全部禁用（含屏幕广播）
  python patch_disable_control.py --no-screen         # 不禁屏幕广播（保留）
  python patch_disable_control.py --restore           # 还原
  python patch_disable_control.py --status            # 查看当前状态
  python patch_disable_control.py --path "D:/xxx/MultiClient.exe"  # 指定路径

安全: 修改前自动备份（*.bak），还原从备份恢复，字节级校验。
"""
import os, sys, struct, hashlib, argparse, shutil

# ─── 样本指纹 ────────────────────────────────────────────────────────────────
SAMPLE_NAME = "MultiClient.exe"
SAMPLE_MD5 = "b8bb9b809e8f45918f6759d4cb51f5b0"
SAMPLE_SIZE = 1189376

# ─── Patch 点定义 ────────────────────────────────────────────────────────────
# (label, file_offset, orig_bytes, new_bytes, required)
PATCHES = [
    ("屏幕广播入口",     0x2ED70, bytes.fromhex("558bec"), bytes.fromhex("31c0c3"), False),  # 可选
    ("键鼠锁指令",       0x1A210, bytes.fromhex("558bec"), bytes.fromhex("31c0c3"), True),
    ("行为管控转发",     0x18BA0, bytes.fromhex("558bec"), bytes.fromhex("31c0c3"), True),
]

# ─── 默认搜索路径 ────────────────────────────────────────────────────────────
DEFAULT_DIRS = [
    r"C:\Program Files (x86)\Os-Easy\os-easy multicast teaching system",
    r"C:\Program Files\Os-Easy\os-easy multicast teaching system",
    r"D:\Os-Easy\os-easy multicast teaching system",
]


def find_sample(explicit_path=None):
    """定位 MultiClient.exe"""
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


def is_patched(data):
    """检查每个 patch 点的当前状态"""
    results = []
    for label, off, orig, new, req in PATCHES:
        cur = data[off:off+len(orig)]
        if cur == new:
            results.append((label, "已 patch"))
        elif cur == orig:
            results.append((label, "未 patch"))
        else:
            results.append((label, f"异常: {cur.hex(' ')}"))
    return results


def do_status(path):
    print(f"\n{'='*60}")
    print(f"  {SAMPLE_NAME} 状态")
    print(f"  路径: {path}")
    print(f"  大小: {os.path.getsize(path)}  (预期 {SAMPLE_SIZE})")
    md5 = md5_of(path)
    print(f"  MD5:  {md5}")
    if md5 == SAMPLE_MD5:
        print(f"  指纹: ✓ 与原始样本一致")
    else:
        print(f"  指纹: ⚠ 与原始样本不同（可能已 patch 或版本不同）")
    data = open(path, "rb").read()
    print(f"\n  Patch 点状态:")
    for label, state in is_patched(data):
        icon = "●" if "已 patch" in state else "○" if "未 patch" in state else "!"
        print(f"    {icon} {label:<12} {state}")
    print(f"{'='*60}\n")


def do_patch(path, skip_screen=False):
    """执行 patch"""
    print(f"\n[1/5] 校验样本...")
    if os.path.getsize(path) != SAMPLE_SIZE:
        print(f"  ✗ 文件大小不符: {os.path.getsize(path)} ≠ {SAMPLE_SIZE}")
        sys.exit(1)
    md5 = md5_of(path)
    if md5 == SAMPLE_MD5:
        print(f"  ✓ MD5 = {md5}（原始样本）")
    else:
        # 检查是否已 patch
        data = open(path, "rb").read()
        statuses = is_patched(data)
        if all("已 patch" in s for _, s in statuses):
            print(f"  ⚠ 文件已被 patch（MD5={md5}），跳过（请先 --restore）")
            sys.exit(0)
        print(f"  ⚠ MD5 不匹配（{md5}），可能是其他版本。继续执行（风险自担）。")
        if input("  确认继续? [y/N] ").lower() != "y":
            sys.exit(0)

    data = bytearray(open(path, "rb").read())

    print(f"\n[2/5] 校验 patch 点原字节...")
    active_patches = []
    for label, off, orig, new, req in PATCHES:
        if not req and skip_screen:
            print(f"  ○ {label:<12} 跳过（--no-screen）")
            continue
        cur = bytes(data[off:off+len(orig)])
        if cur == new:
            print(f"  ⚠ {label:<12} 已是 patch 状态，跳过")
            continue
        if cur != orig:
            print(f"  ✗ {label:<12} 原字节不符: {cur.hex(' ')} ≠ {orig.hex(' ')}")
            print(f"    该文件可能已被修改或版本不同，中止。")
            sys.exit(1)
        print(f"  ✓ {label:<12} off={off:#06x}  {orig.hex(' ')}")
        active_patches.append((label, off, orig, new))

    if not active_patches:
        print("\n  无可执行的 patch（全部已 patch 或被跳过）")
        return

    # 备份
    bak = path + ".bak"
    if not os.path.exists(bak):
        shutil.copy2(path, bak)
        print(f"\n[3/5] 备份 → {os.path.basename(bak)}")
    else:
        print(f"\n[3/5] 备份已存在: {os.path.basename(bak)}（不覆盖）")

    # 执行 patch
    print(f"\n[4/5] 写入 patch ({len(active_patches)} 处)...")
    for label, off, orig, new in active_patches:
        data[off:off+len(orig)] = new
        print(f"  ✓ {label:<12} off={off:#06x}  → {new.hex(' ')}")

    with open(path, "wb") as f:
        f.write(data)

    # 验证
    print(f"\n[5/5] 验证...")
    back = open(path, "rb").read()
    ok = True
    for label, off, orig, new in active_patches:
        if back[off:off+len(orig)] != new:
            print(f"  ✗ {label} 验证失败")
            ok = False
    if ok:
        print(f"  ✓ 全部 patch 验证通过")
        print(f"\n  完成！重启 MultiClient 进程后生效。")
        print(f"  还原: python {os.path.basename(__file__)} --restore")
    else:
        print(f"\n  ✗ 验证失败！请立即 --restore")
        sys.exit(1)


def do_restore(path):
    """从备份还原"""
    bak = path + ".bak"
    if not os.path.exists(bak):
        print(f"\n[错误] 备份不存在: {bak}")
        print(f"  无法还原。请确认之前执行过 patch。")
        sys.exit(1)

    # 验证备份是原始样本
    bak_md5 = md5_of(bak)
    if bak_md5 == SAMPLE_MD5:
        print(f"\n  备份 MD5 = {bak_md5} ✓（原始样本）")
    else:
        print(f"\n  ⚠ 备份 MD5 = {bak_md5}（非原始指纹，可能是二次修改前的备份）")
        if input("  仍要还原? [y/N] ").lower() != "y":
            sys.exit(0)

    shutil.copy2(bak, path)
    print(f"  ✓ 已还原: {path}")
    print(f"  备份保留: {bak}")
    new_md5 = md5_of(path)
    print(f"  还原后 MD5 = {new_md5}")
    if new_md5 == SAMPLE_MD5:
        print(f"  ✓ 与原始样本一致")
    print(f"\n  重启 MultiClient 进程后生效。")


def main():
    ap = argparse.ArgumentParser(description="OsEasy - 禁用教学管控 (MultiClient.exe)")
    ap.add_argument("--path", help=f"{SAMPLE_NAME} 路径（默认自动搜索）")
    ap.add_argument("--no-screen", action="store_true", help="不禁用屏幕广播（仅禁键鼠+行为管控）")
    ap.add_argument("--restore", action="store_true", help="还原（从 .bak 备份恢复）")
    ap.add_argument("--status", action="store_true", help="查看当前 patch 状态")
    args = ap.parse_args()

    path = find_sample(args.path)

    if args.status:
        do_status(path)
    elif args.restore:
        do_restore(path)
    else:
        do_patch(path, skip_screen=args.no_screen)


if __name__ == "__main__":
    main()
