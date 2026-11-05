---
tags: [crypto]
title: RSA44-随机数缺陷-可预测素数
created: '2026-11-03T13:10:00.000Z'
modified: '2026-11-03T13:10:00.000Z'
---

# RSA — 素数可预测（时间戳 / 固定种子）

## 题型识别（一眼看出）

- 生成脚本里出现 `random.seed(int(time.time()))`、`random.seed(1234)`、`Random(os.getpid())`；
- 题面给了"加密发生的时间"、日志时间戳、或直接给一个种子范围；
- n 的位数正常、也没有任何泄露参数——就是随机数坏了。

## 原理

`random` 是 MT19937，种子确定则整条流确定。只要复现出题人的调用序列，`getrandbits(bits)` + `nextprime` 就能还原 p，`n % p == 0` 验证。

爆破对象是**种子**：给定时间窗口 `[T−w, T+w]`，逐个 seed 复现。

```python
def gen_with_seed(seed, bits=512):
    rnd = random.Random(seed)
    p = nextprime(rnd.getrandbits(bits))
    q = nextprime(rnd.getrandbits(bits))      # 顺序也必须一致
    return p, q

for seed in range(T - w, T + w + 1):
    p, _ = gen_with_seed(seed)
    if n % p == 0:
        return p, n // p, seed
```

## 易错点

1. **调用序列必须逐字对齐**：`getrandbits` 的位数、先 p 后 q 的顺序、`nextprime` 前是否还消耗过随机数。差一步就整条流错位，怎么爆都不中。
2. **先拿生成脚本再写复现**，不要凭题目描述猜取素方式（`getPrime` 与 `getrandbits+nextprime` 是两条不同的流）。
3. 耗时 = 候选数 × 单次生成耗时。实测 601 个候选 5.7s，7201 个 65s——**窗口按秒数×4 估，别一上来开一天**。
4. `time.time()` 是 UTC 秒；题面给的是本地时间要换算时区，否则窗口整段错开。
5. 固定种子题通常只给一个 32 位以内的整数，直接单点复现，不需要爆破。

## 验证记录（2026-11-03，实测输出）

```text
n bits = 1023  给定窗口 = 601 个候选种子
命中 seed=1767225737（真实 1767225737），耗时 5.68s
分解成功: True
```

- 同一脚本把窗口放到 7201 个候选（前后各一小时）耗时 65.4s，仍是可接受量级。
- 结论：这类题难度完全在"复现调用序列"，不在算力；单次 `nextprime(512 位)` 约 9ms，决定了爆破上限约 100 个种子/秒。

*最后更新：2026年11月3日*
