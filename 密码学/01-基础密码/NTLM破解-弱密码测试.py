#!/usr/bin/env python
# -*- coding: utf-8 -*-
# NTLM 哈希快速测试：常见弱密码 + 用户名变体
# NTLM(pw) = MD4(UTF-16LE(pw))
from Crypto.Hash import MD4

TARGET = "a7fcb22a88038f35a8f39d503e7f0062"

def ntlm(pw: str) -> str:
    return MD4.new(pw.encode("utf-16-le")).hexdigest()

# 常见弱密码
base = [
    "admin", "admin123", "administrator", "password", "password123",
    "123456", "12345678", "123456789", "1234567890", "1234567",
    "qwerty", "qwerty123", "abc123", "111111", "000000", "666666",
    "888888", "123123", "123321", "520520", "5201314", "1314520",
    "iloveyou", "letmein", "welcome", "welcome1", "monkey", "dragon",
    "master", "football", "baseball", "shadow", "superman", "batman",
    "login", "passw0rd", "p@ssw0rd", "P@ssw0rd", "Passw0rd",
    "root", "toor", "test", "test123", "guest", "user", "user123",
    "ctf", "CTF", "ctf123", "ctf2024", "ctf2025", "ctf@123", "ctf12345",
    "flag", "flag123", "flag{", "key", "key123", "secret", "secret123",
    "hello", "hello123", "world", "world123", "nihao", "zhangsan",
    "wang", "li", "admin888", "admin666", "root123", "rootroot",
    "123456abc", "a123456", "qq123456", "woaini", "woaini1314",
    "hacker", "hacker123", "pass", "pass123", "asdfgh", "zxcvbn",
    "1qaz2wsx", "qazwsx", "qwe123", "love", "love123", "mima",
    "mima123", "wang123", "li123", "zhang123", "chen123", "yang123",
]
# 加数字/符号后缀变体
extra = []
for w in base[:60]:
    for suf in ["1", "123", "1234", "12345", "666", "888", "!", "@", "@123", "2024", "2025"]:
        extra.append(w + suf)
words = list(dict.fromkeys(base + extra))  # 去重保序

hit = None
for i, w in enumerate(words):
    if ntlm(w) == TARGET:
        hit = w
        break

if hit:
    print(f"[+] FOUND: {hit!r}")
    print(f"    NTLM = {ntlm(hit)}")
else:
    print(f"[-] 未命中（已测试 {len(words)} 个候选）")
    print("[*] 建议下一步：hashcat -m 1000 + rockyou 字典")