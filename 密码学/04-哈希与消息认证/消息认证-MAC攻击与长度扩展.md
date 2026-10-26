---
tags: [crypto, hash, mac]
title: 消息认证-MAC攻击与长度扩展
created: '2026-10-26T19:15:00.000Z'
modified: '2026-10-26T19:15:00.000Z'
---

# 消息认证：MAC 攻击面与长度扩展

> **一句话本质**：MAC 证明的是"这串字节出自知道密钥的人之手"，**不证明"它就是当初那条意思、当初那次场合"**——今天三道题全部踩在这条缝上。
>
> 对应 ISCC2026 模块 3 后两条考点（消息认证码攻击面 / 长度扩展）。SM3 算法细节（IV、64 轮、消息扩展）见 [SM3-杂凑算法原理与攻击](../05-国密/SM3-杂凑算法原理与攻击.md)，本篇不重复。
>
> 三题现场：2026-10-25，`D:\python\homework\哈希与消息认证\`（gen_and_check.py 出题自检全 True）。

## 1. 概念地图：密钥不在哈希里，在"用哈希搭认证的方式"里

裸哈希没有密钥，只能证完整性不能证来源。把密钥混进哈希的**用法**才叫 MAC——同样一个 SHA-256，套法不同安全性天差地别：

| 构造 | 有密钥吗 | 问题 |
|---|---|---|
| 裸哈希 `SHA256(msg)` | 无 | 谁都能重算，无认证 |
| `SHA256(SECRET‖msg)` 前缀式 | 有 | 长度扩展（见 §4，MD 结构通病） |
| `HMAC(K, msg)` | 有 | **正规做法**：内外两轮把"中间状态"重新封死 |
| 截断 MAC（tag 取前几个 hex） | — | 任何 MAC 截太短都挨生日攻击（§2） |
| CBC-MAC | 有 | 变长消息可拼接伪造（§3） |

## 2. 截断 MAC · 生日碰撞（题1）

**触发特征**：tag/签名只有**一部分十六进制位**（本题 4 个 hex 字符 = **16 bit**，注意 hex 字符 4 bit 不是 8）。

**原理最小集**：n bit 空间随机取约 2^(n/2) 个值就有一半概率出碰撞（生日规律）。所以**截断 MAC 的安全强度按 n/2 算**，不是按 n。

**现象**：2000 条记录的 tag 列表，实测碰撞 23 对；理论期望 ≈ 2000²/(2·65536) ≈ 30，同量级 ✓。

**攻击是"调包"不是"凑对"**（MAC 侧的关键修正）：
- 找碰撞**全离线**：比较"两个 tag 相不相等"只需要看得见 tag，不需要密钥；
- 但恶意消息的 tag 你**算不出来**（没密钥），所以签名场景那种"两侧各生成 2^(n/2) 凑对"走不通；
- 真实打法：撞上同一 tag 的两条消息**都由银行签发过**（流水里都有），在出示 m1 的场合出示 m2，tag 跟着 m1 走。银行只验 `MAC(提交的消息) == 提交的 tag` 这一条等式，无法追溯 tag 当初签给谁——16 bit 的配对信息在碰撞发生那一刻就永久丢了。

```py
# 生成 2^8 条合法 + 2^8 条恶意 → 期望 1 对跨侧碰撞（hash-then-sign 场景）；
# MAC 场景改为：在已签发集合内部找碰撞对，然后调包提交
seen = {}
pairs = []
for ln in open('mac_list.txt', encoding='utf-8'):
    ln = ln.strip()
    if not ln:
        continue
    msg, tag = ln.split(',')          # 按分隔符切，别用 [-5:] 硬数——tag 长度一变就静默坏
    if tag in seen:
        pairs.append((seen[tag], msg, tag))
    else:
        seen[tag] = msg
