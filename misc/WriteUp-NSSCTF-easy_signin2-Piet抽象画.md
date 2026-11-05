# NSSCTF easy_signin2 WriteUp —— 二进制异或 + pngchunk + 抽象画(Piet)

> 赛事：NSSCTF Round#23 个人专项赛 · Misc（出题人 TOTO / W3NX1Z1）
> 附件：`here_is_your_flag.png`（2.6 MB）、`10xbig_to_more_clear.png`（1.9 KB）
> 提示：`hint: 二进制异或 pngchunk`　`hint2: 抽象画`
> 最终 flag：`NSSCTF{dge8f3hf3da45cd414f7affc5db5dadd}`

---

## 0. 两条提示分别对应什么

| 提示 | 实际含义 |
|---|---|
| 二进制异或 | 整份 PNG 被逐字节异或了某个固定值，先把文件"修"回来 |
| pngchunk | 修回来之后要按 chunk 解析文件结构——里面被拼进了第二张 PNG |
| 抽象画 | 第二张图是 **Piet 语言程序**（Piet 程序长得就像蒙德里安的抽象色块画，色块即指令） |

附件两个文件分工也很清楚：`here_is_your_flag.png` 是真图（被异或毁掉），`10xbig_to_more_clear.png` 是给 Piet 程序的**输入**。

---

## 1. 用异或把 PNG 修回来

用 010 / HxD 打开 `here_is_your_flag.png`，头 8 字节是：

```
CD 14 0A 03 49 4E 5E 4E     ← 不是 PNG
```

正常 PNG 签名是 `89 50 4E 47 0D 0A 1A 0A`。逐字节对比，每一个字节都差同一个值：

```
0xCD ^ 0x89 = 0x44      ('D')
0x14 ^ 0x50 = 0x44
0x0A ^ 0x4E = 0x44
...
```

所以整份文件被异或了 **0x44**，全文件异或回来即可：

```python
data = open('here_is_your_flag.png', 'rb').read()
key = data[0] ^ 0x89            # 用首字节和 0x89 推异或值，不用猜
open('fix.png', 'wb').write(bytes(b ^ key for b in data))
```

技巧点：**异或值不用猜**，拿文件首字节去异或 `0x89` 就自动算出来了。同理如果头被改的是 `Rar!`/`PK`/`%PDF`，换成对应首字节即可。

---

## 2. pngchunk：文件里拼了两张图

对 `fix.png` 按 chunk 解析（长度4 + 类型4 + 数据 + CRC4），结构是这样的：

```
       8  IHDR  len=13         CRC=ok     ← 第 1 张图 2326x4134
      33  pHYs  len=9          CRC=ok
      54  IDAT  len=1048576    CRC=ok
 1048642  IDAT  len=1048576    CRC=ok
 2097230  IDAT  len=523691     CRC=ok     ← 数据到这就完了，却「没有 IEND」
 2620933  IHDR  len=13         CRC=ok     ← 又冒出第二个 IHDR！
 2620958  pHYs  len=9          CRC=ok
 2620979  iTXt  len=1521       CRC=ok     （Photoshop 的 XMP，无用）
 2622512  IDAT  len=2548       CRC=ok
 2625072  IEND  len=0          CRC=ok
```

第 1 张图的 IDAT 之后直接跟上了第二张图的 IHDR，而第二张图**少了自己的 8 字节 PNG 签名**。这就是 `copy /b a.png + b.png` 这类拼接的产物（拼接时把前一个的 IEND、后一个的签名处理掉了）。

处理办法：从第二个 IHDR 的偏移 `2620933` 开始，一直拷到文件末尾，前面补回 `89 50 4E 47 0D 0A 1A 0A`，就能单独打开它：

```python
SIG = b'\x89PNG\r\n\x1a\n'
open('piet_program.png', 'wb').write(SIG + data[2620933:])
```

顺手确认一下：第一个 CRC 全部 ok、`zlib.decompress` 的长度正好等于 `行字节 × 行数`，说明没有别的截断/附加数据，flag 不在第一张图里。

第 1 张图（海报）和第 2 张图（495×495 彩色噪声）长这样：

| fix.png 里的海报（2326×4134） | 切出来的第二张（495×495） |
|---|---|
| NSSCTF 2024-04-28 海报，右下角一个企鹅二维码 | 看着像一堆彩色马赛克，"抽象画" |

海报只是障眼法（`here_is_your_flag.png` 这个文件名本身就是钓鱼）。

---

## 3. 抽象画 = Piet 程序

Piet 是 David Morgan-Mar 设计的一门 esolang，程序就是一张位图：**同色的连通色块(codel) + 颜色变化 = 指令**，写出来的程序天然像蒙德里安的抽象画。所以"抽象画"这条提示就是让你想到 Piet。

**先确定 codel 边长**：第 2 张图是 495×495，观察色块是严格对齐的，同色连续段长度都是 15 的倍数，于是

```
495 / 15 = 33  →  程序是 33 × 33 个 codel
```

（npiet 自己也会报 `codelsize guessed is 15 pixel`。）再看调色板，全图只用了 Piet 规定的 20 色：

