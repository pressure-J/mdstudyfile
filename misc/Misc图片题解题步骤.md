---
title: Misc图片题解题步骤
tags: [misc]
created: '2026-09-09T12:00:00.000Z'
modified: '2026-09-09T12:00:00.000Z'
---

# Misc 图片题解题步骤

## 一、三条铁律(先读)

1. **先免费检查,再上算法**:strings / 文件头 / binwalk 三连,八成题到这就完了
2. **图片"看着正常"才考虑 LSB**,有异常先处理异常(宽高错、缺角、变形)
3. **10 分钟没进展就换思路**,别在一条路上死磕(沿用 crypto 铁律)

## 二、排查流程(按顺序走)

### 第 1 步:文件头 / 真实类型
```python
# 看前 4 字节魔数
89 50 4E 47 = PNG    FF D8 FF = JPG    47 49 46 38 = GIF    42 4D = BMP
```
扩展名可能被改。用工具箱 `misc\03-文件类型识别与strings.py`,拖入文件改 FILE 一行即可。
> **注意**:改 FILE 时只改引号里的路径,**别把注释一起粘进去**(否则报 FileNotFoundError)。

### 第 2 步:strings + 附加数据
```
strings 图片 | grep -iE 'flag|ctf|key|{'
```
找文件尾部藏明文 flag;有 binwalk 的话看有没有藏了另一个文件(zip/图片),有就 `-e` 拆出来。

### 第 3 步:看图片本身有没有"异常"
| 症状 | 处理 |
|------|------|
| 宽高被改(CRC 报错/图片变形) | 修复 IHDR 宽高,恢复后被裁掉的 flag |
| 二维码缺角/变形 | PS 补角/反色后扫码 |
| 图片"看不出异常" | 进入第 4 步 |

### 第 4 步:Exif 元数据
`exiftool 图片` 看注释、作者、GPS——flag 常藏在元数据里。

### 第 5 步:LSB 隐写(重点)
**触发特征**:图看着完全正常,但题目提示"仔细看 / look very closely / 放大镜 / 像素 / LSB / 最低位"。

**原理**:PNG/BMP 无损格式下,每个像素 R/G/B 各取最低 1 位(bit),按行拼成二进制流 → 按 8bit 分组转 ASCII。肉眼看不出的 1-3 级色差,程序能精确还原。

**工具**:
- Linux: `zsteg 图片.png`(自动扫所有通道组合,PNG 首选)
- Windows: 工具箱 `misc\06-像素取色与LSB提取.py`
  - 默认三通道全取;出乱码就改 `CHANNEL = 'R'/'G'/'B'` 单独取
  - 提取结果若是可读文本 → 直接是答案 或 给出密钥
  - 提取结果若是文件签名(PNG/ZIP)→ 已存 `lsb_extracted.bin`,再分析

> **注意**:steghide 只支持 JPEG/BMP,**PNG 用 steghide 无效**,PNG 一律 zsteg。

### 第 6 步:像素取色
flag 藏在特定色值/坐标 → 扫描全图找"特殊颜色"像素(工具箱 `15-` 脚本自带此功能)。

## 三、LSB 提取出"密钥"≠结束,先判断是否就是答案

LSB 提取出的内容分两种情况:
1. **直接是 flag**:`flag{...}` / `picoCTF{...}` → 提交
2. **只是一句提示/密钥**:如 `the secret key is: xxx` → 密钥可能用于:
   - steghide 解 JPEG/BMP(此题是 PNG 则不适用)
   - 解加密压缩包
   - **但有时密钥本身就是答案**(题目只要求提取,flag 就是那段内容)→ 先别急着找第二层,试试直接提交

## 四、实战记录

### 例:"镜子里面的世界" steg.png(放大镜图)
- 图片:800×600 PNG,画面是放大镜+文字 "look very closely"(提示 LSB)
- 流程:文件头识别=PNG → strings 无明文 → 尺寸/格式正常(24bit RGB,无色异常)
- **LSB 全通道提取** → `Hey I think we can write safely in this file without anyone seeing it. Anyway, the secret key is: st3g0_saurus_wr3cks`
- 结果:密钥 `st3g0_saurus_wr3cks` **本身就是答案**
- 教训:①提示"仔细看"几乎必是 LSB;②PNG 不要用 steghide;③LSB 出的是密钥时,先试直接提交再想第二层

### 例:PicoCTF St3g0(pico.flag.png)
- `zsteg pico.flag.png` 输出 `b1,rgb,lsb,xy .. text: "picoCTF{7h3r3_15_n0_5p00n_xxx}$t3g0"`
- 题名 St3g0 就是 LSB 提示;flag 直接藏在 b1,rgb,lsb,xy 这一行

