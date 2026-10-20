---
title: 内存取证题目解题步骤
tags: [misc]
created: '2026-09-09T12:00:00.000Z'
modified: '2026-09-09T12:00:00.000Z'
---

# Misc 内存取证题目解题步骤

## 〇、工具准备(你有现成的)

| 工具 | 位置 | 说明 |
|---|---|---|
| **vol.exe** (Volatility 3) | `D:\网络安全工具\内存取证\vol.exe` | 主工具,自动识别系统、免 profile |
| volshell.exe | 同目录 | 交互式底层调试,做题基本不用 |
| 符号表 | 同目录 `symbols\` | 已内置,首跑自动缓存,较慢属正常 |

**铁律 1**:镜像放**纯英文路径**(如 `C:\opencode_tmp\`),中文路径会报 "File does not exist"。
**铁律 2**:`-o 输出目录` 必须放 `-f` 前面:
```powershell
# 对
vol.exe -o C:\dump -f x.vmem windows.dumpfiles
# 错
vol.exe -f x.vmem windows.dumpfiles --output-dir C:\dump
```

---

## 一、三连:先识别系统,再看进程,再扫文件

```powershell
VOL = "D:\网络安全工具\内存取证\vol.exe"

# ① 系统信息(确认镜像类型/位数,首次跑会下符号表)
& $VOL -f C:\opencode_tmp\Target.vmem windows.info

# ② 进程列表(找可疑进程)
& $VOL -f C:\opencode_tmp\Target.vmem windows.pslist
& $VOL -f C:\opencode_tmp\Target.vmem windows.psscan    # 含已退出/隐藏进程
& $VOL -f C:\opencode_tmp\Target.vmem windows.pstree    # 树形看父子关系
& $VOL -f C:\opencode_tmp\Target.vmem windows.cmdline   # 进程命令行

# ③ 网络连接(找 C2/反弹 shell)
& $VOL -f C:\opencode_tmp\Target.vmem windows.netscan

# ④ 文件扫描(核心,找 flag 藏身)
& $VOL -f C:\opencode_tmp\Target.vmem windows.filescan
& $VOL -f C:\opencode_tmp\Target.vmem windows.filescan | findstr /i "flag ctf zip png HUAWEI"
```

**看什么**:非系统进程、奇怪名字(updatenow.exe 等伪装)、父进程异常、非正常端口。

---

## 二、提取文件(dumpfiles 最容易踩坑)

```powershell
# filescan 输出的第一列是"文件对象地址",用它 dump
& $VOL -o C:\dump -f C:\opencode_tmp\Target.vmem windows.dumpfiles --physaddr 0x7fe72430
```

**关键坑**:`--virtaddr` 经常 dump 失败(返回空表),用 **`--physaddr`** 更稳。文件对象地址在 filescan 第一列。

dump 出的文件名带一串数字前缀(如 `file.0x7fe72430.0xfa8001a5a4f0.xxx.dat`),**不管后缀,直接当原始字节分析**。

---

## 三、密码/凭据提取(虚拟机密码类问1)

```powershell
& $VOL -f C:\opencode_tmp\Target.vmem windows.registry.lsadump
```
- 输出里找 **`DefaultPassword`**,Secret 是 UTF-16LE 十六进制
- 逐字节 `66 00 6c 00` = "fl",即每 2 字节低字节为 ASCII → 可拼出明文
- 还原脚本:
```python
h = "66006c00610067..."   # 从 Hex 列复制
b = bytes.fromhex(h)
print(b.decode('utf-16le', errors='ignore'))
```

其他常用:
```powershell
windows.hashdump      # SAM 密码哈希
windows.registry.userassist  # 用户运行过的程序
windows.registry.printkey --key "Software\Microsoft\Windows\CurrentVersion\Run"
```

---

## 四、华为手机备份加密(高频考点,2021陇剑杯)

**特征**:filescan 里出现 `HUAWEI P40_xxx\picture\storage\MediaTar\images\images0.tar.enc` 和 `info.xml`。

**解密算法**(kobackupdec 逆向结果):
- `images0.tar.enc` = **AES-CTR** 加密的 tar
- 密钥 `key = SHA256(备份密码)[:16]`
- IV(CTR 初始值)= **picture.xml 里的 `<Iv>`**(如 `78CD48D513756101A4350B4C7104DFDA`)
- 备份密码常 = **内存里挖出的虚拟机密码(空格换下划线)**

```python
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from Crypto.Util import Counter

