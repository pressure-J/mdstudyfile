---
tags: [crypto]
title: RSA-Coppersmith高位攻击
created: '2026-09-16T12:00:00.000Z'
modified: '2026-11-03T13:10:00.000Z'
---

# RSA — Coppersmith 部分密钥泄露（高位 / 低位攻击）

## 题型识别（一眼看出）
题目**只给 n、e、c**，外加 p 或 q 的**部分二进制位**（hint）。构造脚本特征：

```python
from Crypto.Util.number import getPrime, bytes_to_long
from secret import flag

p = getPrime(1024)
q = getPrime(1024)
n = p * q
e = 65537
hint1 = p >> 724          # p 的高 300 位
hint2 = q % (2 ** 265)    # q 的低 265 位
ct = pow(bytes_to_long(flag), e, n)
print(hint1); print(hint2); print(n); print(ct)
```

**本质**：RSA 的安全性建立在"不知道 p、q"上；一旦泄露了 p 或 q 足够多的比特位，就能用 Coppersmith 定理把剩下的比特补出来 → 分解 n → 解密。

## Coppersmith 定理（核心工具）
给定模 $N$ 的多项式 $f(x)$（次数 $d$），若 $f$ 有一个足够小的根 $|x_0| < N^{1/d}$，则可以用 LLL 格基约化把它求出来。

在 RSA 里的用法（已知 p 的部分比特）：
- 把 p 的"已知部分"塞进多项式，未知部分当 $x$；
- **未知比特数 ≤ 约 $0.44 \times p\_bits$** 时即可分解（1024 位 p → 约 **454 位**上限）；
- Sage 里直接调用 `f.small_roots(X=, beta=)`：
  - `X` = 未知根的上界（不是越大越好，**超过理论上限反而失效**）
  - `beta` = 因子 p 相对于 n 的大小，理论约 0.5，但**实战取 0.4**（见易错点 1）

## 三种子类型
| 类型 | 已知 | 未知 | 处理 |
|------|------|------|------|
| ① 已知 p 高位 | `p >> k`（高若干位） | 低 $(p\_bits-k)$ 位 | 直接 `f = x + (hint<<k)` |
| ② 已知 p 低位 | `p % 2^k`（低若干位） | 高 $(p\_bits-k)$ 位 | `f = 2^k*x + hint` 后 `.monic()` |
| ③ 已知 p 高位 + q 低位 | `p>>k` 且 `q % 2^m` | 中间位 | **先把 q 低位转成 p 低位**，再当类型②/高位处理 |

类型③就是 **2021 鹤城杯** 这道题，也是最常考的一种。

## 本题原理（鹤城杯，逐步推导）
已知：`hint1 = p >> 724`（p 的高 300 位）、`hint2 = q % 2^265`（q 的低 265 位）。

**第 1 步：把 q 的低位转成 p 的低位。**
对 $n = p\cdot q$ 两边模 $2^{265}$，而 $q \equiv \text{hint2} \pmod{2^{265}}$：

$$n \equiv p\cdot \text{hint2} \pmod{2^{265}} \;\Longrightarrow\; p \equiv n\cdot \text{hint2}^{-1} \pmod{2^{265}}$$

即拿到 **p 的低 265 位** $p_{low}$。

**第 2 步：写出 p 的完整表达式。**
$$p = \underbrace{\text{hint1}\cdot 2^{724}}_{\text{高 300 位}} + \underbrace{p_{low}}_{\text{低 265 位}} + \underbrace{2^{265}\cdot t}_{\text{中间未知}}$$

未知量 $t$ 约 $724-265 = 459$ 位。

**第 3 步：459 > 454，爆破低 5 位。**
Coppersmith 上限约 454 位，多出的 5 位直接枚举：令 $t = 32x + i,\; i \in [0,31]$。

**第 4 步：构造多项式求根。**
$$f(x) = \text{hint1}\cdot 2^{724} + p_{low} + (32x + i)\cdot 2^{265}$$

