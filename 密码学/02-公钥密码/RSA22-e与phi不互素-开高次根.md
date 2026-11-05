---
tags: [crypto, rsa]
title: RSA-e与phi不互素-开高次根
created: '2026-10-24T20:05:00.000Z'
---

# RSA：e 与 φ(n) 不互素（e=1024）开根

> 题目：rsa1024（DASCTF 练习）。费马分解 4 步命中 + 非互素指数开根，脚本在
> `D:\python\CTF工具箱\challenges\rsa1024\solve.py`，flag 实测解出。

## 一、题型识别

```python
e = 1024          # 不是 65537！出题人用"主题数字"当指数
n = p * q         # 1024-bit, p、q 几乎相邻（费马分解）
c = pow(m, e, n)
```

两个信号叠在一起：
1. **e 是 2 的幂**（1024 = 2^10），而素数 p-1 一定是偶数 → `gcd(e, p-1)` ≥ 2，**几乎不可能互素**；
2. 正常解密 `d = pow(e, -1, phi)` 会直接抛 `ValueError: base is not invertible` —— 见到这个报错就别再去修 n、c，转非互素开根。

## 二、机制：为什么不能直接求 d

RSA 解密本质是在模 φ(n) 的乘法群里求 e 的逆元，**逆元存在的充要条件是 gcd(e, φ)=1**。
本题 `gcd(1024, φ) = 2`（φ 里 2 的因子只有 1 个，1024 里有 10 个），逆元不存在，
但**方程 x^1024 ≡ c (mod n) 仍然有解**——只是解不唯一：

- 在模素数 p 下，`x^e = c` 恰有 `g_p = gcd(e, p-1)` 个根（前提：`c^((p-1)/g_p) ≡ 1 (mod p)`，即 c 是 e 次剩余；本题 g_p = 2）；
- q 同理 g_q = 2；
- CRT 合并 → **共 g_p × g_q = 4 个候选明文**，其中只有 1 个是真实 flag，靠结构（可读 ASCII、`.` 填充）+ roundtrip 验证挑出来。

直觉：群里的"开方"本来就有 ±两个根，开更高次方根的个数按 gcd 增长。

## 三、解法（e 是 2 的幂时：逐层开平方）

不用背完整 AMM 算法——e = 2^k 时有个简单等价形式：**从 c 开始逐层开平方，开 k 层**。
正确性：若 x^e = c，则 x^(e/2) 是 c 的一个平方根；对每个平方根再开平方……每层根数最多翻倍，
开不出平方（非剩余）的分支直接剪掉，末层用 `pow(r, e, p) == c` 过滤出真根。

```python
import math, itertools
from gmpy2 import mpz, isqrt, powmod, invert

def sqrt_all(a, p):
    """模素数 p 开平方的全部根（p%4==3 走公式；否则 Tonelli-Shanks）"""
    a %= p
    if a == 0: return [mpz(0)]
    if powmod(a, (p - 1) // 2, p) != 1: return []      # 非剩余，无根
    if p % 4 == 3:
        r = powmod(a, (p + 1) // 4, p)
        return [r, (p - r) % p]
    # Tonelli-Shanks ...
    q_, s = p - 1, 0
    while q_ % 2 == 0: q_ //= 2; s += 1
    z = mpz(2)
    while powmod(z, (p - 1) // 2, p) != p - 1: z += 1
    m, cc, t, r = s, powmod(z, q_, p), powmod(a, q_, p), powmod(a, (q_ + 1) // 2, p)
    while t != 1:
        i, t2 = 0, t
        while t2 != 1: t2 = t2 * t2 % p; i += 1
        b = powmod(cc, 1 << (m - i - 1), p)
        m, cc = i, b * b % p
        t = t * cc % p; r = r * b % p
    return [r, (p - r) % p]

def roots_pow2(c, e, p):
    """x^e = c (mod p)，e = 2^k：逐层开平方 k 层，返回全部 gcd(e,p-1) 个根"""
    c %= p
    roots = [mpz(c)]
    for _ in range(e.bit_length() - 1):
        nxt = []
        for r in roots: nxt.extend(sqrt_all(r, p))
        roots = nxt
        if not roots: return []
    return sorted({r for r in roots if powmod(r, e, p) == c})

# 每个模下取根，CRT 合并 4 组
rp, rq = roots_pow2(c, e, p), roots_pow2(c, e, q)
qinv = invert(q, p)
for xp, xq in itertools.product(rp, rq):
    m = int((xq + q * ((xp - xq) * qinv % p)) % n)
    if pow(m, e, n) != int(c): continue          # roundtrip 验证
    print(m.to_bytes((m.bit_length() + 7) // 8, 'big'))
```

通用 e（含奇因子）时才需要完整 AMM / Sage 的 `Zmod(p)(c).nth_root(e, all=True)`；
本题 e 纯 2 的幂，逐层开平方就够了。

## 四、本题其他两个考点（已覆盖，链一下）

- **费马分解**：题面"两个素数几乎同一时刻出生、只在很小抖动范围内找下一个"→ p、q 差距极小
  （实测 |p-q| ≈ 5.6×10^77，约 256 位，但对 512 位素数来说"极小"）→ 从 ⌈√n⌉ 起试 `a²-n` 是否完全平方，
  **4 步命中**。机制与题型识别见 [[素数分解]] 第二节。
- **明文填充**：`FLAG.ljust(127, b".")` 把 flag 右侧补点到 127 字节 —— 解出的明文尾部一长串 `.`
  不是噪声，是题目的冗余设计，也正好当结构筛选的指纹（4 个候选里唯一"整段可读"的那个就是它）。

## 踩坑

- **`pow(e, -1, phi)` 报 not invertible 不是坏数据**：是 gcd(e,φ)≠1 的正常信号，第一反应查 `gcd(e, p-1)`，别去怀疑 n、c 抄错。
- **CRT 合并出的 4 个候选都要过 `pow(m,e,n)==c`**：数学上 4 个全应通过（它们都是真根），
  实测确实 4 个全过 roundtrip —— **roundtrip 只能证明"是真根"，不能证明"是 flag"**，最后一步挑 flag 靠结构
  （可读 ASCII / 填充特征）。
- **`execute_code` 的沙箱内核没有 gmpy2/sympy**：这类题直接写进 `challenges/<题名>/` 用本机 `py` 跑，
  别在沙箱里撞 `ModuleNotFoundError`。
