# -*- coding: utf-8 -*-
"""RSA44 素数可预测（时间戳 / 固定种子）—— 自验证脚本
题型：生成脚本里出现 random.seed(int(time.time())) 或固定种子，
      题目给 n 和大致时间（或直接给种子范围），复现随机数流即可得到 p。
换题只改「题目数据」一段。
"""
import random
import time
from math import gcd
from sympy import nextprime

# ================= 题目数据（换题改这里） =================
SEED0 = 1767225600          # 题目时间戳（2026-01-01 00:00:00 UTC 左右）
WINDOW = 300                # 题目只给了「大约几点」，向前后各爆 5 分钟（按需放大）
BITS = 512
# ===========================================================

def gen_with_seed(seed, bits=BITS):
    """复现出题脚本的素数生成：固定 seed + getrandbits + nextprime"""
    rnd = random.Random(seed)
    p = nextprime(rnd.getrandbits(bits))
    q = nextprime(rnd.getrandbits(bits))
    return p, q

def attack(n, seed0, window):
    for seed in range(seed0 - window, seed0 + window + 1):
        p, _ = gen_with_seed(seed)
        if n % p == 0:
            return p, n // p, seed
    return None

def main():
    real_seed = SEED0 + 137                     # 出题人当时的真实秒数（题目不给）
    p, q = gen_with_seed(real_seed)
    n = p * q
    print("n bits =", n.bit_length(), " 给定窗口 =", 2 * WINDOW + 1, "个候选种子")

    t0 = time.time()
    r = attack(n, SEED0, WINDOW)
    cost = time.time() - t0
    assert r, "窗口内没命中，扩大范围或确认取素方式（getrandbits 位数/是否 nextprime）"
    a, b, seed = r
    print(f"命中 seed={seed}（真实 {real_seed}），耗时 {cost:.2f}s")
    print("分解成功:", set((a, b)) == {p, q})
    assert set((a, b)) == {p, q}

if __name__ == "__main__":
    main()
