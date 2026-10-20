---
tags: [crypto]
title: RSA-p减1光滑-Pollard p-1
created: '2026-09-17T10:00:00.000Z'
modified: '2026-09-17T10:00:00.000Z'
---

# RSA — p−1 光滑 (Pollard p−1 攻击)

## 题型识别
出题脚本形如：

```python
from random import choice
from Crypto.Util.number import isPrime, sieve_base as primes

def getPrime(bits):
    while True:
        n = 2
        while n.bit_length() < bits:
            n *= choice(primes)      # 反复乘"小素数"
        if isPrime(n + 1):
            return n + 1             # p = n + 1  =>  p-1 = 小素数之积
```

特征：
- 素数不是随机生成的，而是**「小素数连乘 + 1」** → **p−1 / q−1 的所有素因子都很小（光滑 / smooth）**
- 小素数取自 `sieve_base`（本机实测 10000 个，最大 **104729**）
- n 很大（本题 4096 位），普通分解 / 共模 / 低指数 / Wiener 全部无效
- 关键点：**n 大 ≠ 安全，p−1 光滑就完蛋**

## 攻击核心：Pollard p−1

原理（两行数学）：
若 p−1 的所有素因子 ≤ B（即 p−1 是 B-smooth），取指数 $M$ 使 $p-1 \mid M$，则对任意与 p 互素的 $a$：

$$a^{M} \equiv 1 \pmod p \;\Longrightarrow\; p \mid (a^{M}-1) \;\Longrightarrow\; \gcd(a^{M}-1,\; n) \text{ 得到 } p$$

$M$ 的取法：$M = \prod_{p_i \le B} p_i^{e_i}$，其中 $e_i \ge p_i$ 在 p−1 中的重数。

**实现要点（增量法）**：
- p−1、q−1 都在**同一批**小素数上光滑 → 若一把算 $a^M$，可能 p、q 同时整除 → `gcd = n` 失败
- 所以**逐个素数累乘**，每步检查：
  ```
  a ← a^(p_i^E) mod n
  g = gcd(a - 1, n)
  1 < g < n  →  命中
  ```
- 谁的小素因子先被凑齐，就先套出谁

## 关键坑（实测踩过）

1. **指数别取满！** 若按 $p_i^{\lceil 2048/\log_2 p_i \rceil}$ 去覆盖"最大可能重数"，每次 modexp 指数都 ~2048 位，1 万次 → **10 分钟都跑不完**（我第一次就这么超时）。
   正解：p−1 是**随机取** ~130 个素数连乘，同一素数几乎不重复，取 $p_i^{8}$ 足够 → 指数仅 ~128 位 → **秒级**。
2. `gcd == n`（两因子同时完成）时，**换底数** `a = 3, 5, 7...` 重试即可。
3. 要跑到**最大素因子**处才命中：本题在第 9838 个素数（102797）才套出 p —— 别以为跑一半没结果就是方向错。
4. 运行环境：只需 `pycryptodome`（系统 `py` 即可），不必上 gmpy2 / ECM。

## 解题脚本
见同目录 `RSA-p减1光滑-Pollardp-1-solve.py`，换题只改 `n / e / c` 三行。

## 实战记录
- 来源：NCTF 类题；n 4096 位，p / q 各 2048 位
- p−1 = 若干 ≤ 104729 小素数之积
- 命中：`base=2`，第 9838 个素数（102797）
- FLAG：`NCTF{Th3r3_ar3_1ns3cure_RSA_m0duli_7hat_at_f1rst_gl4nce_appe4r_t0_be_s3cur3}`

*最后更新：2026年9月17日*
