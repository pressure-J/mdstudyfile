---
tags: [crypto, rsa]
title: RSA-dp泄露家族
created: '2026-09-06T12:00:00.000Z'
modified: '2026-09-06T12:00:00.000Z'
---

# RSA-dp泄露家族

## 题型识别（一眼看出）

**本质**：dp = d mod (p-1)（dq = d mod (q-1)）泄露。出题人用 CRT 优化 RSA 时拆出的"影子密钥"送人了 → 解密能力白给。

| 变体 | 给了什么 | 打法 |
|---|---|---|
| **dp+dq 泄露** | `p, q, dp, dq, c` | 费马小定理在 p/q 下各解半截 + CRT 合并（**不需要 e 和 n**） |
| **dp-only 泄露** | `e, n, dp, c` | 爆破 k：e·dp−1 = k(p−1)，k < e → 试除 n 找 p（不需要 dq） |

## 变体一：dp+dq（CRT 合并）

### 原理推导
CRT-RSA 优化时，解密拆成两半更快：
$$m_1 = c^{dp} \bmod p,\quad m_2 = c^{dq} \bmod q$$

泄露后攻击者自己也能算这两个半截。由费马小定理（注意 $dp \equiv d \pmod{p-1}$）：
$$c^{dp} \equiv c^d \pmod p,\quad c^{dq} \equiv c^d \pmod q$$

即 m1 = m mod p，m2 = m mod q。**中国剩余定理合并**（x ≡ m1 mod p 且 x ≡ m2 mod q）：
$$m = m_1 + p \cdot \left((m_2 - m_1) \cdot p^{-1} \bmod q\right) \bmod (p \cdot q)$$

### 脚本
`RSA-dp_dq泄露-solve.py`（换题只改 p/q/dp/dq/c 五个数）
```python
m1 = pow(c, dp, p)
m2 = pow(c, dq, q)
inv_p = pow(p % q, -1, q)          # p 在模 q 下的逆
m = (m1 + p * (((m2 - m1) % q) * inv_p % q)) % (p * q)
print(m.to_bytes((m.bit_length()+7)//8, 'big').decode())
```

## 变体二：dp-only（k 爆破）

### 原理推导
由 $d \cdot e \equiv 1 \pmod{(p-1)(q-1)}$，模 p-1 下依然有：
$$e \cdot dp \equiv 1 \pmod{p-1} \;\Rightarrow\; e \cdot dp - 1 = k(p-1)$$

**k 的上界可控**：dp < p-1 ⟹ k < e = 65537。爆破 k 从 1 到 e：
$$p = \frac{e \cdot dp - 1}{k} + 1$$
每次检查 **n % p == 0**，命中即得 p。之后再走 RSA 常规：q = n//p，φ = (p−1)(q−1)，d = e⁻¹ mod φ，m = c^d mod n。

### 脚本
`RSA-dp泄露-solve.py`（换题只改 e/n/dp/c 四个数）
```python
x = e * dp - 1
for k in range(1, e + 1):
    if x % k == 0:
        p = x // k + 1
        if n % p == 0:              # 命中
            q = n // p
            d = pow(e, -1, (p-1)*(q-1))
            m = pow(c, d, n)
```

## 实战记录
- dp+dq 题：明文 `noxCTF{W31c0m3_70_Ch1n470wn}`
- dp-only 题：k=4404 命中，明文 `flag{wow_leaking_dp_breaks_rsa?_98924743502}`，秒出

## 易错点
1. **dp 和 d 别搞混**：dp 是 "d mod (p-1)"，不是 d 本身；它只在模 p-1 的世界里有意义
2. **dp+dq 不需要 e/n**：五件套里压根没有 e 和 n，别去找（也找不到）
3. **CRT 合并的 p⁻¹ 是模 q 的逆**：`pow(p % q, -1, q)`，不是模 p*q
4. **爆破 k 要检查整除**：`e*dp-1` 必须能被 k 整除，cand 才是整数；整除且 n%cand==0 双条件才算命中
5. **dp-only 若爆破不到**：确认 dp < p-1 成立（题给的 dp 通常已满足）；极端情况可放宽 k 到 2e
6. 解出的 m 转字节用 `(m.bit_length()+7)//8` 定长，防止去前导零丢字符

## 相关脚本
- `RSA-dp_dq泄露-solve.py`：dp+dq 变体模板
- `RSA-dp泄露-solve.py`：dp-only 变体模板