### 例:KEY.exe(data URI 伪装 + base64 + 二维码)
- 拿到 `.exe`(3.8KB),**别看扩展名,先看魔数** → 内容是 `data:image/jpg;base64,iVBORw0KGg...`
- **识别特征**:`data:image/...;base64,` 开头 = data URI 伪装(文件其实是 base64 编码的图片)
- 解法:
  1. 去掉 `data:image/jpg;base64,` 前缀
  2. base64 解码 → 得到 133×133 图片(魔数 `89504e47` 实际是 PNG,前缀写的 jpg 是迷惑)
  3. 图片是二维码 → 扫码 → flag
- 教训:①文件伪装题(改扩展名/data URI)一律先看魔数;②data URI 的格式名可能与实际不符(写 jpg 实为 png)

## 五、做题顺序总结

1. 文件头识真类型 → 2. strings/binwalk 找明文 → 3. 看图片有无异常(宽高/二维码)→ 4. Exif → 5. 图正常 → **LSB 提取**(PNG 用 zsteg)→ 6. 结果判断:flag 直接提交 / 密钥再解

> 这是**线性流程**。若想按"线索 → 手法"直接跳（比如一眼看出是 JPEG 且毫无异常），用第六节的对照表 + 6.3 穷举顺序。

> **补充**:拿到任何文件先 `12-文件类型识别`(看魔数),若开头是 `data:image/...;base64,` → 是 base64 图片伪装,去掉前缀解码即可

## 六、常见隐写手法清单（看到什么找什么）

> 上一节是"按顺序走一遍"的**流程**，这一节是"线索 → 手法"的**对照表**。
> 实战里不用死背流程，先看图和题面给了什么，直接跳到对应手法。

### 6.1 按痕迹大小分类（决定先查哪里）

| 类别 | 文件长度 | 有无文件签名 | 典型手法 | 一句话判据 |
|------|---------|------------|---------|-----------|
| **追加型** | 变长 | 有（`PK`/`FFD8`/`GIF8`…） | 尾部藏 zip/图片、多文件拼接 | `strings` 能看到可疑文件名；binwalk 一击即中 |
| **嵌入型** | 不变 | 无 | LSB、隐写算法改像素/系数、元数据 | 图完全正常，`strings` 干净，只能靠工具扫 |
| **伪装型** | 随意 | 与扩展名不符 | 改扩展名、data URI、多格式缝合 | 看魔数，别信扩展名 |

先量长度再决定方向：`stat -c '%s' 图` 与"正常出图后应有的大小"对比。

### 6.2 手法清单（按排查性价比排序）

#### ① 文件尾追加数据（最高频，先查）
图到结束标记就"画完了"，后面多出来的字节没人读，可以塞一整个文件。

- **判据**：`FF D9`/`IEND` 之后还有 `PK\x03\x04`、`FFD8FF` 等签名，`strings` 能读出名（`flag.txt`、`asd/qwe.zip`）
- **做法**：工具箱 `misc\04-PNG结构解析与切附加数据.py`（PNG 走 chunk 到 IEND；JPG 走找尾标记）或 `misc\11-文件分离.py`；等价 binwalk -e / foremost
- **坑**：找宿主图片结尾**只用第一个结束标记**，别 `rfind`——内嵌 ZIP 里还会冒出同样的 `FF D9`，`rfind` 会切出残缺片段

#### ② ZIP 伪加密 / 真加密判别（追加型后面常接这步）
"压缩包要密码"先别急着爆破，先判真假。

- **判据**：压缩方法 `store` 且 `压缩大小 == 原始大小` → **伪加密**（数据没变长）；`压缩大小 ≈ 原始大小 + 12` → **真 ZipCrypto 加密**（每个人头 12 字节）
- **伪加密修复**：只改**目录区 CDH**（`PK\x01\x02` 后第 8 字节）的标志位 `01 08` → `00 08`。改本地文件头 LFH 那个没用（软件只看 CDH）
- **真加密**：去找密码（线索常在图片隐写或题面里），别一上来字典爆破
- **坑**：出题人会把某条目的 CRC32 填坏，`zf.read()` 抛 `BadZipFile("Bad CRC-32")`——文件没坏，按 LFH 手工 carve 条目字节流

#### ③ 色彩通道 LSB（无损格式主力：PNG / BMP）
每像素 R/G/B 各取最低 1 位按行拼接 → 8bit 分组转 ASCII。改动只有 ±1 级色阶，肉眼不可能看出。

