---
tags: [crypto]
title: RSA-Wiener攻击
created: '2026-09-03T17:30:00.000Z'
modified: '2026-10-29T16:30:00.000Z'
---

# RSA — Wiener 攻击（低解密指数）

> **更正（2026-10-29）**：本笔记原来把「祥云杯 2022 common_rsa」当成 Wiener 例题，并贴了一段跑不出结果的脚本。
> 那道题**根本不是 Wiener**（出题人用了 `lcm(p-1,q-1)`，且 p-1、q-1 共享 320 位大因子 g），套本笔记的脚本必然失败：
> 实测 `e/n`、`e/(n±1)` 的 426 个收敛子逐个用 `pow(c, e*d, n) == c` 复验，**0 命中**。
> 原理与正解见 [[RSA-CommonPrime-CPRSA]]，第六节有摘要。

---

## 一、攻击成立的前提

RSA 中 `e` 与 `d` 满足：

$$e \cdot d \equiv 1 \pmod{\varphi(n)}$$

即存在整数 `k`，使得：

$$e \cdot d = k \cdot \varphi(n) + 1$$

**维纳攻击的成立条件：**

$$d < \frac{1}{3} n^{1/4}$$

> ⚠️ 这里的 `φ(n)` 必须是 $(p-1)(q-1)$。若出题脚本写的是 `lcm(p-1, q-1)`（即 λ），下面「用 n 近似 φ(n)」的推导直接作废 —— 这正是那道祥云杯题打不动的原因。

典型指纹：`e` 的位数和 `n` 同量级（$e \approx k\varphi/d$，d 很小时 e 被顶到与 φ 一样大）。

---

## 二、核心推导

### 第 1 步：构造逼近关系

由 $ed = k\varphi(n) + 1$，两边同除以 $d \cdot \varphi(n)$：

$$\frac{e}{\varphi(n)} = \frac{k}{d} + \frac{1}{d \cdot \varphi(n)}$$

即

$$\left| \frac{e}{\varphi(n)} - \frac{k}{d} \right| = \frac{1}{d \cdot \varphi(n)}$$

由于 `d` 和 `φ(n)` 都很大，右边误差项极小。

### 第 2 步：用 n 近似 φ(n)

已知 $\varphi(n) = n - (p+q) + 1$，且 $p+q-1 < 2\sqrt{n}$，可证：

$$\left| \frac{e}{n} - \frac{k}{d} \right| < \frac{2}{\sqrt{n}}$$

### 第 3 步：应用勒让德定理

> **勒让德定理**：若 $\left| \alpha - \frac{p}{q} \right| < \frac{1}{2q^2}$，则 $p/q$ 必为 $\alpha$ 的某个连分数收敛子。

当 $d < \frac{1}{3}n^{1/4}$ 时，可推出 $\frac{2}{\sqrt{n}} < \frac{1}{2d^2}$，定理条件满足。

**结论：`k/d` 一定是 `e/n` 连分数展开的某个收敛子。**

---

## 三、攻击流程图

```
┌──────────────────────────────────────────────────┐
│  输入：公钥 (n, e)，密文 c                         │
├──────────────────────────────────────────────────┤
│  1. 对 e/n 做连分数展开，逐个生成收敛子 p_i / q_i   │
│  2. 令 k = p_i, d = q_i                           │
│     过滤：(e·d - 1) % k == 0                      │
│  3. 算 φ = (e·d - 1) / k                          │
│  4. 令 s = n - φ + 1（应等于 p+q）                 │
│     验证：x² - s·x + n = 0 的判别式是完全平方      │
│  5. 解出 p, q 并校验 p·q == n                      │
│  6. 解密：m = c^d mod n                           │
└──────────────────────────────────────────────────┘
```

第 4 步的判别式校验是**决定性**的：它同时确认「(k,d) 找对了」和「φ 确实是 (p-1)(q-1)」。判别式不是完全平方就跳过，能挡掉所有错误的收敛子。

---

## 四、正确脚本（已自测通过）

本目录 `RSA-Wiener攻击-solve.py`：顶部填 `e` / `n`；留空运行则自动生成一组 d=200bit 的实例自测
（实测输出 `[自测通过] Wiener 攻击正确恢复 p, q, d`）。

核心函数：

```python
from math import isqrt

def cf_expand(a, b):                      # a/b 的连分数展开
    r = []
    while b:
        r.append(a // b)
        a, b = b, a % b
    return r

def convergents(cf):                      # 逐个产生收敛子 (分子, 分母)
    n0, d0, n1, d1 = 0, 1, 1, 0
    for q in cf:
        n2, d2 = q * n1 + n0, q * d1 + d0
        yield n2, d2
        n0, d0, n1, d1 = n1, d1, n2, d2

def wiener_attack(e, n):
    for k, d in convergents(cf_expand(e, n)):
        if k == 0 or (e * d - 1) % k != 0:
            continue
        phi = (e * d - 1) // k
        b = n - phi + 1                   # 希望是 p + q
        disc = b * b - 4 * n
        if disc < 0:
            continue
        s = isqrt(disc)
        if s * s != disc:                 # 判别式非完全平方 → 这个收敛子是假的
            continue
        p, q = (b + s) // 2, (b - s) // 2
        if p * q == n:
            return p, q, d
    return None
```