* 6 色相 × 3 亮度：`FF0000/FFFF00/00FF00/00FFFF/0000FF/FF00FF`（正常），`FFC0C0...`（浅）、`C00000...`（深）
* `FFFFFF` 白 = 直行不执行指令　`000000` 黑 = 墙，撞上要转向

---

## 4. 跑起来：先要喂输入

官方工具是 npiet（`npiet.exe -v 1 piet_program.png`）。运行时它会先打印 `?` 提示要输入——这个程序**开头就 `in(char)`**，不给输入会一直卡在等输入。

输入从哪来？就是第二个附件 `10xbig_to_more_clear.png`：

```python
from PIL import Image
im = Image.open('10xbig_to_more_clear.png').convert('L')
px = im.load()
for y in range(im.height):
    for x in range(im.width):
        if 0 < px[x, y] < 250:      # 把所有中间灰度压成纯黑，抗锯齿/压缩噪声去掉
            px[x, y] = 0
im.resize((im.width*8, im.height*8), Image.LANCZOS).save('out.png')
```

得到一串很"flag 但又不是 flag"的字符串：

```
di`f{cfd7d1fd1ba254dcfa7f4155cfdadadc}
```

注意它是 ``di`f{`` 而不是 `flag{` —— 这是出题人故意做的**逐位偏移**：Piet 程序对每个字符做 `in(c) + k` 再 `out(c)`，k 由色块面积决定。所以肉眼看不出真 flag，必须跑程序。

把上面这串作为输入喂进去，输出就是：

```
flag{dge8f3hf3da45cd414f7affc5db5dadd}
```

---

## 5. 不用 npiet 的纯 Python 跑法

npiet 官网（`bertnase.de/npiet`）经常连不上，索性自己按规范写一个解释器（脚本见 `easy_signin2/piet.py`，也放进了工具箱 `31-Piet抽象画解释器.py`）。

核心逻辑只有三件事：

**① 20 色 → (亮度, 色相)，用色相/亮度的差值查指令表**

| 色相差 | Δ亮度=0 | Δ亮度=+1(变深) | Δ亮度=+2(变浅) |
|---|---|---|---|
| 0 | nop | **push**(刚离开那块面积) | pop |
| 1 | add | subtract | multiply |
| 2 | divide | mod | not |
| 3 | greater | pointer(改 DP) | switch(改 CC) |
| 4 | duplicate | roll | in(number) |
| 5 | **in(char)** | out(number) | **out(char)** |

**② 出块规则**：从当前同色块按 DP 方向取最远的一条边上的 codel；同一条边有多个时用 CC 决定取哪一个（DP=右时 CC=左取最上、CC=右取最下，其余方向同理旋转）；朝 DP 方向走一格，若越界或撞黑就顺时针转 DP 重试，四面全堵 → 程序结束。

**③ 白色特判**：进出白色的移动**不执行**任何指令，白块只当"通道"穿过去。

跑法（`piet.py` 里改顶部 `FILE` / `INPUT` 两行）：

```powershell
py piet.py
# [*] codel 边长 = 15，程序尺寸 = 33 x 33
# [+] 输出: flag{dge8f3hf3da45cd414f7affc5db5dadd}
```

我用 JS 实现的 `piet-interpreter` 和自己写的这个 Python 版各跑了一遍，输出完全一致，可以排除解释器实现 bug 导致的假答案。

---

## 6. 完整流程一句话版

```
here_is_your_flag.png
  └─ 逐字节异或 0x44 ──> 正常 PNG（NSSCTF 海报，无 IEND）
        └─ 解 chunk：第二个 IHDR 起被拼了一张缺签名的 PNG
              └─ 补 89 50 4E 47 0D 0A 1A 0A 切出来 ──> 495x495 = 33x33 codel 的 Piet 程序
                    └─ 输入 = 10xbig_to_more_clear.png 阈值化读出的 di`f{cfd7...}
                          └─ 跑 Piet ──> flag{dge8f3hf3da45cd414f7affc5db5dadd}
                                └─ 提交 NSSCTF{...}
```

## 7. 踩坑记录

* **别只看文件头**：头修好能打开，但你不知道里面还塞了第二张图，一定要把 chunk 列表打出来看有没有"第二个 IHDR"、有没有 IEND。
* **异或值不必猜**：`首字节 ^ 0x89` 一步到位；有 hint 也只说"二进制异或"，没给值，就是要你自己推。
* **codel 边长要算**：495 的因数有 3/5/9/11/15/33/45/55/99/165，凭感觉试很浪费；用"同色连续段长度的 gcd"一次定 15。
* **Piet 程序要输入**：直接跑会卡住（npiet 打印 `?` 等输入），别以为程序坏了。`10xbig_to_more_clear.png` 那张马赛克字就是输入源。
* **输入看着像假 flag**：``di`f{...}`` 是逐位 +k 偏移后的结果，硬猜"字母错位"猜不出来；这张图只有 176×44（约 4px/字符），肉眼极易认错一两个字符——判据是喂进去跑出来的结果必须整体符合 flag 结构，错一位那一位就废。
