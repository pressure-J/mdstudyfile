# Web基础 · 数字的不同写法 / 通配符 / 正则表达式

> 定位：三个看起来无关、实则同源的概念——**同一串字符，在不同"解释器"里含义不同**
> 关联题目：Ping 命令注入（通配符被黑名单封死后改走 `grep -r`）、Unicorn Shop（Unicode 数字语义绕过长度校验）
> 环境：本机实测（Python 3.12.6 / git-bash）

---

## 零、总纲：到底是谁在解释你的输入

这是理解全文的关键。用户输入 `fla*` 这一串字符，它在不同环节会被**不同的解释器**赋予不同含义：

```
用户输入  "fla*"
    │
    ├─► shell 解释   → glob 展开成实际文件名 flag.php
    ├─► Python glob  → 同样展开成文件名列表
    ├─► Python fnmatch → 当成"模式"，去匹配别的字符串
    └─► 正则引擎     → '*' 的含义完全不同（重复前一个元素）

用户输入  "万"
    │
    ├─► int() / Number() / intval()  → 解析失败
    └─► unicodedata.numeric() / intl → 10000
```

**安全漏洞的本质，就是"你以为输入是普通字符串，但某个环节把它当成了有特殊语义的东西"。**

---

## 一、数字的不同写法

### 1. 值 ≠ 写法

键盘上的 `9` 只是 Unicode 表里的码点 **U+0039**。Unicode 里有一整批字符，语义是数字，只是外观不是阿拉伯数字。

本机实测（`unicodedata.numeric()`）：

```
字符   类别            码点      int()        unicodedata.numeric()
9      ASCII 数字      U+0039    9            9.0
１     全角数字         U+FF19    1            1.0
٩     阿拉伯-印度数字   U+0669    9            9.0
९     天城文数字       U+096F    9            9.0
⑨     带圈数字         U+2468    ValueError   9.0      ← int() 不认
²     上标            U+00B2    ValueError   2.0
½     分数            U+00BD    ValueError   0.5
Ⅹ     罗马 10         U+2169    ValueError   10.0
Ⅿ     罗马 1000       U+216F    ValueError   1000.0
ↈ     罗马扩展 100000  U+2188    ValueError   100000.0
一     汉字 1          U+4E00    ValueError   1.0
十     汉字 10         U+5341    ValueError   10.0
万     汉字 1e4        U+4E07    ValueError   10000.0
亿     汉字 1e8        U+4EBF    ValueError   100000000.0
```

### 2. 分水岭：解析器认不认

同一个 `万`，各语言标准解析函数的表现：

| 解析器 | `'万'` | `'９'` 全角 | 说明 |
|---|---|---|---|
| Python `int()` | ValueError | ValueError | 只认 ASCII |
| JS `Number()` | NaN | NaN | 同上 |
| PHP `intval()` | 0 | 0 | 同上 |
| Python `unicodedata.numeric()` | 10000.0 | 1.0 | **Unicode 感知** |
| PHP `intl` / `NumberFormatter` | 10000 | 1 | **ICU 库，Unicode 感知** |
| JS `Intl.NumberFormat` | 10000 | 1 | 同上 |

### 3. 怎么变成绕过手法（Unicorn Shop 题眼）

```php
if (mb_strlen($price) > 1) die("too long");   // 按"字符个数"算 → '万' = 1 个字符
$p = <unicode感知的解析>($price);              // 按"数值语义"算 → '万' = 10000
if ($p < 1337) die("not enough");
```

两个校验用了**两套取值口径**：一个数字符个数，一个取数值语义。`万` 是 1 字符 / 3 字节，于是同时满足"长度=1"和"值=10000"。

> **绕过要点：不是编码技巧，而是口径不一致。** 遇到"长度限制"和"数值要求"互相矛盾时，先问：服务端数长度和取数值，用的是同一个字符串表示吗？

### 4. 相关变体：同形异义字 (Homoglyph)

