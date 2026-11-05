---
tags: [crypto]
title: RSA-CommonPrime-CPRSA
created: '2026-10-29T16:30:00.000Z'
modified: '2026-10-29T16:30:00.000Z'
---

# RSA — Common Prime RSA（p-1、q-1 共享大因子 g，Wiener 失效）

> 起源：**祥云杯 2022 · common_rsa**（本笔记就是这道题逼出来的）。
> 结论先放这里：`d` 只有 135 位（远小于 $n^{1/4}$），但**套 Wiener 一定失败**，
> 正解是 **Jochemsz–May 多元格攻击**（Sage，45 维格，跑 70 秒）。
> flag = `flag{9aecf8d8-6966-4ffa-96b0-2e744d28baf2}`

---

## 一、题型识别（一眼看出）

出题脚本长这样（`0/task.py` 原文，本笔记全部分析都基于它）：

```python
from Crypto.Util.number import getPrime, isPrime, bytes_to_long, inverse
from math import lcm

def gen(g):
    bits = 512 - g.bit_length()
    while True:
        a = getPrime(bits)          # 192 位
        p = 2 * a * g + 1           # p-1 = 2ag
        if isPrime(p):
            return p

g = getPrime(320)                   # ★ p、q 共用同一个 320 位素数 g
p = gen(g)
q = gen(g)                          # q-1 = 2bg
n = p * q
d = getPrime(135)                   # 小私钥
phi = lcm(p - 1, q - 1)             # ★ λ = 2gab，不是 (p-1)(q-1)
e = inverse(d, phi)
c = pow(flag, e, n)
```

三个指纹，只要中一个就往这里想：

1. `p = 2*a*g + 1`、`q = 2*b*g + 1`，**同一个 g**（`gen(g)` 只换 a/b）→ 文献里叫 **Common Prime RSA (CP-RSA)**。
2. `phi = lcm(p-1, q-1)`（不是 `(p-1)*(q-1)`）。
3. `e` 的位数明显小于 `n`（本题 n 1025 位、e 703 位；普通 Wiener 题的 e 与 n 同量级）。
   ——因为 $e = (k\lambda+1)/d$，λ 比 n 小 320 位、d 只有 135 位，两者差不多抵消。

本题实测参数（用解出的 p、q 反算）：

| 量 | 位数 | 说明 |
|---|---|---|
| n | 1025 | $n=(2ga+1)(2gb+1)=4g^2ab+2g(a+b)+1$ |
| e | 703 | ≈ kλ/d |
| g | 320 | gcd(p-1, q-1) = 2g |
| a, b | 192 / 192 | p-1 = 2ag, q-1 = 2bg |
| λ = 2gab | 704 | φ 用的是它 |
| d | 135 | 小私钥 |
| k | 134 | ed - 1 = kλ |

---

## 二、为什么 Wiener / 连分数必然失败

Wiener 的两根支柱，这里**两根都塌**：

### 塌点 1：连分数的目标分数不对

Wiener 找的是 $k/d$ 是 $e/n$ 的收敛子，靠的是 $\lambda \approx n - 2\sqrt{n}$。
这里

$$\lambda = 2gab = \frac{n-1}{2g} - (a+b) \approx \frac{n}{2g}, \qquad g = n^{0.312}$$

于是

$$\frac{k}{d} \approx \frac{e}{\lambda} \approx 2g \cdot \frac{e}{n}$$

是 `e/n` 的 $2g \approx 2^{321}$ 倍 —— **根本不是 `e/n` 的收敛子**。

再算误差确认它也不是「最佳逼近」：$k/(gd)$ 与 $2e/n$ 的差

$$\left|\frac{2e}{n} - \frac{k}{gd}\right| = \frac{|2egd - nk|}{n\,gd} \approx \frac{2k(a+b)}{nd} \approx 2^{-833}$$

而勒让德定理要求 $< \dfrac{1}{2(gd)^2} \approx 2^{-911}$，**差约 78 位**。
所以哪怕分母放到 $gd$（455 位）这个量级，连分数也捞不到它。

