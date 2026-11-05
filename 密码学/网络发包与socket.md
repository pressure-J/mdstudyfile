# 网络发包与靶机交互（发包模板）

> **一句话**：靶机题就是一次对话——它先给你要素（nonce / 密文 / 公钥 / IV），你本地算，发回去，它验对才给 flag。**收发直接用 pwntools，不要自己写 socket 封装。**

---

## 一、看到什么就该翻这篇

| 题目特征 | 用什么 |
|---|---|
| 给 `IP:端口`，连上去先吐一串提示文字 | `recvuntil` / `recvline` 切分 |
| 要求「计算 XX 再发回来」「用算出的口令登录」 | `sendlineafter` + 本地算法 |
| 密文、签名、`r‖s` 这类不可打印字节 | `recvn` + 长度前缀（`u32`/`p32`，注意端序） |
| 要试很多组参数（逐字节猜、爆破 IV 第 1 字节） | 循环复用同一个 `remote` 对象 |
| 靶机偶尔拒绝连接或超时 | 重试包装 |

比赛里讲师描述的流程就是这个：切到场景靶机 → 进邮件服务器 → **伪造用户名密码发请求** → 拿 flag。手点浏览器只能做一次、算错要重头来，写成脚本才能批量试参数、把算法嵌进去。

---

## 二、原理：TCP 是字节流，不是消息

这是所有坑的根源。

```text
应用层以为：   [消息1]      [消息2]      [消息3]
TCP 实际传输： ──字节字节字节字节字节字节字节字节──→
接收方 recv：  可能一次收到 1.5 个消息，也可能分 5 次收到半个消息
```

TCP 只保证三件事：**字节按序到达、不丢、不重**。它**不保证**「一次 `recv` = 一条完整消息」。

所以：
- `recv(4096)` 的语义是「**最多**给 4096 字节」，只给你 3 个字节也完全合法
- 「一条消息到哪结束」必须应用层自己定帧边界
- 「收完了没有」不能靠单次 `recv` 的返回值判断，只能靠协议规则

### 三种定帧方案，pwntools 都有现成的

| 方案 | pwntools API | 适用 |
|---|---|---|
| **分隔符** | `recvuntil(delim)` / `recvline()` / `sendlineafter(delim, data)` | 文本协议、提示语、`flag{...}` |
| **长度前缀** | `recvn(4)` → `u32(..., endian="big")`；发 `p32(n, endian="big")` | 二进制（密文、签名、序列化） |
| **定长** | `recvn(n)` | 协议长度固定 |

**没必要自己实现 `recvuntil`**——它内部就是「循环 recv 直到缓冲区出现 delimiter，剩下的留在缓冲区」，pwntools 早已处理好多收、超时、EOF 这些边界。

### 但原理还是要懂，因为你得判断它是怎么卡住的

三件 pwntools 替你做了、出问题时你必须能自己解释的事：

1. **多收的数据留在缓冲区**：`recvuntil(b"nonce=")` 之后紧跟 `recvline()` 才能拿到那一行，是因为前者把后面的字节留在 tube 内部缓冲区里了。
2. **`recvn(n)` 保证收满 n 字节**：它会在内部循环 recv，直到够数或对端关闭（关闭则抛 `EOFError`）。
3. **`send` 内部就是 `sendall`**：不会出现「只发出去一半」的问题。

---

## 三、必踩的坑（都是实测踩出来的）

| 坑 | 现象 | 原因与解法 |
|---|---|---|
| 把 `recv(1024)` 当「读完整条消息」 | 本地正常，连远端偶尔少半句 | 用 `recvuntil` / `recvn` |
| 二进制数据等换行 | 一直阻塞到超时 | 密文里没有 `0x0a`；用 `recvn` + 长度前缀 |
| **`p32`/`u32` 忘了端序** | 连上了但一直不动，像网络问题 | **pwntools 默认小端**：`u32(b"\x00\x00\x00\x10")` = `268435456`，`u32(..., endian="big")` 才是 `16`。读错就变成 `recvn(268MB)` 死等 |
| 每次读都重新 `remote()` | 靶机状态复位、nonce 变了、可能被限流 | 一条连接走完全流程，算法循环在里面做 |
| 提示语没吃掉就发答案 | 后面的解析多带前缀文字 | 用 `sendlineafter(b"提示语", data)`，一次性「等它说完再发」 |
| 用 `nc` 手工做 | 只能做一次，参数改不动 | 写脚本 |
| 觉得「本地通就行」 | 上靶机才发现分帧问题 | 本地起假靶机反复压（本篇脚本就是干这个的） |

