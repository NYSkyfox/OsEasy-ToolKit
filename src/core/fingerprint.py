# src/core/fingerprint.py
# 文件指纹工具 —— MD5 / 大小，用于样本版本校验

import os
import hashlib


def md5_of(path: str, chunk: int = 1 << 20) -> str:
    """计算文件 MD5（分块读取，大文件友好）。"""
    h = hashlib.md5()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(chunk), b""):
            h.update(block)
    return h.hexdigest()


def size_of(path: str) -> int:
    return os.path.getsize(path)


def describe(path: str) -> dict:
    """返回 {path, size, md5}。文件不存在时 size=-1, md5=''。"""
    if not os.path.isfile(path):
        return {"path": path, "size": -1, "md5": ""}
    return {"path": path, "size": os.path.getsize(path), "md5": md5_of(path)}