### 塌点 2：验证公式用错了 φ

原脚本/笔记里的验证是：$\phi = (ed-1)/k$，然后令 $s = n-\phi+1$ 当 $p+q$，解 $x^2 - sx + n = 0$。
这里 $\phi$ 拿到的是 **λ**，而 $n - \lambda + 1 \neq p+q$，判别式永远不会是完全平方 → 每个候选都被丢掉。

### 实测（不是推理，是真跑）

对 `e/n`、`e/(n-1)`、`e/(n+1)` 三种分数，共 **426 个收敛子**，逐个用最通用的合法性检验
`pow(c, e*d, n) == c`（合法 d 必然满足 $ed \equiv 1 \bmod \lambda$）→ **0 命中**。

所以「d 够小 → Wiener 一定能打」是**错的**：Wiener 依赖 φ 的具体形式。

---

## 三、正解：Jochemsz–May 多元格攻击

思路：不求近似，直接用代数关系造一个**多元多项式方程**，把 (d, 两个中间量) 当小根，用 LLL 求小根。

### 1. 造方程

$$ed - 1 = k\lambda = k \cdot 2gab$$
$$n - 1 = 4g^2ab + 2g(a+b)$$

两式联立消掉 $ab$ 与 $(a+b)$：注意 $(ed-1)^2 = 4g^2k^2a^2b^2$，而

$$(ed-1)^2 + (ed-1)\cdot k(a+b) = 4g^2k^2a^2b^2 + 2gk^2ab(a+b) = (n-1)\cdot k^2ab$$

令 $x=d,\; y=ka,\; z=kb$（则 $y+z=k(a+b)$，$yz=k^2ab$），整理得

$$f(x,y,z) = e^2x^2 + ex(y+z-2) - (n-1)yz - (y+z-1) = 0$$

**根就是** $x_0 = d$（135 位）、$y_0 = ka$（326 位）、$z_0 = kb$（325 位）。

> 已验证：把真值代进去，$f$ **恰好等于 0**（不是模意义下的 0）。

### 2. 定规模参数

$$\gamma = \frac{|g|}{|n|} = \frac{320}{1024},\qquad \delta = \frac{|d|}{|n|} = \frac{135}{1024}$$

$$X = n^{\delta},\quad Y = Z = n^{\delta + 1/2 - \gamma},\quad \tau = \frac{1/2+\gamma-4\delta}{2\delta},\quad t = \lfloor \tau m \rfloor$$

取 $m = 2$ → $t = 2$，得到 **45×45 的三角格**。

### 3. 造格 + LLL + 结式消元

- 集合 $S$（$f^{m-1}$ 的单项式）、$M$（$f^{m}$ 的单项式），用 **x-shift** 造移位多项式（基可三角化）；
- LLL 取出最前面两个短向量 $h_1, h_2$（它们与 $f$ 在根处同为零，但代数独立）；
- 结式消元：$h_1.\text{resultant}(f, z)$、$h_2.\text{resultant}(f, z)$ → 再对 $y$ 求结式 → 解出 $x_0=d$；
- 回代：$h_1.\text{resultant}(h_2, z)$ 在 $x=d$ 下解出 $y_0=ka$，再代回 $f$ 得 $z_0=kb$；
- $k = \gcd(ka, kb)$，$a = ka/k$，$b = kb/k$，$g = (ed-1)/(2kab)$，$p = 2ga+1$，$q = 2gb+1$。

### 4. 实测运行结果

```
polynomials: 45, monomials: 45
LLL...
found d  = 43537666061967240103046969418264699447211
found ka = 113185249960967522359271714498731379489008820545093736413757557183361738076423481997792886095964619
found kb = 65091063458065557958176952331165445863728617874376711020857814617709047531474784928192290152527899
p = 21007149684731457068332113266097775916630249079230293735684085460145700796880956996855348862572729597251282134827276249945199994121834609654781077209340587
q = 12080882567944886195662683183857831401912219793942363508618874146487305963367052958581455858853815047725621294573192117155851621711189262024616044496656907
flag = flag{9aecf8d8-6966-4ffa-96b0-2e744d28baf2}
```