```python
'а'  # U+0430 西里尔小写 a —— 和英文 'a' U+0061 肉眼无法分辨
'А'  # U+0410 西里尔大写 A
```
用途：绕过字符串黑名单。`аdmin`（首字母是西里尔）在很多朴素比较里能骗过 WAF。同理还有 `０`(全角) vs `0`、`１` vs `1`。

---

## 二、通配符（glob）—— 不是 shell 专有

### 1. 基本语法

| 符号 | 含义 | 例子 | 结果 |
|---|---|---|---|
| `*` | 任意长度（含 0）任意字符，**不跨目录** | `fla*` | `flag.php flag2.txt` |
| `?` | **恰好一个**字符 | `fla?.php` | `flag.php` |
| `[abc]` | 方括号内任选一个 | `[fi]*` | `flag.php flag2.txt index.php` |
| `[a-z]` | 区间内任选一个 | `[a-i]*` | 同上 |
| `[!abc]` | 取反（shell 里是 `[!..]`，不是 `[^..]`） | | |
| `**` | 跨目录递归（**需显式开启**） | `**/*.php` | 含子目录 |

### 2. 谁在用 glob（重点回答"是不是 shell 专有"）

**不是 shell 专有。** glob 是一个通用语法，多个环境都实现了它：

| 环境 | 实现 | 是否碰文件系统 |
|---|---|---|
| **shell (bash)** | 内建 glob，命令交给程序**前**展开 | 是 |
| **Python** | `glob.glob()` / `pathlib.Path.glob()` | 是 |
| **Python** | `fnmatch.fnmatch()` —— 纯字符串匹配 | **否** |
| **Node.js** | `glob` / `minimatch` 包 | 视 API |
| **Windows cmd** | `*` `?` 但**由程序自己解释**（cmd 不展开） | 否 |
| **PowerShell** | `Get-ChildItem -Path`、`-like` | 视命令 |
| **各种构建工具** | `.gitignore`、Webpack glob、Makefile | 是 |

实测对比：

```python
import glob, fnmatch
glob.glob('fla*')       # ['flag.php', 'flag2.txt']       ← 语法和 shell 完全一致
glob.glob('*.php')      # ['flag.php', 'index.php']
glob.glob('fla?.php')   # ['flag.php']
glob.glob('[fi]*')      # ['flag.php', 'flag2.txt', 'index.php']
glob.glob('**/*.php', recursive=True)  # 含 sub/deep.php ← '**' 才递归
```

```python
fnmatch.fnmatch('flag.php', 'fla?.php')      # True   ← 纯字符串, 不读磁盘
fnmatch.fnmatch('flaX.php', 'fla?.php')      # True
fnmatch.fnmatch('flag.txt', 'fla?.php')      # False
fnmatch.translate('fla?.php')                # '(?s:fla.\\.php)\\Z'
```

**`fnmatch.translate()` 这一行揭示了一个重要事实：glob 在内部被翻译成了正则。**
所以 glob 和正则不是两套东西，而是**同一套匹配引擎的两层外壳**：glob 是简化的、面向文件名的子集，正则才是完整的表达力。

### 3. 一个高频坑：fnmatch 在 Windows 下不区分大小写

```python
fnmatch.fnmatch('Flag.PHP', 'flag.php')      # True   ← Windows 上大小写不敏感
fnmatch.fnmatchcase('Flag.PHP', 'flag.php')  # False  ← 严格
```
原因：`fnmatch` 会调用 `os.path.normcase`，Windows 把它转成小写。做安全校验时如果用了 `fnmatch` 且跑在 Windows，可能存在大小写绕过。

### 4. shell 独有的两个特性（这才是 shell 专有的部分）

① **展开时机**：shell 在**把命令交给程序之前**就展开了。用 Python 脚本证明：

```python
import sys; print(sys.argv[1:])
```
```bash
$ py argv.py fla*        # 不加引号 → 程序收到 ['flag.php', 'flag2.txt']
$ py argv.py "fla*"      # 加引号   → 程序收到 ['fla*']
```
**这解释了命令注入题的经典 payload**：`cat fla*` 之所以能读 `flag.php`，是因为**shell 展开发生在 PHP 的黑名单检查之后**。PHP 只看到字符串 `fla*`，而 shell 才把它变成真实文件名——代码层根本不知道最终会读到什么文件。

