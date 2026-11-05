# -*- coding: utf-8 -*-
"""RSA43 p+1 光滑（Williams p+1）—— 自验证脚本
题型：p+1 是 B-smooth（生成脚本常见 p = 小素数连乘 - 1）。
原理：Lucas 序列满足 V_{p+1} ≡ 2 (mod p)；把 M = lcm(1..B) 的素幂
      逐级复合到 P 上（V_a(V_b(P)) = V_{ab}(P)），最后 gcd(V_M - 2, n) 命中 p。
      这是 p-1 攻击的镜像：p-1 光滑时 p-1 攻击赢，p+1 光滑时这一招赢。
换题只改「题目数据」一段。
"""
import random
from math import gcd
from sympy import nextprime, isprime, primerange

# ================= 题目数据（换题改这里） =================
B_LADDER = (1000, 10000, 100000)          # 逐级加大光滑界（要覆盖 p+1 的素幂）
BASES = (3, 5, 7, 11)          # 固定小基
RANDOM_BASES = 12              # 再补若干个随机大基（关键，见笔记「基的坑」）
# ===========================================================

def lucas_v(k, P, n):
    """迭代式 Lucas V_k(P, 1) mod n：V_0=2, V_1=P,
       V_2m = V_m^2-2, V_{2m+1} = V_m V_{m+1} - P, V_{2m+2} = V_{m+1}^2-2"""
    if k == 0:
        return 2 % n
    P %= n
    v0, v1 = P % n, (P * P - 2) % n      # (V_1, V_2)
    for bit in bin(k)[3:]:               # 跳过最高位 '1'
        v2m = (v0 * v0 - 2) % n
        v2m1 = (v0 * v1 - P) % n
        v2m2 = (v1 * v1 - 2) % n
        if bit == '0':
            v0, v1 = v2m, v2m1
        else:
            v0, v1 = v2m1, v2m2
    return v0

def prime_powers(B):
    """升序返回 ≤B 的所有素数幂（连乘起来就是 lcm(1..B)）"""
    for pr in primerange(2, B + 1):
        pk = pr
        while pk * pr <= B:
            pk *= pr
        yield pk

def williams(n, B, bases=BASES, rnd=None):
    """V 序列可复合：先逐级作用素数幂，最后取 gcd(V-2, n)。
       基 P 必须让 (P^2-4 | p) = -1 才命中，所以随机大基各占一半概率。"""
    rnd = rnd or random.Random(11)
    Ps = list(bases) + [rnd.randrange(2, n) for _ in range(RANDOM_BASES)]
    for P in Ps:
        x = P % n
        for pk in prime_powers(B):
            x = lucas_v(pk, x, n)
        g = gcd(x - 2, n)
        if 1 < g < n:
            return g, n // g, P
    return None

def build_smooth_p(bits=300, B=10000):
    """造 p+1：每个素幂都 ≤ B（B-powersmooth），这样 lcm(1..B) 才能被 p+1 整除"""
    rnd = random.Random(7)
    small = list(primerange(2, 200))
    for _ in range(20000):
        m = 1
        for pr in small:
            pk = pr
            while pk * pr <= B and rnd.random() < 0.7:
                pk *= pr
            m *= pk
            if m.bit_length() >= bits:
                break
        if m.bit_length() >= bits and isprime(m - 1):
            return m - 1, m
    raise RuntimeError("没造出光滑 p，调大 bits/B")

def main():
    p, M = build_smooth_p()
    q = nextprime(random.getrandbits(512))
    n = p * q
    print("p 位数 =", p.bit_length(), "  p+1 全是 ≤199 的小素数幂（B-powersmooth）")
    print("n bits =", n.bit_length())

    for B in B_LADDER:
        r = williams(n, B)
        if r:
            a, b, P = r
            ok = set((a, b)) == {p, q}
            print(f"B={B:<8} 命中: 基 P={P}  分解成功={ok}")
            assert ok
            return
        print(f"B={B:<8} 未命中，加大 B")
    raise SystemExit("B 加到 2e5 仍未命中，检查 p+1 是否真的光滑")

if __name__ == "__main__":
    main()
