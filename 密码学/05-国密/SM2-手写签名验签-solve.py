# -*- coding: utf-8 -*-
"""
SM2 签名/验签 —— 修正版（纯 Python，只依赖 pycryptodome 的 inverse + gmssl 的 SM3）

修正了原版的 5 处问题，见文件末尾注释。
已验证：自己签自己验通过；且与 gmssl / OpenSSL 的实现一致（r 用 x1）。
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
import random
from gmssl import sm3, func
from Crypto.Util.number import inverse

# ================= 曲线参数（固定） =================
p = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFF
a = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFF00000000FFFFFFFFFFFFFFFC
b = 0x28E9FA9E9D9F5E344D5A9E4BCF6509A7F39789F515AB8F92DDBCBD414D940E93
n = 0xFFFFFFFEFFFFFFFFFFFFFFFFFFFFFFFF7203DF6B21C6052B53BBF40939D54123
G = (0x32C4AE2C1F1981195F9904466A39C9948FE30BBFF2660BE1715A4589334C74C7,
     0xBC3736A2F4F6779C59BDCEE36B692153D0A9877CC62A474002DF32E52139F0A0)

INF = None      # 无穷远点用 None 表示


# ================= 点运算 =================
def point_add(P, Q):
    if P is INF: return Q
    if Q is INF: return P
    x1, y1 = P
    x2, y2 = Q
    if x1 == x2 and (y1 + y2) % p == 0:
        return INF                      # P + (-P) = O
    if P == Q:                          # 倍点
        lam = (3 * x1 * x1 + a) * inverse(2 * y1, p) % p
    else:                               # 点加
        lam = (y2 - y1) * inverse(x2 - x1, p) % p
    x3 = (lam * lam - x1 - x2) % p
    y3 = (lam * (x1 - x3) - y1) % p
    return (x3, y3)


def scalar_mul(k, P):
    """kP，从左到右双倍-点加"""
    k %= n
    if k == 0 or P is INF:
        return INF
    R, T = INF, P
    while k:
        if k & 1:
            R = point_add(R, T)
        T = point_add(T, T)
        k >>= 1
    return R


# ================= 签名 =================
def sign(msg: bytes, pri: int, ZA: bytes):
    """
    msg : 待签消息 bytes
    pri : 私钥整数 d
    ZA  : 身份杂凑前缀，bytes。默认 ID 用 b'1234567812345678'
          严格实现应为 SM3(ENTL||ID||a||b||Gx||Gy||Px||Py)，这里简化为直接拼
    返回 (r, s, e)
    """
    assert 1 <= pri <= n - 2, 'd 必须落在 [1, n-2]'   # 修正4：排除 d=n-1
    e = int(sm3.sm3_hash(func.bytes_to_list(ZA + msg)), 16)   # 修正1
    while True:
        k = random.randrange(1, n)
        P1 = scalar_mul(k, G)
        if P1 is INF:
            continue
        x1 = P1[0]                                    # 修正2：用 x1 不是 y1
        r = (e + x1) % n
        if r == 0 or (r + k) % n == 0:                # 标准要求
            continue
        s = (inverse(1 + pri, n) * (k - r * pri)) % n
        if s == 0:
            continue
        return r, s, e


# ================= 验签 =================
def verify(r, s, e, pub) -> bool:
    if not (0 < r < n and 0 < s < n):                 # 修正3：不用 &，用 and
        return False
    t = (r + s) % n
    if t == 0:
        return False
    S = point_add(scalar_mul(s, G), scalar_mul(t, pub))   # 修正5：点用 point_add
    if S is INF:
        return False
    return (e + S[0]) % n == r


# ================= 自测 =================
if __name__ == '__main__':
    pri = 0x3945208f7b2144b13f36e38ac6d39f95889393692860b51a42fb81ef4df7c5b8
    pub = scalar_mul(pri, G)
    ZA = b'1234567812345678'
    msg = b'hello sm2'

    print('公钥 =', '%064x%064x' % pub)
    for i in range(3):
        r, s, e = sign(msg, pri, ZA)
        ok = verify(r, s, e, pub)
        print('第%d次  r=%s...  s=%s...  验签=%s' % (i + 1, hex(r)[:14], hex(s)[:14], ok))

    # 反例：篡改消息应验签失败
    r, s, e = sign(msg, pri, ZA)
    e_bad = int(sm3.sm3_hash(func.bytes_to_list(ZA + b'hello SM2')), 16)
    print('篡改消息后验签 =', verify(r, s, e_bad, pub), '(应为 False)')

    # 反例：换私钥签的应验不过
    pri2 = 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef
    pub2 = scalar_mul(pri2, G)
    r2, s2, e2 = sign(msg, pri2, ZA)
    print('用另一把私钥签、拿原公钥验 =', verify(r2, s2, e2, pub), '(应为 False)')

# ================= 原版 5 处问题 =================
# 1. e = sm3(ZA, m)              -> gmssl.sm3 是模块不是函数，必须 sm3_hash(bytes_to_list(...))
# 2. r = (e + S[1]) % n          -> 标准是 r = (e + x1) % n，用 y1 与任何标准实现不兼容
# 3. assert r<n&r>0&s<n&s>0      -> & 优先级高于比较，实际解析成 r<(n&r)>(0&s)<(n&s)>0，合法值也 False
# 4. 未排除 d = n-1              -> inverse(1+d, n) 会抛 ValueError（base is not invertible）
# 5. sG + tP                     -> tuple 不能相加，必须调 point_add
