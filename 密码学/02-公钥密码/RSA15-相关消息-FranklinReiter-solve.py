# -*- coding: utf-8 -*-
"""RSA15 相关消息攻击（Franklin-Reiter）—— 自验证脚本
题目给 (n, e, c1, c2)，两个明文满足 m2 = a*m1 + b（同 n、同 e、e 小）。
原理：m1 同时是 x^e - c1 和 (a*x+b)^e - c2 在 Z_n[x] 里的根，
      两者在模 n 下的 gcd 就是 x - m1。
换题只改「题目数据」一段。
"""
import random
from sympy import nextprime

# ================= 题目数据（换题改这里） =================
E = 3
A, B = 0x100, 0x2333          # m2 = A*m1 + B
# ===========================================================

def ptrim(a, n):
    while len(a) > 1 and a[-1] % n == 0:
        a.pop()
    return a

def pmul(a, b, n):
    r = [0] * (len(a) + len(b) - 1)
    for i, x in enumerate(a):
        x %= n
        if not x:
            continue
        for j, y in enumerate(b):
            r[i + j] = (r[i + j] + x * y) % n
    return ptrim(r, n)

def ppow(a, k, n):
    r = [1]
    for _ in range(k):
        r = pmul(r, a, n)
    return r

def pmod(a, m, n):
    """a mod m（模 n 系数），m 首项必须可逆，否则返回 None"""
    a = a[:]
    dm = len(m) - 1
    if dm == 0:
        return [0]
    try:
        inv = pow(m[-1], -1, n)
    except ValueError:
        return None
    while len(a) > dm:
        d = len(a) - 1 - dm
        coef = a[-1] * inv % n
        if coef:
            for i in range(dm + 1):
                a[d + i] = (a[d + i] - coef * m[i]) % n
        ptrim(a, n)
    return ptrim(a, n)

def pgcd(a, b, n):
    """Z_n[x] 上求 gcd，返回首一多项式；中途系数不可逆则返回 None"""
    a = ptrim([x % n for x in a], n)
    b = ptrim([x % n for x in b], n)
    while not (len(b) == 1 and b[0] == 0):
        r = pmod(a, b, n)
        if r is None:
            return None
        a, b = b, r
    try:
        inv = pow(a[-1], -1, n)
    except ValueError:
        return None
    return [(c * inv) % n for c in a]

def main():
    random.seed(20261103)
    p = nextprime(random.getrandbits(256))
    q = nextprime(random.getrandbits(256))
    n = p * q
    m1 = random.getrandbits(200)
    m2 = (A * m1 + B) % n
    c1, c2 = pow(m1, E, n), pow(m2, E, n)

    print("n bits =", n.bit_length(), " e =", E)
    print("题目给定: n, e, c1, c2, a, b（不知道 m1、m2）")

    f = [(-c1) % n, 0, 0, 1]                 # x^e - c1
    g = pmul([B % n, A % n], [B % n, A % n], n)
    g = pmul(g, [B % n, A % n], n)
    g = [(g[i] - (c2 if i == 0 else 0)) % n for i in range(len(g))]   # (a*x+b)^e - c2

    h = pgcd(f, g, n)
    assert h and len(h) == 2, "gcd 退化，换一个 a 或 b 重试"
    rec = (-h[0]) % n                        # x - m1  =>  常数项 = -m1
    print("gcd 次数 =", len(h) - 1, " 恢复 m1 =", hex(rec)[:24], "...")
    print("m1 与原值一致:", rec == m1)
    print("m2 复原:", (A * rec + B) % n == m2)
    assert rec == m1

if __name__ == "__main__":
    main()
