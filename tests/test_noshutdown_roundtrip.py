#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_noshutdown_roundtrip.py
==================================
noshutdown 文件版往返测试（纯逻辑，跨平台，无需真实样本 / 无第三方依赖）。

重构后：执行逻辑统一在 src/core/va_patch.VAPatchExecutor，
patch 点配置在 src/patches/noshutdown.py（纯数据）。

构造一个最小但合法的 PE32 伪样本：
  - 单 .text 节，RVA 0x1000 .. 0x101000，rawptr=0x1000（rawptr 对齐）
  - 目标点 VA 0x4A9660 (RVA 0x0A9660) 落在 .text 内，入口写原始 55 8b ec
然后跑：
  dry_run(可 patch) -> patch(inplace, 写 31 c0 c3) -> 校验字节
  -> 重复 patch(幂等) -> status(已 patch) -> restore(还原) -> 校验
逐阶段断言文件字节，验证 PE 解析 / VA 定位 / 备份还原正确性。

内存版依赖 Windows 进程 API，本测试不覆盖（跨平台限制）。

运行：python3 tests/test_noshutdown_roundtrip.py
"""

import os
import sys
import struct
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.core.va_patch import VAPatchExecutor
from src.patches import get_va_target

PASS = 0
FAIL = 0


def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
        print("  ✓ " + msg)
    else:
        FAIL += 1
        print("  ✗ " + msg)


def build_fake_pe(path, image_base, point_va, orig):
    """构造最小 PE32，点 VA 落在 .text 内（rawptr 对齐，off==RVA）。"""
    size = 0x100000
    blob = bytearray(b"\x00" * size)

    blob[0:2] = b"MZ"
    struct.pack_into("<I", blob, 0x3c, 0x80)          # e_lfanew = 0x80
    blob[0x80:0x84] = b"PE\0\0"
    # COFF header @0x84: machine,nsec,ts,sym,nsym,opt_size,char
    struct.pack_into("<HHIIIHH", blob, 0x84, 0x14c, 1, 0, 0, 0, 0xE0, 0)
    opt = 0x98
    struct.pack_into("<H", blob, opt, 0x10b)           # magic PE32
    struct.pack_into("<I", blob, opt + 28, image_base)  # ImageBase
    # Section table @ opt+opt_size = 0x178: 1 section
    so = 0x178
    struct.pack_into("<8s", blob, so, b".text\0\0\0")
    struct.pack_into("<IIII", blob, so + 8, 0x100000, 0x1000, 0x100000, 0x1000)

    rva = point_va - image_base
    off = 0x1000 + (rva - 0x1000)
    blob[off:off + 3] = orig
    with open(path, "wb") as f:
        f.write(bytes(blob))
    return off


def main():
    target = get_va_target("noshutdown")
    pt = target.files[0].patch_points[0]
    image_base = target.image_base

    fd, path = tempfile.mkstemp(suffix=".exe")
    os.close(fd)
    try:
        target_off = build_fake_pe(path, image_base, pt.va, pt.orig)
        print("── 构造伪样本，目标 fileoff=0x%06x ──" % target_off)
        check(target_off == pt.va - image_base, "目标偏移 = RVA（rawptr 对齐）")

        def silent(line):
            pass

        ex = VAPatchExecutor(target, path, log=silent)

        print("── 阶段1：dry_run（应可 patch）──")
        ok = ex.dry_run(strict=True)
        check(ok, "dry-run 返回 True")
        with open(path, "rb") as f:
            data = f.read()
        check(bytes(data[target_off:target_off + 3]) == pt.orig,
              "文件初始入口 = orig")

        print("── 阶段2：patch(inplace)（写入 patch 字节）──")
        pok = ex.patch(inplace=True, strict=True)
        check(pok, "patch 返回 True")
        with open(path, "rb") as f:
            data = f.read()
        check(bytes(data[target_off:target_off + 3]) == pt.new,
              "patch 后入口 = %s" % pt.new.hex(" "))
        check(os.path.exists(path + target.backup_ext), "已生成备份")
        with open(path + target.backup_ext, "rb") as f:
            bak = f.read()
        check(bytes(bak[target_off:target_off + 3]) == pt.orig,
              "备份中为原始 orig")

        print("── 阶段3：重复 patch（应幂等跳过）──")
        pok2 = ex.patch(inplace=True, strict=False)
        check(pok2, "重复 patch 返回 True（幂等）")

        print("── 阶段4：status（应显示已 patch）──")
        st = ex.status()
        check(st["points"][0][1] == "已 patch", "status 读出入口 = 已 patch")

        print("── 阶段5：restore（还原）──")
        rok = ex.restore()
        check(rok, "restore 返回 True")
        with open(path, "rb") as f:
            data = f.read()
        check(bytes(data[target_off:target_off + 3]) == pt.orig,
              "还原后入口 = orig")

        print("── 阶段6：dry_run（应回到可 patch）──")
        ok3 = ex.dry_run(strict=True)
        check(ok3, "还原后 dry-run 校验通过")

    finally:
        for p in (path, path + target.backup_ext):
            if os.path.exists(p):
                os.remove(p)

    print("\n===== 结果：%d 通过 / %d 失败 =====" % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