- **判据**：图完全没有其他异常，题面提示"仔细看 / look closely / 像素 / 最低位"
- **做法**：`misc\06-像素取色与LSB提取.py`（默认三通道全取；乱码改成只取 R/G/B 单通道）
- **坑**：**PNG 用 steghide 无效**（steghide 不吃 PNG 的像素域），PNG 一律走 LSB / zsteg

#### ④ JPEG 压缩域隐写（steghide —— 最容易漏的一类）
**这类最"干净"**：文件长度不变、尾部无附加数据、`strings`/`binwalk`/010 全空，但确实藏了东西。

- **原理**：不做像素 LSB，而是改**量化后的 DCT 系数**（JPEG 压缩时产生的那些系数），用**成对系数交换**（graph matching）保证每个系数值的出现频率几乎不变 → 卡方/RS 一阶统计检测抓不到
- **口令的双重作用**：口令既当加密密钥，又当 PRNG 种子决定"哪批系数承载数据、按什么顺序"。所以口令错时读出来是噪音，不是解密失败
- **判据**：图看着正常、其他手法全空 → 直接 `steghide info`
- **做法**：
  ```bash
  steghide info 图.jpg -p ""             # 报 embedded file "ko.txt" 即为有货
  steghide extract -sf 图.jpg -p "" -f   # 空口令提取（很多题就是空口令）
  ```
- **坑 1（PowerShell）**：PS 5.1 会把**空字符串参数直接丢掉**，`-p ""` 传到 exe 只剩 `-p` → 报 `the "-p" argument must be followed by the passphrase`。三种正确写法：① 加 `--%` 停止解析（`steghide --% extract -sf x.jpg -p "" -f`，**推荐**）② 干脆不传 `-p`，交互提示时直接回车 ③ 换到 cmd.exe 执行。实测 `cmd /c "... " ..."` 嵌套引号写法反而**传不对**，别用
- **坑 2（编码）**：提取出的 `ko.txt` 之类常是 **GBK 编码**，读数用 `open(rb).read().decode('gbk')`，别当 UTF-8
- **坑 3（版本差异）**：0.5.1 口令错报 `could not extract any data with that passphrase!`；新版报 `extracted data is not valid`

#### ⑤ PNG 宽高隐写（改 IHDR 藏被裁掉的部分）
把 IHDR 的宽/高改小，图片只显示一部分；改回来露出下方被裁区域里的 flag。

- **判据**：图片被截断/变形、CRC 校验错误
- **做法**：按 IHDR 的 CRC32 反解正确的宽高（枚举宽高算 CRC 撞中即得），或直接用工具箱 PNG 结构脚本改
- **关键**：改完要**同步重算 CRC**，否则多数工具拒绝渲染

#### ⑥ Exif / 元数据
`exiftool 图`，flag 常藏在 Comment / ImageDescription / Artist / GPS，也可能整段是 base64。注意有些题会把 EXIF 段本身做成第二层容器。

#### ⑦ 二维码与视觉变形
- 二维码：先扫（工具箱 `misc\05-二维码解码.py`），扫不出再考虑缺角/变形/反色/反转
- **半张或者错位的二维码**：拼接两张互补的图 → 用 PS"正片叠底/叠加"合并；也常见"反色后再扫"
- **像素画/色块**：题面给一个很大像素格 → 每个格子的颜色映射成比特

#### ⑧ 文件后缀 / data URI 伪装
- **判据**：开头是 `data:image/png;base64,` 之类 → 文件其实是 base64 文本，不是二进制图
- **做法**：去掉前缀 → base64 解码 → 得到真图。注意前缀写的格式可能和真实格式不符（写 jpg 实为 png）
- **原则**：**永远先看魔数，不信扩展名**（`.exe` 可能整个是文本，`.jpg` 可能整个是 zip）

#### ⑨ 多帧动图 / 多文件拼接
GIF/APNG：逐帧翻，某帧只有 flag（一帧一帧看，或用 06 脚本的帧处理）
多文件：一个文件里拼了若干完整图片，按签名逐个切出来

#### ⑩ 频域 / 抗压缩隐写（低频但会考）
- **outguess**：JPEG，需密钥；`outguess -k 'key' -r in.jpg out`（题面常给 key 提示，如"abc"）
- **F5**：JPEG，`java Extract 图.jpg`
- **盲水印**：两张几乎一样的图 → 差分/`blind_watermark` 提取
- **音频才算**：频谱图（`Audacity` 切 spectrogram）、摩斯、DTMF——但图片题偶尔混进"音频藏图"

