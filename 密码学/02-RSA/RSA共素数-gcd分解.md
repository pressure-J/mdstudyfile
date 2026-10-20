---
tags: [crypto]
title: RSA共素数-gcd分解
created: '2026-09-08T12:00:00.000Z'
modified: '2026-09-08T12:00:00.000Z'
---

# RSA共素数攻击（共享素数 gcd 分解）

## 题型识别（一眼看出）
- 给了**多组 `(n, c)`**（常见 20+ 组），且 **e 固定**（常为 65537）
- 出题脚本形如：

```python
p = getPrime(512)          # 所有 n 共用一个 p
for i in range(...):
    q_i = getPrime(512)
    n_i = p * q_i          # 只有 q 不同
    c_i = pow(m, e, n_i)   # 同一个明文 m
```

**本质**：复用同一个素数 p 生成多个模数 → 任意两个 n 的 **gcd 就是 p**。

## 攻击条件
- 至少两个 n 共享素数（gcd ≠ 1）
- 拿到公共素数 p 后，`q = n/p` 即可完整分解

## 原理推导
$$n_1 = p \cdot q_1, \quad n_2 = p \cdot q_2 \Rightarrow \gcd(n_1, n_2) = p$$

两两求最大公约数，直接命中共享素数，**完全不需要分解大数**。

## 解题脚本
见 `D:\python\CTF工具箱\crypto\17-RSA共素数-gcd分解.py`
```python
from math import gcd
# NS=[n1,n2,...], CS=[c1,c2,...], E=65537  （同一下标一一对应）
p = gcd(NS[0], NS[1])        # 两两求 gcd 得共享素数
q = NS[0] // p
d = pow(E, -1, (p-1)*(q-1))  # 模逆
m = pow(CS[0], d, NS[0])
print(m.to_bytes(...))       # flag
```

## 易错点与区分
1. **优先 gcd，别先硬分解**：多组 n 的题，第一反应就是两两 `gcd`，秒出；不要 ECM 硬啃
2. **与"低指数广播"区分**：共享素数靠**多个 n 的 gcd**；低指数广播靠**多个 n + 小 e(3/5) + CRT 开方**。看 e 大(65537)→共享素数；e 小→广播
3. **p 必须与 n 互素才是素数**：若 gcd 得到的 p 是合数或不互素，此法退化为 rho 变体（见 `RSA共素数-rho变体-solve.py`）
4. 两个 n 解出的 m 应相同（同一明文），可互相校验

## 实战记录
- 来源：某多组 n 共素数题（21 组 n，e=65537）
- 第 5 组 n（2282203973...）与第 18 组 n（1959144138...）共享素数 p，gcd 秒出
- 结果：`flag{abdcbe5fd94e23b3de429223ab9c2fdf}`

*最后更新：2026年9月8日*
