# CTF 离线速查表（Misc + Crypto）

> 内存取证题（vmem/mem/raw）：详细步骤见《Misc内存取证解题步骤.md》——vol.exe 用法、华为备份解密、lsadump 提密码。

> 本人用：比赛**不能使用 AI**，一切知识外挂为这份表 + 本地脚本库。
> 比赛环境：**线上 + 浏览器可用** → 纯算法在线工具（CyberChef/dCode/Factordb）可现场用；
> 但**本地脚本库仍要提前备好**（Writeup 要可复现、录屏要自洽，且防比赛断网/工具打不开）。
>
> **创宇杯硬约束（合规红线）**：
> ① 比赛全程只做"看题→查本表→手动改脚本数据→跑"，**不碰 AI/聊天工具/浏览器问答**（全程录屏）；
> ② 本表的每个脚本赛前必须**亲手改数据跑通一次**并理解原理——Writeup 要逻辑自洽、可复现、防雷同，不懂原理写不出来；
> ③ 只操作赛题给定的 IP/端口，不扫描不越权（违规=取消成绩）；
> ④ 赛后用 `Get-FileHash 录屏.mp4` 算 MD5 写进 Writeup，录屏不可剪辑。
>
> **浏览器红线（线上赛）**：比赛用专用浏览器配置（关 Edge Copilot 侧边栏、卸 AI 插件）；
> 禁用一切 LLM 网站与搜索引擎 AI 摘要；只开上面的工具白名单站点。

---

## 一、Misc 题型识别 → 工具 → 命令

### 0. 万能第一步（每道题必做）
```bash
# Kali：
file flag   # 看真实文件类型
strings flag | grep -iE 'flag|ctf|key|{'
xxd flag | head -50   # 看文件头魔数
binwalk flag   # 看有没有藏文件
```
> Windows 替代：`py` 跑 python 脚本读文件头 / 010 Editor（已有 BurpSuite 的主机可另装 HxD 绿色版）。

### 1. 文件类型/头损坏
| 症状 | 处理 |
|---|---|
| 文件打不开 | 对照魔数表修复头部 |
| 图片宽高错误（CRC 报错） | 改宽高（png 用脚本改 IHDR） |
| 扩展名被改 | `file` 看真实类型改回来 |

**常见魔数**：
`89 50 4E 47`=PNG、`FF D8 FF`=JPG、`47 49 46 38`=GIF、`50 4B 03 04`=ZIP、`7F 45 4C 46`=ELF、`42 4D`=BMP、`25 50 44 46`=PDF、`52 61 72 21`=RAR

### 2. 图片隐写
| 手法 | 特征 | 工具 |
|---|---|---|
| 附加数据 | binwalk 显示有文件 | `binwalk -e file`、`foremost` |
| LSB 隐写 | 图片看着正常 | `zsteg`（png/bmp）、`steghide` |
| steghide | 无明显异常 | `steghide extract -sf file`（可能需密码） |
| Exif 信息 | 注释/作者字段 | `exiftool file` |
| 二维码 | 缺角/变形 | PS 补角 / 微信扫 / 局部反色 |
| 像素取色 | flag 藏在特定色值 | python PIL 脚本提取 |

### 3. 音频隐写
| 手法 | 特征 | 工具 |
|---|---|---|
| 频谱图 | 听不出名堂 | Audacity：视图→频谱图，字写在频谱里 |
| 摩斯密码 | 波形有长短短间隔 | Audacity 看波形 + 手抄摩斯 |
| 慢速/倒放 | 语音含糊 | Audacity 变速/反转 |

### 4. 压缩包
| 症状 | 处理 |
|---|---|
| 加密压缩包 | `zip2john a.zip > h.txt; john h.txt`（弱密码字典秒出） |
| 伪加密 | **① 先免费解压：`Expand-Archive -LiteralPath a.zip -DestinationPath out -Force`（Windows 自带，不看加密位，伪加密秒解）**；② 不行再 python 改加密位清零（`09 00`→`08 00`，本地头+中央目录都改）；rar 用 `RAR_FILE_HEAD` 改 flag 位 |
| CRC32 爆破 | 小文件已知明文+CRC → `crc32` 爆破脚本 |
| 明文攻击 | 知道包内一个文件的内容 → `pkcrack` |