password = b"W31C0M3_T0_THiS_34SY_F0R3NSiCX"   # 问1密码,空格换下划线
iv = bytes.fromhex("78CD48D513756101A4350B4C7104DFDA")
data = open("images0.tar.enc.dat", "rb").read()

key = SHA256.new(password).digest()[:16]
ctr = Counter.new(128, initial_value=int.from_bytes(iv, byteorder="big"), little_endian=False)
dec = AES.new(key, AES.MODE_CTR, counter=ctr).decrypt(data)
open("flag.tar", "wb").write(dec)
```

解 tar → 得图片 → 图片里的字符串(通常还要按提示处理空格/下划线)即 flag。

**经验**:info.xml 里 `productModel="NoPassword"`、`snHash=666...` 常是**出题人放的误导**,别被带偏。真正的密码靠别的题/别的线索拿。

---

## 五、通用内存取证思路(不看题也要会)

1. **先跑 `windows.info`** 确认镜像能读、是什么系统
2. **pslist/psscan/pstree/cmdline** 找可疑进程和命令
3. **filescan** 找 flag/压缩包/图片/关键文件(`findstr` 过滤)
4. **dumpfiles --physaddr** 提取目标文件
5. **strings** 已 dump 的文件/进程内存搜 `flag|key|http`
   ```powershell
   strings.exe -n 6 C:\dump\xxx.dmp | findstr /i "flag key http"
   ```
6. 特殊场景:
   - 虚拟机密码 → `lsadump`
   - 加密备份 → 找到密码线索(常是另一问的答案)解密
   - 隐藏文件/回收站 → filescan 搜 `$Recycle|Recycler|_`
7. **flag 提示别忽略**:如 "no space but underline" = 把结果里的空格换成下划线

---

## 六、常见坑

1. **中文路径**报 "File does not exist" → 复制到英文路径
2. **dumpfiles --virtaddr 空表** → 换 `--physaddr`
3. **首跑慢**是下符号表,正常
4. **flag 可能藏多步**:先找密码(问1)→ 解密(问2)→ 图片(问3),环环相扣
5. **加密文件别硬猜密码** → 题目/其他问会给线索,别暴力爆破
6. **`\keysvc`、杀软白名单等系统字符串是噪声**,别当成线索

---

## 七、实战记录(2021 陇剑杯 · 内存分析)

**问1 虚拟机密码**:
```powershell
vol.exe -f Target.vmem windows.registry.lsadump
# DefaultPassword = flag{W31C0M3 T0 THiS 34SY F0R3NSiCX}
```

**问2 备份图片 flag**:
1. filescan 找 `HUAWEI P40_2021-aa-bb xx.yy.zz\...\images0.tar.enc`(对象地址 0x7fe72430)
2. dumpfiles --physaddr 提取 16KB enc 文件
3. 密码 = 问1 flag 空格换下划线:`W31C0M3_T0_THiS_34SY_F0R3NSiCX`
4. AES-CTR + IV 解密 → tar → `Pictures/flag/mmexport1630152510463.png`
5. 图片内容:`TH4NK Y0U F0R DECRYPTING MY DATA` → 空格换下划线
   → **`flag{TH4NK_Y0U_F0R_DECRYPTING_MY_DATA}`**

*最后更新：2026年9月9日*