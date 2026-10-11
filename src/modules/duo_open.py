#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
oseasy_duo_open.py
==================
极域(OSeasy)多媒体电子教室 —— 双端互斥「双开」patch 工具(单文件, 含 GUI)。

自包含: 核心 patch 逻辑 + tkinter/ttk(vista) 图形界面 + 命令行, 三合一。
仅依赖 Python 3.8+ 标准库, 无需 pip 安装任何第三方包。

背景(逆向结论见 docs/reverse-analysis/24_双端互斥启动机制实证.md)
------------------------------------------------------------------
Teacher.exe / Student.exe 启动时用「命名事件存在性检测」做互斥:

  检测原语  OpenEventW(0x1f0003, 0, name)   # 事件存在 -> 返回非空句柄
  Student  FUN_004bb0b0 @ 0x4bb0b0
  Teacher  FUN_005b9420 @ 0x5b9420

  启动链连续两次调用该函数(查 TeacherEvent / StudentEvent),
  任一"存在"就弹 5 秒倒计时警告框(DuiLib CMessageBoxDlg)并退出, 不进主界面。

原理
----
把检测原语函数体最前面 3 字节替换为:
      31 C0    xor eax, eax     ; 返回值 EAX = 0
      C3       ret              ; 直接返回
使检测函数恒返回 0 (= FALSE = 事件不存在)。两端启动检查全部放行, 各自
CreateEvent 自己的事件(TeacherEvent / StudentEvent, 名字不同)后正常进入
主界面, 实现同时运行。只改 3 字节, 不碰任何业务逻辑 / 配置 / 端口 / 弹窗。

用法
----
  # GUI (无参数, 推荐)
  python oseasy_duo_open.py

  # 命令行: 预览(不写盘)
  python oseasy_duo_open.py --dry-run --strict Teacher.exe Student.exe

  # 命令行: 生成双开版(输出 *_duo_open.exe, 不动原文件)
  python oseasy_duo_open.py --strict Teacher.exe Student.exe

  # 命令行: 原地修改(先写 .duo_open.bak 备份) / 还原
  python oseasy_duo_open.py --inplace --strict Teacher.exe Student.exe
  python oseasy_duo_open.py --restore Teacher.exe Student.exe

  # 文件名不含 teacher/student 时, 按顺序手动指定角色
  python oseasy_duo_open.py --targets teacher student a.exe b.exe