取 `.monic()` 后 `small_roots(X=2^454, beta=0.4)` 求出 $x$，还原 $p$，分解 n，解密。

> 直观理解：p 的高 300 位 + 低 265 位 = 565 位已知，只剩 459 位未知；超过一半的比特都知道了，Coppersmith 就能补齐中间那段。

## 解题脚本
见同目录 `RSA-Coppersmith高位攻击-solve.py`（**必须用 SageMath 运行**，普通 Python 没有 `small_roots`）。

```python
# 核心片段
R = 2 ** 265
p_low = n * inverse_mod(hint2, R) % R          # p 的低 265 位
for i in range(2 ** 5):                        # 爆破低 5 位
    f = hint1 * (2 ** 724) + p_low + (x * 32 + i) * R
    roots = f.monic().small_roots(X=2 ** 454, beta=0.4)
    if roots:
        p = (Integer(roots[0]) * 32 + i) * R + hint1 * (2 ** 724) + p_low
        break
```

## 验证记录（2026-09-16）
- **2021 鹤城杯原题**实测：在 $i=19$ 命中 p，SageMath 9.3 全程 **37.5 s**
- 还原 `p = 133637329398256221348922087205912367118213472434713498908220867690672019569057789598459580146410501473689139466275052698529257254973211963162087316149628000798221014338373126500646873612341158676084318494058522014519669302359038980726479317742766438142835169562422371156257894374341629012755597863752154328407`，`n % p == 0` ✓
- flag：`flag{ef5e1582-8116-4f61-b458-f793dc03f2ff}`

