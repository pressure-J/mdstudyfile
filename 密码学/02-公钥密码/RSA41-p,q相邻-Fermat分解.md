---
tags: [crypto]
title: RSA41-p,q相邻-Fermat分解
created: '2025-10-26T08:24:36.356Z'
modified: '2026-09-16T12:30:00.000Z'
---

# 素数分解

## 一、基本情况（小素数直接分解）
如果给定素数小于 256 位，通常可以通过 sympy、gmpy2 等库直接分解：

```python
from sympy import factorint
n = 1234567
w = factorint(n)
print(w)
```

## 二、Fermat 分解（p、q 相邻 / nextprime 场景）

### 题型识别
构造脚本里出现 `nextprime`，即 p、q 是**相邻素数**（中间没有其他素数）：

```python
p = sympy.nextprime(secret_num)
q = sympy.nextprime(p)        # q 紧跟在 p 后面 → q - p 很小
```

或提示"p、q 很接近""n 接近完全平方数"。

**本质**：`nextprime` 保证 `q = p + 素数间隔`，1024 位量级素数间隔约 `ln(2^1024) ≈ 710`，所以 `p ≈ q ≈ √n` → n 非常接近完全平方 → 可用 Fermat 分解**秒破**。

### 原理
用平方差把 n 写成两平方之差：

$$n = \left(\frac{p+q}{2}\right)^2 - \left(\frac{p-q}{2}\right)^2 = a^2 - b^2$$

其中 $a=\frac{p+q}{2}\approx\sqrt n$，$b=\frac{p-q}{2}$ 很小。从 $a=\lceil\sqrt n\rceil$ 起递增，检查 $a^2-n$ 是否为完全平方；命中即 $p=a-b,\ q=a+b$。

因为 $b$ 极小，迭代次数约 $\dfrac{(p-q)^2}{8n}$，通常几步甚至**一次就命中**。

### 代码
```python
from math import isqrt          # Python 3.8+ 自带整数开方，无需 gmpy2

def fermat(n):
    a = isqrt(n)
    if a * a < n:
        a += 1
    while True:
        b2 = a * a - n
        b = isqrt(b2)
        if b * b == b2:
            return a - b, a + b     # p, q
        a += 1

if __name__ == "__main__":
    n = ...                          # 填入题目给的 n
    p, q = fermat(n)
    assert p * q == n
    print(p, q)
```

### 易错点
1. 用 `math.isqrt`（整数开方）或 `gmpy2.isqrt`，**别用浮点 `math.sqrt`**，2048 位数会丢精度。
2. 判据必须是 `b*b == b2`（完全平方），不能只看近似。
3. p、q 差距越小越快；若差距大（如随机两个 1024 位素数），Fermat 会退化到 $O(\sqrt n)$，不可用。
4. `nextprime` 是**严格大于**参数的素数，所以 `q = nextprime(p)` 保证 p、q 之间无其他素数。

### 验证记录（2026-09-16）
- 用 `random.getrandbits(1024)` 造 secret → `p = nextprime(secret)`、`q = nextprime(p)`，n = p·q
- 实测 `q - p = 104`，Fermat 分解 **0 次迭代（一步命中）**，耗时 < 0.01s；`nextprime` 造题本身耗时 0.35s
- 恢复的 p、q 与原值一致 ✓

*最后更新：2026年9月16日*
