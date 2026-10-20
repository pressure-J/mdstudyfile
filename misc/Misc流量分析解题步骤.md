---
title: 流量分析题目解题步骤
tags: [misc]
created: '2026-09-09T12:00:00.000Z'
modified: '2026-09-09T12:00:00.000Z'
---

# Misc 流量分析题目解题步骤

## 一、先看全貌(10 秒内定位方向)

```sh
# 命令行快速看协议分布(哪个协议占大头,方向就出来了)
D:\网络安全工具\Wireshark\tshark.exe -r 文件.pcap -q -z io,phs
```
或 Wireshark 界面:`Statistics → Protocol Hierarchy`。

同时碰运气搜字符串:打开文件后 `Ctrl+F` → String → 搜 `flag` / `{` / `key`。

## 二、按协议逐类排查

| 协议 | 怎么找 | 看什么 |
|------|--------|--------|
| HTTP | 过滤 `http` | Follow 流,看 POST 参数、响应体、cookie |
| FTP/Telnet | 明文协议 | 用户名密码、传输的文件 |
| SMTP/POP3 | 邮件协议 | 附件(常藏 flag 或另一个文件) |
| DNS | 过滤 `dns` | 子域名逐字符拼 flag、TXT 记录隐藏数据 |
| ICMP | 过滤 `icmp` | payload 里藏数据 |
| TLS/HTTPS | 过滤 `tls` | 需 keylog 文件解密,或放弃(看别的层) |

## 三、Follow 流(核心操作)

对可疑包 **右键 → Follow → TCP Stream**,看完整对话。

**识别套路**:
- 看到 `exam_currentuser`、`PHPSESSID` 等 cookie 超长 → 可能是被多次 URL 编码的 flag 数据(`%25XX` 要解多层)
- 看到大量 `ini_set` / `open_basedir` / `chdir` → 是 WebShell 操作流量(蚁剑/菜刀),flag 藏在响应里
- 看到一个字符一个包(每包长度 1)→ 直接 Follow 拼回完整文本

## 四、提取文件

### 4.1 导出入口(Wireshark)

```
File → Export Objects → HTTP / SMB / TFTP / FTP-DATA / DICOM ...
```

按协议选对应入口；不确定就先看协议统计(第一步)。导出后**不要信扩展名**。

### 4.2 第一件事:验真类型(魔数)

扩展名随便改，文件头骗不了人。一行看前 16 字节:

```powershell
py -c "print(open(r'导出文件.php','rb').read(16))"
```

| 文件头(hex) | 真实类型 | 说明 |
|------------|---------|------|
| `FF D8 FF E0/E1` | JPEG | 图片 |
| `89 50 4E 47` | PNG | 图片 |
| `47 49 46 38` | GIF | 动图 |
| `50 4B 03 04` | ZIP(含 docx/xlsx/apk/jar) | 压缩包 |
| `52 61 72 21` | RAR | 压缩包 |
| `37 7A BC AF` | 7z | 压缩包 |
| `25 50 44 46` | PDF | 文档 |
| `7F 45 4C 46` | ELF | Linux 可执行 |
| `4D 5A` | PE/EXE | Windows 可执行 |
| `3C 3F 70 68 70`(`<?php`) | 真 PHP | 源码/木马 |
| 全是 `A-Za-z0-9+/=` | **base64 文本** | 先解码再判类型 |
| 全是 `0123456789abcdef` | hex 文本 | 先 hex 解码 |
| `%xx%xx` | URL 编码 | 先 URL 解码 |

### 4.3 各类型处理思路

- **JPEG/PNG/GIF** → 直接打开看；再做 `strings` / `binwalk -e` / `zsteg`(PNG LSB)；看 EXIF；PNG 试改宽高。
- **ZIP/RAR/7z** → 先 `Expand-Archive`(Windows 自带不看伪加密)；不行再爆破/改标志位。
- **PDF/文档** → 提取文本、看内嵌文件。
- **ELF/PE** → 逆向、查字符串、跑一下。
- **真 PHP 源码/木马** → 审计逻辑找 flag；一句话木马则结合流量解参数。
- **base64/hex/URL 文本** → **先解码**，解完再回到本表判断真实类型。

### 4.4 通用兜底流程

1. 看魔数 → 2. 若像编码文本 → 解码后再看魔数 → 3. 按真实类型走工具链 → 4. 图片/压缩包再考虑隐写/拼接。

> **核心套路**:导出的文件往往是「伪装 + 编码」双层。本例 `fenxi.php` 就是**文件名骗人 + base64 编码的 JPEG**。

## 五、USB 流量(超高频考点)

过滤 `usb` 看设备:
- **键盘**:`usb.transfer_type == 0x01` 抓 HID 按键数据 → 解键盘映射还原按键
- **鼠标**:`usb.capdata` / `usbhid.data` 里的相对位移 → 累加画轨迹

> **详细步骤见** `Misc-USB流量分析解题步骤.md`(设备定位、字节布局、键码表、坐标还原代码、实战记录)。
> 现成脚本:`D:\python\CTF工具箱\misc\08-USB鼠标流量还原轨迹.py`

## 六、常见坑

1. **包 ≠ 流**:一行一个包,一条流可能拆成几十包。看到一堆小包先 Follow,别逐个看。
2. **一个字符一包**:代理流量常见(如 7890 端口),Follow 拼回即可。
3. **flag 不一定是明文**:可能是多层编码(URL → base64 → 再 URL),解一层看不出来就再解。
4. **导出文件验真类型**:别信扩展名,用文件头魔数识别。

## 七、实战记录

### 例:easycap.pcap(代理端口逐字符)
- 82 帧,**只有一条 TCP 流**(172.31.98.199 → 192.155.81.86:7890)
- 每个包只带 1 字节,Follow 后拼出 `FLAG:3185b87afc86711dee0175502190d116a8071`
- 结论:flag 被拆成 80+ 个单字符包,Follow 流即还原

### 例:数据包1.pcapng(WebShell 操作流量)
- 大量 `POST /index.php?user-app-register`,每条是一次独立操作(80+ 条流)
- 响应 cookie `exam_currentuser` 是多次编码的数据,需逐层 URL 解码
- 教训:先看 `io,phs` 协议统计,别一开始就 Follow 每条流

### 例:fenxi.php(导出文件伪装成 base64 图片)
- 从流量里导出 `fenxi.php`，打开发现全是 base64 文本，开头 `/9j/4AAQSkZJRg`
- `/9j/4` 是 JPEG 魔数 `FF D8 FF E0` 的 base64 → 文件根本不是 PHP，是**伪装成 php 的 base64 图片**
- 解码得一张图，图上直接写着 flag:`flag{209acebf6324a09671abc31c869de72c}`
- 解码命令:

```powershell
py -c "import base64; open('out.jpg','wb').write(base64.b64decode(open('fenxi.php','rb').read()))"
```

- 教训:导出文件先验真类型(魔数/是否纯 base64)，别被扩展名带偏。

## 八、做题顺序总结

1. 协议统计看方向 → 2. 搜 flag/关键字 → 3. 按协议过滤 → 4. Follow 可疑流 → 5. 提文件 → 6. 解码/分析

*最后更新：2026年9月14日*