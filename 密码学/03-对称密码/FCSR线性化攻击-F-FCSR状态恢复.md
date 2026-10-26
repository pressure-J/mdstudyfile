---
tags: [crypto, stream-cipher, fcsr, state-recovery]
title: FCSR线性化攻击-F-FCSR状态恢复
created: '2026-10-12T11:00:00.000Z'
modified: '2026-10-12T11:00:00.000Z'
---

# F-FCSR 线性化攻击：从 64MB 密钥流恢复状态

> 题目：DASCTF「FCSR」（附件 `task.py` + `hint`(64MB) + `flag`）
> flag：`flag{aa2820e236a5092c9d5fa56aec042301}`
> 考点：**滤波式 FCSR 的线性化攻击**（Hell–Johansson），把非线性进位寄存器"冻住"后整个密码退化成线性系统。

## 一、题目结构

`task.py` 是一个流密码：

```python
feedback = 0xae985dff26619fc58623dc8aaf46d5903dd4254e   # 滤波器 = 反馈抽头

class Task:
    def __init__(self, key, iv):
        self.state = (iv << 80) | key        # 160 位主寄存器 M
        self.C = 0                           # 进位寄存器
        for i in range(20): self.clock(); S[i] = self.F()
        self.state = 拼接(S[0..19])          # 20 字节回填成 160 位
        self.C = 0
        for _ in range(162): self.clock()

    def clock(self):
        fb = feedback if (self.state & 1) else 0
        self.state >>= 1
        buffer = self.state ^ self.C
        self.C &= self.state                 # ← 唯一的非线性来源
        self.C ^= (buffer & fb)
        self.state = buffer ^ fb

    def F(self):                             # ← 纯线性滤波器
        buffer = self.filter & self.state
        buffer ^= buffer >> 32
        buffer ^= buffer >> 64
        buffer ^= buffer >> 96
        buffer ^= buffer >> 128
        buffer &= 0xffffffff
        buffer ^= buffer >> 16
        buffer ^= buffer >> 8
        return buffer & 0xff

f = open("hint","wb")
for i in range(2**26):
    ffcsr.clock(); f.write(ffcsr.F().to_bytes(1,"big"))   # 裸密钥流
f = open("flag","wb")
f.write(ffcsr.encrypt(flag))                              # 紧随其后的 38 字节密文
```

三个关键量：

- `feedback` 就是 **F-FCSR-H**（eSTREAM 硬件流密码）里的 `d = (1+|q|)/2`，160 位、83 个 1。
- `hint` 是**裸密钥流**（2²⁶ 字节），不是密文。
- `flag` 是**同一状态继续**加密的 38 字节，所以恢复状态后即可解密。

## 二、先看清哪些是线性的

### 2.1 滤波器 `F()` 是 GF(2) 线性的

`F()` 里全是 AND / XOR / 移位，**没有加法**，所以它是 GF(2) 上的线性映射。逐位展开：

$$
z_k[r]=\bigoplus_{\substack{p\in D\\p\equiv r\;(\mathrm{mod}\;8)}} M_k[p]\;,\qquad r=0,\dots,7
$$

即输出字节的第 r 位 = 主寄存器 M 中"抽头位置 D 且下标 ≡r (mod 8)"的那些位的异或。实测验证：把 `F()` 换成"20 字节逐字节 AND 后 XOR"，2000 组随机状态输出完全一致。

### 2.2 非线性只在进位寄存器 `C` 上

`clock()` 里唯一非线性项是 `self.C &= self.state`（两个变量相乘）。其余（移位、异或、条件选择 `fb`）对 `M` 都是仿射的。所以：

> **只要让 C 恒定**，整个密码就退化成对 M 的线性系统，而输出 z 线性依赖 M ⇒ 用线性代数直接解 M。

这就是 Hell–Johansson 攻击（*Breaking the F-FCSR-H Stream Cipher in Real Time*，ASIACRYPT 2008）的核心。

### 2.3 仿射性的实测

- `clock` 对 state 整体**不是**仿射的（实测 1/2/3/5/…/161 步全失败）——因为含 `C & L`。
- 但固定 m0 序列后每步对 (M,C) 是仿射的，所以线性系统在事件窗口内成立。

## 三、事件的精确定义

记主寄存器 $M$、进位 $C$，$D$ 为 feedback 的 1 位集合。

`C` 的更新式：

$$
C_{k+1}=(C_k\wedge L_k)\;\oplus\;\big((L_k\oplus C_k)\wedge fb\big),\qquad L_k=M_k\gg 1
$$