### 服务端的一个坑（自己搭靶机时会撞上）

用 pwntools `listen()` 在 `while` 循环里反复 `wait_for_connection()`：第一次连接处理完、`close()` 之后，同一个 listen 对象会**立刻再返回一个已关闭的幽灵连接**，循环空转——实测每秒上百次、日志刷到 6000+ 行，看起来像被打爆了。

**结论：服务端用标准库 `socketserver`（现成的多连接 TCP 框架 + `makefile('rb')` 的 `readline()`/`read(n)` 分帧），pwntools 留给客户端。**

---

## 四、完整脚本（两个都已实测跑通）

文件位置（`py` 直跑）：

- `D:\python\CTF工具箱\net\00-本地靶机模拟器.py` — 假靶机（标准库 `socketserver`）
- `D:\python\CTF工具箱\net\01-发包模板-核心收发.py` — 发包模板（pwntools）

### 为什么用 pwntools 而不是自己写

本机 `D:\徐利杰\python.exe`（Python 3.12）已装 **pwntools 4.15.0**，且 Windows 11 上实测可用：

```text
remote(host, port)  → 连远端          ✅
listen(port)        → 起监听          ✅
process([...])      → 起本地进程      ✅
recvuntil / recvn / recvline / sendlineafter / recvall   ✅
p32 / u32 / p64 / u64                                    ✅
```

一句话：这些收发原语手写一遍只会引入 bug，没有任何收益。

### 4.1 假靶机模拟器

真靶机连不上也练不了，自己起一个同协议的假靶机才能反复压边界。两种模式：文本（算 md5 应答）、二进制（长度前缀帧）。

```python
# -*- coding: utf-8 -*-
"""
00-本地靶机模拟器.py —— 用来练"跟靶机交互"的假靶机

真靶机连不上、也练不了，自己起一个同协议的假靶机才能反复压边界。

启动：  py 00-本地靶机模拟器.py            # 文本协议（默认）
        py 00-本地靶机模拟器.py --bin      # 二进制长度前缀协议

协议（文本模式）——模仿比赛里"算出口令再登录"的那种题：
  靶机 ->  [+] ISCC-2026 challenge
  靶机 ->  nonce=8f3a2c1d
  靶机 ->  send md5(nonce + 'ISCC') first 8 hex chars
  客户端 -> <8位十六进制>
  靶机 ->  [+] OK token=<12位hex>
  靶机 ->  [+] FLAG{...}

为什么不自己写 accept 循环：用标准库 socketserver（现成的多连接 HTTP-less TCP 框架），
读行/读固定长度用 socket.makefile('rb') 的 readline()/read(n) —— 都不需要手写。

⚠ 踩坑记录（实测）：服务端最初想用 pwntools 的 listen() + wait_for_connection()
  循环，结果第一次连接处理完、关闭通道之后，同一个 listen 对象会反复返回
  "已关闭的幽灵连接"，while 循环空转（实测每秒上百次、日志刷到 6000+ 行）。
  服务端这种"长期跑、反复接客"的场景用 socketserver 更稳；pwntools 留给客户端。
"""
import argparse
import hashlib
import os
import socketserver

PORT = 9999
MODE = "text"


def handle_text(req, f):
    nonce = os.urandom(4).hex()
    req.sendall(b"[+] ISCC-2026 challenge\n")
    req.sendall(b"nonce=" + nonce.encode() + b"\n")
    req.sendall(b"send md5(nonce + 'ISCC') first 8 hex chars\n")

    answer = f.readline().strip().decode(errors="replace")   # 标准库读一行
    expect = hashlib.md5((nonce + "ISCC").encode()).hexdigest()[:8]

    if answer == expect:
        token = os.urandom(6).hex()
        req.sendall(b"[+] OK token=" + token.encode() + b"\n")
        req.sendall(b"[+] FLAG{you_got_the_handshake_" + token[:6].encode() + b"}\n")
    else:
        req.sendall(b"[-] WRONG answer, got=" + answer.encode() + b"\n")


def handle_bin(req, f):
    """二进制帧：4字节大端长度 + 数据。用来练'密文不是可打印字符'的情况"""
    payload = os.urandom(16)                                 # 假装是一段密文
    req.sendall(len(payload).to_bytes(4, "big") + payload)

    n = int.from_bytes(f.read(4), "big")                     # read(4) 保证读满 4 字节
    body = f.read(n)                                         # read(n) 保证读满 n 字节

    if body == payload[::-1]:                                # 约定：把密文倒序发回来
        req.sendall(b"[+] FLAG{bin_frame_ok}\n")
    else:
        req.sendall(b"[-] WRONG frame, hex=" + body.hex().encode() + b"\n")


class Handler(socketserver.BaseRequestHandler):
    def handle(self):
        print("[靶机] connection from %s:%d" % self.client_address, flush=True)
        f = self.request.makefile("rb")                      # 标准库：readline()/read(n)
        try:
            handle_bin(self.request, f) if MODE == "bin" else handle_text(self.request, f)
        except Exception as e:
            print("[靶机] handler error:", e, flush=True)
        finally:
            f.close()


class Server(socketserver.ThreadingTCPServer):
    allow_reuse_address = True                               # 重启服务不卡端口
    daemon_threads = True


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--bin", action="store_true")
    a = ap.parse_args()
    MODE = "bin" if a.bin else "text"
    print("[靶机] listening on 127.0.0.1:%d  mode=%s" % (PORT, MODE), flush=True)
    Server(("127.0.0.1", PORT), Handler).serve_forever()      # 标准库的 accept 循环
```

