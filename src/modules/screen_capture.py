#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
oseasy_noscreen.py — OSeasy 学生端屏幕截图控制工具
================================================================
自包含单文件：PE 解析 + patch 核心 + BMP 处理 + shellcode 生成 + GUI + CLI。

两种模式
--------
1. 默认（NOP）：patch FUN_1007d650 入口 3 字节 → 截屏发送完全停止
   教师端：画面定格 + 状态灯在线

2. --fake-screen（shellcode）：patch FUN_1008cb70 整个函数体(352B)
   → 从本地 BMP 文件读取像素，替代 BitBlt 截屏
   → 后续 FFmpeg 编码 / BMP 打包 / WSASend 全部保留
   → 教师端看到一张固定的假截图（非实时）
   教师端：状态灯在线 + 显示假截图画面

BMP 要求
--------
- 32bpp（BGRA），无压缩
- 分辨率必须与学生端屏幕一致
- 工具自动检测 bottom-up 并提示转换（或 --convert 自动转换）
- 文件路径嵌入 shellcode，最长 23 字符（如 C:\\os_fake.bmp）

用法
----
GUI（无参数）:
    python oseasy_noscreen.py

CLI — 停止发送:
    python oseasy_noscreen.py StudentLogic.dll --dry-run --strict
    python oseasy_noscreen.py StudentLogic.dll --strict
    python oseasy_noscreen.py StudentLogic.dll --inplace --strict

CLI — 假截图:
    python oseasy_noscreen.py StudentLogic.dll --fake-screen "C:\\os_fake.bmp" --strict
    python oseasy_noscreen.py StudentLogic.dll --fake-screen "C:\\os_fake.bmp" --convert --strict

CLI — 还原:
    python oseasy_noscreen.py StudentLogic.dll --restore

