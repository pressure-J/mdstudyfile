# -*- coding: utf-8 -*-
"""RSA33 d 与 φ 泄露 —— 自验证脚本（两条独立的分解路径）
路径一：给了 φ(n)  → p+q = n - φ + 1，解 x^2 - (p+q)x + n = 0
路径二：给了 d(n)  → ed-1 是 φ 的倍数，随机 a 做「平方链 + gcd」概率分解
换题只改「题目数据」一段。
"""
import random
from math import gcd, isqrt
from sympy import nextprime

# ================= 题目数据（换题改这里） =================
E = 65537
# ===========================================================

def from_phi(n, phi):
    """φ 泄露：韦达定理一步解出 p、q"""
    s = n - phi + 1                 # p + q
    d = s * s - 4 * n               # (p-q)^2
    r = isqrt(d)
    assert r * r == d, "判别式不是完全平方，题目的 φ 与 n 不匹配"
    return (s - r) // 2, (s + r) // 2

def from_d(n, e, d):
    """d 泄露：ed-1 = 2^s * r，沿平方链找非平凡 gcd"""
    t = e * d - 1
    s = (t & -t).bit_length() - 1   # 因子 2 的个数
    r = t >> s
    tries = 0
    for a in range(2, 200):
        tries += 1
        x = pow(a, r, n)
        for j in range(s):
            g = gcd(x - 1, n)
            if 1 < g < n:
                return g, n // g, a, j, tries
            x = x * x % n
    raise RuntimeError("换更多基 a 重试")

def main():
    random.seed(20261103)
    p = nextprime(random.getrandbits(512))
    q = nextprime(random.getrandbits(512))
    n, phi = p * q, (p - 1) * (q - 1)
    d = pow(E, -1, phi)

    print("== 路径一：只给 n 和 φ ==")
    a1, b1 = from_phi(n, phi)
    print("恢复成功:", set((a1, b1)) == {p, q}, " p 位数 =", a1.bit_length())

    print("== 路径二：只给 n、e、d ==")
    a2, b2, base, j, tries = from_d(n, E, d)
    print("恢复成功:", set((a2, b2)) == {p, q},
          f" 命中基 a={base}, 平方链 j={j}, 用了 {tries} 次尝试")

    print("== 对照：手上有 c 时其实不用分解 ==")
    m = 12345678901234567890
    c = pow(m, E, n)
    print("pow(c,d,n) 直接解密:", pow(c, d, n) == m)

    assert set((a1, b1)) == {p, q} and set((a2, b2)) == {p, q}

if __name__ == "__main__":
    main()