print(len(pairs), pairs[:5])          # 实测 23 对
# 调包提交：signed 里只有 m1，提交 (m2, tag_m1)，银行重算 MAC(m2)==tag_m1 → 接受
```

**防御**：tag ≥ 96 bit；时间戳/序号/nonce 防"调包+重放"（MAC 管不了上下文）。

**代码坑**：文件里 tag 是字符串 `'6f14'`，手抄成整数 `0x6f14` 后 `==` 永远 False——**攻击被类型混用压死**，而不是攻击失败。数据从代码里流出来，别中途人肉转手。

## 3. CBC-MAC · 拼接伪造（题2）

**触发特征**：题面给 CBC-MAC（或"分组密码链式 tag"）+ **样本是单块**（16 字节）但验证端**不限块数**。

**概念分层**（容易糊的点）：CBC 是"用分组密码搭加密器"的管线，CBC-MAC 是借同一骨架搭**认证器**——零件相同（都是 E_K），接法不同：

| | CBC 加密模式 | CBC-MAC |
|---|---|---|
| 链条公式 | $C_i = E_K(P_i \oplus C_{i-1})$ | $t_i = E_K(M_i \oplus t_{i-1})$ |
| 初始值 | 随机 IV，随密文传 | **固定 0**，不传 |
| 输出 | 全部密文块 | **只留最后**一个 t 当 tag |
| 目的 | 机密性 | 完整性/认证 |

单块消息链条只转一轮：`MAC(A) = E_K(A ⊕ 0) = E_K(A)`。

**攻击推导**：银行给 `tagA = MAC(A)`、`tagB = MAC(B)`，提交 32 字节 `M = A ‖ Y`，银行算两轮：

```text
t1 = E_K(A) = tagA                ← 第一轮输出 = 你已知的 tagA（中间态公开！）
t2 = E_K(Y ⊕ t1) = E_K(Y ⊕ tagA)  ← 要它 == tagB
```

让喂进 E_K 的内部值恰好是 B（银行自己给过 `E_K(B) = tagB` 这对）：

$$Y = B \oplus tagA \;\Rightarrow\; t_2 = E_K(B) = tagB$$

**已知明密对优先于求逆**——第一反应 $Y = tagB \oplus tagA$ 是错法，它默认了 $E_K$ 能像括号一样约掉，本质是在无意识求 $D_K$。**攻击题里任何时候发现自己在求 $D_K$，路就走岔了。**

```py
from server import bank
import json
s = json.load(open('samples.json', encoding='utf-8'))['samples']
A  = bytes.fromhex(s[0]['record_hex']); tagA = s[0]['tag_hex']
B  = bytes.fromhex(s[1]['record_hex']); tagB = s[1]['tag_hex']
Y = bytes(a ^ b for a, b in zip(B, bytes.fromhex(tagA)))
M = A + Y
print(bank.verify(B, tagB))    # 对照组（已知好例子）：True
print(bank.verify(M, tagB))    # 拼接伪造：True，银行从未签发过 M
```

**缺陷定性**：变长消息 + 无长度域的 CBC-MAC 不能当唯一防线（CMAC 把长度编码进首块来补）。伪造消息后半截是乱码——打穿的是 MAC 层，离"伪造可读转账"还隔上层格式解析。

**环境事故教训**：题2 曾因 server.py 每次导入随机生成密钥、与 samples.json 的签名不同源，`verify(B, tagB)` 恒 False。**排障先跑"已知好例子"对照**，一步分清"我的攻击错了"vs"环境坏了"。

## 4. MD 结构 · 长度扩展（题3）

**触发特征**：`sig = Hash(SECRET ‖ data)`，SECRET 未知（长度 0..63 爆破），要为 `data‖glue‖append` 造合法摘要。SM3/SHA-256/MD5/SHA-1 同打。

**定性**：不是压缩函数的数学缺陷（64 轮搅拌机很强），是 **MD 骨架的固有性质**：① 摘要 = 中间状态（末尾不再混入任何东西）；② 填充规则完全公开可复算。"可续压"永远是事实，是否成为攻击取决于用法（裸哈希不受影响，前缀式 MAC 中招）。防御：HMAC（封死状态）、SHA-3 海绵结构（换骨架）。

**五站骨架**（SM3 笔记 2.1–2.3 同款，今天手搓验证）：

```text
任意长度消息 M
  │ ①填充：0x80 + 若干 0x00 + 8字节大端 bit 长度，总长凑成 64 的倍数
  ▼
切成 64 字节块  B0 B1 B2 …
  │ ②链式碾压：V = IV → V = compress(V, B0) → V = compress(V, B1) → …
  ▼
