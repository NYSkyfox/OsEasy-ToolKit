#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tests/test_dog_roundtrip.py
===========================
dog_license（教师端 加密狗 / 点数限制 解除）往返测试
（纯逻辑，跨平台，无需真实样本 / 无第三方依赖）。

执行逻辑在 src/core/dog_patch.DogPatchExecutor，
配置在 src/patches/dog_license.py（纯数据）。

覆盖 4 种定位范式，各用独立临时目录 + 构造伪样本：
  anchor   max_connect   MainLogic.dll  放原始锚点 → 未修改 → apply → 已修改 → restore
  multi    fake_dog      Teacher.exe    放两子锚点  → 未修改 → apply → 已修改(2/2) → restore
  va       nodog_dialog  Teacher.exe    合法 PE 含 VA 点 → 未修改 → apply → 已修改 → restore
  config   config_limit  skin/core.conf 改 /Limit/ → 验证新值 + 重签

运行：python3 tests/test_dog_roundtrip.py
"""

import os
import re
import sys
import struct
import tempfile

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.core.dog_patch import DogPatchExecutor, recompute_conf_sig
from src.patches import get_dog_solution

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


def silent(line):
    pass


def _tmp_dir():
    return tempfile.mkdtemp(prefix="dog_")


def _clean(path):
    for p in (path, path + ".bak"):
        if os.path.exists(p):
            try:
                os.remove(p)
            except OSError:
                pass

# ── anchor: max_connect ──────────────────────────────────
def test_anchor():
    sol = get_dog_solution("max_connect")
    d = _tmp_dir()
    path = os.path.join(d, "MainLogic.dll")
    blob = bytearray(b"\x00" * 0x2000)
    off = 0x100
    blob[off:off + len(sol.anchor)] = sol.anchor
    with open(path, "wb") as f:
        f.write(bytes(blob))
    print("── anchor: max_connect ──")
    ex = DogPatchExecutor(d, log=silent)
    st, _ = ex.status(sol)
    check(st == "未修改", "初始 status = 未修改（实际 %s）" % st)
    ok, _msg = ex.apply(sol)
    check(ok, "apply 返回 True")
    data = open(path, "rb").read()
    check(bytes(data[off + sol.anchor_off:off + sol.anchor_off + len(sol.new)]) == sol.new,
          "patch 后 = new（6 NOP）")
    st, _ = ex.status(sol)
    check(st == "已修改", "patch 后 status = 已修改（实际 %s）" % st)
    check(os.path.exists(path + ".bak"), "已生成备份")
    ok, _ = ex.restore(sol)
    check(ok, "restore 返回 True")
    data = open(path, "rb").read()
    check(bytes(data[off:off + len(sol.anchor)]) == sol.anchor, "还原后 = 原始 anchor")
    _clean(path)


# ── multi: fake_dog ──────────────────────────────────────
def test_multi():
    sol = get_dog_solution("fake_dog")
    d = _tmp_dir()
    path = os.path.join(d, "Teacher.exe")
    blob = bytearray(b"\x00" * 0x2000)
    p1, p2 = sol.patches
    o1, o2 = 0x100, 0x300
    blob[o1:o1 + len(p1["anchor"])] = p1["anchor"]
    blob[o2:o2 + len(p2["anchor"])] = p2["anchor"]
    with open(path, "wb") as f:
        f.write(bytes(blob))
    print("── multi: fake_dog ──")
    ex = DogPatchExecutor(d, log=silent)
    st, _ = ex.status(sol)
    check(st == "未修改", "初始 status = 未修改（实际 %s）" % st)
    ok, _msg = ex.apply(sol)
    check(ok, "apply 返回 True")
    data = open(path, "rb").read()
    check(bytes(data[o1 + p1["anchor_off"]:o1 + p1["anchor_off"] + len(p1["new"])]) == p1["new"],
          "子patch 2a = new")
    check(bytes(data[o2:o2 + len(p2["new"])]) == p2["new"], "子patch 2b = new")
    st, _ = ex.status(sol)
    check(st == "已修改(2/2)", "patch 后 status = 已修改(2/2)（实际 %s）" % st)
    ok, _ = ex.restore(sol)
    check(ok, "restore 返回 True")
    data = open(path, "rb").read()
    check(bytes(data[o1:o1 + len(p1["anchor"])]) == p1["anchor"], "还原后 2a = 原始")
    check(bytes(data[o2:o2 + len(p2["anchor"])]) == p2["anchor"], "还原后 2b = 原始")
    _clean(path)


# ── va: nodog_dialog ─────────────────────────────────────
def test_va():
    sol = get_dog_solution("nodog_dialog")
    d = _tmp_dir()
    path = os.path.join(d, "Teacher.exe")
    ibase = 0x400000
    rva = sol.va - ibase          # 0x15a900
    size = 0x160000
    blob = bytearray(b"\x00" * size)
    blob[0:2] = b"MZ"
    struct.pack_into("<I", blob, 0x3c, 0x80)
    blob[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<HHIIIHH", blob, 0x84, 0x14c, 1, 0, 0, 0, 0xE0, 0)
    opt = 0x98
    struct.pack_into("<H", blob, opt, 0x10b)
    struct.pack_into("<I", blob, opt + 28, ibase)
    so = 0x178
    struct.pack_into("<8s", blob, so, b".text\0\0\0")
    struct.pack_into("<IIII", blob, so + 8, size, 0x1000, size, 0x1000)
    off = 0x1000 + (rva - 0x1000)   # == rva（rawptr 对齐）
    blob[off:off + 3] = sol.orig
    with open(path, "wb") as f:
        f.write(bytes(blob))
    print("── va: nodog_dialog ──")
    ex = DogPatchExecutor(d, log=silent)
    st, _ = ex.status(sol)
    check(st == "未修改", "初始 status = 未修改（实际 %s）" % st)
    ok, _msg = ex.apply(sol)
    check(ok, "apply 返回 True")
    data = open(path, "rb").read()
    check(bytes(data[off:off + len(sol.new)]) == sol.new, "patch 后 = new（xor eax,eax;ret）")
    st, _ = ex.status(sol)
    check(st == "已修改", "patch 后 status = 已修改（实际 %s）" % st)
    ok, _ = ex.restore(sol)
    check(ok, "restore 返回 True")
    data = open(path, "rb").read()
    check(bytes(data[off:off + 3]) == sol.orig, "还原后 = orig")
    _clean(path)


# ── config: config_limit ─────────────────────────────────
def test_config():
    sol = get_dog_solution("config_limit")
    d = _tmp_dir()
    skin = os.path.join(d, "skin")
    os.makedirs(skin, exist_ok=True)
    path = os.path.join(skin, "core.conf")
    text = "/Version/1.0/\n/Limit/5/\n/MD5/AAAAAAAAAAAAAAAA/\n"
    with open(path, "wb") as f:
        f.write(text.encode("gbk"))
    print("── config: config_limit ──")
    ex = DogPatchExecutor(d, log=silent)
    st, _ = ex.status(sol)
    check(st == "当前 /Limit/5/", "初始 status = 当前 /Limit/5/（实际 %s）" % st)
    ok, _msg = ex.apply(sol, limit_val="999999")
    check(ok, "apply 返回 True")
    data = open(path, "rb").read().decode("gbk", "replace")
    check("/Limit/999999/" in data, "patch 后 /Limit/999999/ 已写入")
    m = re.search(r"/MD5/([^/]*)/", data)
    check(m is not None, "存在 /MD5/ 行")
    # 去掉 /MD5/ 行后重算，应等于写入的签名（自洽性）
    without = "\n".join(l for l in data.splitlines() if not l.strip().startswith("/MD5/"))
    expect = recompute_conf_sig(without)
    check(m and m.group(1) == expect, "重签 /MD5/ 自洽")
    ok, _ = ex.restore(sol)
    check(ok, "restore 返回 True")
    data = open(path, "rb").read().decode("gbk", "replace")
    check("/Limit/5/" in data, "还原后 /Limit/5/")
    _clean(path)


def main():
    test_anchor()
    test_multi()
    test_va()
    test_config()
    print("\n===== 结果：%d 通过 / %d 失败 =====" % (PASS, FAIL))
    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())