#### ⑪ 图片本身是"载体容器"
- **PDF/docx 里嵌图**：解压容器取 `word/media/*`
- **图其实是压缩包**：直接改后缀或用 7z 打开
- **图是磁盘镜像**：`7z x 图.vmdk` 展开（是的，CTF 真考过）

### 6.3 一张图没有线索时的穷举顺序

```
1. 看魔数，确认是真图片（不是改了后缀的 zip / base64 文本）
   ↓ 是图
2. strings + 查尾部附加数据（04 / 11 脚本）→ 有 zip 就走「伪加密判别 → 真加密找密码」
   ↓ 没有
3. Exif 元数据
   ↓ 没有
4. 看画面异常：宽高/缺角/错位二维码/多帧
   ↓ 都正常
5. LSB（PNG/BMP）或 steghide（JPEG）
   ↑ 两类格式分开走，别拿错工具
   ↓ 还是空
6. 频域（outguess/F5，题面给了 key 就试）、盲水印、图像差分
```

> **两个最容易走错的分叉**：
> ① 格式决定工具——**PNG 用 LSB/zsteg，JPEG 用 steghide/outguess**，互换必失败；
> ② "文件一点都不大、binwalk 也空"不代表没东西，压缩域隐写就是这种特征，直接上 steghide info。

### 6.4 手法 → 工具箱脚本对照

| 手法 | 工具箱脚本（`D:\python\CTF工具箱\misc\`） | 备注 |
|------|------|------|
| 扩展名伪装 / 看魔数 | `03-文件类型识别与strings.py` | 同时给 strings + 可疑串标记 |
| 尾部追加数据 | `04-PNG结构解析与切附加数据.py` | PNG 走 chunk；JPG 找尾标记 |
| 通用文件分离 | `11-文件分离.py` | 等价 binwalk -e / foremost |
| LSB / 像素取色 | `06-像素取色与LSB提取.py` | 两功能合一，默认 RGB 全取 |
| 二维码 | `05-二维码解码.py` | 扫不出再考虑变形 |
| data URI 伪装图 | `07-dataURI还原图片.py` | 去掉前缀解码 |
| Exif | 本机未装 exiftool（可选装） | 也可用 Python `PIL.Image._getexif()` |
| JPEG 压缩域 | **steghide**（非 Python，D:\python\CTF工具箱\steghide\steghide.exe） | 先 `info` 再 `extract` |

---

## 七、综合实战：九连环（追加型 + 压缩域 + 伪加密）

完整走一遍"追加型 + 压缩域 + 伪加密"三件套，正好把 6.2 的 ①②③④ 全串一遍。

**题目**：`123456cry.jpg`（48984 字节，300×300）

| 步骤 | 操作 | 结果 |
|------|------|------|
| ① 找尾部数据 | 搜 `FF D9` 得两处：`0x4C66`、`0x4D33`。**取第一个** | `0x4C66` 后紧跟 `50 4B 03 04`，即内嵌 ZIP（29424 字节）|
| ② 判加密真伪 | 看 CDH 标志位 `01 08` + 压缩大小==原始大小 | **伪加密**，改 `01 08`→`00 08` |
| ③ 解外层 | 解出 `asd/good-已合并.jpg`（29992）+ `asd/qwe.zip`（184）| 图片长度不变、无附加数据、strings 干净 |
| ④ JPEG 压缩域 | 其他手法全空 → `steghide info good-已合并.jpg -p ""` | 命中：`embedded file "ko.txt": size 48.0 Byte` |
| ⑤ 提取密码 | `steghide extract -sf good-已合并.jpg -p "" -f` | `ko.txt`（GBK）="看到这个图片就是压缩包的密码：`bV1g6t5wZDJif^J7`" |
| ⑥ 内层是真加密 | `qwe.zip` 标志位 `0x0801` + 压缩大小 184 > 原始 22 | 确认真加密（ZipCrypto）|
| ⑦ 解出 flag | `7z x qwe.zip -pbV1g6t5wZDJif^J7 -y` | **flag{1RTo8w@&4nK@z*XL}** |

**这题的三个知识点**：
1. `rfind` 找 `FF D9` 会切坏（ZIP 内部也有该字节对）——用第一个结束标记
2. 伪加密只改 CDH，改 LFH 无效
3. 图片"什么都没藏"的样子其实就是藏了——steghide 改的是 DCT 系数，文件长度和统计特征全都不变

> **reproduce 用脚本**：解题代码见 `D:\python\CTF工具箱\challenges\` 下的现场脚本（改顶部 `SRC` 一行即可复用）。

*最后更新：2026年10月9日*
