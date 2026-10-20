---
tags: [python]
title: 文本文件读取与正则提取
created: '2026-09-08T00:00:00.000Z'
modified: '2026-09-08T00:00:00.000Z'
---

# Python 读取文本文件并提取 n、e 为列表

> 来源：CTF RSA 题给了一个存有 20 组 `n = ...`、`e = 65537` 的文本文件，需要把整数读成 Python 列表继续解题。

## 一、核心需求

文件内容是这种格式（顶部声明一个 e，下面每块一个 n/c）：

```
m = xxxxxxxx
e = 65537
========== n c ==========
n = 204749188940517785333052623456018809280882844711218237540497253540724771558...
c = 974463908243330865728978769213595400782053398596897741316275722596415018912...
n = 209188199606488913494382630469549022109591464078609807421659302537813187592...
```

目标：把 **20 个 `n`** 读成一个整数列表 `ns`，把 **所有 `e`** 读成列表 `es`。

## 二、读取 + 正则提取

```python
import re

text = open(r'C:\Users\徐利杰\Downloads\1.txt', encoding='utf-8').read()

ns = [int(x) for x in re.findall(r'n = (\d+)', text)]   # 20 个 n（int）
es = [int(x) for x in re.findall(r'e = (\d+)', text)]   # 所有 e（20 个 65537）

print(ns)
print(es)
```

运行结果：`ns` 长度 20，`es` 长度 20（全是 65537）。

## 三、关键点逐条解释

### 1. `open(..., encoding='utf-8')` —— 指定编码

- Windows 上默认编码是 `gbk`，若文件是 UTF-8 且含中文/特殊字符，不加 `encoding='utf-8'` 会报 `UnicodeDecodeError`。
- 本题文件其实全 ASCII，但养成习惯永远显式指定 `encoding` 最稳妥。

### 2. `re.findall(r'n = (\d+)', text)` —— 抓所有匹配

- `re.findall` 返回**所有**匹配的分组内容，得到字符串列表。
- `\d+` 匹配连续数字；`(\d+)` 是捕获组，只取括号里那段（即 `= ` 后面的整数）。
- 结果 `ns` 是**字符串列表**，要用于 RSA 运算需转成 int。

### 3. `int(x)` 列表推导 —— 字符串 → 整数

```python
ns = [int(x) for x in re.findall(r'n = (\d+)', text)]
```

把每个提取出来的十进制数字字符串转成整数，得到可直接算 RSA 的大数列表。

### 4. `re.findall` vs `re.search` —— 全部 vs 单个

- `re.findall` → 所有匹配，返回**列表**。
- `re.search` → 只返回第一个匹配（一个 match 对象），取 `.group()` 得到内容。

```python
e = int(re.search(r'e = (\d+)', text).group(1))  # 只取第一个 e
```

若文件顶部已声明唯一一个 e，用 `re.search` 更清晰；若每块都有重复 e，用 `re.findall`。

## 四、常见坑

| 坑 | 现象 | 解决 |
|---|---|---|
| 忘了 encoding | `UnicodeDecodeError: 'gbk' codec` | `open(..., encoding='utf-8')` |
| 路径含中文/空格 | `FileNotFoundError` | 用 `r'...'` 原始字符串或 `\\` 转义 |
| 忘了转 int | 后续 `pow`/解密报类型错 | `int(x)` |
| 手写 open 不关 | 资源占用 | 用 `with open(...) as f:` 自动关闭 |

推荐写法（with 自动关文件）：

```python
with open(r'路径', encoding='utf-8') as f:
    text = f.read()
```

## 五、完整可跑脚本

```python
import re

with open(r'C:\Users\徐利杰\Downloads\1.txt', encoding='utf-8') as f:
    text = f.read()

ns = [int(x) for x in re.findall(r'n = (\d+)', text)]
es = [int(x) for x in re.findall(r'e = (\d+)', text)]

print(f"共 {len(ns)} 个 n")
print(ns)
print("e =", set(es))   # 用 set 看是否所有 e 一致
```

## 六、小结

1. `open(encoding='utf-8').read()` 读全文 → `re.findall` 正则抓分组 → `int()` 转整数 → 列表推导成 list。
2. `re.findall` 取全部，`re.search` 取首个。
3. 永远显式指定 `encoding`，路径用原始字符串 `r'...'`，用 `with` 管理文件生命周期。

*最后更新：2026年9月8日*