拿到 `d` 后 `m = pow(c, d, n)` 即可。

---

## 五、跑不出结果的排查顺序

| 现象 | 原因 | 下一步 |
|------|------|--------|
| 收敛子全被判别式挡掉 | d 不够小（$d > n^{1/4}/3$） | 换 Boneh–Durfee（格攻击，d < n^0.292） |
| `e` 很小、`d` 很大 | 这是「小 e」不是「小 d」 | 小 e 开方 / 广播 / 相关消息 |
| `e` 比 n 少一大截、`d` 明明很小 | 出题人用了 `lcm`，或 p-1、q-1 有大公因子 | **Wiener 无效**，看 [[RSA-CommonPrime-CPRSA]] |
| 解出的明文是乱码 | 找到的 d 是假的 | 用 `pow(c, e*d, n) == c` 复验 d |

> 复验 d 的通用技巧：合法 d 一定满足 `pow(c, e*d, n) == c`（因 $ed \equiv 1 \bmod \lambda$）。
> 它不依赖 φ 的具体形式，比「解判别式」更稳——排查「到底是不是 Wiener 题」时先跑这一句。

---

## 六、实例更正：祥云杯 2022 common_rsa 为什么打不动

原笔记贴的那组数据（n 1025 位 / e 703 位 / c）**不是 Wiener 题**。出题脚本（`0/task.py`）：

```python
def gen(g):
    bits = 512 - g.bit_length()
    while True:
        a = getPrime(bits)          # 192 位
        p = 2 * a * g + 1           # p-1 = 2ag
        if isPrime(p):
            return p

g = getPrime(320)                   # ★ p、q 共用同一个 320 位素数 g
p, q = gen(g), gen(g)               # q-1 = 2bg
n = p * q
d = getPrime(135)                   # d 确实很小……
phi = lcm(p - 1, q - 1)             # ★ 但 φ 是 λ = 2gab，不是 (p-1)(q-1)
e = inverse(d, phi)
```

两个致命差异，任何一个都让 Wiener 失效：

1. **目标分数错了**：`ed - 1 = k·λ`，而 $\lambda = 2gab \approx n/(2g)$，所以
   $k/d \approx e/\lambda \approx 2g \cdot e/n$ —— 是 `e/n` 的 $2g \approx 2^{321}$ 倍，压根不是它的收敛子。
   （更精确地：$k/(gd)$ 与 $2e/n$ 的误差约 $2^{-833}$，而勒让德要求 $< 2^{-911}$，差约 78 位，所以也不是「最佳逼近」，连分数拿不到。）
2. **校验式错了**：即使捞到 (k,d)，`s = n - φ + 1` 里的 φ 若是 λ，`s ≠ p+q`，判别式永远不是完全平方。

正解是格子攻击（Jochemsz–May 多元 Coppersmith），见 [[RSA-CommonPrime-CPRSA]]。

---

## 七、一句话总结

> 由 $ed = k\varphi + 1$ 推出 $\frac{e}{n} \approx \frac{k}{d}$，误差小于 $\frac{1}{2d^2}$；根据**勒让德定理**，$\frac{k}{d}$ 必为 $\frac{e}{n}$ 连分数展开的某个收敛子，枚举收敛子即可恢复私钥 `d`，全程无需分解 `n`。
> —— 前提是 φ 就是 (p-1)(q-1)，且 e 与 n 同量级。

---

## 八、超出 Wiener 边界：Boneh-Durfee（d < n^0.292）

Wiener 能用的区间是 `d < n^0.25/3`。若题面的 d 只比这大一点（如 `d ≈ n^0.27`），连分数就捞不到 `k/d` 了：

- **Wiener**：把 `ed − 1 = kφ` 化成 `e/n ≈ k/d`，靠勒让德定理（误差 < 1/(2d²)）从连分数收敛子里捞；
- **Boneh-Durfee**：不近似，联立 `ed − 1 = kφ` 与 `φ = n − (p+q) + 1`（记 `s = p+q`），得二元多项式
  $$1 + x\,(n+1-y) \equiv 0 \pmod e,\qquad x = k,\; y = s$$
  再用二元 Coppersmith（构造格 + LLL）同时求小根；
- **界**：`d < n^0.292` 可行（渐近结果，实际参数略保守）。超过 0.292 就不是"小 d"题。

**实战口径**：`e ≈ n` 且 d 落在 0.25～0.292 之间 → 认出是 BD，记一句"超 Wiener 边界，需二元格"就跳。参数调优（m、t、X、Y）够磨一整天，性价比极低。
