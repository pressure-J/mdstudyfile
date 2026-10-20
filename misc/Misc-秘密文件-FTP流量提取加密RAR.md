---
title: Misc-秘密文件-FTP流量提取加密RAR
tags: [misc, 流量分析, ftp, rar, writeup]
created: '2026-10-09T14:00:00.000Z'
modified: '2026-10-09T14:00:00.000Z'
---

# 秘密文件（BUUCTF）· FTP 流量提取加密 RAR

> 题型：**FTP 明文传输 + 加密压缩包爆破**。属于「文件传输类」流量题的标准套路。
> 难度：入门。考点只有两个：① 会不会从 FTP-DATA 里抠出文件 ② 会不会爆 4 位数字密码。

## 一、题目

某公司内网被入侵，抓到了入侵流量，问偷走了什么机密文件。

附件：`305df1f78bef4ccfd2a3bd0fe4a6c0d7.pcapng`（33 KB，200 帧）

## 二、10 秒定方向

```sh
D:\网络安全工具\Wireshark\tshark.exe -r 305df1f78bef4ccfd2a3bd0fe4a6c0d7.pcapng -q -z io,phs
```

协议分级里 **`ftp` 有 17 帧**——方向立刻确定。这是一台真机被抓的包，混着大量噪音（SSDP / LLMNR / NBNS / DNS / ESET 遥测 / 猎豹遥测 / 若干半开 TCP），**只有 FTP 这条线是真的**。

## 三、FTP 会话全过程

过滤 `ftp`：

| 帧 | 方向 | 内容 |
|---|---|---|
| 15 | S→C | **`220 HI, i know you are a hacker who is trying to hack me ,but can u find where is the flag?`** |
| 19/22 | C→S | `USER ctf` / `PASS ctf` |
| 39 | C→S | `PORT 172,16,66,100,30,158` → 数据端口 **7838** |
| 45 | C→S | `LIST` |
| 95 | C→S | **`RETR 6b0341642a8ddcbeb7eca927dae6d541.rar`** |
| 89 | C→S | `PORT 172,16,66,100,30,162` → 数据端口 **7842** |
| 133 | C→S | `QUIT` |

出题人那句横幅就是**题目明示**：flag 在文件里。

**被动端口换算**（`PORT a,b,c,d,p1,p2` → `IP: p1*256+p2`）：

```
30*256 + 158 = 7838   ← LIST 的数据连接
30*256 + 162 = 7842   ← RETR 的数据连接
```

## 四、把 RAR 抠出来

FTP 的文件内容走**独立的数据连接**（这里是对端的 7838 / 7842 端口），不在 21 端口上，所以要认准数据流。

**图形界面做法**：`File → Export Objects → FTP-DATA`，一键导出。

**命令行做法**（本次采用）：先看 `LIST` 内容，确认文件名和大小——

```sh
# 流 1 就是 LIST 的数据连接，服务器→客户端方向
tshark.exe -r 文件.pcapng -Y "tcp.stream==1 && ip.src==172.16.80.153" \
  -T fields -e tcp.payload | tr -d '\r\n' | xxd -r -p

# 输出：
# 01-12-16 10:42AM    196 6b0341642a8ddcbeb7eca927dae6d541.rar
```

再抠 RAR 本体（走数据连接的那条流）：

```sh
tshark.exe -r 文件.pcapng -Y "tcp.stream==6 && ip.src==172.16.80.153" \
  -T fields -e tcp.payload | tr -d '\r\n' | xxd -r -p > flag.rar
```

得到 **196 字节**，文件头 `52 61 72 21 1A 07 00`（=`Rar!\x1a\x07\x00`，RAR5 格式）。

## 五、破密码

直接解压提示要密码：

```
7z l flag.rar  →  Enter password:  ❌
```

**没有任何密码提示 → 先试常见弱密码**。这是 2016 年的题，出题意图就是 **4 位纯数字**：

```python
import subprocess, os, shutil
for i in range(10000):
    pw = '%04d' % i
    if os.path.exists('tmpout'): shutil.rmtree('tmpout')
    r = subprocess.run(['7z','x','-y','-p'+pw,'-otmpout','flag.rar'], capture_output=True)
    if r.returncode == 0:
        print('密码:', pw); break
```

跑到 **1903** 命中。

> **效率提示**：123 秒能跑完 10000 个，说明用 `7z` 命令行子进程爆破在这个规模完全够用。上更大字典（8 位、字母数字）才需要 `ARCHPR` / `hashcat`（RAR5 的 KDF 很慢，hashcat 要配 `-m 13000`）。

## 六、结果

```
密码: 1903
```

解出 `6b0341642a8ddcbeb7eca927dae6d541.txt`（38 字节）：

```
flag{d72e5a671aa50fa5f400e5d10eedeaa5}
```

## 七、这题学到什么

1. **FTP 是明文的**：账号密码（`ctf/ctf`）、命令、文件内容全在包里。`ftp` 过滤器一开，攻击过程一览无余。
2. **FTP 传文件走独立的数据连接**，别在 21 端口找文件内容。认准 `PORT` 命令算出来的端口，或直接 `Export Objects → FTP-DATA`。
3. **`PORT` 命令的端口是三段式**：`p1*256+p2`，别当成十进制直接读。
4. **加密压缩包先猜强度**：题目年份久 + 无提示 → 4 位数字起步，别一上来就上大字典。
5. **真机抓的包噪音极多**：本题 200 帧里，真正有用的只有 FTP 那 17 帧。协议分级 + 会话列表先筛一遍，能省掉大量无效阅读。

## 八、同类题

| 题目 | 套路 |
|---|---|
| BUUCTF 秘密文件 | 本题：FTP + 加密 RAR 爆破 |
| BUUCTF 被偷走的文件 | 同上，FTP-DATA 提取，密码字典不同 |
| 各类 FTP 题变体 | 密码可能藏在横幅、文件名、`LIST` 结果或同包的 DNS/HTTP 里 |

> **通用口诀**：明文协议（FTP/Telnet/HTTP/SMTP）→ 先看会话内容 → 找文件传输 → 导出 → 是一张加密压缩包就爆破。

*最后更新：2026年10月9日*
