#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_noshutdown_roundtrip.py
==================================
noshutdown 文件版往返测试（纯逻辑，跨平台，无需真实样本 / 无第三方依赖）。

构造一个最小但合法的 PE32 伪样本：
  - 单 .text 节，RVA 0x1000 .. 0x101000
  - 目标函数 FUN_004a9660 (RVA 0x0A9660) 落在 .text 内
  - 入口 3 字节写为原始 55 8b ec
然后跑：
    file_dry_run(可 patch) -> file_patch(inplace, 写入 31 c0 c3) -> 校验字节
    -> file_restore(还原) -> 校验字节
逐阶段断言文件字节，验证 PE 解析 / RVA 定位 / 备份还原正确性。

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

from src.modules import noshutdown

PASS = 0
FAIL = 0


def check(cond, msg):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"  ✓ {msg}")
    else:
        FAIL += 1
        print(f"  ✗ {msg}")


def build_fake_pe(path):
    """构造最小 PE32，RVA 0x0A9660 -> fileoff 0x0A9660（rawptr==va==0x1000）。"""
    size = 0x100000
    blob = bytearray(b"\x00" * size)

    # DOS header
    blob[0:2] = b"MZ"
    struct.pack_into("<I", blob, 0x3c, 0x80)          # e_lfanew = 0x80

    # PE signature
    blob[0x80:0x84] = b"PE\0\0"

    # COFF header (at 0x84): machine,nsec,ts,sym,nsym,opt_size,char
    struct.pack_into("<HHIIIHH", blob, 0x84, 0x14c, 1, 0, 0, 0, 0xE0, 0)

    # Optional header (PE32, at 0x98)
    opt = 0x98
    struct.pack_into("<H", blob, opt, 0x10b)            # magic PE32
    struct.pack_into("<I", blob, opt + 28, 0x400000)    # ImageBase (PE32 @ +28)

    # Section table (at opt + opt_size = 0x178): 1 section
    so = 0x178
    struct.pack_into("<8s", blob, so, b".text\0\0\0")
    # vsize, va, rawsz, rawptr  @ so+8
    struct.pack_into("<IIII", blob, so + 8, 0x100000, 0x1000, 0x100000, 0x1000)

    # 目标函数入口写原始字节
    target_off = 0x1000 + (noshutdown.FUNC_RVA - 0x1000)  # = 0x0A9660
    blob[target_off:target_off + 3] = noshutdown.ORIG_BYTES

    with open(path, "wb") as f:
        f.write(bytes(blob))
    return target_off


def main():
    fd, path = tempfile.mkstemp(suffix=".exe")
    os.close(fd)
    try:
        target_off = build_fake_pe(path)
        print(f"── 构造伪样本，目标 fileoff=0x{target_off:06x} ──")
        check(target_off == noshutdown.FUNC_RVA, "目标偏移 = RVA（rawptr 对齐）")

        def silent(line):
            pass

        print("── 阶段1：file_dry_run（应可 patch）──")
        ok, pe = noshutdown.file_dry_run(path, log=silent)
        check(ok, "dry-run 返回 True")
        check(pe.target_off == target_off, f"PE 解析 target_off=0x{pe.target_off:06x}")
        check(pe.image_base == 0x400000, f"ImageBase=0x{pe.image_base:06x}")
        with open(path, "rb") as f:
            data = f.read()
        check(bytes(data[target_off:target_off + 3]) == noshutdown.ORIG_BYTES,
              "文件初始入口 = 55 8b ec")

        print("── 阶段2：file_patch(inplace)（写入 31 c0 c3）──")
        pok = noshutdown.file_patch(path, inplace=True, log=silent)
        check(pok, "file_patch 返回 True")
        with open(path, "rb") as f:
            data = f.read()
        check(bytes(data[target_off:target_off + 3]) == noshutdown.PATCH_BYTES,
              "patch 后入口 = 31 c0 c3")
        check(os.path.exists(path + noshutdown.BACKUP_EXT), "已生成 .noshutdown.bak")
        with open(path + noshutdown.BACKUP_EXT, "rb") as f:
            bak = f.read()
        check(bytes(bak[target_off:target_off + 3]) == noshutdown.ORIG_BYTES,
              "备份中为原始 55 8b ec")

        print("── 阶段3：重复 file_patch（应幂等跳过）──")
        pok2 = noshutdown.file_patch(path, inplace=True, strict=False, log=silent)
        check(pok2, "重复 file_patch 返回 True（幂等）")

        print("── 阶段4：file_status（应显示已拦截）──")
        st_bytes = noshutdown.file_status(path, log=silent)
        check(st_bytes == noshutdown.PATCH_BYTES, "status 读出入口 = patch 字节")

        print("── 阶段5：file_restore（还原）──")
        rok = noshutdown.file_restore(path, log=silent)
        check(rok, "file_restore 返回 True")
        with open(path, "rb") as f:
            data = f.read()
        check(bytes(data[target_off:target_off + 3]) == noshutdown.ORIG_BYTES,
              "还原后入口 = 55 8b ec")

        print("── 阶段6：file_dry_run（应回到可 patch）──")
        ok3, _ = noshutdown.file_dry_run(path, log=silent)
        check(ok3, "还原后 dry-run 校验通过")

    finally:
        for p in (path, path + noshutdown.BACKUP_EXT):
            if os.path.exists(p):
                os.remove(p)

    print(f"\n===== 结果：{PASS} 通过 / {FAIL} 失败 =====")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())