> **伪加密识别**：文件内容实际未加密（压缩后大小≈原大小 / store 存储），只是标志位 bit0=1 吓人。识别=看数据是否真加密，解=先试自带解压。已实战验证（flag{Adm1N-B2G-kU-SZIP}）。

### 5. 流量分析（pcap）
```bash
tshark -r a.pcap -Y "http" -T fields -e http.request.uri   # HTTP
tshark -r a.pcap -Y "tcp.payload" -T fields -e tcp.payload   # 原始 payload
# 大文件传输：File → Export Objects → HTTP
# USB 流量：usb.capdata 提取键盘按键 → 键码转字符（脚本）
# 蓝牙/无线：先看协议树有没有 BLE ATT / Radiotap
```
> 主机已有 Wireshark，直接 GUI 打开：统计→协议分级 先看是什么流量，再过滤。

### 6. 编码/转换（Misc 高频！）
| 编码 | 特征 | 离线解 |
|---|---|---|
| Base64 | `A-Za-z0-9+/=`，长度 4 倍数 | `echo xxx | base64 -d` |
| 十六进制 | 全是 0-9a-f | `xxd -r -p` |
| Morse | `. - /` 或 `. _` | python 查表 |
| 培根 | 只有 a/b 两字符（长度 5 倍数） | python 查表 |
| 栅栏/凯撒 | 字母表移位 | python 爆破所有位移 |
| 维吉尼亚 | 相对凯撒有密钥、整体 IC≈0.04 | python：IC 定长度 + 逐列卡方（Kasiski 仅供参考） |
| Brainfuck/Ook | `+-><[].,` 或 `Ook.` | 在线转离线：python 解释器 |
| >>><<< 编码 | 三个符号 | python |
| 与佛论禅/社会主义核心价值观 | 中文字符串 | 离线脚本 |
| UU/XX 编码 | `begin/end` 头 | `uudecode` |
| 颜文字/JSFuck | `[]()!+` 组合 | 浏览器 console 运行 |

**通用万能钥匙**：CyberChef 离线版（提前下载 ZIP 版）→ Recipe 里 `From Base64`/`From Hex` 随便拖。**必须提前下载存 U 盘。**
> **线上赛修正**：CyberChef 在线版（gchq.github.io/CyberChef）可直接用；dCode.fr 破解古典密码、
> quipqiup.com 破替换密码、Factordb 查 RSA 分解——全站纯算法非 AI，放心用。

---

## 二、Crypto 题型识别 → 打法