当 $m_0=M_k[0]=0$ 时 $fb=0$，退化为：

$$
C_{k+1}=C_k\wedge L_k
$$

**若此刻 $C_k=2^p$（单比特），则只需 $L_k$ 的第 p 位为 1，即 $M_k[p+1]=1$，就有 $C_{k+1}=2^p$ 保持不变。**

于是定义事件 $E(p)$：

$$
C_t=2^p,\qquad\text{且}\quad m_0=0\ \text{与}\ C=2^p\ \text{在接下来的 20 步内一直保持}
$$

事件成立时（本脚本 `self_test()` 实测）：

$$
M_{t+j}=(M_t\gg j)\oplus K_j,\qquad K_j=\bigoplus_{i<j}(2^p\gg i)
$$

代进线性的 $F$，得到 **8 个互相解耦的 20×20 线性方程组**：

$$
\underbrace{\bigoplus_{u:\;c+8u-j\in D} M_t[c+8u]}_{\text{未知数 }x_u}
=\underbrace{\mathrm{hint}[t{+}j{-}1][(c-j)\bmod 8]}_{z\text{ 的位}}\;\oplus\;\underbrace{\big[F(K_j)\big][(c-j)\bmod 8]}_{\text{已知常数}}
$$

$c=0,\dots,7$ 各解一次高斯消元，拼回 $M_t$ 的 160 位。

### 3.1 已知位：低 40 位由事件唯一确定

事件条件本身钉死了 $M_t$ 的两族位：

| 条件 | 结论 | 说明 |
|---|---|---|
| $m_0=0$ | $M_t[i]=K_i[0]$，$i=0..19$ | 保证 20 步内 m0 都为 0 |
| $C$ 恒为 $2^p$ | $M_t[i+p+1]=1\oplus K_i[p+1]$，$i=0..19$ | $(M_{t+i}\gg1)$ 的第 p 位为 1 |

$p\ge19$ 时第一族全部为 0（$K_i[0]=0$），第二族落在 $q\ge20$ 的高位区，于是简化为"低 20 位 = 0"——这正是可以**与 p 无关地快速预筛**的形态。

### 3.2 $p$ 的取值

$C\subseteq D$ 恒成立（实测），所以 $C=2^p$ 要求 $p\in D$，共 **83 个候选**。本题实际命中 $p=1$（即 $C=2$）。

事件是"碰运气"的事件：实测自然密度约 $2^{-25.3}$，而题目给了 $2^{26}$ 字节——**刚好够命中一两次**。这正是题目给这么大数据的用意（少于 2²⁴ 就基本扫不到）。

## 四、为什么一开始的路线全错了（踩坑记录）

这部分比正确路径更值钱，记下来避免重蹈。

| 弯路 | 现象 | 真相 |
|---|---|---|
| 以为事件是 `C=0` | `d_k = z_k ⊕ ROT(z_{k-1})` 在 64MB 里最长只连续 3 步为 0，够不到 20 步 | `m0=0` 确实把 C 推向 0，但**"C=0 之后必须继续 m0=0"** 才线性；纯 C=0 事件实测密度 $2^{-24.4}$，且我导出的事件状态与 KS 对不上 |
| 以为关系是 `z_k ⊕ ROT(z_{k-1}) = F(C) ⊕ m0·F(D)` | 99.5% 失败 | 位移后的抽头集合 $A_r=\{p+1:p\in D_r\}$ 与 $D_{r+1}$ 并不相等（8 个类里有 7 个类对不上），所以不能简单 ROT |
| 用 `rref_solve` 回代 | 随机 3000 例里 2445 例给出**不满足方程**的解 | 回代顺序写错；改成标准 RREF（全消元，每行只剩一个主元）后 5000+1600 例全过 |
| 未知数不设限直接解 20×20 | 各类秩 18~20，非满秩 ⇒ 解不唯一，恢复值是某个解而非真值 | 必须把"事件条件确定的位"当已知常数代入，只对剩余位求解；这样每类恰好满秩、唯一 |
| 一致性约束数算错 | 一度以为只有 7 条（$2^{-7}$ 剪枝），伪命中满地 | 把已知位代换方向搞反（应并入 RHS 的常数项）；修正后每类 4~6 条、合计 40 条 |
| 在命令行/字符串里手写 `\x00`、NUL | payload 看着对但不生效 | shell 与 HTTP 参数都传不了真 NUL；必须发 `%00` 或用文件/脚本传字节 |

## 五、脚本与用法

**通用脚本**（工具箱）：`D:\python\CTF工具箱\crypto\23-FCSR线性化攻击.py`