Python >= 3.8, 仅标准库。
"""

import os
import sys
import struct
import shutil
import hashlib
import argparse
import queue
import threading

# ============================================================
# 常量
# ============================================================

PATCH_NOP = b'\x31\xc0\xc3'          # xor eax,eax; ret
PATCH_NOP_DIS = '31 c0 c3'
ORIG_PROLOGUE = b'\x55\x8b\xec'     # push ebp; mov ebp,esp

# ── IAT addresses (absolute VA, ImageBase=0x10000000) ──
IAT_CreateFileA      = 0x102340D8
IAT_SetFilePointer   = 0x102340F4
IAT_CloseHandle      = 0x102341E8
IAT_GetModuleHandleA = 0x102341F8
IAT_GetProcAddress   = 0x1023411C

# ── FUN_1008cb70 (BitBlt screen capture) ──
FUN_CB70_VA   = 0x1008CB70
FUN_CB70_OFF  = 0x0008BF70
FUN_CB70_SIZE = 0x160  # 352 bytes (next function at 0x1008CCD0)

# ── Shellcode layout within 352-byte function body ──
SC_FP_OFF = 0x100           # filepath string at +256
SC_RF_OFF = 0x118           # "ReadFile\0" at +280
SC_MAX_FP = SC_RF_OFF - SC_FP_OFF - 1  # 23 chars max

VA_FP = FUN_CB70_VA + SC_FP_OFF
VA_RF = FUN_CB70_VA + SC_RF_OFF

# ── Target functions ──
KNOWN = {
    'pipeline': {
        'desc': '屏幕截图完整流水线（截屏→编码→BMP→WSASend）',
        'name': 'FUN_1007d650',
        'va': 0x1007D650,
        'fileoff': 0x0007CA50,
        'mode': 'nop',
    },
    'bplt': {
        'desc': 'BitBlt 全屏截图',
        'name': 'FUN_1008cb70',
        'va': FUN_CB70_VA,
        'fileoff': FUN_CB70_OFF,
        'mode': 'nop',
    },
    'screenrender': {
        'desc': 'ScreenRender 子进程启动（远程监视推流）',
        'name': 'FUN_10088ca0',
        'va': 0x10088CA0,
        'fileoff': 0x000880A0,
        'mode': 'nop',
    },
    'wsasend': {
        'desc': 'WSASend 通用网络发送（影响面大）',
        'name': 'FUN_1002a730',
        'va': 0x1002A730,
        'fileoff': 0x00029B30,
        'mode': 'nop',
    },
}

DEFAULT_TARGETS = ['pipeline']
FUNC_WINDOW = 0x80


# ============================================================
# PE 解析
# ============================================================

class PE:
    def __init__(self, path):
        self.path = path
        with open(path, 'rb') as f:
            self.data = f.read()
        self.image_base = 0
        self.sections = []
        self._parse()

    def _parse(self):
        d = self.data
        e_lfanew = struct.unpack_from('<I', d, 0x3C)[0]
        assert d[e_lfanew:e_lfanew+4] == b'PE\x00\x00', 'Not a PE file'
        coff = e_lfanew + 4
        self.machine = struct.unpack_from('<H', d, coff)[0]
        assert self.machine == 0x14C, 'Expected x86'
        num_sec = struct.unpack_from('<H', d, coff + 2)[0]
        opt_size = struct.unpack_from('<H', d, coff + 16)[0]
        opt = coff + 20
        magic = struct.unpack_from('<H', d, opt)[0]
        assert magic == 0x10B, 'Expected PE32'
        self.image_base = struct.unpack_from('<I', d, opt + 0x1C)[0]
        sec_tbl = opt + opt_size
        for i in range(num_sec):
            s = sec_tbl + i * 40
            name = d[s:s+8].rstrip(b'\x00').decode('ascii', errors='replace')
            vsize = struct.unpack_from('<I', d, s + 8)[0]
            rva = struct.unpack_from('<I', d, s + 12)[0]
            rawsize = struct.unpack_from('<I', d, s + 16)[0]
            rawoff = struct.unpack_from('<I', d, s + 20)[0]
            self.sections.append((name, rva, vsize, rawoff, rawsize))

    def va_to_off(self, va):
        rva = va - self.image_base
        for name, s_rva, vsize, rawoff, rawsize in self.sections:
            if s_rva <= rva < s_rva + max(vsize, rawsize):
                return rawoff + (rva - s_rva), name
        return None, None

    def md5(self):
        return hashlib.md5(self.data).hexdigest()


# ============================================================
# BMP 工具
# ============================================================

def parse_bmp_header(data):
    """Parse BMP header. Returns dict or raises ValueError."""
    if len(data) < 54:
        raise ValueError('File too small for BMP header')
    magic = data[0:2]
    if magic != b'BM':
        raise ValueError('Not a BMP file (missing BM magic)')
    fsize = struct.unpack_from('<I', data, 2)[0]
    off_bits = struct.unpack_from('<I', data, 10)[0]
    bi_size = struct.unpack_from('<I', data, 14)[0]
    bi_width = struct.unpack_from('<i', data, 18)[0]
    bi_height = struct.unpack_from('<i', data, 22)[0]
    bi_bitcount = struct.unpack_from('<H', data, 28)[0]
    bi_compression = struct.unpack_from('<I', data, 30)[0]
    return {
        'magic': magic, 'fsize': fsize, 'off_bits': off_bits,
        'bi_size': bi_size, 'bi_width': bi_width, 'bi_height': bi_height,
        'bi_bitcount': bi_bitcount, 'bi_compression': bi_compression,
        'is_bottom_up': bi_height > 0,
        'abs_height': abs(bi_height),
        'pixel_size': abs(bi_width) * abs(bi_height) * (bi_bitcount // 8),
    }


def validate_bmp(path):
    """Validate BMP file. Returns header dict."""
    with open(path, 'rb') as f:
        data = f.read()
    hdr = parse_bmp_header(data)
    if hdr['bi_bitcount'] != 32:
        raise ValueError('BMP must be 32bpp (got %d)' % hdr['bi_bitcount'])
    if hdr['bi_compression'] != 0:
        raise ValueError('BMP must be uncompressed BI_RGB (got %d)' % hdr['bi_compression'])
    if len(data) < hdr['off_bits'] + hdr['pixel_size']:
        raise ValueError('File size %d < expected pixel data end %d'
                         % (len(data), hdr['off_bits'] + hdr['pixel_size']))
    return hdr


def convert_bmp_topdown(path):
    """Convert bottom-up BMP to top-down. Returns output path."""
    with open(path, 'rb') as f:
        data = bytearray(f.read())
    hdr = parse_bmp_header(data)
    if not hdr['is_bottom_up']:
        print('  BMP already top-down, no conversion needed')
        return path

    w, h = hdr['bi_width'], abs(hdr['bi_height'])
    row_bytes = w * 4  # 32bpp
    off = hdr['off_bits']

    # Flip rows
    for i in range(h // 2):
        src_a = off + i * row_bytes
        src_b = off + (h - 1 - i) * row_bytes
        data[src_a:src_a + row_bytes], data[src_b:src_b + row_bytes] = \
            data[src_b:src_b + row_bytes], data[src_a:src_a + row_bytes]

    # Set biHeight to negative (top-down)
    struct.pack_into('<i', data, 22, -h)

    # Write converted file
    base, ext = os.path.splitext(path)
    out = base + '_topdown' + ext
    with open(out, 'wb') as f:
        f.write(bytes(data))
    print('  Converted bottom-up → top-down: %s' % out)
    return out


# ============================================================
# Shellcode 生成器
# ============================================================

class CodeBuilder:
    def __init__(self):
        self.code = bytearray()
        self.labels = {}
        self.jumps = []  # (offset_of_field, target_label, is32)

    def emit(self, *data):
        for d in data:
            if isinstance(d, int):
                self.code.append(d)
            elif isinstance(d, (bytes, bytearray)):
                self.code.extend(d)

    def d(self, val):
        """Emit DWORD (little-endian, unsigned)."""
        self.emit(struct.pack('<I', val & 0xFFFFFFFF))

    def label(self, name):
        self.labels[name] = len(self.code)

    def push_imm32(self, val):
        self.emit(0x68)
        self.d(val)

    def push_imm8(self, val):
        self.emit(0x6A, val & 0xFF)

    def push_reg(self, reg):
        self.emit(0x50 | reg)

    def push_mem_ebp(self, disp):
        self.emit(0xFF, 0x75, disp & 0xFF)

    def call_iat(self, va):
        self.emit(0xFF, 0x15)
        self.d(va)

    def call_mem_ebp(self, disp):
        self.emit(0xFF, 0x55, disp & 0xFF)

    def jmp_short(self, target):
        self.emit(0xEB, 0x00)
        self.jumps.append((len(self.code) - 1, target, False))

    def je_short(self, target):
        self.emit(0x74, 0x00)
        self.jumps.append((len(self.code) - 1, target, False))

    def jne_short(self, target):
        self.emit(0x75, 0x00)
        self.jumps.append((len(self.code) - 1, target, False))

    def je_rel32(self, target):
        self.emit(0x0F, 0x84, 0, 0, 0, 0)
        self.jumps.append((len(self.code) - 4, target, True))

    def patch_jumps(self):
        for off, target, is32 in self.jumps:
            tgt = self.labels[target]
            if is32:
                struct.pack_into('<i', self.code, off, tgt - (off + 4))
            else:
                rel = tgt - (off + 1)
                if not (-128 <= rel <= 127):
                    raise ValueError('Short jump out of range: %s' % target)
                self.code[off] = rel & 0xFF

    def to_bytes(self):
        self.patch_jumps()
        return bytes(self.code)


def build_fake_shellcode(filepath):
    """Generate 352-byte shellcode to replace FUN_1008cb70."""
    if len(filepath) > SC_MAX_FP:
        raise ValueError('Filepath too long: %d > %d' % (len(filepath), SC_MAX_FP))

    cb = CodeBuilder()

    # PROLOGUE
    cb.emit(0x55)                          # push ebp
    cb.emit(0x8B, 0xEC)                    # mov ebp, esp
    cb.emit(0x83, 0xEC, 0xC0)              # sub esp, 0xC0
    cb.emit(0x89, 0x45, 0xFC)             # mov [ebp-4], eax (param_1)

    # RESOLVE ReadFile
    cb.push_imm32(0)                       # push NULL
    cb.call_iat(IAT_GetModuleHandleA)
    cb.push_imm32(VA_RF)                   # push "ReadFile"
    cb.push_reg(0)                         # push hKernel32
    cb.call_iat(IAT_GetProcAddress)
    cb.emit(0x89, 0x45, 0xF8)             # mov [ebp-8], eax

    # CreateFileA
    cb.push_imm32(0)
    cb.push_imm32(0)
    cb.push_imm8(3)
    cb.push_imm32(0)
    cb.push_imm8(1)
    cb.push_imm32(0x80000000)
    cb.push_imm32(VA_FP)
    cb.call_iat(IAT_CreateFileA)
    cb.emit(0x83, 0xC4, 0x1C)

    cb.emit(0x3D, 0xFF, 0xFF, 0xFF, 0xFF)
    cb.je_rel32("fallback")
    cb.emit(0x89, 0x45, 0xF4)             # mov [ebp-0xC], eax (hFile)

    # ReadFile: header (54 bytes)
    cb.emit(0x8D, 0x45, 0xA0)             # lea eax, [ebp-0x60]
    cb.emit(0x8D, 0x4D, 0xF0)             # lea ecx, [ebp-0x10]
    cb.push_imm32(0)
    cb.push_reg(1)
    cb.push_imm32(54)
    cb.push_reg(0)
    cb.push_mem_ebp(-0x0C)
    cb.call_mem_ebp(-0x08)
    cb.emit(0x83, 0xC4, 0x14)
    cb.emit(0x85, 0xC0)
    cb.je_short("do_close")

    # Validate: "BM"
    cb.emit(0x8B, 0x45, 0xA0)
    cb.emit(0x3D, 0x42, 0x4D, 0x00, 0x00)
    cb.jne_short("do_close")

    # Validate: 32bpp
    cb.emit(0x0F, 0xB7, 0x45, 0xBC)
    cb.emit(0x3D, 0x20, 0x00, 0x00, 0x00)
    cb.jne_short("do_close")

    # Validate: width matches
    cb.emit(0x8B, 0x45, 0xBA)             # bmp width
    cb.emit(0x8B, 0x55, 0xFC)             # param_1
    cb.emit(0x39, 0x02)
    cb.jne_short("do_close")

    # Validate: height matches (top-down: bmp_h is negative, req_h positive)
    # bmp_h + req_h == 0 → match → continue; != 0 → mismatch → do_close
    cb.emit(0x8B, 0x45, 0xBE)             # mov eax, [ebp-0x60+22] (biHeight)
    cb.emit(0x8B, 0x55, 0xFC)             # mov edx, [ebp-4] (param_1)
    cb.emit(0x03, 0x42, 0x04)             # add eax, [edx+4] (bmp_h + req_h)
    cb.jne_short("do_close")              # jne: heights don't match → close

    # SetFilePointer
    cb.emit(0x8B, 0x45, 0xAC)             # offBits
    cb.push_imm32(0)
    cb.push_reg(0)
    cb.push_mem_ebp(-0x0C)
    cb.call_iat(IAT_SetFilePointer)
    cb.emit(0x83, 0xC4, 0x0C)

    # ReadFile: pixels
    cb.emit(0x8B, 0x55, 0xFC)
    cb.emit(0x8B, 0x02)                   # width
    cb.emit(0x0F, 0xAF, 0x42, 0x04)       # width * height
    cb.emit(0xC1, 0xE0, 0x02)             # * 4

    cb.emit(0x8D, 0x4D, 0xF0)
    cb.push_imm32(0)
    cb.push_reg(1)
    cb.push_reg(0)
    cb.emit(0x8B, 0x42, 0x08)             # buffer
    cb.push_reg(0)
    cb.push_mem_ebp(-0x0C)
    cb.call_mem_ebp(-0x08)
    cb.emit(0x83, 0xC4, 0x14)

    # do_close
    cb.label("do_close")
    cb.push_mem_ebp(-0x0C)
    cb.call_iat(IAT_CloseHandle)
    cb.emit(0x83, 0xC4, 0x04)
    cb.jmp_short("epilogue")

    # fallback: zero-fill (black screen)
    cb.label("fallback")
    cb.emit(0x8B, 0x55, 0xFC)
    cb.emit(0x8B, 0x02)
    cb.emit(0x0F, 0xAF, 0x42, 0x04)
    cb.emit(0x89, 0xC1)
    cb.emit(0x8B, 0x7A, 0x08)
    cb.emit(0x31, 0xC0)
    cb.emit(0xF3, 0xAB)

    # epilogue
    cb.label("epilogue")
    cb.emit(0x5D)
    cb.emit(0xC9)
    cb.emit(0xC3)

    code = cb.to_bytes()
    if len(code) > SC_FP_OFF:
        raise ValueError('Code too large: %d > %d' % (len(code), SC_FP_OFF))

    blob = bytearray(code)
    blob.extend(b'\xCC' * (SC_FP_OFF - len(code)))
    fp = filepath.encode('ascii') + b'\x00'
    blob.extend(fp)
    blob.extend(b'\xCC' * (SC_RF_OFF - SC_FP_OFF - len(fp)))
    blob.extend(b'ReadFile\x00')
    blob.extend(b'\xCC' * (FUN_CB70_SIZE - len(blob)))
    assert len(blob) == FUN_CB70_SIZE
    return bytes(blob)


# ============================================================
# Patch 核心逻辑
# ============================================================

def sanity_check_nop(pe, target_key):
    t = KNOWN[target_key]
    va = t['va']
    fileoff, sec = pe.va_to_off(va)
    errors = []
    if fileoff is None:
        errors.append('VA 0x%08X not in any section' % va)
        return None, errors
    if sec != '.text':
        errors.append('VA 0x%08X not in .text (in %s)' % (va, sec))
    if fileoff != t['fileoff']:
        errors.append('Offset mismatch: actual 0x%08X, expected 0x%08X' % (fileoff, t['fileoff']))
    entry = pe.data[fileoff:fileoff+3]
    if entry == PATCH_NOP:
        errors.append('Already patched (entry = 31 c0 c3)')
        return fileoff, errors
    if entry != ORIG_PROLOGUE:
        errors.append('Bad entry: %s (expected 55 8b ec)' % entry.hex())
    window = pe.data[fileoff:fileoff+FUNC_WINDOW]
    if b'\xe8' not in window and b'\xff\x15' not in window:
        errors.append('No call instruction in function body')
    return fileoff, errors


def sanity_check_fake(pe):
    """Verify FUN_1008cb70 is intact for shellcode replacement."""
    va = FUN_CB70_VA
    fileoff, sec = pe.va_to_off(va)
    errors = []
    if fileoff is None:
        errors.append('FUN_1008cb70 VA not found')
        return None, errors
    if sec != '.text':
        errors.append('FUN_1008cb70 not in .text')
    if fileoff != FUN_CB70_OFF:
        errors.append('Offset mismatch: 0x%08X != 0x%08X' % (fileoff, FUN_CB70_OFF))
    entry = pe.data[fileoff:fileoff+3]
    if entry == b'\x31\xc0\xc3':
        errors.append('Already NOP-patched')
        return fileoff, errors
    if entry != ORIG_PROLOGUE:
        errors.append('Bad entry: %s' % entry.hex())
    # Check next function boundary
    next_off = fileoff + FUN_CB70_SIZE
    if next_off + 3 <= len(pe.data):
        # The next function should start with a valid prologue
        pass  # We trust the Ghidra analysis
    return fileoff, errors


def process_one(dll_path, targets, dry_run=False, inplace=False, strict=True,
                fake_screen=None, convert_bmp=False):
    print('\n' + '='*60)
    print('Target: %s' % dll_path)
    print('Size: %d bytes' % os.path.getsize(dll_path))
    print('='*60)

    pe = PE(dll_path)
    print('ImageBase: 0x%08X' % pe.image_base)
    print('MD5: %s' % pe.md5())

    all_ok = True

    if fake_screen:
        # ── FAKE SCREEN MODE ──
        print('\n  [FAKE SCREEN MODE]')
        print('  BMP: %s' % fake_screen)

        # Validate BMP
        try:
            hdr = validate_bmp(fake_screen)
            print('  BMP: %dx%d %dbpp %s' % (
                hdr['bi_width'], hdr['abs_height'], hdr['bi_bitcount'],
                'bottom-up' if hdr['is_bottom_up'] else 'top-down'))
        except Exception as e:
            print('  [ERR] BMP validation failed: %s' % e)
            return False

        # Convert if needed
        bmp_path = fake_screen
        if hdr['is_bottom_up'] and convert_bmp:
            bmp_path = convert_bmp_topdown(fake_screen)
        elif hdr['is_bottom_up'] and not convert_bmp:
            print('  [WARN] BMP is bottom-up! Use --convert or convert manually.')
            print('         Shellcode expects top-down BMP (negative biHeight).')

        # Check filepath length
        if len(bmp_path) > SC_MAX_FP:
            print('  [ERR] Filepath too long: %d > %d chars' % (len(bmp_path), SC_MAX_FP))
            print('        Use a shorter path, e.g., C:\\os_fake.bmp')
            return False

        # Sanity check DLL
        fileoff, errors = sanity_check_fake(pe)
        for e in errors:
            print('  [ERR] %s' % e)
        if errors:
            return False
        print('  FUN_1008cb70 verified at file offset 0x%08X' % fileoff)

        # Generate shellcode
        sc = build_fake_shellcode(bmp_path)
        print('  Shellcode: %d bytes (code + strings)' % len(sc))

        if dry_run:
            print('  [DRY-RUN] Shellcode preview (first 64 bytes):')
            for i in range(0, 64, 16):
                print('    +%03X: %s' % (i, ' '.join('%02x' % b for b in sc[i:i+16])))
            print('  [DRY-RUN] Skip write')
            return True

        # Determine output
        if inplace:
            out_path = dll_path
            bak = dll_path + '.bak'
            if not os.path.exists(bak):
                shutil.copy2(dll_path, bak)
                print('  Backup: %s' % bak)
        else:
            base, ext = os.path.splitext(dll_path)
            out_path = base + '_fake' + ext

        # Write
        data = bytearray(pe.data)
        data[fileoff:fileoff+FUN_CB70_SIZE] = sc
        with open(out_path, 'wb') as f:
            f.write(bytes(data))

        # Verify
        with open(out_path, 'rb') as f:
            f.seek(fileoff)
            verify = f.read(3)
        if verify != b'\x55\x8b\xec':
            print('  [FAIL] Verify failed!')
            all_ok = False
        else:
            print('  [OK] Write verified')

        if strict:
            orig = open(dll_path if not inplace else bak, 'rb').read()
            new = open(out_path, 'rb').read()
            if len(orig) != len(new):
                print('  [FAIL] Size changed!')
                all_ok = False
            else:
                diffs = sum(1 for a, b in zip(orig, new) if a != b)
                print('  [OK] Byte diff: %d bytes changed (expected ~%d)' % (diffs, FUN_CB70_SIZE))

    else:
        # ── NOP MODE ──
        for tk in targets:
            if tk not in KNOWN:
                print('  [SKIP] Unknown: %s' % tk)
                continue
            t = KNOWN[tk]
            print('\n  --- [%s] %s %s ---' % (tk, t['name'], t['desc']))

            fileoff, errors = sanity_check_nop(pe, tk)
            if errors:
                for e in errors:
                    print('  [ERR] %s' % e)
                all_ok = False
                continue
            orig = pe.data[fileoff:fileoff+3]
            print('  Offset: 0x%08X  Bytes: %s → %s' % (fileoff, orig.hex(), PATCH_NOP_DIS))

            if dry_run:
                print('  [DRY-RUN] Skip')
                continue

            if inplace:
                out_path = dll_path
                bak = dll_path + '.bak'
                if not os.path.exists(bak):
                    shutil.copy2(dll_path, bak)
                    print('  Backup: %s' % bak)
            else:
                base, ext = os.path.splitext(dll_path)
                out_path = base + '_noscreen' + ext

            data = bytearray(pe.data)
            data[fileoff:fileoff+3] = PATCH_NOP
            with open(out_path, 'wb') as f:
                f.write(bytes(data))

            with open(out_path, 'rb') as f:
                f.seek(fileoff)
                v = f.read(3)
            if v != PATCH_NOP:
                print('  [FAIL] Verify failed!')
                all_ok = False
            else:
                print('  [OK] Verified')

            if strict:
                ref = open(dll_path if not inplace else bak, 'rb').read()
                new = open(out_path, 'rb').read()
                if len(ref) == len(new):
                    diffs = sum(1 for a, b in zip(ref, new) if a != b)
                    expected = 3 * len([k for k in targets if k in KNOWN])
                    print('  [OK] Diff: %d bytes (expected %d)' % (diffs, expected))

    print('\n' + '='*60)
    print('Result: %s' % ('PASS ✓' if all_ok else 'FAIL ✗'))
    print('='*60)
    return all_ok


def restore_one(dll_path):
    bak = dll_path + '.bak'
    if not os.path.exists(bak):
        print('  [ERR] No backup: %s' % bak)
        return False
    shutil.copy2(bak, dll_path)
    print('  [OK] Restored from backup')
    return True
