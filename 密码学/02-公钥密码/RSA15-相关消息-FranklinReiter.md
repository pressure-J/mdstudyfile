---
tags: [crypto]
title: RSA15-相关消息-FranklinReiter
created: '2026-11-03T13:10:00.000Z'
modified: '2026-11-03T13:10:00.000Z'
---

# RSA — 相关消息攻击（Franklin-Reiter）

## 题型识别（一眼看出）

- 同一个 `n`、同一个 `e`，给了**两组密文** `c1, c2`；
- 两个明文有**已知线性关系**：`m2 = a·m1 + b`（题面直接给 `a`、`b`，或说"同一消息的两种填充"）；
- `e` 很小（3、5 这类），e 大时多项式次数会爆炸。

与共模攻击的区别：共模是**同 n 不同 e、同一 m**；这里是**同 n 同 e、不同但相关的 m**。

## 原理

`m1` 是 `f(x) = x^e − c1` 在模 n 下的根；由 `c2 = (a·m1 + b)^e`，`m1` 也是 `g(x) = (a·x+b)^e − c2` 的根。

所以 `f` 与 `g` 在 `Z_n[x]` 上有公因子 `x − m1`：

$$
\gcd\bigl(x^e - c_1,\;(ax+b)^e - c_2\bigr) = x - m_1
$$

首一化后常数项取负就是 `m1`。`e=3` 时两个三次多项式做一次欧几里得除法就结束。

## 代码（核心，脚本全文见同目录 `RSA15-相关消息-FranklinReiter-solve.py`）

```python
def pmod(a, m, n):              # a mod m，系数在 Z_n 上
    a, dm = a[:], len(m) - 1
    inv = pow(m[-1], -1, n)     # 首项不可逆会抛 ValueError，见易错点 1
    while len(a) > dm:
        d = len(a) - 1 - dm
        coef = a[-1] * inv % n
        for i in range(dm + 1):
            a[d + i] = (a[d + i] - coef * m[i]) % n
        ptrim(a, n)
    return ptrim(a, n)

f = [(-c1) % n, 0, 0, 1]                          # x^3 - c1
g = [(A*x + B)^e - c2 的展开]                      # 逐次 pmul 更省心
h = pgcd(f, g, n)                                 # 首一化后 = x - m1
m1 = (-h[0]) % n
```

## 易错点

1. **`Z_n[x]` 不是域**：欧几里得除法要除首项系数，而模 n 下可能不可逆（n 是合数）。捕获 `ValueError` 后换一组 `(a,b)` 重试，概率很低但一定会遇到。
2. `e` 只能小。`e=65537` 时两个多项式都是 6 万次，直接放弃——那种题面不是这条路。
3. 关系式必须精确。`m2 = m1 + b` 就是 `a=1`；若题面给的是"同一消息不同 padding"，先把两段 padding 的关系写成线性式再套。
4. 多项式乘法别手写嵌套循环求幂，用重复平方（`ppow`），否则 e 稍大就卡死。

## 验证记录（2026-11-03，实测输出）

```text
n bits = 511  e = 3
题目给定: n, e, c1, c2, a, b（不知道 m1、m2）
gcd 次数 = 1  恢复 m1 = 0x30c2a5b56c73ea70b92da6 ...
m1 与原值一致: True
m2 复原: True
```

结论：两次密文做一次多项式 gcd 即出明文，耗时毫秒级；`gcd` 结果次数恒为 1（首一化后即 `x − m1`）。

*最后更新：2026年11月3日*