注: patch 地址针对特定版本(见 KNOWN 表); 换版本脚本会自动校验并中止。
"""

import os
import sys
import struct
import shutil
import hashlib
import argparse

# ---------------- 核心常量 ----------------
# patch 字节: xor eax, eax ; ret  (让检测函数恒返回 0)
PATCH = b'\x31\xc0\xc3'
PATCH_DIS = 'xor eax, eax ; ret'

# 已逆向确认的检测原语 (角色 -> (VA, 符号名))
# ImageBase 均为 0x400000 (PE32 x86)
KNOWN = {
    'teacher': (0x5b9420, 'FUN_005b9420'),
    'student': (0x4bb0b0, 'FUN_004bb0b0'),
}

FUNC_WINDOW = 0x40  # 检测函数体 sanity check 扫描范围


# ---------------- 核心逻辑(与 GUI / CLI 共用) ----------------
class PE:
    """最小 PE32(x86) 解析, 提供 VA -> 文件偏移 映射。"""

    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.data = f.read()
        d = self.data
        self.e_lfanew = struct.unpack_from('<I', d, 0x3c)[0]
        if d[self.e_lfanew:self.e_lfanew + 4] != b'PE\0\0':
            raise ValueError('不是 PE 文件')
        coff = self.e_lfanew + 4
        self.machine = struct.unpack_from('<H', d, coff)[0]
        self.nsec = struct.unpack_from('<H', d, coff + 2)[0]
        self.opt = coff + 20
        magic = struct.unpack_from('<H', d, self.opt)[0]
        if magic == 0x20b:
            raise ValueError('是 PE32+(64位), 本工具仅支持 PE32(x86)')
        self.imagebase = struct.unpack_from('<I', d, self.opt + 0x1C)[0]
        sec = self.opt + 0xE0
        self.sections = []
        for i in range(self.nsec):
            b = sec + i * 40
            name = d[b:b + 8].rstrip(b'\x00').decode('utf-8', 'replace')
            vsize = struct.unpack_from('<I', d, b + 8)[0]
            va = struct.unpack_from('<I', d, b + 12)[0]
            rsize = struct.unpack_from('<I', d, b + 16)[0]
            roff = struct.unpack_from('<I', d, b + 20)[0]
            self.sections.append((name, va, vsize, roff, rsize))

    def va_to_off(self, va):
        rva = va - self.imagebase
        for name, va_s, vs, ro, rs in self.sections:
            if va_s <= rva < va_s + max(vs, rs):
                return ro + (rva - va_s)
        return None

    def section_of(self, va):
        rva = va - self.imagebase
        for name, va_s, vs, ro, rs in self.sections:
            if va_s <= rva < va_s + max(vs, rs):
                return name
        return None

    def md5(self):
        return hashlib.md5(self.data).hexdigest()


def sanity_check(pe, off):
    """检测函数体(入口起 FUNC_WINDOW 字节内)应含 `call [abs ptr]`(FF 15),
    因为 OpenEventW 经全局函数指针动态调用。"""
    window = pe.data[off:off + FUNC_WINDOW]
    return b'\xff\x15' in window


def match_target(fname, explicit):
    if explicit:
        return explicit
    low = os.path.basename(fname).lower()
    if 'teacher' in low:
        return 'teacher'
    if 'student' in low:
        return 'student'
    return None


def process_one(path, tname, args):
    """对一个 exe 打 patch, 返回是否成功。"""
    print('\n=== %s  [%s] ===' % (os.path.basename(path), tname))
    pe = PE(path)
    va, sym = KNOWN[tname]
    print('  machine=0x%x  imagebase=0x%x' % (pe.machine, pe.imagebase))
    off = pe.va_to_off(va)
    if off is None:
        print('  !! VA %#x 不在任何 section, 该样本地址不匹配, 中止' % va)
        return False
    sec = pe.section_of(va)
    print('  目标 %s @ VA %#x -> fileoff %#x  (section %s)' % (sym, va, off, sec))

    orig = pe.data[off:off + 3]
    if orig == PATCH:
        print('  !! 入口已是 31 C0 C3, 疑似已 patch, 跳过')
        return False

    found = sanity_check(pe, off)
    tag = 'OK' if found else 'NOT FOUND'
    print('  sanity: 函数体内 call [ptr](FF 15) 特征 -> %s' % tag)
    if not found and args.strict:
        print('  !! [--strict] 未确认函数体特征, 中止 (去掉 --strict 可继续)')
        return False

    print('  原 3 字节 : %s' % orig.hex(' '))
    print('  将写为    : %s  (%s)' % (PATCH.hex(' '), PATCH_DIS))

    if args.dry_run:
        print('  [dry-run] 未写盘')
        return True

    if args.inplace:
        out = path
        bak = path + '.duo_open.bak'
        if not os.path.exists(bak):
            shutil.copy2(path, bak)
            print('  备份     -> %s' % os.path.basename(bak))
    else:
        root, ext = os.path.splitext(path)
        out = root + '_duo_open' + ext

    buf = bytearray(pe.data)
    buf[off:off + 3] = PATCH
    with open(out, 'wb') as f:
        f.write(bytes(buf))

    with open(out, 'rb') as f:
        chk = f.read()
    ok = chk[off:off + 3] == PATCH
    print('  写入     -> %s' % os.path.basename(out))
    print('  读回校验 : %s  [%s]' % (chk[off:off + 3].hex(' '), 'OK' if ok else 'FAIL'))
    print('  MD5      : %s -> %s' % (pe.md5(), hashlib.md5(chk).hexdigest()))
    return ok


def restore_one(path, args):
    bak = path + '.duo_open.bak'
    if not os.path.exists(bak):
        print('\n=== %s ===\n  !! 无备份 %s, 无法还原' % (path, bak))
        return False
    shutil.copy2(bak, path)
    print('\n=== %s ===\n  已用 %s 还原' % (path, os.path.basename(bak)))
    return True
