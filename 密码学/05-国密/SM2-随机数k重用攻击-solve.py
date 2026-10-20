# -*- coding: utf-8 -*-
"""
国密 SM2 —— 签名随机数 k 重用攻击 solve 脚本

适用特征：
    给出两组 SM2 签名（同一签名者、同一坏随机数 k），或只给 (r,s) 对 + 消息。
    判定征兆：由 r 反推 x1 = (r - e) mod n，两组 x1 相同 → k 重用。

题目数据（本脚本已填一组自洽演示数据，换题只改下面 6 行）
用法: 换题把 R1/S1/E1/R2/S2/E2 换成题面给的十六进制即可。
      E 值 = SM3(ZA || M)，若题面只给消息没给 e，用 sm3_z() 自己算。
"""
import binascii
from gmssl import sm2 as G

# ================= 换题只改这几行 =================
R1 = 0xfeda69ee52bdbdc80756f67d2560d8c3e7be43ced00e7072efe5dfb73c163cd1
S1 = 0x111cb2a6188b786ea97a6084bb11fca4fd7add53c1a423ab9225f9c4343e3aa4
E1 = 0x0833e242fb78e7fc4d39fd3fa12a975471fa950af8abef259992cb07469bb2d8
R2 = 0xa5610ffe2446fe2c4fbaafc85dd07a05875a99361f3ff3c15b637707d3bc732f
S2 = 0x17ee62e296912cef43526a4304265d2bc423ddd0b20b007ce7014baec96105bd
E2 = 0xaeba8851cd022860959db68ad99a3895839ac9dd69a3779f58cc566118172a59
# 仅用于自检，真实解题时删掉/填 None
D_TRUE = 0x3945208f7b2144b13f36e38ac6d39f95889393692860b51a42fb81ef4df7c5b8
# =================================================

n = int(G.default_ecc_table['n'], 16)
g = G.default_ecc_table['g']


def sm3_z(msg: bytes, pub_hex: str) -> int:
    """按 GM/T 0003 计算 e = SM3(ZA || M)，ZA 绑定签名者身份"""
    c = G.CryptSM2(private_key='0' * 64, public_key=pub_hex)
    return int(c._sm3_z(msg), 16)


def recover_private_key(r1, s1, e1, r2, s2, e2):
    """
    SM2:  s = (1+d)^-1 * (k - r*d) mod n
    相减: s1 - s2 = (1+d)^-1 * d * (r2 - r1)
    令 t = (s1-s2)/(r2-r1) = d/(1+d)
    =>  d = t/(1-t)
    """
    t = (s1 - s2) * pow(r2 - r1, -1, n) % n
    return t * pow(1 - t, -1, n) % n


def recover_k(r, s, e, d):
    """由 s = (1+d)^-1(k - rd) 反解 k"""
    return (s * (1 + d) + r * d) % n


def main():
    print('[*] n =', '%064x' % n)
    print()
    print('[1] 第 1 组签名签名者公钥点 x 坐标反推（检测 k 重用）')
    x1a = (R1 - E1) % n
    x1b = (R2 - E2) % n
    print('    x1(第1次) =', '%064x' % x1a)
    print('    x1(第2次) =', '%064x' % x1b)
    print('    -> x 坐标相同，判定 k 重用:', x1a == x1b)
    if x1a != x1b:
        print('    [!] 未命中，说明两组签名不是同一个 k')

    print()
    print('[2] 恢复私钥')
    t = (S1 - S2) * pow(R2 - R1, -1, n) % n
    d = t * pow(1 - t, -1, n) % n
    print('    t = (s1-s2)/(r2-r1) =', '%064x' % t)
    print('    d = t/(1-t)          =', '%064x' % d)

    print()
    print('[3] 自检：用恢复的 d 反推 k')
    k = recover_k(R1, S1, E1, d)
    print('    k(恢复) =', '%064x' % k)

    # 用恢复出的 d 和 k 验证能重算出一致的签名
    cc = G.CryptSM2(private_key='%064x' % d, public_key='')
    P = cc._kg(k, g)
    xk = int(P[:64], 16)
    r_check = (E1 + xk) % n
    print('    用 d 和 k 重算 r1 =', '%064x' % r_check)
    print('    与题面 r1 一致:', r_check == R1)

    if D_TRUE is not None:
        print()
        print('[4] 与真实私钥对照:', 'MATCH ✅' if d == D_TRUE else 'MISMATCH ❌')
        print('    真实 d =', '%064x' % D_TRUE)

    print()
    print('[!] 反例：套用 ECDSA 公式 k=(e1-e2)/(s1-s2) 在这里是错的')
    print('    SM2 的 s = (1+d)^-1(k-rd) 与 ECDSA 的 s = k^-1(z+rd) 形式不同，')
    print('    照抄 ECDSA 公式只能得到垃圾值。')
    k_wrong = (E1 - E2) * pow(S1 - S2, -1, n) % n
    print('    k(错公式) =', '%064x' % k_wrong)
    print('    k(正确)   =', '%064x' % k)


if __name__ == '__main__':
    main()
