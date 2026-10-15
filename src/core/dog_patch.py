# src/core/dog_patch.py
# 教师端「加密狗 / 点数限制」解除执行器 —— 供 GUI / CLI 共用
#
# 本域定位范式独立于 patch_engine（固定偏移）与 va_patch（VA 型）：
#   anchor  唯一字节锚点定位 + 双态识别（未改 / 已改 / 丢失）
#   multi   同一文件多个锚点子 patch（一次备份，逐个应用）
#   va      单点 VA -> 文件偏移（复用 va_patch.PE，不重复 PE 解析）
#   config  文本配置改值 + MD5 重签名（非二进制 PE，改 skin/core.conf）
#
# 设计：
#   DogSolution       单个方案的纯数据（配置在 src/patches/dog_license.py）
#   DogPatchExecutor  对单个安装目录执行 detect / apply / restore
#
# 备份：文件级（<target>.bak）。共享同一文件的多方案（fake_dog 与
#       nodog_dialog 都 patch Teacher.exe）共用一份备份，还原时整文件恢复。
#
# UI 无关：日志通过构造时注入的 log 回调输出（默认打印 stdout）。

import os
import re
import shutil
import hashlib
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Tuple

from src.core.va_patch import PE


# ── 数据定义 ──────────────────────────────────────────────
@dataclass
class DogSolution:
    """教师端授权解除的一个方案（纯数据，无执行逻辑）。"""
    key: str                    # 唯一标识，如 "max_connect"
    name: str                   # 显示名
    tag: str = ""               # 标签（如 "[治本·推荐]"）
    target: str = ""            # 相对安装目录的文件路径（"Teacher.exe" / "skin/core.conf"）
    loc_type: str = "anchor"    # anchor / multi / va / config
    md5: str = ""               # 原始样本 MD5（config 型可空）
    size: int = 0               # 原始样本大小（config 型可空）
    desc: str = ""              # 人类可读描述
    # ── anchor / va 单 patch ──
    anchor: bytes = b""         # 唯一锚点字节串
    anchor_off: int = 0         # patch 字节在锚点内的偏移
    orig: bytes = b""           # 期望原始字节
    new: bytes = b""            # 替换字节
    # ── va ──
    imagebase: int = 0          # 仅说明用（实际 VA->off 由 PE 解析）
    va: int = 0                 # 绝对 VA
    # ── multi 子 patch（一次备份，逐个应用） ──
    # 每项 dict: {label, anchor(bytes), anchor_off(int), orig(bytes), new(bytes)}
    patches: List[dict] = field(default_factory=list)


# ── 日志回调 ──────────────────────────────────────────────
class _Sink:
    """默认打印到 stdout 的日志接收器；GUI 注入后改为写文本框。"""
    def __call__(self, line: str):
        print(line)


# ── core.conf 签名算法（config 方案） ─────────────────────
# /MD5/ 签名字母表（nibble 0-9a-f -> char）
# 来源：ModifyLimitConfig.exe 偏移 81820 直接铁证
ALPHA = "NPQR6STU7VWX8YZ9"


def sig_encode(md5hex: str) -> str:
    return ''.join(ALPHA[int(c, 16)] for c in md5hex)


def recompute_conf_sig(text: str) -> str:
    """按 core.conf 文本重算 /MD5/ 签名。
    去掉 /MD5/ 行后，每行 /k/v/ 取 k+v 顺序拼接，MD5 后按表查字。"""
    parts = []
    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        if s.startswith('/MD5/'):
            continue
        if s.startswith('/') and s.endswith('/'):
            b = s[1:-1]
            if '/' in b:
                k, v = b.split('/', 1)
                parts.append(k + v)
            else:
                parts.append(b)
        else:
            parts.append(s)
    return sig_encode(hashlib.md5(''.join(parts).encode('gbk', 'replace')).hexdigest())


# ── 定位 / 双态识别（纯函数，作用于 data） ────────────────
def _anchor_status(data: bytes, sol: DogSolution) -> Tuple[Optional[int], str]:
    """锚点定位，同时识别『原始』『已修改』两态。
    返回 (offset, status)；status: 'orig'/'patched'/'missing'。"""
    prefix = sol.anchor[:sol.anchor_off]
    patched = prefix + sol.new          # 前缀(不改) + NOP
    orig = sol.anchor                    # 前缀 + 原指令
    if data.count(patched) == 1:
        return data.find(patched) + sol.anchor_off, "patched"
    if data.count(orig) == 1:
        return data.find(orig) + sol.anchor_off, "orig"
    return None, "missing"


