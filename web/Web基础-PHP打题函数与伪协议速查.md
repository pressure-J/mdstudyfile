# Web 基础：PHP 打题函数速查表与伪协议全家桶

> 来源：ZJCTF「NiZhuanSiWei」等文件包含/反序列化实战题沉淀，2026-09-01
> 定位：PHP 审计题的"词典"——看不懂代码、不认识伪协议时翻这篇
> 实战场景：任何给 PHP 源码的题（文件包含、反序列化、命令执行、SSRF）

---

## 一、最小函数集：看懂 90% 的 PHP 题只需要这些

**核心思路**：PHP 函数几千个，但 CTF 高频的就几十个。**遇到不认识的当场查 php.net/manual/zh/ 就行，会查比会背重要**。下面按作用分组：

### 1. 输入获取（入口）

| 函数/变量 | 人话解释 | 常见用法 |
|---|---|---|
| `$_GET['x']` | 拿 URL `?x=值` | `?cmd=ls` → `$_GET['cmd']` |
| `$_POST['x']` | 拿 POST body 里的参数 | 表单提交 |
| `$_COOKIE['x']` | 拿 Cookie | `Cookie: user=xxx` |
| `$_REQUEST['x']` | GET/POST/Cookie 全要 | 不区分来源 |
| `$_SERVER['HTTP_X']` | 拿 HTTP 头 | `X-Forwarded-For`、UA 等 |
| `file_get_contents("php://input")` | 拿原始请求体 | POST body 全文（伪协议入口） |

### 2. 输出（看结果 / 泄漏信息）

| 函数 | 人话解释 | 注意 |
|---|---|---|
| `echo` / `print` | 输出字符串 | 输出对象时触发 `__toString()` |
| `print_r()` / `var_dump()` | 打印数组/对象结构 | 调试神器，审计时经常让源码"现原形" |
| `highlight_file()` / `show_source()` | 高亮显示文件源码 | 读 PHP 源码（不执行） |
| `phpinfo()` | 输出 PHP 配置全貌 | 泄漏版本、禁用函数、环境变量 |

### 3. 文件操作（高危区）

| 函数 | 人话解释 | 危险点 |
|---|---|---|
| `file_get_contents($f)` | 把文件内容读成字符串 | 参数可控 → 读任意文件（配合伪协议） |
| `file_put_contents($f, $c)` | 把字符串写进文件 | 参数可控 → 写 webshell |
| `include` / `require` | 加载并**执行** PHP 文件 | 参数可控 → LFI/RFI 文件包含 |
| `fopen/fread/fwrite` | 底层文件读写 | 同上 |
| `readfile()` | 直接输出文件内容 | 读文件 |
| `unlink()/rename()/copy()` | 删/改/拷文件 | 参数可控可删站 |

### 4. 字符串与编码

| 函数 | 人话解释 |
|---|---|
| `strlen()` | 字符串长度 |
| `substr($s, $i, $n)` | 截取部分字符串 |
| `str_replace($a,$b,$s)` | 替换（过滤靠它实现时可用双写绕过） |
| `strpos($s, $k)` | 查 k 在 s 里的位置（找不到返回 false） |
| `trim()` | 去首尾空格 |
| `md5()` | 哈希（弱类型比较 `==` 可以绕过） |
| `base64_encode/decode` | base64 编解码（和 filter 伪协议是搭档） |
| `serialize/unserialize` | 序列化/反序列化（反序列化漏洞核心） |
| `urlencode/urldecode` | URL 编解码（payload 传输必备） |

### 5. 正则与判断

| 函数 | 人话解释 | 绕过点 |
|---|---|---|
| `preg_match('/x/', $s)` | 正则匹配，有就返回 1 | 黑名单最常见实现，可用数组/换行/编码绕过 |
| `preg_replace('/x/', $r, $s)` | 正则替换 | `/e` 修饰符 = 命令执行（老版本） |
| `isset($x)` | 变量是否存在 | — |
| `empty($x)` | 是否为空 | `0`、`"0"`、`null` 都算空 |
| `exit()/die()` | 立刻终止程序 | 被拦时后面的代码不执行 |
| `is_numeric($x)` | 是否数字 | 数字+字母绕过（`1e3`） |
| `in_array($x, $arr)` | 是否在数组里 | 默认松散比较 |

### 6. 系统与命令（RCE 高危区）

| 函数 | 人话解释 |
|---|---|
| `system()` | 执行命令并输出结果（最常用） |
| `exec()` | 执行命令，只返回最后一行 |
| `shell_exec()` | 执行命令返回全部输出，不输出到页面 |
| `passthru()` | 执行并原样输出二进制 |
| `` `cmd` ``（反引号） | `shell_exec` 的简写 |
| `eval($code)` | 把字符串当 PHP 代码执行 |
| `assert($code)` | 字符串为真时当代码执行（老版本） |

