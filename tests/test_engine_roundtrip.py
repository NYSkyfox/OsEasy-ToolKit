#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_engine_roundtrip.py
==============================
patch_engine 往返测试（纯逻辑，跨平台，无需真实样本 / 无第三方依赖）。

用 screenrender_windowed 目标（单点 + 语义校验）构造一个临时"伪样本"，
在 patch 点写入原始字节、在语义校验点写入锚定字节，然后跑：
    status(未 patch) → apply(写入) → status(已 patch) → restore(还原) → status(未 patch)
逐阶段断言文件字节，验证引擎正确性。

运行：python3 tests/test_engine_roundtrip.py
"""

import os
import sys
import tempfile

# 保证项目根在 sys.path
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.core import PatchEngine, ST_NONE, ST_DONE
from src.patches.screenrender_windowed import TARGET

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


def main():
    # ── 构造伪样本 ──
    # 大小不必等于 target.size（apply 会因 size 不符走 confirm 分支，测试里 confirm 返回 True）
    size = 0x1C000
    blob = bytearray(b"\x00" * size)

    off = TARGET.patches[0].offset          # 0x1BDA6
    orig = TARGET.patches[0].orig           # 8b 45 58
    new = TARGET.patches[0].new             # 31 c0 90
    coff, cbytes = TARGET.patches[0].check  # 0x1BDA9, 89 82 44 08 00 00

    blob[off:off + len(orig)] = orig
    blob[coff:coff + len(cbytes)] = cbytes

    fd, path = tempfile.mkstemp(suffix=".exe")
    os.close(fd)
    with open(path, "wb") as f:
        f.write(bytes(blob))

    try:
        # 静默日志（避免刷屏）
        def silent(line):
            pass

        eng = PatchEngine(TARGET, path, log=silent)

        print("── 阶段1：status（应为未 patch）──")
        st = eng.status()
        check(st["exists"], "文件存在")
        s0 = st["points"][0][1]
        check(s0 == ST_NONE, f"初始状态=未 patch (实际 {s0})")
        with open(path, "rb") as f:
            check(bytes(f.read()[off:off + len(orig)]) == orig, "文件初始字节=orig")

        print("── 阶段2：apply（写入 new）──")
        ok = eng.apply(confirm=lambda m: True)
        check(ok, "apply 返回 True")
        with open(path, "rb") as f:
            data = f.read()
        check(bytes(data[off:off + len(new)]) == new, "patch 点已写入 new")
        check(bytes(data[coff:coff + len(cbytes)]) == cbytes, "语义校验点保持 cbytes")
        check(os.path.exists(path + ".bak"), "已生成 .bak 备份")
        with open(path + ".bak", "rb") as f:
            check(bytes(f.read()[off:off + len(orig)]) == orig, "备份中为原始 orig")

        print("── 阶段3：status（应为已 patch）──")
        st = eng.status()
        s1 = st["points"][0][1]
        check(s1 == ST_DONE, f"patch 后状态=已 patch (实际 {s1})")

        print("── 阶段4：重复 apply（应幂等跳过）──")
        ok2 = eng.apply(confirm=lambda m: True)
        check(ok2, "重复 apply 返回 True（幂等）")

        print("── 阶段5：restore（还原）──")
        rok = eng.restore(confirm=lambda m: True)
        check(rok, "restore 返回 True")
        with open(path, "rb") as f:
            data = f.read()
        check(bytes(data[off:off + len(orig)]) == orig, "还原后字节=orig")

        print("── 阶段6：status（应回到未 patch）──")
        st = eng.status()
        s2 = st["points"][0][1]
        check(s2 == ST_NONE, f"还原后状态=未 patch (实际 {s2})")

        print("── 阶段7：dry_run（应可 patch）──")
        dr = eng.dry_run()
        check(dr, "dry_run 校验通过")

    finally:
        for p in (path, path + ".bak"):
            if os.path.exists(p):
                os.remove(p)

    print(f"\n===== 结果：{PASS} 通过 / {FAIL} 失败 =====")
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())