#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通用哈希/明文爆破脚本
======================
适用：已知 MD5/SHA 哈希（或片段），明文部分未知，穷举未知字符。
特性：
  - 模板用 ? 占位未知字符（如 'TASC?O3RJMV?WDJKX?ZM'）
  - 支持多个哈希片段子串匹配，取交集筛唯一解
  - hashlib 只收 bytes，模板和字符均需 encode
  - 纯标准库，改 TEMPLATE / TARGET_PARTS / HASH_ALGO 即跑
用法：py MD5爆破-solve.py
"""

import hashlib
import itertools
import time

# ===== 改这里 =====
TEMPLATE = 'TASC?O3RJMV?WDJKX?ZM'   # ? 为未知字符占位
TARGET_PARTS = ['e9032', 'da', '911513']  # 期望哈希的多个子串片段（交集筛选）
HASH_ALGO = 'md5'                   # 算法：md5 / sha1 / sha256 / sha512
CHARSET = range(32, 127)            # 可打印 ASCII：32(空格)~126(~)，127 取不到
# ==================

def make_hash(data: bytes) -> str:
    h = hashlib.new(HASH_ALGO)
    h.update(data)
    return h.hexdigest()

def fill_template(template: str, values) -> str:
    """把模板里的 ? 依次替换成 values 对应的字符"""
    it = iter(values)
    return ''.join(next(it) if ch == '?' else ch for ch in template)

def matches(digest: str, parts) -> bool:
    """所有片段都出现在 digest 里才为真"""
    return all(p in digest for p in parts)

def main():
    q = TEMPLATE.count('?')
    print(f"未知字符数: {q}  穷举量: {CHARSET.stop - CHARSET.start}**{q} = {(CHARSET.stop - CHARSET.start) ** q:,}")
    t0 = time.time()
    found = []
    # 用组合而不是全量笛卡尔积可大幅减分支（本题不需要，保留注释供扩展）
    for combo in itertools.product(CHARSET, repeat=q):
        plain = fill_template(TEMPLATE, (chr(i) for i in combo))
        d = make_hash(plain.encode())
        if matches(d, TARGET_PARTS):
            found.append((plain, d))
            print(f"[命中] {plain} -> {d}")
    dt = time.time() - t0
    print(f"耗时 {dt:.1f}s  共 {len(found)} 个解")
    if len(found) == 1:
        print(f"唯一解明文: {found[0][0]}")
        print(f"完整哈希:   {found[0][1]}")
    elif len(found) > 1:
        print("多个解，需增加片段进一步筛选")

if __name__ == '__main__':
    main()