# Wiener 攻击 solve 脚本 (低解密指数 RSA)
# 适用条件: d < n^(1/4)/3   (e 通常非常大, 接近 n 的位数)
# 用法: 填 e / n 两行后直接跑; 或直接运行做内置自测
from math import isqrt

def cf_expand(a, b):          # a/b 的连分数展开
    r = []
    while b:
        r.append(a // b)
        a, b = b, a % b
    return r

def convergents(cf):          # 逐个产生收敛子 (分子, 分母)
    n0, d0 = 0, 1
    n1, d1 = 1, 0
    for q in cf:
        n2 = q * n1 + n0
        d2 = q * d1 + d0
        yield n2, d2
        n0, d0, n1, d1 = n1, d1, n2, d2

def wiener_attack(e, n):
    for k, d in convergents(cf_expand(e, n)):
        if k == 0 or (e * d - 1) % k != 0:
            continue
        phi = (e * d - 1) // k
        b = n - phi + 1                       # p + q
        disc = b * b - 4 * n
        if disc < 0:
            continue
        s = isqrt(disc)
        if s * s != disc:
            continue
        p = (b + s) // 2
        q = (b - s) // 2
        if p * q == n:
            return p, q, d
    return None

# ================= 填题数据 =================
e = 0    # TODO: 题目给的 e
n = 0    # TODO: 题目给的 n
# ============================================

if e and n:
    res = wiener_attack(e, n)
    if res:
        p, q, d = res
        print(f"p = {p}")
        print(f"q = {q}")
        print(f"d = {d}")
        print("flag 解法: d = pow(e, -1, φ) 的逆元关系 -> m = pow(c, d, n)")
    else:
        print("Wiener 失败: d 可能不满足 d < n^0.25/3, 换 Boneh-Durfee(需要格)")
else:
    # ---- 内置自测: 构造 d 小的 RSA 并攻击 ----
    from Crypto.Util.number import getPrime, inverse
    p = getPrime(512); q = getPrime(512)
    n2 = p * q
    d2 = getPrime(200)                        # 满足 d < n^0.25/3
    e2 = inverse(d2, (p - 1) * (q - 1))
    res = wiener_attack(e2, n2)
    assert res and res[0] * res[1] == n2 and res[2] == d2
    print("[自测通过] Wiener 攻击正确恢复 p, q, d")