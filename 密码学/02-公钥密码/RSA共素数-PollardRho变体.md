---
tags: [crypto]
title: RSA共素数-PollardRho变体
created: '2026-09-03T16:30:00.000Z'
modified: '2026-09-03T16:30:00.000Z'
---

# RSA共素数 (Common Prime) — Pollard Rho 变体

## 题型识别
出题脚本形如：

```python
g = getPrime(int(nbits * gamma))                  # 公共大素数, 约 0.48*nbits 位
a = getRandomNBitInteger(int(alpha * nbits))      # 小量, 约 0.02*nbits 位
p = 2 * g * a + 1
b = getRandomNBitInteger(int(alpha * nbits))
q = 2 * g * b + 1
n = p * q
```

特征三件套：
- **p-1 和 q-1 共享大素数因子 g**（几百位，`getPrime(int(nbits*gamma))`）
- **a、b 很小**（`getRandomNBitInteger(int(alpha*nbits))`，alpha 通常 0.02 → 20 位）
- **gcd(a,b)=1**（保证 gcd(p-1, q-1) = 2g 精确成立）
- n 位数正常，共模/低指数/直接分解均无效

## 攻击核心：Pollard rho 变体
标准 rho 期望 O(√p) ≈ 2^256 步，对 1024 位 n 不可行。
**把迭代函数换成**：

$$f(x) = (x^{n-1} + 3) \bmod n$$

### 为什么快（两行数学）
1. 阶公式：$\operatorname{ord}(x^{k}) \mid \dfrac{p-1}{\gcd(p-1,\, k)}$。取 $k = n-1$：$\gcd(p-1, n-1) = \gcd(p-1, q-1) = 2g$（因 gcd(a,b)=1）
2. 所以 $x^{n-1} \bmod p$ 的**阶整除 $(p-1)/2g = a$**（a 仅 20 位）→ **一次迭代后序列落入 ≤2^20 个元素的小子群**；模 q 同理落入 ≤2^20 的 b 阶小子群 → ρ 碰撞约 √2^20 ≈ 2^10 步内出现 → `gcd(|a-b|, n)` 秒级捞到 p

**+3 是微扰**：防止序列退化（落入不动点/短环）。

⚠️ 加速的真正关键不是"共享因子 g 大"（g 只保证 gcd(p-1,q-1) 精确 = 2g），而是 **a、b 小 → 剩余子群小 → 碰撞空间小**。

实测：1024 位 n **约 6~21 秒**出 p、q（耗时看随机起点，最快 1.5s，串行重试在最坏起点可能更久；真实题目规模偶发 30s+，属正常）。

## 解题脚本
见同目录 `RSA共素数-rho变体-solve.py`，换题只改 `n/e/c` 三行。

## 易错点 / 实战经验
1. **不要走"分解 n-1 找 g"的弯路**：虽然 n-1 = 2g·h（h = 2gab+a+b，且 h mod 2g = a+b）数学上成立，但分离 g 需要 ECM 硬分解几百位大数——**CTF 出题人不会出算不出来的题**，正解永远是 rho 变体直接在 n 上跑
2. **运行环境**：脚本需要 `gmpy2` + `pycryptodome`——`py`（Python 3.12.6）两者都有，直接 `py xxx.py` 跑。~~旧笔记写的 `D:\Sagemath\python.exe` 已不存在（那是被卸载的 Miniconda，不是 SageMath）~~，SageMath 实际在 `C:\Users\徐利杰\AppData\Local\SageMath 9.3\`，调用方法见 [常用函数](../常用函数.md)
3. 若题目未保证 gcd(a,b)=1，rho 多跑几轮随机起点即可（脚本 while True 循环自动重试）

## 实战记录
- 来源：共素数 RSA 题（nbits=1024, gamma=0.48 → g 491 位, a/b 20 位）
- e = 58337（16 位小素数）
- p、q 均为 512 位素数
- FLAG: `SangFor{0a8c2220-4c1b-32c8-e8c1-adf92ec7678b}`

*最后更新：2026年9月3日*