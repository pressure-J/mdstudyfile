---
title: Python 语法基础速查(CTF解题向)
tags: [python]
created: '2026-09-09T12:00:00.000Z'
modified: '2026-09-09T12:00:00.000Z'
---

# Python 语法基础速查(CTF 解题向)

> 目标:能独立读懂/写出 CTF 解题脚本。每个概念都配"解题场景"的例子。
> 建议配合 `py xxx.py` 实际运行看输出。本文只讲核心,不讲全部。

## 1. 变量与类型(不声明类型)

```python
x = 5          # 整数 int
y = 3.14       # 浮点 float
s = "flag{abc}"  # 字符串 str
b = True       # 布尔 bool
n = None       # 空值

# 类型随时可查可转
print(type(x))          # <class 'int'>
print(int("42"))        # 字符串转整数 42
print(str(42))          # 整数转字符串 "42"
print(hex(255))         # '0xff'  常用!大数转十六进制
print(int("ff", 16))    # 'ff' 十六进制转十进制 255
```

**CTF 场景**:RSA 里 `hex(m)` 看明文、`int(密文串, 16)` 还原大整数。

## 2. 字符串操作(高频)

```python
s = "NSSCTF{hello_world}"

print(len(s))            # 19 长度
print(s[0])              # 'N' 按下标取(从0开始)
print(s[-1])             # '}' 负数=从末尾取
print(s[5:10])           # 'F{hel' 切片 [起:止) 左闭右开
print(s[5:-1])           # 'F{hello_world' 去掉最后一个字符  ← 超常用
print(s.lower())         # 全部小写
print(s.upper())         # 全部大写
print(s.replace("_", " "))   # 替换  ← 陇剑杯提示"空格换下划线"就用它
print(s.startswith("NS"))    # True
print(s.endswith("}"))       # True
print("flag" in s)           # True 判断子串是否存在
```

**CTF 场景**:`flag[5:-1]` 去掉 `flag{` 和 `}` 取中间;`replace(" ","_")` 换分隔符。

## 3. 列表 list(数组,可增删)

```python
arr = [1, 2, 3, "a", "b"]
print(len(arr))          # 5
print(arr[0])            # 1
arr.append(4)            # 末尾加元素 → [1,2,3,"a","b",4]
arr.pop()                # 删末尾 → [1,2,3,"a","b"]
arr.pop(0)               # 删下标0 → [2,3,"a","b"]
arr = sorted(arr, key=str)  # 排序(按字符串序)
print(arr)

# 列表推导式(★必会,CTF 极常用)
# [表达式 for 元素 in 序列 if 条件]
nums = [1, 2, 3, 4, 5]
squares = [n * n for n in nums]            # [1,4,9,16,25]
evens = [n for n in nums if n % 2 == 0]    # [2,4]

# 把字符串拆成字符列表 / 列表拼成字符串
chars = list("abc")        # ['a','b','c']
s = ''.join(chars)         # 'abc'
```

**CTF 场景**:`[chr(x) for x in [72,105]]` 把 ASCII 列表变字符串;`''.join(...)` 拼 flag。

## 4. 字典 dict(key→value,像映射表)

```python
d = {"name": "ctf", "score": 100}
print(d["name"])        # ctf 取值
d["new"] = "yes"        # 加键值对
print(d.get("x", 0))    # 取不到返回默认值 0,不会报错
print(d.keys())         # 所有键
print(d.values())       # 所有值
print(d.items())        # 所有 (键,值) 对

# 遍历字典(★常用)
for k, v in d.items():
    print(k, v)

# 用字典做计数(★CTF 频率统计)
from collections import Counter
freq = Counter("aabbbc")
print(freq)             # Counter({'b':3,'a':2,'c':1})
print(freq.most_common(1))  # [('b',3)] 最高频
```

**CTF 场景**:字母频率分析(替换密码)、词频统计、建立映射表。

## 5. 条件 if / elif / else

```python
x = 10
if x > 100:
    print("大")
elif x > 5:
    print("中")       # 走这里
else:
    print("小")

# 条件里常用运算符
# == 等于, != 不等于, > < >= <=
# and 且, or 或, not 非
# in 包含判断
if "flag" in "my flag" and x == 10:
    print("ok")
```

**CTF 场景**:判断解密结果是否像明文(`if "flag" in text`)。

## 6. 循环 for / while

