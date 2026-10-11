# src/core/patch_engine.py
# 统一的字节 patch 引擎 —— 供 GUI / CLI 共用
#
# 设计：
#   PatchPoint  单个 patch 点（偏移 + 原字节 + 新字节 + 可选语义校验 + 是否必需）
#   PatchTarget 一个目标文件（文件名 / MD5 指纹 / 大小 / patch 点列表 / 描述）
#   PatchEngine 对单个目标文件执行 apply / restore / status / dry_run
#
# 语义：
#   - apply: 逐点校验原字节 → 备份 → 写入 → 读回验证
#   - restore: 从 .bak 还原
#   - status: 返回每个 patch 点当前状态（未 patch / 已 patch / 异常）
#   - 版本不匹配时按字节校验继续（可选 strict 中止）

import os
import shutil
from dataclasses import dataclass, field
from typing import Callable, Optional

from src.core import fingerprint


# ── 状态常量 ──────────────────────────────────────────────
ST_NONE = "未 patch"
ST_DONE = "已 patch"
ST_BAD = "异常"
ST_SKIP = "跳过"


@dataclass
class PatchPoint:
    label: str
    offset: int
    orig: bytes
    new: bytes
    required: bool = True
    # 可选语义校验：紧随 patch 点的锚定字节 (offset, expected_bytes)
    check: Optional[tuple] = None  # (off, bytes)
    # 跳过开关名（GUI 用，如 "screen"）
    toggle_key: Optional[str] = None


@dataclass
class PatchTarget:
    key: str                # 唯一标识，如 "multiclient_disable"
    name: str               # 显示名，如 "禁用教学管控"
    sample_name: str        # 目标文件名，如 "MultiClient.exe"
    md5: str                # 原始样本 MD5
    size: int               # 原始样本大小
    description: str        # 人类可读描述
    patches: list = field(default_factory=list)
    # 默认应跳过的 toggle_key（GUI 未勾选时跳过）
    default_skips: list = field(default_factory=list)


# ── 日志回调 ──────────────────────────────────────────────
class _Sink:
    """默认打印到 stdout 的日志接收器；GUI 注入后改为写文本框。"""
    def __call__(self, line: str):
        print(line)