② **引号规则**（shell 专有，务必记牢）：

| 引号 | `*` 展开? | 变量 `$x` 展开? | 反引号 `` ` `` 执行? |
|---|---|---|---|
| 不加引号 | ✅ | ✅ | ✅ |
| 双引号 `"..."` | ❌ | ✅ | ✅ |
| 单引号 `'...'` | ❌ | ❌ | ❌（最强隔离） |

实测：
```bash
$ echo 引号外: fla*              → 引号外: flag.php flag2.txt
$ echo "引号内: fla*"            → 引号内: fla*
$ echo "today is `echo 2026-10-05`"  → today is 2026-10-05     (双引号内反引号仍展开)
$ echo 'today is `echo 2026-10-05`'  → today is `echo ...`     (单引号内不展开)
```

> 单引号是"最安全的兜底"：任何字符放进去都变成字面量。CTF 里 WAF 挡不住时，往往能从引号拼接或反引号执行找到缝。

---

## 三、正则表达式（regex）—— 也不是 shell 专有

### 1. 最容易混的对比：`*` 含义完全相反

| | 通配符 glob | 正则 regex |
|---|---|---|
| `*` | 前面**整个模式** → 任意长度 | 修饰**前一个元素** → 重复 0~n 次 |
| 匹配对象 | 文件名 | 任意文本 |
| 通用写法 | `fla*` | `fla.*` |
| 谁实现 | shell / glob 库 / fnmatch | **所有主流语言内建的独立引擎** |

正则本质上是一门**独立的小型语言**，它的"宿主"非常多：

| 宿主 | 用法 |
|---|---|
| shell | `grep -E`、`sed`、`awk`、bash `=~` |
| Python | `re` 模块 |
| PHP | `preg_match` / `preg_replace` |
| JS | `RegExp`、`/pattern/` |
| Java | `java.util.regex` |
| 数据库 | MySQL `REGEXP`、PostgreSQL `~` |
| 编辑器 | VSCode 查找、vim `/` |
| 工具 | `rg`(ripgrep)、`nginx location ~`、`ModSecurity`、各种 WAF |

所以：**glob 是用来"找文件"的，正则才是"匹配文本"的通用工具。** 它们不是同一个层级的东西。

### 2. 元字符速查

| 符号 | 含义 | 例子 |
|---|---|---|
| `.` | 任意一个字符（默认不含换行） | `a.c` → `abc` `axc` |
| `*` | 前一元素重复 **0~n** 次 | `ab*` → `a` `ab` `abbb` |
| `+` | 前一元素重复 **1~n** 次 | `ab+` → `ab` `abbb`（不含 `a`） |
| `?` | 前一元素 **0 或 1** 次 | `colou?r` → `color` `colour` |
| `{n,m}` | 重复 n~m 次 | `a{2,3}` → `aa` `aaa` |
| `^` `$` | 行/串 首、尾锚定 | `^abc` `xyz$` |
| `[...]` / `[^...]` | 字符类 / 取反字符类 | `[0-9]` `[^0-9]` |
| `\d` `\w` `\s` | 数字 / 单词字符 / 空白 | `\d+` |
| `\b` | 单词边界 | `\bcat\b` |
| `\|` | 或 | `cat\|dog` |
| `(...)` | 分组/捕获 | `(ab)+` |
| `\` | 转义为字面量 | `\.` 匹配真正的点 |

实测：
```bash
$ grep -E '^h' t.txt        → hello123            (行首锚定)
$ grep -E '[0-9]+' t.txt    → hello123 / abc-456  (连续数字)
$ grep -E '^[A-Z]+$' t.txt  → HELLO               (整行全大写)
```

注意 glob→regex 的语义映射（易错点）：
- glob `*` ↔ regex `.*`
- glob `?` ↔ regex `.`
- glob `[ab]` ↔ regex `[ab]`（**这个恰好一致**）

### 3. 三个高频陷阱

**① 贪婪 vs 懒惰**
```
文本: <a>1</a><b>2</b>
<.*>   → 匹配整串 <a>1</a><b>2</b>   （贪婪，吃到底）
<.*?>  → 只匹配 <a>                  （加 ? 变懒惰）
```

**② `.` 默认不匹配换行**，除非加 `s` 修饰符（Python 用 `re.DOTALL`）。
→ PHP `preg_match('/.*f.*l.*a.*g.*/', $ip)` 里 `.` 不含 `\n`，**理论上**可用 `%0a` 拆开关键字绕过；但 Ping 题里黑名单同时禁了 `\x00-\x1f`（含换行），这条路被封死。**这就是"正则写漏 + 但另有补丁"的典型双重保险。**

**③ `match` 与 `search` 的区别（Python）**
```python
re.match(r'la', 'flag')    # None     ← match 只从串首开始
re.search(r'la', 'flag')   # <Match>  ← search 任意位置
```
PHP 的 `preg_match` 等价于 `search`（部分匹配）。所以 `preg_match('/flag/', $input)` 只要输入**包含** `flag` 就拦——这也是为什么绕过思路是"打散重拼"（`fla$1g`、`fla*`、变量拼接）。

### 4. 黑名单为什么总被绕过

| 通病 | 绕过手法 |
|---|---|
| 只禁字面量（小写） | `FLAG` / `Flag` / 全角 |
| 只禁单字符 | 拼接：`fla""g` `fla$1g` `$a$b` |
| 正则写太窄 | DVWA Medium 只禁 `&&` 却没禁 `&` |
| 没加 `s` / `i` | `%0a` 拆行、大小写 |
| 散点顺序正则 | `/.*f.*l.*a.*g.*/` 拦不住 `grep -r . .` |

**核心结论：黑名单是"枚举禁止项"，一定有遗漏；白名单（只允许符合格式的输入）才是安全的。**

---

## 四、一张表串起三者

| | 数字写法 | 通配符 glob | 正则 regex |
|---|---|---|---|
| 匹配/表达对象 | 单个字符的"值" | 文件名 | 任意文本 |
| 典型符号 | `①٩９万Ⅹↈ` | `* ? [abc]` | `.* + ? ^$ \d ()` |
| `*` 含义 | — | 任意长度字符串 | 前一元素重复 0~n |
| 谁解释 | Unicode 感知的数字解析器 | shell / `glob` / `fnmatch` | 各语言的独立正则引擎 |
| 是否 shell 专有 | 否（是 Unicode 标准） | **否** | **否** |
| CTF 用途 | 绕过长度校验、同形字绕过黑名单 | 绕过关键字黑名单读文件 | 既是防御工具、也是被绕对象 |

---

## 五、知识点沉淀

1. **数字的"值"和"写法"要分开看**。`int()`/`Number()`/`intval()` 只认 ASCII，而 `unicodedata.numeric()`/`intl`/`Intl` 是 Unicode 感知的。两者行为不同 → 漏洞空间。
2. **glob 不是 shell 专有**。Python 有 `glob`（读磁盘）和 `fnmatch`（纯字符串）两个模块；语法与 shell 一致。`fnmatch.translate()` 暴露了 **glob 本质是正则的简化外壳**。
3. **正则不是 shell 专有**，它是几乎所有语言/工具内置的独立引擎；shell 只是众多宿主之一（`grep -E` 等）。
4. **shell 真正专有的是"展开时机"和"引号规则"**：glob 展开发生在程序收到参数**之前**，这正是命令注入题里 `cat fla*` 能绕过 PHP 黑名单的根本原因——**代码层检查的是字符串，shell 层执行的是展开后的真实文件名，两者之间存在认知差**。
5. **单引号是最强隔离**（连反引号都不展开），双引号次之（仍允许变量和反引号），不加引号最危险。
6. **遇到"规则互相矛盾"的题**，先问："服务端数长度和取数值，用的是同一个字符串表示吗？"