### 4.2 发包模板（pwntools）

```python
# -*- coding: utf-8 -*-
"""
01-发包模板-核心收发.py —— 跟靶机交互的骨架（pwntools 版，不重复造轮子）

【为什么直接用 pwntools】
  靶机题的本质是一次"对话"：它先给要素（nonce / 密文 / 公钥 / IV），
  你算完发回去，它验对才给 flag。手点 nc/浏览器只能做一次，写成脚本才能
  批量试参数、把算法嵌进去、失败自动重连。
  而"按分隔符收、精确收 N 字节、打包长度前缀"这些 pwntools 全都有现成的，
  自己写一遍除了引入 bug 没有任何好处。

  本机已装：pwntools 4.15.0（解释器 D:\\徐利杰\\python.exe，Python 3.12）
  实测可用的 API（Windows 11 上全部正常，别以为 Windows 跑不了 pwntools）：
    remote(host, port) / listen(port) / process([...])   ← 三种通道都验证过
    recvuntil / recvline / recvn / recv / recvall / sendlineafter / sendline / send
    p32 / u32 / p64 / u64                                ← 长度前缀打包。⚠ 默认小端，大端要写 endian="big"

  ⚠ 两个实测到的坑：
    1) p32/u32 默认小端。大端的长度前缀不写 endian="big"，16 会被读成 268435456，
       然后 recvn 死等 —— 表现就是"连上了但一直不动"，极易误判成网络问题。
    2) 服务端别用 listen() 在循环里反复 wait_for_connection()，会返回幽灵连接空转，
       详见 00-本地靶机模拟器.py 顶部注释。
"""
import hashlib
import sys
import time

from pwn import context, remote, log, p32, u32

context.log_level = "info"          # 想看清收发的每个字节改成 "debug"


# ============================================================
#  用法 A：文本协议（"给我要素 → 我算 → 发回去 → 拿 flag"）
# ============================================================
def solve_text(host="127.0.0.1", port=9999):
    io = remote(host, port)

    # 1) 收挑战，停在已知标记上，再截出一行
    io.recvuntil(b"nonce=")
    nonce = io.recvline().strip().decode()
    log.info("nonce = %s", nonce)

    # 2) 本地算（这里换成真实算法：RSA 解密 / AES 解密 / padding oracle 逐字节猜…）
    answer = hashlib.md5((nonce + "ISCC").encode()).hexdigest()[:8]
    log.info("answer = %s", answer)

    # 3) sendlineafter：等提示语出现再发，避免和靶机的输出抢时序
    io.sendlineafter(b"chars\n", answer.encode())

    # 4) 收尾。recvall 会一直读到对端关闭
    resp = io.recvall(timeout=5).decode(errors="replace")
    io.close()
    print(resp)
    return resp


# ============================================================
#  用法 B：二进制协议（长度前缀帧，密文/签名的场景）
# ============================================================
def solve_bin(host="127.0.0.1", port=9999):
    io = remote(host, port)

    # 先读 4 字节长度（recvn 保证收满），再按长度读正好的内容 —— 别等换行
    n = u32(io.recvn(4), endian="big")               # ⚠ pwntools 默认小端！大端长度前缀必须显式指定
    cipher = io.recvn(n)
    log.info("收到 %d 字节密文: %s...", n, cipher[:16].hex())

    # 你的处理（这里演示"倒序"，实际是 AES 解密 / 解出 token 之类）
    payload = cipher[::-1]

    io.send(p32(len(payload), endian="big") + payload)   # 服务端按大端读，打包也要大端
    print(io.recvline().decode(errors="replace").strip())
    io.close()


# ============================================================
#  用法 C：正则抠要素（响应格式不确定时的兜底）
# ============================================================
def extract(pattern, text, default=None):
    import re
    m = re.search(pattern, text, re.S)
    return m.group(1) if m else default


# ============================================================
#  用法 D：失败重试（靶机偶发拒绝/超时）
# ============================================================
def with_retry(fn, host, port, tries=5, delay=1.0):
    last = None
    for i in range(tries):
        try:
            return fn(host, port)
        except (EOFError, TimeoutError, OSError) as e:
            last = e
            log.warning("第 %d 次失败: %s", i + 1, e)
            time.sleep(delay)
    raise last


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "text"
    with_retry(solve_bin if mode == "bin" else solve_text, "127.0.0.1", 9999)
```

