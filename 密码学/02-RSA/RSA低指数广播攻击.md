---
tags: [crypto]
title: RSA低指数广播攻击
created: '2026-09-08T12:00:00.000Z'
modified: '2026-09-08T12:00:00.000Z'
---

# RSA低指数广播攻击（Håstad Broadcast Attack）

## 题型识别（一眼看出）
题目给 **多对 `(N, c)`**（常见三对），且都是同一明文、同一个小的公钥指数 e 加密：

- 给了三组 `N1/c1, N2/c2, N3/c3`（也可能更多），`N` 两两不同且互素
- 出题脚本形如：

```python
c1 = pow(m, e, N1)
c2 = pow(m, e, N2)
c3 = pow(m, e, N3)   # 同一个 m、同一个 e
```

**本质**：明文太短，`m^e` 没有触到任何一个 N，于是跨模数之间**没有"模"截断**——中国剩余定理能把它们精确拼回 `m^e`，再开 e 次方即得明文。

## 攻击条件
- 拿到 e 组 `(N, c)`，且这些 N 两两互素
- 要求 `m^e < N1*N2*...*Ne`（明文足够小、e 足够小才满足，一般 e=3 配三组即可）

## 原理推导
若直接开根，`m^e` 每次都被 `mod Ni` 破坏。但由加密关系：
$$c_i \equiv m^e \pmod{N_i}$$

按中国剩余定理构造唯一的 `M`：
$$M \equiv c_i \pmod{N_i},\quad M = m^e$$

**因为 `m^e < N1*N2*N3`，CRT 解出的 M 就是没有取模的真值**，直接整数开 e 次根：
$$m = \sqrt[e]{M}$$

## 解题脚本（纯 Python，无第三方依赖）
```python
from functools import reduce

# ① 先还原进制：本题数字只含 0-4 → 其实是 5 进制，int(s, 5) 转回十进制
N1 = int('33131032...', 5)   # 每串 441 位 5 进制 ≈ 1024 bit
c1 = int('31002000...', 5)
N2, c2, N3, c3 = ...
# 若本来就是十进制大整数，直接 int(...) 即可

# ② 中国剩余定理合并
def crt(a, m):
    M = reduce(lambda x, y: x * y, m)
    s = 0
    for ai, mi in zip(a, m):
        Mi = M // mi
        s += ai * Mi * pow(Mi, -1, mi)
    return s % M

M = crt([c1, c2, c3], [N1, N2, N3])

# ③ 整数开 e 次方（牛顿迭代，纯整数，不溢出）
def iroot(n, k):
    if n == 0: return 0, True
    x = 1 << ((n.bit_length() + k - 1) // k)   # 初始估计 x ≈ n^(1/k)
    while True:
        y = ((k - 1) * x + n // x ** (k - 1)) // k
        if y >= x: break
        x = y
    return x, x ** k == n

m, ok = iroot(M, 3)
assert ok, "不是整立方 → 攻击条件不满足或 e 猜错"
flag = m.to_bytes((m.bit_length() + 7) // 8, 'big').decode()
print(flag)
```

## 易错点
1. **进制陷阱**：题面数字只含 0-4/0-7 等小集合时，先怀疑是 5/8 进制（本题 441 位"5 进制"还原后恰是 1024 bit 标准 RSA，长度对上是强信号）。直接按十进制解读会全错
2. **开方溢出**：几百上千位大数用 `x ** (1/3)` 会 `OverflowError: int too large to convert to float`，必须用**纯整数牛顿迭代**（初始估计用 `1 << (bit_length/k)`）
3. **e 不一定给明**：先试 3，不行试 5/7；若 M 开根余数不为 0 说明 e 猜错
4. **易与共模攻击混淆**：共模是"多 e 单 n"；广播是"多 n 单 e"。看给的是**多个模数**还是**多个指数**
5. **gcd(Ni,Nj) ≠ 1 时的另一路**：若 N 间有公因子，优先走"共素数"分解而非广播，先跑一遍两两 gcd 再决定

## 实战记录
- 来源：noxCTF（flag 格式 `noxCTF{...}`）
- 本题三串数字全由 0-4 构成，为 5 进制；`int(s, 5)` 后 N 均为 1024 bit
- 三 N 两两 gcd = 1（无公因子），e=3 成立，CRT 后 M ≈ 1101 bit
- 结果：`noxCTF{D4mn_y0u_h4s74d_wh47_4_b100dy_b4s74rd!}`

*最后更新：2026年9月8日*
