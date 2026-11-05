# -*- coding: utf-8 -*-
# RSA23 附加：明文高位（立体化消息 / stereotyped message）Coppersmith
# 用法：SageMath 9.3 运行
#   "C:/Users/徐利杰/AppData/Local/SageMath 9.3/runtime/bin/bash.exe" -lc \
#     "/opt/sagemath-9.3/sage /cygdrive/d/path/to/this.sage"
# 场景：e 很小（3/5），明文有已知前缀（flag{...}、固定 padding），未知部分 < n^(1/e)

from sage.all import *

# ================= 题目模拟（换题改成题目给的数据） =================
p = random_prime(2**512 - 1, lbound=2**511)
q = random_prime(2**512 - 1, lbound=2**511)
n = p * q
e = 3
flag = b"flag{stereotyped_message_coppersmith_2026}"
m = Integer(int.from_bytes(flag, "big"))
shift = 64                      # 未知低 64 位（题目给 m 的高位 = m >> 64）
known = m >> shift
c = Integer(pow(m, e, n))
# ===================================================================

print("n bits =", n.nbits(), " m bits =", m.nbits(), " 未知位数 =", shift)
print("要求 未知位 < n^(1/e) = 2^%d" % (n.nbits() // e))

R = Zmod(n)
PR = PolynomialRing(R, "x")
x = PR.gen()
f = (known * 2**shift + x)**e - c
roots = f.monic().small_roots(X=2**shift, beta=1.0)
assert roots, "small_roots 无解：未知位数超过 n^(1/e)，或 X 取太大"

rec = Integer(roots[0]) + known * 2**shift
print("恢复的 m =", int(rec).to_bytes((int(rec).bit_length() + 7) // 8, "big"))
print("与原明文一致:", rec == m)
assert rec == m