def _subpatch_status(data: bytes, p: dict) -> Tuple[Optional[int], str]:
    """单个子 patch（multi）定位，识别『原始』『已修改』两态。"""
    prefix = p["anchor"][:p["anchor_off"]]
    suffix = p["anchor"][p["anchor_off"] + len(p["orig"]):]
    patched = prefix + p["new"] + suffix
    orig = p["anchor"]
    if data.count(patched) == 1:
        return data.find(patched) + p["anchor_off"], "patched"
    if data.count(orig) == 1:
        return data.find(orig) + p["anchor_off"], "orig"
    return None, "missing"


def _locate(data: bytes, sol: DogSolution,
            pe: Optional[PE] = None) -> Tuple[Optional[int], str]:
    """返回 (offset, errmsg)。成功 errmsg 为空。"""
    if sol.loc_type == "anchor":
        off, st = _anchor_status(data, sol)
        if st == "missing":
            return None, "锚点未命中（原始/已修改态均非唯一），版本可能不符"
        return off, ""
    if sol.loc_type == "va":
        if pe is None:
            return None, "VA 定位缺少 PE 上下文"
        off = pe.va_to_off(sol.va)
        if off is None:
            return None, "VA 0x%X 无法映射到文件" % sol.va
        return off, ""
    return None, "未知定位类型"


