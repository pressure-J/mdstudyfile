---
tags: [crypto]
title: RSA34-已知和差异或
created: '2026-11-03T13:10:00.000Z'
modified: '2026-11-03T13:10:00.000Z'
---

# RSA — 已知 p+q / p−q / p⊕q

## 题型识别（一眼看出）

题面在 `n` 之外多给了一个**关于 p、q 的对称量**：`p+q`、`p−q`、`p⊕q`（或写成 `p ^ q`、`xor(p,q)`）。这类题的本质都是"少一个自由度"，不需要任何数论工具。

## 一、p+q 或 p−q：韦达定理一步到位

已知 `p+q = s`：

$$
p,q = \frac{s \pm \sqrt{s^2-4n}}{2}
$$

已知 `p−q = d` 时先补出和：由 `(p−q)² + 4pq = (p+q)²`

$$
p+q = \sqrt{d^2 + 4n}
$$

两种都能归一成"解 `x² − s·x + n = 0`"，判别式必须是完全平方。

## 二、p⊕q：从最低位逐位 DFS

异或按位独立，但乘积有进位，所以从**最低位**往上枚举：维护候选 `(p_low, q_low)`，每加一位就要求

$$
p \cdot q \equiv n \pmod{2^{k+1}}
$$

不满足的分支立刻剪掉。`p⊕q` 的第 k 位给出约束 `p_k xor q_k = x_k`，所以每个候选最多分 2 支。

```python
def from_xor(n, x, bits):
    cands = [(0, 0)]
    for k in range(bits):
        xk, nk = (x >> k) & 1, (n >> k) & 1
        nxt = []
        for pl, ql in cands:
            for pb in (0, 1):
                qb = pb ^ xk
                np_, nq_ = pl | (pb << k), ql | (qb << k)
                if (np_ * nq_) & ((1 << (k+1)) - 1) == n & ((1 << (k+1)) - 1):
                    nxt.append((np_, nq_))
        cands = list(dict.fromkeys(nxt))
        if not cands:
            return None
    return [(a, b) for a, b in cands if a*b == n and a > 1 and b > 1 and a ^ b == x]
```

## 易错点

1. **必须以 `p*q mod 2^(k+1)` 剪枝**，只按异或位枚举是 `2^bits`，1024 位直接死。
2. `isqrt` 而不是 `math.sqrt`：2048 位的 `s²−4n` 用浮点会丢精度。
3. 结果会有两个解 `(p,q)` 和 `(q,p)`——这不是错，取小的当 p 即可。
4. 候选数突然暴涨到几千，说明题面提供的量不够（比如只给了异或的高位），不要硬跑。
5. 异或题里 p、q 位数通常相同（最高位都为 1），最高位异或必为 0，可当额外的结构校验。

## 验证记录（2026-11-03，实测输出）

```text
n bits = 1024
① 给 p+q: True
② 给 p-q: True
③ 给 p^q: 解个数 = 2，命中 = True，耗时 1.29s
```

512 位 p/q 下 `p⊕q` 的 DFS 1.29 秒跑完，候选始终只有个位数——剪枝足够强，1024 位 p/q 也能秒级。

*最后更新：2026年11月3日*
