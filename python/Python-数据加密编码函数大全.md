---
tags: [python, crypto]
title: Python 数据加密编码函数大全
created: '2026-09-08T00:00:00.000Z'
modified: '2026-09-08T00:00:00.000Z'
---

# Python 数据编码与加密函数大全

> 来源：CTF 密码学 / 通用开发中需要对数据进行编码、哈希、对称加密、非对称加密的场景。

## 零、先分清四类概念

| 类别 | 是否可逆 | 代表库 | 典型函数 | 用途 |
|---|---|---|---|---|
| 编码 | ✅ 可逆 | `base64`、`binascii`、`urllib` | `b64encode`、`hexlify` | 数据格式转换，不是加密 |
| 哈希 | ❌ 不可逆 | `hashlib`、`hmac` | `md5()`、`sha256()` | 指纹、校验、存密码 |
| 对称加密 | ✅ 可逆 | `pycryptodome`、`cryptography` | `AES.new`、`DES.new` | 加解密同一把密钥 |
| 非对称 | ✅ 可逆 | `pycryptodome`、`cryptography` | `RSA.encrypt`、`generate_rsa` | 公私钥，签名 |

> ⚠️ **编码 ≠ 加密**：base64/hex 只是换个表示方式，任何人能还原，**不能当加密用**。

## 一、编码类（base64 等）

内置库，无需安装。

### base64

```python
import base64

s = b"hello"
enc = base64.b64encode(s)      # b'aGVsbG8='
dec = base64.b64decode(enc)    # b'hello'
```

变体：
- `base64.urlsafe_b64encode` — URL 安全（`-`/`_` 替换 `+`/`/`）
- `base64.b32encode` / `b32decode` — base32
- `base64.b16encode` / `b16decode` — 等价 hex
- `base64.b64decode(s, validate=True)` — 严格校验

### hex（binascii）

```python
import binascii

binascii.hexlify(b"abc")    # b'616263'
binascii.unhexlify("616263")  # b'abc'

int("616263", 16)            # 0x616263 → 6382179
bytes.fromhex("616263")      # b'abc'（也可用 bytes.hex()）
```

### URL 编码 / ROT13

```python
import urllib.parse
urllib.parse.quote("a b&c")   # 'a%20b%26c'
urllib.parse.unquote("a%20b")  # 'a b'

import codecs
codecs.encode("abc", "rot13")  # 'nop'（凯撒位移 13，经典 CTF）
```

## 二、哈希类（hashlib / hmac）

单向不可逆，用于指纹、校验、存密码。

### hashlib

```python
import hashlib

data = b"hello"
h = hashlib.md5(data).hexdigest()      # 32 位十六进制
s = hashlib.sha1(data).hexdigest()     # 40 位
h256 = hashlib.sha256(data).hexdigest()# 64 位
h512 = hashlib.sha512(data).hexdigest()# 128 位

# 大文件分块更新
h = hashlib.sha256()
h.update(b"hello "); h.update(b"world")
h.hexdigest()
```

常用属性：
- `.hexdigest()` — 十六进制字符串
- `.digest()` — 原始 bytes
- `hashlib.new('md5', data)` — 按名字创建

> ⚠️ **CTF 坑**：`hashlib.update()` 只收 **bytes**，收 str 会报 `TypeError: Strings must be encoded before hashing`，先 `.encode()`。

### hmac（带密钥的消息认证）

```python
import hmac, hashlib
h = hmac.new(key=b"secret", msg=b"data", digestmod=hashlib.sha256)
h.hexdigest()
```

## 三、对称加密（pycryptodome）

需安装：`pip install pycryptodome`。导入名是 `Crypto`（大写的 C）。

### AES

```python
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import base64

key  = b"0123456789abcdef"          # 16/24/32 字节 = AES-128/192/256
iv   = b"0000000000000000"          # 16 字节
data = b"hello world"               # 必须是 bytes

cipher = AES.new(key, AES.MODE_CBC, iv)
ct = cipher.encrypt(pad(data, AES.block_size))        # 需要 padding
# 传输：base64
b64 = base64.b64encode(ct)

# 解密
cipher = AES.new(key, AES.MODE_CBC, iv)
pt = unpad(cipher.decrypt(base64.b64decode(b64)), AES.block_size)
```

常用模式：`AES.MODE_CBC`（需 IV）、`AES.MODE_ECB`（无需 IV，不推荐）、`AES.MODE_GCM`（带认证）。

### 其他对称

```python
from Crypto.Cipher import DES, ChaCha20

# DES（8 字节密钥）
DES.new(b"01234567", DES.MODE_ECB).encrypt(pad(data, 8))

# ChaCha20（随机 nonce）
cipher = ChaCha20.new(key=b"0"*32)
ct = cipher.nonce + cipher.encrypt(data)
```

## 四、非对称 / RSA（pycryptodome）

```python
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_OAEP
import base64

# 1. 生成密钥
key = RSA.generate(2048)
priv = key.export_key().decode()   # PEM 私钥
pub  = key.publickey().export_key().decode()  # PEM 公钥

# 2. 用公钥加密（公钥只做加密）
rsa_pub = RSA.import_key(pub)
cipher = PKCS1_OAEP.new(rsa_pub)
ct = base64.b64encode(cipher.encrypt(b"secret data"))

# 3. 用私钥解密
rsa_priv = RSA.import_key(priv)
cipher = PKCS1_OAEP.new(rsa_priv)
pt = cipher.decrypt(base64.b64decode(ct))
```

### RSA 常用属性（CTF 必用）

```python
key = RSA.import_key(open("pub.pem").read())
n = key.n          # 模数
e = key.e          # 公钥指数
d = key.d          # 私钥指数（只有私钥对象才有）
p, q = key.p, key.q   # 两个素数因子（只有私钥对象才有）
```

> ⚠️ 公开的 **n、e** 只能算公钥，CTF 里拿到 `n, e, c` 后，加密用 `pow(m, e, n)`，解密要 `pow(c, d, n)`，`d` 需分解 n 才能求。

## 五、快速速查表

| 需求 | 函数 | 可逆 |
|---|---|---|
| base64 编码 | `base64.b64encode` | ✅ |
| hex 编码 | `binascii.hexlify` | ✅ |
| URL 编码 | `urllib.parse.quote` | ✅ |
| ROT13 | `codecs.encode(x,'rot13')` | ✅ |
| MD5 哈希 | `hashlib.md5(x).hexdigest()` | ❌ |
| SHA256 | `hashlib.sha256(x).hexdigest()` | ❌ |
| HMAC | `hmac.new(k,m,hashlib.sha256)` | ❌ |
| AES 加密 | `AES.new(k,MODE_CBC,iv)` | ✅ |
| RSA 加密 | `PKCS1_OAEP.new(pubkey)` | ✅ |

## 六、总结

1. **编码**（base64/hex/url）只是换格式，不是加密，用内置库。
2. **哈希**（hashlib）不可逆，做校验/指纹；`update()` 要 bytes。
3. **对称加密**（AES/DES/ChaCha20）一把密钥加解密，用 pycryptodome 的 `Crypto`。
4. **非对称**（RSA）公私钥，公钥加密私钥解密，CTF 里配合 `pow` 直接用大数运算。
5. 所有加密函数操作对象都是 **bytes**，字符串要先 `.encode()`。

*最后更新：2026年9月8日*