# -*- coding: utf-8 -*-
"""
Rabin 密码 solve 脚本
适用: 给出 n（可分解）、密文 c、明文尾部携带的冗余校验码（本脚本按"位拼接"处理）。
题目数据: n = 523798549, c = 162853095, 校验码 = 二进制 110001 -> 明文 4835626
用法: 换题只改 N / C / CHECK / CHECK_DECIMAL 四行。
"""
import hashlib
from sympy import factorint
from sympy.ntheory.residue_ntheory import sqrt_mod

# ================= 换题只改这几行 =================
N = 523798549
C = 162853095
CHECK = '110001'        # 校验码二进制串
CHECK_DECIMAL = False   # True = 校验码以十进制数字拼在明文后（如 明文4835626 + 49）
DO_MD5 = True           # 顺带输出明文的 32 位小写 md5
# =================================================


def crt(a1, m1, a2, m2):
    """中国剩余定理（通用版，支持不互素）"""
    g, x, _ = _egcd(m1, m2)
    assert (a2 - a1) % g == 0, '同余方程组无解'
    l = m1 // g * m2
    return (a1 + ((a2 - a1) // g * x) % (m2 // g) * m1) % l


def _egcd(a, b):
    if b == 0:
        return a, 1, 0
    g, x1, y1 = _egcd(b, a % b)
    return g, y1, x1 - (a // b) * y1


def rabin_roots(c, p, q):
    """解 x^2 ≡ c (mod p*q)，返回全部根"""
    rp, rq = sqrt_mod(c, p), sqrt_mod(c, q)
    return sorted({crt(sp, p, sq, q) for sp in (rp, p - rp) for sq in (rq, q - rq)})


def main():
    fac = factorint(N)
    print(f'[*] n = {N} 分解 -> {fac}')
    p, q = list(fac)
    assert p * q == N and p != q

    roots = rabin_roots(C, p, q)
    print(f'[*] {len(roots)} 个根: {roots}')
    for r in roots:                       # 自检：每个根的平方都该等于密文
        assert pow(r, 2, N) == C

    k = len(CHECK)
    check_val = int(CHECK, 2)
    print(f'[*] 校验码 = {CHECK} (二进制) = {check_val}，{k} 位\n')
    print('[*] 逐个根剥离校验码:')

    hit = None
    for r in roots:
        if CHECK_DECIMAL:
            plain, tail = r // 10 ** k, r % 10 ** k
            tip, ok = f'末 {k} 位 = {tail}', tail == check_val
        else:
            plain, tail = r >> k, r & ((1 << k) - 1)
            tip, ok = f'低 {k} 位 = {tail:0{k}b}', tail == check_val
        print(f'    root={r}  {tip}  明文={plain}' + ('   <== 命中' if ok else ''))
        if ok:
            hit = plain

    if hit is None:
        print('[!] 无根与校验码相符——检查 CHECK_DECIMAL 或题面拼法')
        return

    print(f'\n[*] 明文 = {hit}')
    if DO_MD5:
        print(f'[*] md5({hit}) = {hashlib.md5(str(hit).encode()).hexdigest()}')


if __name__ == '__main__':
    main()
