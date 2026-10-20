---
tags: [crypto]
title: RSA-Wiener攻击
created: '2026-09-03T17:30:00.000Z'
modified: '2026-09-03T17:30:00.000Z'
---

# RSA — Wiener 攻击（低解密指数）

## 题型识别
看到的特征二选一即可怀疑：
- **e 非常大**（位数接近 n，比如 1024 位 n 配 1020 位 e）
- **d 很小**（构造脚本里 `d = getPrime(200)` 之类，或题目暗示"私钥短"）

## 适用条件
$$d < \frac{1}{3} n^{1/4}$$
理论根源：此条件下 $k/d$ 必然出现在 $e/n$ 连分数的收敛子里。

## 原理（核心推导，三行）
1. $ed \equiv 1 \pmod{\varphi(n)} \Rightarrow ed = 1 + k\varphi(n)$，故
$$\frac{e}{\varphi(n)} \approx \frac{k}{d} \quad,\quad \varphi(n) \approx n \quad\Rightarrow\quad \frac{e}{n} \approx \frac{k}{d}$$
2. $d < \frac13 n^{1/4}$ 时 $\left|\frac{e}{n} - \frac{k}{d}\right| < \frac{1}{2d^2}$ → 满足**连分数最佳逼近定理** → $k/d$ 是 $e/n$ 的某个**收敛子**
3. 遍历 $e/n$ 连分数的所有收敛子 $(k_i, d_i)$ 当候选：
   - $\varphi = (ed_i - 1)/k_i$ 需为整数
   - 由韦达定理：$p + q = n - \varphi + 1$，$pq = n$ → 解 $x^2 - (n-\varphi+1)x + n = 0$
   - **判别式是完全平方** → 得 $p, q$，验证 $pq = n$ 即成功

## 解题脚本
见同目录 `RSA-Wiener攻击-solve.py`（纯 Python 无依赖，填 `e/n` 即跑；留空则内置自测）。

## 验证记录（2026-09-03）
- 512 位 p、q + 200 位 d 的实例：**攻击耗时 1.57 ms**，p/q/d 完全恢复，解密还原 ✓
- 反例（标准 e=65537、d 正常）：正确返回失败（None）✓

## 易错点 / 经验
1. **k=0 的收敛子跳过**（除零/无意义）
2. **判别式 < 0 要 continue**，不是直接失败
3. 判别式平方根用 `isqrt`，不要用浮点 `int(sqrt())`（大数精度会炸）
4. 最终判据双重保险：判别式完全平方 **且** $p \cdot q = n$
5. d 不满足条件时攻击返回 None 属正常——**此时换 Boneh-Durfee**（放宽到 $d < n^{0.292}$，需要格基约化 LLL，学到格后再补）
6. 若题目给了 c，恢复 d 后直接 `m = pow(c, d, n)` 解密

## 面试速答卡
- **Q: Wiener 攻击的条件？** A: $d < \frac13 n^{1/4}$，e 通常很大
- **Q: 为什么连分数收敛子能找到 k/d？** A: 条件满足时 $e/n$ 与 $k/d$ 的距离 < $1/(2d^2)$，连分数最佳逼近定理保证 $k/d$ 是收敛子
- **Q: Wiener 和 Boneh-Durfee 的区别？** A: 同为低 d 攻击；Wiener 用连分数（$d < n^{1/4}/3$），BD 用格把界推到 $n^{0.292}$，需要 LLL

*最后更新：2026年9月3日*