---

## 二、伪协议全家桶（必背清单）

伪协议 = **"假装是文件路径，实际是特殊入口"**。`file_get_contents`、`include`、`fopen` 等吃路径的函数都能用它们。

### 核心两招（先背这两个）

| 场景 | 用法 | 为什么 |
|---|---|---|
| **读 PHP 源码** | `php://filter/read=convert.base64-encode/resource=文件名` | include/fetch 会**执行** php 文件看不到源码；filter 转成 base64 只输出不执行，本地解码即得源码 |
| **伪造文件内容** | `data://text/plain;base64,<base64内容>` 或 `php://input`（POST body 直接写内容） | 需要 `file_get_contents($x)==="某个固定字符串"` 时，自己提交内容满足它 |

### 全清单

| 伪协议 | 干什么 | 经典场景 |
|---|---|---|
| `php://filter` | 读文件+过滤器（base64/rot13/iconv 等） | 读 .php 源码；写日志注入 |
| `php://input` | 请求体当文件内容 | 绕过文件内容检查（POST 写内容） |
| `php://temp` / `php://memory` | 临时内存流 | 少见，配合上传 |
| `php://fd` | 直接访问文件描述符 | 高权限操作 |
| `data://` | 数据流：`data://text/plain;base64,xxx` 或 `data://text/plain,明文` | 伪造内容、绕过固定字符串检查 |
| `phar://` | 读 phar 压缩包内文件 | **phar 反序列化**（无 unserialize 也能触发） |
| `zip://` | 读 zip 内文件 | 配合上传打包含 |
| `file://` | 本地文件 | 读 /etc/passwd 等 |
| `http://` `https://` `ftp://` | 远程拉取当文件 | 远程包含（RFI）、SSRF |
| `glob://` | 目录通配匹配 | 列目录 |

### 记忆口诀

```
读源码不执行  → php://filter/read=convert.base64-encode/resource=xx
伪造内容比内容 → data://text/plain;base64,编码 或 php://input
任意文件读取  → php://filter 或 file://
压缩打包含   → phar://  zip://
远程当文件   → http://  (SSRF/远程包含)
```

---

## 三、拿到 PHP 源码怎么读（方法论）

1. **找入口**：哪些变量接收用户输入（`$_GET`/`$_POST`/`$_COOKIE`...）
2. **找处理**：输入经过了哪些函数（过滤？拼接？）
3. **找危险函数**：文件操作 / 命令执行 / unserialize / eval / include
4. **看过滤**：黑名单（preg_match）还是白名单，能不能绕过
5. **构造 payload**：危险函数需要的参数，从可控输入一步步喂进去

**反序列化题五问**（配合上面用）：
```
入口在哪？ → 哪些类可用？ → 哪个魔术方法危险？ → 危险代码要什么参数？ → 过滤怎么绕？
```

---

## 四、实战示例：ZJCTF「NiZhuanSiWei」是怎么用这些知识的

```
① 入口：$_GET["text"] $_GET["file"] $_GET["password"]
② 处理：text 被 file_get_contents 检查 === "welcome to the zjctf"
   → 绕过：data://text/plain;base64,d2VsY29tZSB0byB0aGUgempjdGY=
③ 危险函数：include($file)（文件包含）、unserialize($password)+echo（反序列化）
④ 过滤：preg_match("/flag/", $file) → file 参数不能含 flag
   → 绕过：php://filter 读 useless.php（不含 flag 字样）拿 Flag 类源码
⑤ 构造：password=O:4:"Flag":1:{s:4:"file";s:8:"flag.php";}
   → echo 对象触发 __toString → file_get_contents("flag.php") 吐源码出 flag
```

---

## 五、面试/考试速答卡

- **读 PHP 源码用啥**：`php://filter/read=convert.base64-encode/resource=文件名`（必须 base64，否则 include 会执行）
- **file_get_contents 内容检查怎么绕**：`data://` 或 `php://input` 自己提交内容
- **include vs file_get_contents**：include 加载并**执行** PHP；file_get_contents 只读字符串不执行
- **echo 一个对象会发生什么**：触发 `__toString()` 魔术方法
- **最常见危险函数**：`include` `file_get_contents` `system` `eval` `unserialize`
- **黑名单 preg_match 常见绕过**：数组参数（preg_match 遇数组返回 false）、换行符 `%0a`、URL 编码
- **函数看不懂怎么办**：查 php.net/manual/zh/，CTF 高频函数就上面几十个