### 1. RSA（你最强项，已有脚本）
速查：**共模 / 共素数 rho / Wiener / 低指数广播 / Fermat / 小素数分解 / dp泄露 / MD5爆破**
> 脚本在 `D:\mdstudyfile\密码学\02-RSA\*-solve.py`（RSA 类）与 `密码学\01-基础密码\`，赛前全部拷 U 盘 + 每份跑一遍验证。
> 笔记总索引：`D:\mdstudyfile\密码学\README.md`（01-基础密码 / 02-RSA / 03-流密码 / 04-其他）。
> 识别四问：① n 能直接分解？② 参数用错了吗（e小/共模/大e）？③ 给了额外信息？④ 素数结构特殊（p-1 光滑/共素数）？
> **铁律：不 ECM 硬啃 500 位大数；一条路超几分钟就换思路。**
> Sahil 的 n 先查 factordb（若比赛联网）→ `D:\Sagemath\python.exe` 跑 sympy.factorint，无 gmpy2 用 py。
>
> **多组 n + 同明文**：优先 `17-RSA共素数-gcd分解.py`（两两 gcd 秒出共享素数），别先想着硬分解。
> **给了公式 A（含 x,y,z 的幂）+ n + c**：`18-RSA-构造A反推参数.py`——先整数开根分离 y，再用余数反推 x，最后 sqrt(n/(x*y)) 定位因子。

### 2. 古典密码（识别靠特征）
| 密码 | 特征 | 打法 |
|---|---|---|
| 凯撒 | 字母整体移位 | 爆破 25 种位移 |
| 仿射 | 单表替换+乘数 | 爆破 a(与26互素)×b |
| **单表替换** | 每个字母固定换成另一字母(乱映射)，词长/标点正常、有重复词 | **`16-单表替换-退火求解.py`**；手推先锚定高频词 |
| 维吉尼亚 | 长密文、整体 IC≈0.04、重复片段间距集中 | **重合指数(IC)定密钥长度（容差内取最小真周期）→ 逐列卡方求位移**；别用 Kasiski 的单个 gcd（任一脏间隔就把它拉成 1） |
| 栅栏 | 重排 | 尝试不同栏数 |
| Playfair | 双字母一组，5x5 表 | 知密钥直接解 |
| 培根 | A/B 双字符 | 查表 |

### 3. 现代密码
| 题型 | 要点 |
|---|---|
| AES/DES ECB | 直接 python `Crypto.Cipher` 解（key/iv 通常题目给） |
| XOR 单字节 | 爆破 256 个 key，找可读明文 |
| XOR 多字节 | 密钥长度猜测（重合指数/Kasiski） |
| RC4/Rabbit | pycryptodome 一步解 |
| 给了 key/iv 的流密码 | 直接调用库函数 |
| LFSR 流密码 | 给加密脚本+输出文件求初始状态 → `19-LFSR状态恢复.py`；连续 N 位输出=N步后状态，逆推即得初态 |
| 流密码密钥重用 | 同一密钥流加密两段 + 给了一组已知明密文对 → `ks = m1⊕c1`，flag = c2⊕ks；见 `密码学\03-流密码\流密码密钥重用.md` |
| **整个文件被加密**（docx/png/pdf 打不开、hex 全乱） | 用**明文魔数当已知明文**反推单字节变换 `c=ROL(p,k)^b` → `33-加密文件-已知明文反推单字节变换.py`（改 DATA+PT）；**判模型**看重复片段距离的 gcd：gcd=1→单字节变换，gcd=4/8→周期密钥异或，重复段 16 对齐且长≥16→ECB；**验证只认 CRC/尾部标记**，别凭魔数 |

### 4. 数论杂题
- 离散对数小阶：暴力或 BSGS（脚本）；模 2 的幂特例见 `密码学\01-基础密码\模2的幂-离散对数.md`（群分解 ±5^b + PH 按位）
- RSA 变种：共私钥、多组n共享素数 → `gcd(n1,n2)`（脚本已有）
- 格密码：低频，比赛遇到先放，最后啃（有 `密码学\04-其他\格密码.md` 笔记）

### 5. 本地脚本库（`D:\python\CTF工具箱\crypto\`，全部已验证跑通）
> 目录 `D:\python\CTF工具箱\crypto\`（旧写的 `D:\mdstudyfile\CTF备赛\crypto_toolkit\` 已不存在，别照旧路径找），全部"改一行数据即跑"：
> 运行方式 `py 文件名.py`（或用 `D:\Sagemath\python.exe`——它是 Miniconda3，不是 SageMath）。08/09 需 pycryptodome。
> **01~05、16 支持两种给法**：`FILE`（填 txt 绝对路径，**密文有换行/很长就用这个**）或 `DATA`（短的单行密文直接粘），FILE 非空时以它为准，自动试 UTF-8-BOM/UTF-8/GBK 编码。
> 空白处理各不相同：维吉尼亚/单表替换/凯撒/仿射保留换行（分组按字母顺序，不影响结果），栅栏自动去空白（换行会被当普通字符参与重排 → 解错），培根去空白、摩斯按行分单词。

| 脚本 | 当看到什么用 | 改哪里 |
|---|---|---|
| 01-凯撒爆破.py | 字母整体平移 | DATA |
| 02-仿射爆破.py | 单表替换但凯撒无果 | DATA |
| 03-栅栏爆破.py | 字母顺序在但分组乱 | DATA |
| 04-培根与摩斯.py | 只有 A/B 两字符 / `.` `-` | DATA |
| 05-维吉尼亚.py | 较长密文、重复片段 | DATA + (可选)KNOWN_KEY |
| 06-XOR单字节爆破.py | hex 乱码提示 xor | DATA_HEX |
| 07-XOR多字节.py | xor 但单字节无果 | DATA_HEX + KEY(给了就填) |
| 08-AES解密模板.py | 给了 key/iv 提示 AES | KEY/IV/DATA/MODE |
| 09-RC4与Rabbit.py | 提示 RC4/Rabbit | KEY/DATA |
| 16-单表替换-退火求解.py | 像英文但字母全乱、凯撒/仿射无果 | FILE（txt 路径，多行用它）/ DATA；结果错词补进 ANCHORS 再跑 |
| 17-RSA共素数-gcd分解.py | 多组 (n,c) 且 e 固定(65537) | NS / CS / E |
| 18-RSA-构造A反推参数.py | 给公式 A(x,y,z) + n + c | A / N / C / E / Y_EXP |
| 19-LFSR状态恢复.py | 给 LFSR 脚本 + 输出文件，求初始状态 | KEY_FILE / MASK / N_BITS |
| 33-加密文件-已知明文反推单字节变换.py | 整个文件被加密（打开报错/魔数不对），有明文魔数可当已知明文 | DATA + PT（已知明文前缀，zip 用 `504b0304140002` 系列） |

**单表替换专项提醒**：
- 识别：词长分布正常、有空格标点、有重复词（如高频 3 字母词常是 `the`），但字母被乱映射。
- 自动跑后约 90% 可读，剩个别词错 → 把确定映射填进 `ANCHORS = {}` 字典（例 `ANCHORS = {'m':'t','j':'h','y':'e'}`，即发现 `mjy` 读 `the`）再跑一遍即收敛。
- 完全手推技巧：单字母词只能是 a/i；重复词锁高频锚点；`(` `)` `;` 标点结构暴露句子框架。
- 离线无忧：统计表+词表已内嵌，零第三方依赖。

**做题流程**：看题 → 对照表格找脚本 → 改数据 → `py` 跑 → 手动检查输出是否可读英文/flag。
**注意**：脚本自带示例数据可先跑通验证环境；换题数据前先看每个脚本顶部注释的"触发特征"。
**比赛当天**：把 crypto_toolkit 整个文件夹拷到比赛机/U 盘；若某脚本报错（缺库），用 `pip install pycryptodome`（SageMath python 已带无需装）。

---

## 三、比赛前 48 小时检查清单

- [ ] **拷 U 盘**：所有 `*-solve.py` 脚本 + 本速查表 + 010/HxD（CyberChef 在线可用，离线版可选）
- [ ] **每个脚本重新跑一遍**（换比赛环境也行，确认能出结果）
- [ ] Kali VM 确认可用：`binwalk foremost steghide zsteg exiftool` 都在
- [ ] Audacity 已装（频谱图）
- [ ] 主机：Wireshark + BurpSuite 已确认
- [ ] `D:\Sagemath\python.exe` 能跑（sympy/gmpy2/pycryptodome）

## 四、比赛当天策略
1. **签到题先做**（送分题，别轻敌跳）
2. **每题限时**：Misc 拆包题 20 分钟内没头绪→跳过换下一题；Crypto RSA 走完速查表 15 分钟没思路→过（**禁止场外求助**，只能自己查表）
3. **flag 格式**：`NSSCTF{...}`/`flag{...}` 大小写敏感，注意掩码样式（`xxxxx******xxx` 也是真 flag）
4. **先拿分再深挖**：一道题卡住 30 分钟 = 亏两道简单题
5. 多解一次的题：把脚本参数写进注释，现场改数据就行
6. **赛后**：录屏文件算 MD5 写入 Writeup：
   ```powershell
   Get-FileHash "D:\录屏\xxx.mp4" -Algorithm MD5   # 一次性算多个：Get-ChildItem *.mp4 | Get-FileHash -Algorithm MD5
   ```

## 五、不能 AI 的替代记忆法（赛前 1 天）
- 把速查表 Ctrl+P 打印成纸质版（可选）
- 手机里存速查表 PDF，随时翻
- 每个题型背一句"触发特征"：看到什么→用什么（上面每张表的"特征"列就是）