## 易错点 / 经验（血泪）
1. **`beta` 必须用 0.4，不要用 0.5**：p、q 位数相同时，`small_roots(beta=0.5)` 正好踩在 q 与 $\sqrt n$ 谁大谁小的随机边界上，时灵时不灵；取 0.4 才稳定。（第一次就是被这个坑住，方向对但参数不对）
2. **未知位超上限必须爆破**：1024 位 p 的 Coppersmith 上限约 454 位，本题 459 位，超了 5 位 → 枚举低 5 位（`i in range(2**5)`），否则 `small_roots` 求不出。
3. **多项式要 `.monic()`**：Sage 的 `small_roots` 要求首一多项式，非首一要先 `f.monic()`。
4. **返回的是 Zmod 元素**：`small_roots` 的根拼回去的 `p` 可能带 `Zmod(n)` 类型，`n // p` 会报 `ZeroDivisionError`；要 `Integer(...)` 转换。
5. **`X` 不是越大越好**：`small_roots` 的 `X` 超过理论上限会失效——取在"刚好覆盖未知位"的值最稳。
6. **环境**：必须 SageMath（本机 `C:\Users\徐利杰\AppData\Local\SageMath 9.3\`，**不在 `py` 里**，普通 Python 无 `small_roots`）。调用方法：
   ```powershell
   cd "C:\Users\徐利杰\AppData\Local\SageMath 9.3"
   .\runtime\bin\bash.exe --login -c "/opt/sagemath-9.3/sage -c '...'"
   ```
7. 一次 `small_roots` 约 1~2 秒，爆破 32 次共几十秒，属正常。

## 面试速答卡
- **Q: Coppersmith 攻击适用于什么场景？** A: 已知 RSA 模数 N 中某个因子 p 的部分比特（高位或低位），未知比特不超过约 $0.44\times p\_bits$ 时，可求出完整 p 从而分解 N。
- **Q: 为什么已知 p 高位能攻击？** A: 把 p 的已知高位固定，未知低位当变量构造模 N 的多项式，用 LLL 求小根，即 Coppersmith 定理。
- **Q: 同时给了 p 高位和 q 低位怎么办？** A: 对 $n=pq$ 模 $2^k$ 把 q 低位转成 p 低位，于是 p 同时有高位和低位，再对中间未知段做 Coppersmith（超出上限就爆破若干低位）。
- **Q: `small_roots` 的 beta 为什么取 0.4 而不是 0.5？** A: beta 是因子相对 N 的大小下界，p、q 同位数时理论约 0.5，但正好在临界点会导致求解不稳定，实战取 0.4 更可靠。
- **Q: 未知位只比上限多几位时怎么处理？** A: 直接爆破多出的那几位（枚举），把未知位压到上限内再跑 Coppersmith。
- **Q: Coppersmith 的数学工具是什么？** A: Howgrave-Graham 构造的格 + LLL 格基约化，找到系数足够小的多项式使小根成为整数根。


## 附一：明文高位（stereotyped message）

### 题型识别
`e` 很小（3/5）、明文有**已知前缀**（`flag{`、固定 padding、已知的部分内容），只给 `n`、`e`、`c`。
判据：**未知位数 < `n^(1/e)`**（e=3、n 1024 位 → 约 341 位）。

### 原理
设 `m = known·2^k + x`（x 是未知低位），则 x 是

$$f(x) = (known \cdot 2^k + x)^e - c \equiv 0 \pmod n$$

的小根，`|x| < 2^k < n^(1/e)`，直接 `small_roots(X=2^k, beta=1.0)`。

**与正文的区别**：正文攻击的是**因子 p 的位**（`beta≈0.4`、上限约 0.44·p_bits）；这里攻击的是**明文本身**（`beta=1.0`、上限 n^(1/e)）。两者都是 Coppersmith，但 beta 和 X 完全不同，别混。

### 代码

```python
R = Zmod(n); PR.<x> = PolynomialRing(R)
f = (known * 2**shift + x)**e - c
roots = f.monic().small_roots(X=2**shift, beta=1.0)
m = Integer(roots[0]) + known * 2**shift
```

### 易错点
1. `beta=1.0`（攻击整模数），不是正文的 0.4。
2. 未知位超 `n^(1/e)` 一点就爆破（同正文第 2 条）。
3. 前缀要精确到字节：`flag{` 是 5 字节 = 40 位，`known` 必须按位对齐，差一位就无解。
4. 脚本：同目录 `RSA23-Coppersmith明文高位-solve.sage`（必须 SageMath 跑）。

### 验证记录（2026-11-03）
- 模拟：n 1024 位、e=3、明文 335 位、未知低 64 位
- `small_roots` 一次命中，恢复 `flag{stereotyped_message_coppersmith_2026}`；含 Sage 启动全程 36.5s

## 附二：d 的部分位（Partial Key Exposure）

### 题型识别
给了 `d` 的低（或高）若干位，如 `d & ((1<<256)-1)`，其余不给。

### 边界（记住，别硬上）
- `ed − 1 = k·φ(n)`，`k ∈ [1, e)`；
- Boneh-Durfee-Frankel：已知 d 的低 **δ ≥ n_bits/4** 位即可分解 n（专门构造的二元格）；
- `δ < n/4` 不保证可行。

### 工程做法（思路）
1. 爆破 k（e 小时只有几个候选）。
2. 由 `e·d_low − 1 ≡ k·φ (mod 2^δ)` 反解 `s = p+q` 的低 δ 位（k 为奇时模 2^δ 可逆）。
3. 在模 2^δ 下解 `p² − s·p + n ≡ 0`，逐位 Hensel 提升得到 p 的低 δ 位。
4. δ 足够大（接近 p_bits 的一半）时可退化成"已知 p 低位"，用本文类型②的一元 Coppersmith 收复；**δ = n/4 时未知位超过一元上限，必须上二元格**。

> **状态：本条只有方法与边界，没有可跑脚本。** 完整 PKE 需要 Boneh-Durfee 的二元格构造，属于既定路线里"遇到就跳"的一类——认得题面、说得出 0.25/0.292/n4 这几个界就够了。

*最后更新：2026年11月3日*