class PatchEngine:
    def __init__(self, target: PatchTarget, path: str, log: Optional[Callable] = None):
        self.target = target
        self.path = path
        self.log = log or _Sink()

    # ── 基础 ──────────────────────────────────────────
    @property
    def bak(self) -> str:
        return self.path + ".bak"

    def _skip_set(self, toggles: list) -> set:
        """合并 target 默认跳过 + 调用方传入的跳过项。"""
        s = set(self.target.default_skips or [])
        for k in toggles or []:
            s.add(k)
        return s

    def _read(self) -> bytes:
        with open(self.path, "rb") as f:
            return f.read()

    # ── 校验 ──────────────────────────────────────────
    def verify_sample(self) -> bool:
        """校验文件大小 + MD5。返回是否完全匹配原始样本。"""
        if not os.path.isfile(self.path):
            self.log(f"  ✗ 文件不存在: {self.path}")
            return False
        size = fingerprint.size_of(self.path)
        md5 = fingerprint.md5_of(self.path)
        if size != self.target.size:
            self.log(f"  ✗ 大小不符: {size} ≠ {self.target.size}")
            return False
        if md5 == self.target.md5:
            self.log(f"  ✓ 指纹匹配 = {md5}（原始样本）")
            return True
        self.log(f"  ⚠ 指纹不匹配 = {md5}")
        self.log(f"    原始指纹 = {self.target.md5}（可能已 patch 或版本不同）")
        return False

    def point_states(self, data: bytes, skips: set = None) -> list:
        """返回 [(label, state, detail)]。skips 中的 toggle_key 标为跳过。"""
        skips = skips or set()
        out = []
        for p in self.target.patches:
            if p.toggle_key and p.toggle_key in skips:
                out.append((p.label, ST_SKIP, "（未启用）"))
                continue
            cur = bytes(data[p.offset:p.offset + len(p.orig)])
            if cur == p.new:
                out.append((p.label, ST_DONE, cur.hex(" ")))
            elif cur == p.orig:
                out.append((p.label, ST_NONE, cur.hex(" ")))
            else:
                out.append((p.label, ST_BAD, cur.hex(" ")))
        return out

    # ── status ────────────────────────────────────────
    def status(self, toggles: list = None) -> dict:
        if not os.path.isfile(self.path):
            return {"exists": False, "points": [], "md5": "", "size": -1}
        data = self._read()
        skips = self._skip_set(toggles)
        points = self.point_states(data, skips)
        return {
            "exists": True,
            "path": self.path,
            "size": fingerprint.size_of(self.path),
            "md5": fingerprint.md5_of(self.path),
            "md5_ok": fingerprint.md5_of(self.path) == self.target.md5,
            "points": points,
        }

    # ── apply ─────────────────────────────────────────
    def apply(self, toggles: list = None,
              confirm: Optional[Callable[[str], bool]] = None) -> bool:
        """执行 patch。confirm 用于版本不匹配时的二次确认（GUI 注入弹窗）。"""
        if not os.path.isfile(self.path):
            self.log(f"  ✗ 文件不存在: {self.path}")
            return False

        self.log("\n[1] 校验样本...")
        matched = self.verify_sample()
        if not matched:
            # 版本不匹配：若是“已 patch”则跳过；否则需确认
            data = self._read()
            states = self.point_states(data, self._skip_set(toggles))
            active = [s for _, s, _ in states if s != ST_SKIP]
            if active and all(s == ST_DONE for s in active):
                self.log("  ⚠ 目标点已全部 patch，跳过（如需还原请先 restore）")
                return True
            if confirm is None:
                self.log("  ✗ 版本不匹配，需人工确认（strict 模式下中止）")
                return False
            if not confirm("文件指纹与原始样本不一致，仍要按字节校验继续 patch？"):
                self.log("  ✗ 已取消")
                return False
            self.log("  ⚠ 用户确认继续（风险自担）")

        data = bytearray(self._read())
        skips = self._skip_set(toggles)

        self.log("\n[2] 校验 patch 点原字节...")
        active = []
        for p in self.target.patches:
            if p.toggle_key and p.toggle_key in skips:
                self.log(f"  ○ {p.label:<12} 跳过")
                continue
            cur = bytes(data[p.offset:p.offset + len(p.orig)])
            if cur == p.new:
                self.log(f"  ○ {p.label:<12} 已是 patch 状态，跳过")
                continue
            if cur != p.orig:
                self.log(f"  ✗ {p.label:<12} 原字节不符: {cur.hex(' ')} ≠ {p.orig.hex(' ')}")
                self.log("    该文件可能已被修改或版本不同，中止。")
                return False
            # 语义校验
            if p.check:
                coff, cbytes = p.check
                ccur = bytes(data[coff:coff + len(cbytes)])
                if ccur != cbytes:
                    self.log(f"  ✗ {p.label:<12} 语义校验失败: {ccur.hex(' ')} ≠ {cbytes.hex(' ')}")
                    return False
            self.log(f"  ✓ {p.label:<12} off={p.offset:#06x}  {p.orig.hex(' ')}")
            active.append(p)

        if not active:
            self.log("\n  无可执行的 patch（全部已 patch 或被跳过）")
            return True

        self.log(f"\n[3] 备份 → {os.path.basename(self.bak)}")
        if not os.path.exists(self.bak):
            shutil.copy2(self.path, self.bak)
        else:
            self.log("  （备份已存在，不覆盖）")

        self.log(f"\n[4] 写入 {len(active)} 处...")
        for p in active:
            data[p.offset:p.offset + len(p.orig)] = p.new
            self.log(f"  ✓ {p.label:<12} off={p.offset:#06x}  → {p.new.hex(' ')}")
        with open(self.path, "wb") as f:
            f.write(bytes(data))

        self.log("\n[5] 读回验证...")
        back = self._read()
        ok = True
        for p in active:
            if bytes(back[p.offset:p.offset + len(p.new)]) != p.new:
                self.log(f"  ✗ {p.label} 验证失败")
                ok = False
        if ok:
            self.log("  ✓ 全部验证通过")
            return True
        self.log("  ✗ 验证失败！请立即 restore")
        return False

    # ── restore ───────────────────────────────────────
    def restore(self, confirm: Optional[Callable[[str], bool]] = None) -> bool:
        if not os.path.exists(self.bak):
            self.log(f"\n  ✗ 备份不存在: {self.bak}")
            return False
        bak_md5 = fingerprint.md5_of(self.bak)
        if bak_md5 == self.target.md5:
            self.log(f"\n  备份指纹 = {bak_md5} ✓（原始样本）")
        else:
            self.log(f"\n  ⚠ 备份指纹 = {bak_md5}（非原始）")
            if confirm is None:
                self.log("  ✗ 需人工确认（strict 中止）")
                return False
            if not confirm("备份与原始样本指纹不一致，仍要还原？"):
                return False
        shutil.copy2(self.bak, self.path)
        self.log(f"  ✓ 已还原: {self.path}")
        self.log(f"  还原后指纹 = {fingerprint.md5_of(self.path)}")
        return True

    # ── dry_run ───────────────────────────────────────
    def dry_run(self, toggles: list = None) -> bool:
        """只校验、不写盘。返回校验是否通过。"""
        if not os.path.isfile(self.path):
            self.log(f"  ✗ 文件不存在: {self.path}")
            return False
        self.verify_sample()
        data = self._read()
        skips = self._skip_set(toggles)
        self.log("\n  Patch 点校验（dry-run，不写盘）:")
        ok = True
        for p in self.target.patches:
            if p.toggle_key and p.toggle_key in skips:
                self.log(f"  ○ {p.label:<12} 跳过")
                continue
            cur = bytes(data[p.offset:p.offset + len(p.orig)])
            if cur == p.new:
                self.log(f"  ○ {p.label:<12} 已 patch")
            elif cur == p.orig:
                self.log(f"  ✓ {p.label:<12} off={p.offset:#06x}  可 patch")
            else:
                self.log(f"  ✗ {p.label:<12} 原字节不符: {cur.hex(' ')}")
                ok = False
        return ok