---

## 五、实测输出

文本协议，连续 3 次连接（`py 00-本地靶机模拟器.py` 起靶机，另开终端跑客户端）：

```text
[*] nonce = 7494160a
[*] answer = 971aad72
[+] FLAG{you_got_the_handshake_81ab56}

[*] nonce = 7fdd9c89
[*] answer = 9c6100c8
[+] FLAG{you_got_the_handshake_5df4f8}

[*] nonce = 313e23cb
[*] answer = 51907f1a
[+] FLAG{you_got_the_handshake_05af5d}
```

靶机侧日志——3 次连接就是 3 行，没有幽灵连接：

```text
[靶机] listening on 127.0.0.1:9999  mode=text
[靶机] connection from 127.0.0.1:51369
[靶机] connection from 127.0.0.1:51371
[靶机] connection from 127.0.0.1:51372
```

二进制长度前缀帧（靶机加 `--bin`，客户端 `py 01-发包模板-核心收发.py bin`）：

```text
[*] 收到 16 字节密文: 80ed9088b12a5891d74fb6384d7ba472...
[+] FLAG{bin_frame_ok}
```

端序实测（这是那个「连上了但不动」的元凶）：

```text
u32 默认(小端) = 268435456
u32 endian=big = 16
p32(16) 默认 = 10000000    p32(16,big) = 00000010
```

---

## 六、换成真题只改三处

拿到真题后，在 `solve_text()` 里动三个地方，收发部分别碰：

```text
① 收要素   recvuntil(b"nonce=") → 改成靶机真实提示语
           nonce = io.recvline().strip().decode()

② 本地算   answer = md5(...)[:8] → 换成你的算法：
           RSA 解密 / AES 解密 / padding oracle 逐字节猜 / SM2 解 k 复用

③ 回发     sendlineafter(b"chars\n", answer) → 改成靶机要的格式：
           文本？十六进制字符串？二进制？带前缀？
```

**要素格式不确定时的兜底**：先把靶机原始响应整个打出来（`context.log_level = "debug"` 能看清每个字节），再用正则 `re.search(r"token=([0-9a-f]+)", resp)` 抠。

**逐字节交互题型**（padding oracle、长度扩展爆破 SECRET 长度）必须**复用同一连接**：`for` 循环写在 `remote()` 之后，不要每轮重连。

---

## 七、赛前 30 秒自查

- [ ] 靶机给的是文本还是二进制？二进制就别等换行。
- [ ] 长度前缀是**大端还是小端**？`u32`/`p32` 默认小端，大端要写 `endian="big"`。
- [ ] 这个算法要不要几百上千次交互？要就复用连接。
- [ ] 回发的编码对不对？hex 字符串还是裸字节、带不带前缀、大小写。
- [ ] 提示语吃干净了没有？`sendlineafter` 比 `sendline` 稳。
- [ ] 超时设了没有？慢算法题调大，别用默认。
- [ ] 连不上先单独测一次 `remote()`，别在整段逻辑里找错。

---

## 八、相关文件

- 工具箱脚本：`D:\python\CTF工具箱\net\00-本地靶机模拟器.py`、`01-发包模板-核心收发.py`
- 工具层笔记：`常用函数.md`（密码学库怎么调）
- 协议层题目（TLS / IPSec / SSH 的随机数复用）→ `04-密码协议\` 目录（待补）
