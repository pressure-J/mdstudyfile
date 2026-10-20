---
tags: [python]
title: str与bytes编码
created: '2026-09-04T12:00:00.000Z'
modified: '2026-09-04T12:00:00.000Z'
---

# Python3 语法：str 与 bytes 编码

> 来源：CTF MD5 爆破脚本报错 `TypeError: Strings must be encoded before hashing` 引出的 Python 语法知识点

## 一、核心概念：str 和 bytes 是两种东西

Python 2 到 Python 3 最大的区别之一：字符串的"身份"变了。

| | Python 2 | Python 3 |
|---|---|---|
| str | 本质是字节序列 | 是 Unicode 文本（字符序列） |
| 字节类型 | 无独立类型 | bytes |
| `'中'` 的长度 | 按字节数算 | 按字符数算，len = 1 |
| 遍历字符串 | 得到字符 | 得到字符（str）或整数（bytes） |

```python
s = 'abc'          # str，文本
b = b'abc'         # bytes，二进制，显示带 b 前缀
print(type(s))     # <class 'str'>
print(type(b))     # <class 'bytes'>
print(len('中'))        # 1   （字符数）
print(len('中'.encode()))  # 3 （UTF-8 编码后 3 个字节）
```

## 二、为什么会报 "Strings must be encoded before hashing"

`hashlib` 的 `update()` 只收 bytes——哈希是对"字节"做运算，不是对"文本"。文本必须先编码成字节：

```python
import hashlib
m = hashlib.md5()
m.update('abc')            # ❌ TypeError: Strings must be encoded before hashing
m.update('abc'.encode())   # ✅ 先转 bytes
```

**口诀：hashlib 只吃 bytes，喂之前先 `.encode()`。** 网上老 writeup（Python 2 时代）抄到 Python 3 必踩这个坑。

## 三、encode() / decode() 双向转换

```python
'中'.encode('utf-8')          # b'\xe4\xb8\xad'  文本 → 字节
b'\xe4\xb8\xad'.decode('utf-8')  # '中'            字节 → 文本
```

- 默认编码 UTF-8，参数可省略
- 方向用错会报 `AttributeError: 'bytes' object has no attribute 'encode'`（bytes 只能 decode 回文本）

## 四、什么时候必须 bytes（常见场景）

| 场景 | 要求 |
|---|---|
| `hashlib.update()` | bytes |
| 文件二进制读写 `'rb' / 'wb'` | bytes |
| `socket.send()` | bytes |
| `base64.b64encode(x)` | 输入输出都是 bytes（结果要 `.decode()` 才是字符串） |
| `json.dumps()` / `print()` | str（反过来，bytes 要 decode 才能打印成文本） |

## 五、脚本里其他常用语法

### chr() / ord()：数字和字符互转

```python
chr(65)   # 'A'   数字 → 字符
ord('A')  # 65    字符 → 数字
```

爆破脚本里 `chr(i)` 就是拿 ASCII 码数字拼出字符。

### `in` 运算符：字符串子串判断

```python
'e9032' in 'e9032994dabac08080091151380478a2'  # True，判断"是否包含子串"
3 in [1, 2, 3]                                  # True，也用于列表成员判断
```

注意 `in` 是"包含"不是"相等"；多个片段用 `and` 做交集筛选。`'da'` 这种短片段很容易命中，片段越多筛选越准。

### range() 右开区间

```python
range(32, 127)   # 生成 32~126，不包含 127
list(range(3))   # [0, 1, 2]
```

CTF 爆破里 `range(32, 127)` = 空格(32) 到 `~`(126) 的全部可打印 ASCII，共 95 个字符。

## 六、识别 Python 2 老代码（网上的 writeup 常见）

看到这些特征基本是 Py2 写的，抄进 Py3 要改：

- `m.update('字符串')` 直接传 str → 加 `.encode()`
- `print 'xxx'` 不带括号 → 改 `print('xxx')`
- `xrange` → 直接 `range` 即可（Py3 的 range 就是迭代器）

**通用改写套路**：字符串要喂给"字节系" API（hashlib / 文件 / socket / base64）时一律 `.encode()`；从这些 API 拿回来的 bytes 要 `print` 前先 `.decode()`。

*最后更新：2026年9月4日*