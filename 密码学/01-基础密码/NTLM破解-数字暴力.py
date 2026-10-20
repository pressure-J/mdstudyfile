#!/usr/bin/env python
# -*- coding: utf-8 -*-
# NTLM 数字/短密码暴力：MD4(UTF-16LE(pw)) == target
# 纯数字 1~7 位 + 常见短模式
from Crypto.Hash import MD4
import itertools, time, sys

TARGET = "a7fcb22a88038f35a8f39d503e7f0062"

def ntlm(pw: str) -> str:
    return MD4.new(pw.encode("utf-16-le")).hexdigest()

start = time.time()
count = 0

def check(pw):
    global count
    count += 1
    if ntlm(pw) == TARGET:
        print(f"[+] FOUND: {pw!r}  (尝试 {count} 次, 耗时 {time.time()-start:.1f}s)")
        return True
    if count % 200000 == 0:
        print(f"[*] 已尝试 {count} 个, 累计 {time.time()-start:.1f}s", flush=True)
    return False

# 1) 纯数字 1~6 位（先小后大）
for n in range(1, 7):
    for digits in itertools.product("0123456789", repeat=n):
        if check("".join(digits)):
            sys.exit(0)
    print(f"[*] {n} 位纯数字完成, 累计 {time.time()-start:.1f}s", flush=True)

# 2) ctf 相关变体扩展
ctf_list = ["ctf", "ctf0", "ctf1", "ctf123", "lab", "lab123", "admin", "administrator",
            "flag", "flag123", "test", "guest", "user", "root", "toor", "hack", "hacker",
            "password", "pass", "p@ss", "qwer", "qwerty", "asdf", "zxcv", "1qaz", "zaq1",
            "love", "iloveyou", "520", "1314", "6666", "8888"]
seen = set()
for w in ctf_list:
    for suf in ["", "1", "2", "123", "1234", "12345", "666", "888", "!", "@", "#", "0", "00", "2024", "2025", "2026"]:
        cand = w + suf
        if cand not in seen:
            seen.add(cand)
            if check(cand):
                sys.exit(0)

print(f"[-] 未命中。总尝试 {count} 次, 耗时 {time.time()-start:.1f}s")
print("[*] 建议: 换大字典(hashcat+rockyou) 或根据题目上下文猜密码格式")