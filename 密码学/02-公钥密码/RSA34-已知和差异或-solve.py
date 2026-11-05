# -*- coding: utf-8 -*-
"""RSA34 已知 p+q / p−q / p⊕q —— 自验证脚本
① 给 p+q 或 p−q：配 n = pq 解 x^2-(p+q)x+n=0
② 给 p⊕q：从最低位逐位 DFS，用 p*q ≡ n (mod 2^k) 剪枝
换题只改「题目数据」一段。
"""
import random
from math import isqrt
from sympy import nextprime

# ================= 题目数据（换题改这里） =================
BITS = 512          # p、q 的位长（题目一般给 512/1024）
# ===========================================================

def quadratic(n, s):
    """已知 p+q（或由差算出的和），解二次方程"""
    d = s * s - 4 * n                 # (p-q)^2
    r = isqrt(d)
    assert r * r == d, "判别式不是完全平方"
    return (s - r) // 2, (s + r) // 2

def from_diff(n, diff):
    """已知 p-q：先补出 p+q = sqrt(diff^2 + 4n)"""
    s = isqrt(diff * diff + 4 * n)
    assert s * s == diff * diff + 4 * n
    return quadratic(n, s)

def from_xor(n, x, bits):
    """已知 p^q：低位逐位枚举，每步用乘积的低位约束剪枝"""
    cands = [(0, 0)]
    mask = 1
    for k in range(bits):
        nk = (n >> k) & 1
        xk = (x >> k) & 1
        nxt = []
        for pl, ql in cands:
            for pb in (0, 1):
                qb = pb ^ xk
                np_ = pl | (pb << k)
                nq_ = ql | (qb << k)
                if (np_ * nq_) & ((1 << (k + 1)) - 1) == n & ((1 << (k + 1)) - 1):
                    nxt.append((np_, nq_))
        cands = list(dict.fromkeys(nxt))
        if not cands:
            return None
        if len(cands) > 4096:                 # 候选爆炸说明题面还给少了信息
            cands = cands[:4096]
    return [(a, b) for a, b in cands if a * b == n and a > 1 and b > 1 and (a ^ b) == x]

def main():
    random.seed(20261103)
    p = nextprime(random.getrandbits(BITS))
    q = nextprime(random.getrandbits(BITS))
    n = p * q
    print("n bits =", n.bit_length())

    a1, b1 = quadratic(n, p + q)
    print("① 给 p+q:", set((a1, b1)) == {p, q})

    a2, b2 = from_diff(n, abs(p - q))
    print("② 给 p-q:", set((a2, b2)) == {p, q})

    import time
    t0 = time.time()
    sols = from_xor(n, p ^ q, BITS + 2)
    cost = time.time() - t0
    print(f"③ 给 p^q: 解个数 = {len(sols or [])}，命中 = "
          f"{bool(sols) and set(sols[0]) == {p, q}}，耗时 {cost:.2f}s")
    assert set((a1, b1)) == {p, q} and set((a2, b2)) == {p, q}
    assert sols and set(sols[0]) == {p, q}

if __name__ == "__main__":
    main()