# ── 执行器 ────────────────────────────────────────────────
class DogPatchExecutor:
    """教师端授权解除执行器。

    用法：
        ex = DogPatchExecutor(r"C:\\Os-Easy\\...\\teaching system", log=...)
        ex.detect_all(solutions)                 # 检测全部方案状态
        ex.apply(sol, limit_val="999999")        # 应用单个方案
        ex.restore(sol)                          # 还原单个方案
    """

    def __init__(self, dirpath: str, log: Optional[Callable] = None):
        self.dirpath = dirpath
        self.log = log or _Sink()

    # ── 基础 ──────────────────────────────────────────
    def _fp(self, sol: DogSolution) -> str:
        return os.path.join(self.dirpath, sol.target.replace("/", os.sep))

    def _read(self, sol: DogSolution) -> Optional[bytes]:
        fp = self._fp(sol)
        if not os.path.exists(fp):
            return None
        with open(fp, "rb") as f:
            return f.read()

    def _pe(self, sol: DogSolution) -> Optional[PE]:
        if sol.loc_type != "va":
            return None
        try:
            return PE(self._fp(sol))
        except Exception:
            return None

    # ── 状态 ──────────────────────────────────────────
    def status(self, sol: DogSolution) -> Tuple[str, str]:
        """返回 (状态文本, 颜色tag)。tag: info/ok/done/err。"""
        data = self._read(sol)
        if data is None:
            return "缺失 %s" % sol.target, "err"
        if sol.loc_type == "config":
            return self._config_status(data), "info"
        if sol.loc_type == "multi":
            states = [_subpatch_status(data, p)[1] for p in sol.patches]
            if any(s == "missing" for s in states):
                return "锚点未命中(版本差异?)", "err"
            if all(s == "patched" for s in states):
                return "已修改(%d/%d)" % (len(states), len(states)), "done"
            if all(s == "orig" for s in states):
                return "未修改", "ok"
            n = sum(1 for s in states if s == "patched")
            return "部分修改(%d/%d)" % (n, len(states)), "done"
        off, err = _locate(data, sol, self._pe(sol))
        if off is None:
            return err, "err"
        cur = data[off:off + len(sol.orig)]
        if cur == sol.new:
            return "已修改", "done"
        if cur == sol.orig:
            return "未修改", "ok"
        return "字节不符(版本差异?)", "err"

    def _config_status(self, data: bytes) -> str:
        m = re.search(r'/Limit/([^/]*)/', data.decode('gbk', 'replace'))
        val = m.group(1) if m else "?"
        return "当前 /Limit/%s/" % val

    def detect_all(self, solutions: List[DogSolution]) -> None:
        """检测全部方案状态，逐行写入 log。"""
        self.log("=" * 60)
        self.log("安装目录：%s" % self.dirpath)
        for i, sol in enumerate(solutions, 1):
            label = "%d. %s %s" % (i, sol.name, sol.tag)
            data = self._read(sol)
            if data is None:
                self.log("%s  ->  [缺失 %s]" % (label, sol.target), "err")
                continue
            md5 = hashlib.md5(data).hexdigest()
            state, _color = self.status(sol)
            md5mark = "" if sol.loc_type == "config" else (
                "" if md5 == sol.md5 else "  [MD5与样本不同!]")
            self.log("%s\n      %s  MD5=%s%s\n      状态：%s" % (
                label, os.path.basename(sol.target), md5, md5mark, state))
        self.log("=" * 60)

    # ── 应用 ──────────────────────────────────────────
    def apply(self, sol: DogSolution, limit_val: str = "999999") -> Tuple[bool, str]:
        fp = self._fp(sol)
        if not os.path.exists(fp):
            return False, "找不到目标文件 %s" % sol.target
        data = open(fp, 'rb').read()
        md5 = hashlib.md5(data).hexdigest()

        if sol.loc_type == "config":
            return self._apply_config_file(fp, limit_val)

        # ---- multi: 一次备份，逐子 patch 应用 ----
        if sol.loc_type == "multi":
            results = []
            for p in sol.patches:
                off, st = _subpatch_status(data, p)
                if st == "missing":
                    return False, "子补丁 %s 锚点未命中（MD5=%s，版本可能不符）" % (
                        p["label"], md5)
                results.append((off, st))
            if all(st == "patched" for _, st in results):
                return True, "全部已修改，跳过"
            bak = fp + ".bak"
            if not os.path.exists(bak):
                shutil.copy2(fp, bak)
            buf = bytearray(data)
            msgs = []
            for (off, st), p in zip(results, sol.patches):
                if st == "patched":
                    msgs.append("%s 已修改" % p["label"])
                    continue
                cur = data[off:off + len(p["orig"])]
                if cur != p["orig"]:
                    return False, "子补丁 %s 字节不符：实际 %s，期望 %s（MD5=%s）" % (
                        p["label"], cur.hex(' '), p["orig"].hex(' '), md5)
                buf[off:off + len(p["new"])] = p["new"]
                msgs.append("%s 已修改 (0x%X: %s→%s)" % (
                    p["label"], off, p["orig"].hex(' '), p["new"].hex(' ')))
            try:
                with open(fp, 'wb') as f:
                    f.write(bytes(buf))
            except PermissionError:
                return False, "写入失败：文件被占用，请先关闭 Os-Easy"
            self.log("；".join(msgs))
            return True, "；".join(msgs)

        # ---- 单 patch（anchor / va） ----
        off, err = _locate(data, sol, self._pe(sol))
        if off is None:
            return False, err
        cur = data[off:off + len(sol.orig)]
        if cur == sol.new:
            return True, "已是修改状态，跳过"
        if cur != sol.orig:
            return False, "字节不匹配：实际 %s，期望 %s（MD5=%s，版本可能不符）" % (
                cur.hex(' '), sol.orig.hex(' '), md5)
        bak = fp + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(fp, bak)
        buf = bytearray(data)
        buf[off:off + len(sol.new)] = sol.new
        try:
            with open(fp, 'wb') as f:
                f.write(bytes(buf))
        except PermissionError:
            return False, "写入失败：文件可能被教师端进程占用，请先关闭 Os-Easy 再试"
        msg = "已修改（文件偏移 0x%X：%s -> %s）" % (
            off, sol.orig.hex(' '), sol.new.hex(' '))
        self.log(msg)
        return True, msg

    def _apply_config_file(self, fp: str, limit_val: str) -> Tuple[bool, str]:
        raw = open(fp, 'rb').read()
        text = raw.decode('gbk', 'replace')
        if not re.search(r'/Limit/[^/]*/', text):
            return False, "core.conf 中未找到 /Limit/ 行"
        old = re.search(r'/Limit/([^/]*)/', text).group(1)
        text = re.sub(r'/Limit/[^/]*/', '/Limit/%s/' % limit_val, text)
        sig = recompute_conf_sig(text)
        text = re.sub(r'/MD5/[^/]*/', '/MD5/%s/' % sig, text)
        bak = fp + ".bak"
        if not os.path.exists(bak):
            shutil.copy2(fp, bak)
        with open(fp, 'wb') as f:
            f.write(text.encode('gbk'))
        msg = "/Limit/%s/ -> /Limit/%s/，重签 /MD5/%s/" % (old, limit_val, sig)
        self.log(msg)
        return True, msg

    # ── 还原 ──────────────────────────────────────────
    def restore(self, sol: DogSolution) -> Tuple[bool, str]:
        fp = self._fp(sol)
        bak = fp + ".bak"
        if not os.path.exists(bak):
            return False, "无备份 %s" % os.path.basename(bak)
        try:
            shutil.copy2(bak, fp)
        except PermissionError:
            return False, "还原失败：文件被占用，请先关闭 Os-Easy"
        msg = "已还原 %s" % os.path.basename(fp)
        self.log(msg)
        return True, msg