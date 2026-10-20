# 模2的幂-离散对数 solve 脚本
# 用法: py 模2的幂-离散对数-solve.py  (Python 3.8+, 纯内置库)
# 换题只改下面 m / c 两个数据

m = 73964803637492582853353338913523546944627084372081477892312545091623069227301
c = 21572244511100216966799370397791432119463715616349800194229377843045443048821

k = 256
N = 1 << k

def dlog5(h, kk=k):
    # 解 5^d = h (mod 2^kk)，要求 h≡1 mod 4，返回 d∈[0, 2^(kk-2))
    N = 1 << kk
    m_exp = kk - 2
    g = 5
    g_inv = pow(g, -1, N)
    d = 0
    r = h % N
    for i in range(m_exp):
        val = pow(r, 1 << (m_exp - 1 - i), N)   # 得阶2元素的幂
        if val != 1:                            # 该位为 1
            d |= 1 << i
            r = (r * pow(g_inv, 1 << i, N)) % N
    return d

def norm(h):
    # 剥掉 ±1 符号: 返回 ≡1 mod 4 的那份 (5 的幂)
    return h % N if h % 4 == 1 else (-h) % N

B = dlog5(norm(m))          # = b
D = dlog5(norm(c))          # = b*e (mod 2^(k-2))

mod = 1 << (k - 2)
t = 0
while (B >> t) % 2 == 0 and (B >> t) != 0:
    t += 1
mod2 = 1 << (k - 2 - t)
e = ((D >> t) * pow((B >> t) % mod2, -1, mod2)) % mod2

print('e =', e)
print('flag =', e.to_bytes((e.bit_length() + 7) // 8, 'big'))