```python
# for 遍历
for i in range(5):       # 0,1,2,3,4
    print(i)
for i in range(2, 8, 2): # 2,4,6 (起,止,步长)
    print(i)
for ch in "abc":         # 遍历字符串
    print(ch)
for i, v in enumerate([10,20]):  # 带下标 (0,10),(1,20)
    print(i, v)

# while 循环
n = 5
while n > 0:
    n -= 1

# 暴力爆破(★CTF 核心):试所有可能
for key in range(0, 256):      # 单字节 XOR 爆破 256 个
    print(key)
```

**CTF 场景**:爆破位移、爆破 XOR key、逐字符试 flag。

## 7. 函数 def

```python
def add(a, b):
    return a + b

result = add(3, 4)   # 7

# 默认参数、返回多个值
def parse(s, prefix="flag{"):
    if s.startswith(prefix):
        return s[len(prefix):-1], True   # 返回元组(可解包)
    return s, False

inner, ok = parse("flag{abc}")
print(inner, ok)   # abc True
```

**CTF 场景**:把解题逻辑封装成函数,换个题只改参数不改代码。

## 8. 文件读写(CTF 必备)

```python
# 读文本
data = open("key.txt", "r").read()          # 整个读成字符串
lines = open("data.txt").readlines()        # 每行一个元素

# 读二进制(★加密/图片/内存数据都是二进制)
raw = open("file.enc", "rb").read()         # 得到 bytes

# 写
open("out.txt", "w").write("result")
open("out.bin", "wb").write(raw_bytes)

# 推荐 with 写法(自动关文件)
with open("file.enc", "rb") as f:
    data = f.read()
```

**CTF 场景**:读密文文件、读内存 dump 出的二进制、写解密结果。

## 9. 字节与编码(加密题核心)

```python
b = b"\x66\x6c\x61\x67"     # bytes 字面量
print(b.decode())            # 'flag' bytes→字符串

s = "flag"
print(s.encode())            # b'flag' 字符串→bytes

# 整数 ↔ 字节(★RSA 解出 m 转明文)
m = 123456789
byte_len = (m.bit_length() + 7) // 8
mb = m.to_bytes(byte_len, 'big')     # 整数→bytes
print(mb.decode(errors='ignore'))

# 十六进制 ↔ bytes
h = "666c6167"
print(bytes.fromhex(h))              # b'flag'
print(b"flag".hex())                 # '666c6167'

# base64
import base64
print(base64.b64encode(b"flag").decode())   # ZmxhZw==
print(base64.b64decode("ZmxhZw=="))         # b'flag'
```

**CTF 场景**:RSA `m.to_bytes(...).decode()` 出 flag;hex/base64 互转。

## 10. 常用内建函数

```python
len()     # 长度
int() str() float() hex() bin() ord() chr()   # 类型转换
ord("a")  # 97 字符→ASCII
chr(97)   # 'a' ASCII→字符
max() min() sum() abs()
range()   # 造数字序列
sorted(list, reverse=True)   # 排序
enumerate(list)              # 带下标遍历
zip(a, b)                    # 两个列表成对打包
filter / map                 # 过滤/映射(进阶)
```

**CTF 场景**:`ord/chr` 逐字符转换、`zip` 两个数组配对。

## 11. 模块导入

```python
import math                    # 数学
import hashlib                 # MD5/SHA 哈希
import re                      # 正则(文本提取)
from collections import Counter  # 计数
import itertools               # 排列组合(爆破)

# 第三方(密码学题常用,SageMath python 自带)
from Crypto.Cipher import AES, ARC4
from Crypto.Hash import SHA256, HMAC, MD5
from Crypto.Util.number import long_to_bytes, bytes_to_long, inverse
from Crypto.Util import Counter, Padding
```

## 12. 最容易卡住的三个坑

1. **`[a:b]` 是左闭右开**:`s[0:5]` 取下标 0-4,不含 5。忘了就错一位。
2. **bytes 和 str 不能混用**:`b"x" + "y"` 报错,先 `.decode()` 或 `.encode()`。
3. **整数除法**:`5/2` = 2.5(Py3),要整数用 `5//2` = 2。大数千万别用 `/`。

---

## 自测:能不能独立读懂这个脚本?

```python
from Crypto.Cipher import AES
from Crypto.Util import Counter

data = open("enc.bin", "rb").read()
iv = bytes.fromhex("78CD48D513756101A4350B4C7104DFDA")
key = __import__("hashlib").sha256(b"password").digest()[:16]

ctr = Counter.new(128, initial_value=int.from_bytes(iv, "big"), little_endian=False)
dec = AES.new(key, AES.MODE_CTR, counter=ctr).decrypt(data)
print(dec.decode(errors="ignore"))
```

试着不看答案,说出每一行在干什么。能说出来 = 这一章达标。

*最后更新：2026年9月9日*