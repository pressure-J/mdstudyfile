# -*- coding: utf-8 -*-
"""
国密 SM4 —— 工作模式攻击 solve 脚本（零依赖纯 Python）

覆盖三种最高频考点：
  1. ECB  → 相同明文块产生相同密文块，可检测重复 / 猜测 / 块重排
  2. CBC  → 篡改前一个密文块，可精确控制后一个明文块的对应字节（比特翻转）
  3. OFB/CTR → IV 复用 = 密钥流复用，C_a ^ C_b ^ P_a = P_b

依赖：pip install gmssl（本机已装）。gmssl 的 CryptSM4 只有 ECB/CBC，
      OFB 这里用 one_round 自己拼（避免依赖 openssl 命令行）。

用法：按注释改下面的 KEY / IV / 数据，直接 py 本脚本.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8')
from gmssl import sm4

# ================= 换题只改这几行 =================
KEY = bytes.fromhex('0123456789abcdeffedcba9876543210')
IV = bytes(16)

# 考点1 ECB：明文（按 16 字节切块，块0 与 块2 故意相同）
ECB_PLAIN = b'NAME=alice______' * 2 + b'NAME=bob________'

# 考点2 CBC：想让哪个字节变成什么
CBC_PLAIN = b'SESSION=AAAAAAA' + b'role=guest' + b'XXXXXX'
CBC_TARGET_OFFSET = 4          # 第二块内偏移（role=guest 的 'g' 在 4）
CBC_TARGET_CHAR = b'G'         # 想把 'g' 改成 'G'

# 考点3 OFB：两组同 IV 的明密文，已知其中一组明文
OFB_PA = b'card_num=6228480010301477'
OFB_CB = None                  # 另一组密文（hex）；None 则脚本自造演示
# =================================================


def enc_block(key, b):
    c = sm4.CryptSM4()
    c.set_key(key, sm4.SM4_ENCRYPT)
    return bytes(c.one_round(c.sk, list(b)))


def dec_block(key, b):
    c = sm4.CryptSM4()
    c.set_key(key, sm4.SM4_DECRYPT)
    return bytes(c.one_round(c.sk, list(b)))


def ofb_keystream(key, iv, n):
    """OFB 密钥流：反复加密 iv，串起来截取 n 字节"""
    out = b''
    cur = iv
    while len(out) < n:
        cur = enc_block(key, cur)
        out += cur
    return out[:n]


def ctr_keystream(key, iv, n):
    """CTR 密钥流：iv 每块 +1 后加密"""
    out = b''
    cnt = int.from_bytes(iv, 'big')
    while len(out) < n:
        out += enc_block(key, cnt.to_bytes(16, 'big'))
        cnt += 1
    return out[:n]


def pad16(b):
    return b + bytes(-len(b) % 16)


def main():
    print('=' * 68)
    print('[考点1] ECB —— 相同明文块 -> 相同密文块')
    print('=' * 68)
    pt = pad16(ECB_PLAIN)
    blocks = [pt[i:i + 16] for i in range(0, len(pt), 16)]
    cbs = [enc_block(KEY, b) for b in blocks]
    for i, (pb, cb) in enumerate(zip(blocks, cbs)):
        print('  明文块%d = %-18r 密文块%d = %s' % (i, pb, i, cb.hex()))
    # 找重复
    seen = {}
    dups = []
    for i, cb in enumerate(cbs):
        if cb in seen:
            dups.append((seen[cb], i))
        else:
            seen[cb] = i
    print('  重复密文块索引对:', dups if dups else '无')
    if dups:
        a, b = dups[0]
        print('  => 块 %d 与块 %d 明文相同，攻击者据此推断明文结构' % (a, b))
        # 块重排：把两个块的密文互换，解密后明文顺序被改
        sw = cbs[:]
        sw[a], sw[b] = sw[b], sw[a]
        dec = b''.join(dec_block(KEY, x) for x in sw)
        print('  交换这两个密文块后解出的明文:', dec[:len(blocks) * 16])

    print()
    print('=' * 68)
    print('[考点2] CBC —— 改 C_i 的 1 bit -> P_(i+1) 对应 bit 翻转')
    print('=' * 68)
    p = pad16(CBC_PLAIN)
    print('  原明文块2 =', p[16:32])
    c = sm4.CryptSM4(); c.set_key(KEY, sm4.SM4_ENCRYPT)
    CT = c.crypt_cbc(IV, p)
    C1b, C2b = CT[:16], CT[16:32]
    diff = CBC_TARGET_CHAR[0] ^ p[16 + CBC_TARGET_OFFSET]
    C1mod = bytearray(C1b)
    C1mod[CBC_TARGET_OFFSET] ^= diff
    C1mod = bytes(C1mod)
    # CBC 解密：P_i = D(C_i) ^ C_(i-1)
    p1n = bytes(a ^ b for a, b in zip(dec_block(KEY, C1mod), IV))
    p2n = bytes(a ^ b for a, b in zip(dec_block(KEY, C2b), C1mod))
    print('  篡改 C1 第 %d 字节后：' % CBC_TARGET_OFFSET)
    print('    块1 明文 =', p1n[:16], '  <- 整体随机化（不可控，所以只打第二块）')
    print('    块2 明文 =', p2n[:16])
    print('    块2 只改了目标字节:', all(p2n[i] == p[16 + i]
                                        for i in range(16) if i != CBC_TARGET_OFFSET))
    print('    目标字节 %r -> %r' % (chr(p[16 + CBC_TARGET_OFFSET]), chr(p2n[CBC_TARGET_OFFSET])))
    print('  => 配合 padding oracle 可逐字节解密整段明文（CBC 最经典攻击）')

    print()
    print('=' * 68)
    print('[考点3] OFB / CTR —— IV 复用 = 密钥流重用')
    print('=' * 68)
    n = max(len(OFB_PA), 16)
    ks = ofb_keystream(KEY, IV, n)
    ca = bytes(a ^ b for a, b in zip(OFB_PA, ks))
    print('  OFB 密钥流 =', ks.hex())
    print('  已知 A 明文 =', OFB_PA)
    print('  已知 A 密文 =', ca.hex())
    if OFB_CB is None:
        pb = b'card_num=6228480010309999'
        cb = bytes(a ^ b for a, b in zip(pb, ks))
        print('  B 密文（演示造）=', cb.hex())
    else:
        pb = None
        cb = OFB_CB if isinstance(OFB_CB, bytes) else bytes.fromhex(OFB_CB)
    rec = bytes(x ^ y ^ z for x, y, z in zip(cb, ca, OFB_PA))
    print('  C_a ^ C_b ^ P_a =', rec)
    print('  即解出 B 的明文:', rec)
    print('  => 不需要密钥，只要同一 IV 下拿到一组已知明密文')

    print()
    print('[附] CTR 模式同理（只是密钥流由 iv 递增加密生成）')
    ks_ctr = ctr_keystream(KEY, IV, n)
    print('  CTR 密钥流 =', ks_ctr.hex())
    print('  与 OFB 密钥流不同（CTR 是计数器，OFB 是迭代加密）:', ks_ctr != ks)
    print('  但 IV/计数器复用都会导致密钥流复用，攻击方式完全相同')


if __name__ == '__main__':
    main()