耗时约 **70 秒**（SageMath 9.3，Windows）。

---

## 四、脚本与运行方式

主脚本：`D:\python\CTF工具箱\crypto\30-RSA-CommonPrime-JochemszMay.sage`
副本：本目录 `RSA-CommonPrime-CPRSA-solve.sage`（同内容，改了顶部 n/e/c 就能跑）

**必须用 Sage 跑**（要 LLL + 多元多项式结式，`py` + `pycryptodome` 做不到）。本机启动方式：

```bash
"C:\Users\徐利杰\AppData\Local\SageMath 9.3\runtime\bin\bash.exe" -lc "/opt/sagemath-9.3/sage /cygdrive/d/python/CTF工具箱/crypto/30-RSA-CommonPrime-JochemszMay.sage"
```

要点：Windows 版 Sage 是 Cygwin 环境，`sage` 不在 PATH 里，必须走 `runtime\bin\bash.exe -lc` + `/opt/sagemath-9.3/sage`；路径用 `/cygdrive/d/...`，整段加引号（含中文目录也没问题）。

---

## 五、比赛里的「非预期」捷径

祥云杯 2022 这道题公开后，**这个 n 已经被 factordb 收录**（题是静态数据，所有人拿到同一组）。
原赛 wp（S1gMa）就是直接查在线分解：

```python
from Crypto.Util.number import long_to_bytes, inverse
from math import lcm
q = 21007149684731457068332113266097775916630249079230293735684085460145700796880956996855348862572729597251282134827276249945199994121834609654781077209340587
p = 12080882567944886195662683183857831401912219793942363508618874146487305963367052958581455858853815047725621294573192117155851621711189262024616044496656907
d = inverse(e, lcm(p-1, q-1))     # 用 φ=(p-1)(q-1) 也行，因为 e 与两者都互素
print(long_to_bytes(pow(c, d, n)))
```

**但这只是环境红利**，题目重放/改参数就没了 —— 真会打还得靠第三节的格攻击。

---

## 六、踩坑记录

1. **`bytes(int)` 不是 int→bytes**：`bytes(pow(c, d, n))` 会去**造一个长度等于该整数的零字节串** → `OverflowError: cannot fit 'int' into an index-sized integer`。
   正解：`Integer(...)` 转 hex 再 `bytes.fromhex`（见脚本尾部），或 `pycryptodome` 的 `long_to_bytes`。
2. **p、q 顺序会互换**：解出来的 `(p, q)` 与网上 wp 里的顺序可能相反；永远 `assert p*q == n`，别用位置判断。
3. **γ、δ 必须按题目规模改**：`gamma = g位数/n位数`、`delta = d位数/n位数`；抄参数不改 → 格维度/界不对，LLL 出来的向量不够短。
4. **`Y = Z` 上界别写成 `p-1`**：根是 $ka$、$kb$（约 326 位），不是 $p-1$（512 位）。代码注释里写"根 = (d, p-1, q-1)"是**错的**，按 $n^{\delta+1/2-\gamma}$ 算出来的界才对得上。
5. **先花 1 分钟排除 Wiener**：跑一句 `pow(c, e*d, n) == c` 检验收敛子，全 miss 就直接上格，别在连分数上耗时间。

---

## 七、一句话总结

> `p = 2ga+1`、`q = 2gb+1` 共用大素数 g、且 φ 用 `lcm` 时，**e 会比 n 短一大截**，此时「d 小」并不能让 Wiener 生效
> （目标是 $2g\cdot e/n$，不是 $e/n$）。把
> $(ed-1)^2+(ed-1)k(a+b)=(n-1)k^2ab$ 改写成 $f(d,ka,kb)=0$，
> 用 Jochemsz–May 的 x-shift 格 + LLL + 结式消元求出小根，即可恢复 d 与 p、q。