③摘要 = 最后那个 V（8 个 32 位字 = 32 字节）
```

**md_pad（手搓版，与 hashlib 对拍 8/8 True 实测）**：

```py
def md_pad(length: int) -> bytes:
    """length：原始消息的字节数。返回填充字节。"""
    k = (56 - length - 1) % 64      # 解方程 (length + 1 + k) % 64 == 56；% 对负数返回正数，免分类讨论
    return b'\x80' + b'\x00' * k + struct.pack('>Q', length * 8)   # 长度写 bit，大端

def manual_sha256(msg: bytes) -> str:
    padded = msg + md_pad(len(msg))
    assert len(padded) % 64 == 0    # 探雷器：写给自己，当场拦截填充错误
    v = list(IV)
    for i in range(0, len(padded), 64):
        v = compress(v, padded[i:i + 64])
    return ''.join('%08x' % x for x in v)   # 没有任何额外步骤——摘要就是 V
```

对拍验收必含 **L=55、56 两个边界**（55 时填充恰好收进第一块，56 时溢出到第二块）。

**攻击三步**（md_pad 用两次 + 续压一次）：

```py
state = list(struct.unpack('>8I', bytes.fromhex(sig)))    # 摘要 → 中场状态
for secret_len in range(0, 64):
    glue   = md_pad(secret_len + len(params))             # 假想 SECRET‖params 的收尾
    suffix = append + md_pad(secret_len + len(params) + len(glue) + len(append))
    forged_digest = digest_from_state(state, suffix)      # 从中间状态续压
    forged_msg    = params + glue + append                # 提交给服务端的字节
# 64 组候选逐个发服务端，被接受的那个 secret_len 即真实长度（本题 37）
```

**两处填充别混**（本轮最核心的细节）：
- glue 的长度字段**不含 append**——实测伪造消息里 `0x01d0` = 464 bit = 58 字节 = 37(SECRET) + 21(params) ✓；
- suffix 里**没有 glue**——glue 的效果已经压进 sig 了，服务端视角里它属于"已压完"的部分。

## 5. 盲区清单（10/25 三题复盘）

1. 4 个 hex 字符 = 16 bit（hex 4 bit），不是 32
2. 生日规律 n/2；截断 MAC 强度按 n/2 算 → tag ≥ 96 bit + 序号/时间戳
3. MAC 证明"字节出自密钥持有者"，不证明"是当初那条意思、那个场合"
4. 已知明密对优先于求逆——发现自己在求 $D_K$ 就是路走岔了的信号
5. `'0x80'` 是 4 字符字符串 ≠ `b'\x80'` 1 字节；密码脚本里数据保持 bytes 到最后一刻
6. 取模消分支：`(56-length-1)%64` 等价于双分支 if/else，短且无 off-by-one
7. 排障先跑"已知好例子"对照，分清"我的攻击错了"vs"环境坏了"
8. 长度扩展打**结构**（MD 骨架），MD5 碰撞打**算法**（压缩函数弱）——两类攻击对象不同

## 6. 赛前 30 秒自查

| 现象 | 先想什么 |
|---|---|
| tag/签名只有部分 hex 位 | 截断 MAC → 生日碰撞调包，工作量 2^(n/2) |
| CBC-MAC / 链式 tag + 变长消息 | 拼接 `A ‖ (B ⊕ tagA)`，前提拿到 ≥2 个样本 tag |
| `sig = Hash(SECRET‖data)` 要伪造 | 长度扩展：md_pad 两次 + 爆破 SECRET 长度 0..63 |
| 推导中想求 $D_K$ / 想"约掉" E_K | 停——改找已知明密对复用 |
| 要 HMAC 结构题 | 内外两轮 + ipad/opad，封死中间状态 |
| SM3 变体（IV/常数改动） | 先核对是否标准 SM3，见 05-国密专篇 |

## 相关文件

- 三题现场 + 出题自检：`D:\python\homework\哈希与消息认证\`（题1 mac_list / 题2 server.py+samples / 题3 sha256_lib+verify.py）
- SM3 同源攻击脚本：[SM3-长度扩展攻击-solve.py](../05-国密/SM3-长度扩展攻击-solve.py)
- 姊妹篇：[SM3-杂凑算法原理与攻击](../05-国密/SM3-杂凑算法原理与攻击.md) ｜ [工作模式与配置缺陷](../03-对称密码/工作模式与配置缺陷.md)（CBC 加密侧的比特翻转与本题 CBC-MAC 同骨架不同病）
