#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""rsa1024 — 费马分解 + e=1024 非互素开根（逐层开平方 + CRT）"""

import math
import itertools
from gmpy2 import mpz, isqrt, powmod, invert

# ================= 配置区 =================
n = mpz(100795671860737972021334521272554380428367793812878527064430927026275906890032777339631169861887598785641855189764327496638791143405442270376747977115069190214798206664398228363742086173342997747246656538851473832377171344539209200408526008991695290361018961983612856277403499719193081611659440940616262571149)
c = mpz(1286700630158721940102335512084113258284972272281062499273299025096054388683589179977773407319763462365872933124984005829271230759887798088167140028005604344132128070810731253967228966728249520805009215596621584420115455006537661922704990998669169811260057535995543256909881343280855246383985848414166109855)
E = 1024
# ==========================================

# ---------- 步骤1：费马分解（p、q 几乎相邻） ----------
def fermat(n, steps=500000):
    a = isqrt(n)
    if a * a < n:
        a += 1
    for i in range(1, steps + 1):
        b2 = a * a - n
        b = isqrt(b2)
        if b * b == b2:
            return a - b, a + b, i
        a += 1
    return None, None, steps

p, q, it = fermat(n)
assert p is not None, "费马分解失败"
assert p * q == n
print(f"[+] 费马分解命中，迭代 {it} 步")
print("p =", p)
print("q =", q)
print("|p-q| =", q - p)
print("p%4 =", p % 4, " q%4 =", q % 4)

g_p = math.gcd(E, int(p) - 1)
g_q = math.gcd(E, int(q) - 1)
print("gcd(e, p-1) =", g_p, " gcd(e, q-1) =", g_q)

# ---------- 步骤2：模素数开平方（Tonelli-Shanks 全根） ----------
def sqrt_all(a, p):
    """模素数 p 开平方，返回 0 个或 2 个根"""
    a %= p
    if a == 0:
        return [mpz(0)]
    if powmod(a, (p - 1) // 2, p) != 1:
        return []
    if p % 4 == 3:
        r = powmod(a, (p + 1) // 4, p)
        return [r, (p - r) % p]
    # Tonelli-Shanks（p % 4 == 1 时）
    q_, s = p - 1, 0
    while q_ % 2 == 0:
        q_ //= 2
        s += 1
    z = mpz(2)
    while powmod(z, (p - 1) // 2, p) != p - 1:
        z += 1
    m, cc, t, r = s, powmod(z, q_, p), powmod(a, q_, p), powmod(a, (q_ + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1:
            t2 = t2 * t2 % p
            i += 1
        b = powmod(cc, 1 << (m - i - 1), p)
        m, cc = i, b * b % p
        t = t * cc % p
        r = r * b % p
    return [r, (p - r) % p]

def roots_pow2(c, e, p):
    """x^e = c (mod p)，e = 2^k：从 c 开始逐层开平方，共 k 层。
    正确性：若 x^e=c，则 x^(e/2) 是 c 的平方根，逐层递归成立；
    每层根数最多翻倍，开不出平方的分支（非剩余）直接剪掉。
    末层用 pow(r,e,p)==c 过滤，只留真根。"""
    c %= p
    roots = [mpz(c)]
    for _ in range(e.bit_length() - 1):
        nxt = []
        for r in roots:
            nxt.extend(sqrt_all(r, p))
        roots = nxt
        if not roots:
            return []
    return sorted({r for r in roots if powmod(r, e, p) == c})

rp = roots_pow2(c, E, p)
rq = roots_pow2(c, E, q)
print(f"[+] 模 p 下根数: {len(rp)} (期望 {g_p})")
print(f"[+] 模 q 下根数: {len(rq)} (期望 {g_q})")
assert len(rp) == g_p and len(rq) == g_q, "根数与 gcd(e,p-1) 不符"

# ---------- 步骤3：CRT 合并 + roundtrip 验证（铁律） ----------
qinv = invert(q, p)
Ni = int(n)
ci = int(c)
print("\n=== CRT 候选（过 pow(m,e,n)==c 验证的才打印） ===")
for xp, xq in itertools.product(rp, rq):
    m = int((xq + q * ((xp - xq) * qinv % p)) % n)
    if pow(m, E, Ni) != ci:
        continue
    b = m.to_bytes((m.bit_length() + 7) // 8, "big")
    print("[候选]", b)
