# -*- coding: utf-8 -*-
"""
国密 SM3 —— 长度扩展攻击（Length Extension Attack）solve 脚本

适用特征：
    题面形式为 digest = SM3(SECRET || user_data)，SECRET 未知；
    要求伪造 SM3(SECRET || user_data || padding || append) 的合法摘要。
    看到 MAC/签名 = 哈希(密钥前缀 || 数据) 这种结构就要想到它。

原理：SM3 与 SHA-256 同为 Merkle-Damgard 结构，摘要 = 最后一次压缩的
      内部状态 V，没有把原始长度再混入。拿到 digest 等于拿到 V，
      可从该状态继续压缩追加数据。

用法: 换题只改下面几行。
"""
from gmssl import sm3, func

# ================= 换题只改这几行 =================
ORIG_DIGEST = None          # 留 None 则由脚本自造一组演示数据；解题时填题面的 digest hex
ORIG_DATA = b'user=guest&role=guest'
APPEND = b'&role=admin'
SECRET_LEN_RANGE = range(0, 64)   # 未知 SECRET 长度的爆破范围
# 仅用于演示/自检：真实 SECRET。解题时填 None（不知道密钥）
SECRET_DEMO = b's3cr3t_k3y_16byte'
# =================================================


def sm3_pad(msg_len: int):
    """按 MD 规则生成填充字节：0x80 + 若干 0x00 + 8 字节大端比特长度"""
    p = [0x80]
    while (msg_len + len(p)) % 64 != 56:
        p.append(0x00)
    p += (msg_len * 8).to_bytes(8, 'big')
    return p


def digest_from_state(state_words, suffix: bytes) -> str:
    """从内部状态 V 继续压缩 suffix（必须 64 字节整数倍），得到最终摘要"""
    v = list(state_words)
    assert len(suffix) % 64 == 0, f'suffix 必须是 64 的整数倍，当前 {len(suffix)}'
    for i in range(0, len(suffix), 64):
        v = sm3.sm3_cf(v, list(suffix[i:i + 64]))
    return ''.join('%08x' % x for x in v)


def sm3_extend(digest_hex: str, secret_len: int, orig_data: bytes, append: bytes):
    """
    返回 (伪造消息, 伪造摘要)
    伪造消息 = orig_data || glue || append，服务的会认它的摘要
    glue 是原消息 (SECRET||orig_data) 的 MD 填充，已体现在已知 digest 里，
    因此从 state 继续压缩的部分只有 append + tail
    """
    total = secret_len + len(orig_data)
    state = [int(digest_hex[i * 8:(i + 1) * 8], 16) for i in range(8)]
    glue = sm3_pad(total)
    new_total = total + len(glue) + len(append)
    tail = sm3_pad(new_total)
    suffix = append + bytes(tail)
    forged_digest = digest_from_state(state, suffix)
    forged_msg = orig_data + bytes(glue) + append
    return forged_msg, forged_digest


def main():
    if ORIG_DIGEST is None:
        assert SECRET_DEMO is not None, '演示模式需要 SECRET_DEMO'
        orig_digest = sm3.sm3_hash(func.bytes_to_list(SECRET_DEMO + ORIG_DATA))
        print('[0] 演示模式：服务端密钥 =', SECRET_DEMO, '(实际长度 %d)' % len(SECRET_DEMO))
    else:
        orig_digest = ORIG_DIGEST
        print('[0] 解题模式：题面 digest =', orig_digest)

    print()
    print('[1] 攻击者已知：')
    print('    data   =', ORIG_DATA.decode(errors='replace'))
    print('    digest =', orig_digest)
    print('    要追加 =', APPEND.decode(errors='replace'))

    print()
    print('[2] 爆破 SECRET 长度', SECRET_LEN_RANGE.start, '..', SECRET_LEN_RANGE.stop - 1)
    hits = []
    for L in SECRET_LEN_RANGE:
        m, d = sm3_extend(orig_digest, L, ORIG_DATA, APPEND)
        if SECRET_DEMO is not None:
            # 演示模式下能用真密钥校验；实战中靠服务端是否接受来判定
            if sm3.sm3_hash(func.bytes_to_list(SECRET_DEMO + m)) == d:
                hits.append((L, m, d))
        else:
            # 实战：每个长度都输出一组候选，逐个拿去请求服务端
            hits.append((L, m, d))

    if SECRET_DEMO is not None:
        for L, m, d in hits:
            print('    命中！SECRET 长度 =', L)
            print('    伪造消息 =', m)
            print('    伪造摘要 =', d)
        if not hits:
            print('    [!] 范围内未命中，扩大 SECRET_LEN_RANGE')
    else:
        print('    共生成', len(hits), '组候选（长度 0..63）')
        for L, m, d in list(hits)[:3]:
            print('      长度=%-3d 摘要=%s' % (L, d))
        print('    ... 逐个提交给服务端，被接受的那组即为正确长度')

    if hits:
        L, m, d = hits[0]
        print()
        print('[3] 伪造结果（用第 1 组演示）：')
        print('    伪造消息 =', m)
        print('    伪造摘要 =', d)
        if SECRET_DEMO is not None:
            real = sm3.sm3_hash(func.bytes_to_list(SECRET_DEMO + m))
            print('    服务端会算出的摘要 =', real)
            print('    >>> 服务端接受伪造请求:', real == d)

    print()
    print('[!] 易错点：SECRET 长度必须正确，否则整个填充算错、摘要全错。')
    print('    只有真实长度那一组才能通过校验（演示模式下已自动验证）。')


if __name__ == '__main__':
    main()