```bash
py 23-FCSR线性化攻击.py hint.txt flag.txt
```

自检会先跑合成事件（8/8），再全量扫描。换题只改顶部参数区：

```python
FEEDBACK = 0xae98...4e     # 题目里的 feedback 常量
NBYTES   = 2 ** 26         # hint 长度
EVENT_LEN = 20
```

**C 加速版**（64MB 全量扫描必需）：`crypto\fcsr_c\` 下的 `gen_tbl2.py` + `attack3.c` + `tbl4.h`

```bash
py gen_tbl2.py                      # 生成事件检测/恢复表
gcc -O3 -o attack3.exe attack3.c -lm
./attack3.exe hint.txt flag.txt
```

C 版把 83 个 p 归成 **9 种形态**（$p\ge19$ 一种 + 8 个小 p），每种形态预生成 20~40 条一致性掩码；先掩码剪枝（$2^{-40}$ 级），再对通过的窗口做 8 次 20×20 高斯消元 + 120 字节前向验证。

**本题结果**：

```
### 通过 t=23773208 p=1
M = 341e6b45d26bec50a382d6f6568e3170c6bffffc
明文: flag{aa2820e236a5092c9d5fa56aec042301}
```

## 六、验证记录（都真跑过）

| 验证项 | 方法 | 结果 |
|---|---|---|
| F 是线性的 | 与"20 字节逐字节 AND 后 XOR"对照 2000 组 | 100% 一致 |
| 前向模型 $M_{t+j}=(M_t\gg j)\oplus K_j$ | 事件窗口内逐步比对 | 成立 |
| 8×20 线性方程 | 用真实 $M_t$ 逐方程验算 | 0/160 不符 |
| 恢复算法自检 | 合成事件 × 74 个 p | 74/74 |
| 端到端（合成） | 注入事件 + 加密 flag | 解出 `flag{Synthetic_FCSR_attack_verified_2026}` |
| 事件条件（真实数据） | t=23773208 处逐步核验 | m0=0 共 20/20 步、C 恒为 2¹ 共 20/20 步 |
| 长距离一致性 | 从恢复状态推到 hint 末尾，抽查 5 个点 + 末字节 | 全部匹配 |
| 解密自洽 | 明文格式 + 内层 32 位全 hex | `flag{...}` ✓ |

## 七、知识点沉淀

1. **"线性滤波器 + 非线性进位"是 FCSR 家族的固定弱点形状**。看到 `F()` 里只有 AND/XOR/移位、而 `clock()` 里有 `C &= state` 这种两个变量的 AND，就应该想到"把 C 冻住 ⇒ 全系统线性"。
2. **事件攻击的通用套路**：找一个"非线性项退化为常数"的状态（这里 $C=C_0$ 恒定），在这个窗口内把非线性系统线性化，用线性代数解状态。这类事件往往**稀有但可检测**——所以出题人会给你超大密钥流（这里 2²⁶ 字节）让你等到它发生。
3. **判据要能只看密钥流看出来**。本题最终的有效判据是"$C=2^p$ 且 20 步内 m0=0"，它等价于窗口的 20 字节满足 40 条线性奇偶约束——**完全不需要知道内部状态**。
4. **已知位必须当常数代入，不能塞进未知数**。否则子系统不满秩，解出的是无穷多解里的任意一个，恢复值系统性错误（我在这上面卡了很久，症状是"方程全对、解就是不对"）。
5. **GF(2) 消元一律用 RREF**（全消元 + 每行只留一个主元），回代极易写错位序；写完务必用随机系统自测（"解是否满足 A x = r"，而不是"是否等于原始 x"——因为非满秩时原始 x 只是众多解之一）。
6. **fbbit 的"类内位移自相似性"不成立**：不能假设 $2D_r=D_{r+1}$。本题 8 个类里 7 个不满足，所以不能用"整体右移 + ROT 输出字节"来简化方程。

## 八、相关

- 原始论文：Hell & Johansson, *Breaking the F-FCSR-H Stream Cipher in Real Time*, ASIACRYPT 2008（[iacr eprint 版](https://iacr.org/archive/asiacrypt2008/53500563/53500563.pdf)）
- 同库：[LFSR状态恢复](LFSR状态恢复.md) —— LFSR 版的状态恢复（更简单，直接逆推）
- 同库：[流密码密钥重用](流密码密钥重用.md) —— 另一类流密码弱点
- 工具箱：`crypto\23-FCSR线性化攻击.py`、`crypto\fcsr_c\`（C 加速版）
