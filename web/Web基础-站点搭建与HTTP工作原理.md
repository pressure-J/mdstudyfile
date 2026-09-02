# Web 基础：站点搭建与 HTTP 工作原理

> 来源：课程实验《Web站点搭建与工作原理分析》（LAMP 环境 + 虚拟主机 + WordPress，2025-2026 第二学期），以课件详细版（27 页实验指导）为主
> 定位：Web 安全的知识底盘——不懂"一次访问全流程"就理解不了后面所有攻击发生在哪一环；面试网络基础必答
> 实战场景：任何 Web 渗透测试的起点；讲项目时"我在 Kali 上搭了整套 LAMP 靶场"是最好的开场

---

## 一、原理概述：Web 是什么

**WWW（万维网）** 是构建在互联网之上、由互相链接的超文本文档组成的信息系统。1989 年蒂姆·伯纳斯-李在 CERN 发明了它，并定义了**三大关键技术**：

1. **URI**（统一资源定位符）：给互联网上每个资源一个唯一地址
2. **HTML**（超文本标记语言）：描述网页内容的格式
3. **HTTP**（超文本传输协议）：浏览器与服务器之间的通信标准

**必须分清的概念**（面试基础题）：**Web ≠ 互联网（Internet）**——互联网是承载万物的网络基础设施，Web 只是跑在它上面的众多服务之一（还有邮件、FTP、DNS 等）。Web 的规范不是哪家公司定的，而是 **W3C（万维网联盟）** 制定的，核心标准是 HTML、CSS、XML。

**几个关键角色**：
- **Web 服务器**：存放网页文档的计算机（Apache、Nginx、IIS）
- **Web 客户端**：读取网页的计算机，通过**浏览器**查看页面
- 浏览器的读取过程：发一个 HTTP 请求 → 服务器返回 HTML → 浏览器按 HTML 标签的"结构说明"渲染出页面

---

## 二、一次访问的全流程（面试核心，必须能画出来）

从输入网址回车到看到页面，完整链路是：**DNS 解析 → TCP 三次握手 → HTTP 请求 → 服务器处理 → HTTP 响应 → TCP 四次挥手 → 浏览器渲染**。

### 1. DNS 域名解析（把域名翻译成 IP）

| 步骤 | 动作 |
|---|---|
| ① | 浏览器向**本地 DNS 服务器**发送域名查询报文 |
| ② | 本地 DNS 把请求转发到**根 DNS 服务器** |
| ③ | 根服务器根据 `.com` 后缀返回 **com 顶级域名服务器** 的 IP |
| ④ | 本地 DNS 带着域名访问顶级域名服务器 |
| ⑤ | 顶级服务器根据 `imooc.com` 返回 **二级域名服务器** IP |
| ⑥ | 本地 DNS 访问二级域名服务器 |
| ⑦ | 二级服务器查询到域名对应的**真实 IP**（如 210.1.17.89）返回 |
| ⑧ | 本地 DNS 把最终 IP 透传给浏览器 |

**本质**：DNS 是一棵从根向叶子逐级查询的树，每一级只负责告诉"下一级去哪找"。这也是为什么 **hosts 文件能劫持域名**——本地解析优先于网络查询，实验里给 www.static.com 绑 127.0.0.1 就是手动"造假"了一条 DNS 记录，实现不注册域名也能访问站点。

### 2. TCP 三次握手（建立连接）

```
客户端 ──SYN (seq=J)──────────▶ 服务器   客户端进入 SYN_SENT
客户端 ◀──SYN+ACK (ack=J+1)─── 服务器   服务器进入 SYN_RCVD
客户端 ──ACK (ack=K+1)────────▶ 服务器   双方进入 ESTABLISHED
```

**为什么是三次**：双方都需要确认"我能发、你能收"。两次不够（服务器无法确认客户端的接收能力），四次浪费。

### 3. HTTP 请求与响应

请求报文 = **请求行 + 请求头 + 空行 + 请求体**；响应报文 = **状态行 + 响应头 + 空行 + 响应体**。Chrome 按 F12 → Network 能直接看到原始报文，这是之后所有抓包分析的基础。

**状态码速查**（面试必背）：

| 类别 | 代表状态码 | 含义 |
|---|---|---|
| 1xx | 100 Continue | 服务器已收到请求头，请继续 |
| 2xx | 200 OK | 请求成功 |
| 3xx | 301 Moved Permanently | 资源转移，请求被重定向 |
| 4xx | 404 Not Found | 资源不存在（客户端错误） |
| 5xx | 500 Internal Server Error | 服务器内部错误 |

> 安全视角：**401/403**（未认证/未授权）与 200 的差异、**302 跳转目标**，都是渗透测试判断"接口是否可越权、重定向去哪"的依据。

### 4. 服务器内部处理链路

请求打进服务器后：**网关层（Nginx）** 最先接收 → 路由转发到 Web 服务 → 业务逻辑（可能要查数据库）→ 返回结果。开发者的日常工作集中在"Web 业务服务"这一环（Spring/Django/ThinkPHP 等框架）。

### 5. TCP 四次挥手（断开连接）

```
客户端 ──FIN (seq=u)──────────▶ 服务器   ① 我要断开了
客户端 ◀──ACK (ack=u+1)──────── 服务器   ② 收到你的断开请求
客户端 ◀──FIN (seq=w)────────── 服务器   ③ 我也要断开了
客户端 ──ACK (ack=w+1)────────▶ 服务器   ④ 确认，连接关闭
```

**为什么是四次**：TCP 是全双工的，每一方向都要单独完成"我要关→对方确认"，所以比握手多一次。

### 6. 浏览器渲染（把代码变成页面）

服务器返回的 HTML/CSS/JS 要经过浏览器解析才能显示：
- **HTML 解析器**：标签 → **DOM 树**节点
- **CSS 解析器**：生成 CSS 规则树（选择器从右到左匹配）
- **JS 解析器**：解析脚本

**关键细节（面试加分）**：HTML 和 CSS 解析是**多线程并行**的，CSS 解析失败不影响 HTML；但 **JS 解析一旦异常会终止 HTML 解析**——这是历史上"把 `<script>` 放在 body 底部、用 defer/async"的根本原因。**安全视角：XSS 注入的 `<script>` 正是钻进了解析链里被执行。**

---

## 三、Web 前后端与 LAMP 架构

### 前端 vs 后端（分工理解）

| | 前端 | 后端 |
|---|---|---|
| 职责 | 用户可见的一切：布局、特效、交互 | 业务逻辑、数据存取、权限判断 |
| 技术 | HTML、CSS、JavaScript（进阶 Vue/React/Angular） | PHP、Java、Python、ASP.NET 等 + 数据库 |
| 典型例子 | 注册表单的页面长什么样 | 注册信息存进数据库、登录时比对密码 |

**一次注册请求的完整故事**（实验的核心代码流程）：前端表单收集用户名密码 → `register.php` 接 POST 请求 → `mysqli_query` 把数据 `INSERT INTO users` → 返回"Record inserted successfully"。登录则是 `SELECT ... WHERE username='$user' AND password='$pwd'`，查到就 `session_start()` 标记 `$_SESSION['loggedin']=true` 并跳转主页面。

> **安全视角（重点）**：实验里这些"能跑就行"的代码正是后面的漏洞温床——`INSERT INTO users ... '$user'` 是**字符串拼接 SQL = SQL 注入**；把用户输入直接 `echo` 回页面 = **XSS**；session 直接信任不换 ID = 会话固定。**能看懂这份安全代码，才懂后面为什么漏洞那么多。**

### 常见后端服务器分类（面试可背）

| 类型 | 代表 | 职责 |
|---|---|---|
| Web 服务器 | Apache、Nginx、IIS | 收 HTTP 请求、返回静态资源 |
| 应用服务器 | Tomcat、JBoss、WebLogic | 跑业务逻辑 |
| 数据库服务器 | MySQL、Oracle、SQL Server | 存储与查询数据 |
| 缓存服务器 | Redis、Memcached | 热点数据放内存加速 |
| 文件/消息队列/安全 | FTP、RabbitMQ/Kafka、防火墙/反代 | 各自专项 |

### LAMP 架构

**LAMP = Linux + Apache + MySQL + PHP**，最经典的开源 Web 架构：Linux 是操作系统底座，Apache 收 HTTP 请求，MySQL 存数据，PHP 写业务。开源、免费、稳定、可扩展，能满足大多数 Web 应用需求。Windows 下的等价替代：**XAMPP、PHPStudy、WampServer**。

---

## 四、网站构建实战（方法论）

### 1. LAMP 环境搭建与常用命令

```bash
# Apache 服务管理（Kali 自带；Ubuntu 需 apt install apache2）
sudo service apache2 start|stop|restart|status     # 或 systemctl 同款
sudo systemctl enable apache2                       # 开机自启
apache2 -v                                          # 查版本

# MySQL（Ubuntu 需 apt install mysql-server）
sudo service mysql start
sudo mysql -u root                                  # root 登录

# PHP 测试：/var/www/html 下建 test.php
# <?php echo "<h1>Hello World!</h1>"; ?>
# 浏览器访问 http://localhost/test.php 看到输出 = PHP 在 Apache 上跑通
```

**为什么这三样要装在一起**：页面要动态生成（PHP）→ 数据要存（MySQL）→ 对外要有人收请求（Apache），每个环节各管一摊，这就是"架构"。

### 2. 虚拟主机：一台服务器，多个站点

**原理**：同一台 Apache 按**域名**把请求分发到不同目录，如同多台"逻辑主机"共用一个物理服务器，目录之间互不干扰——这就是站点**隔离**的实现基础。

```apache
# /etc/apache2/sites-available/www-static-com.conf
<VirtualHost *:80>
    ServerName www.static.com
    DocumentRoot /var/www/static
    <Directory "/var/www/static">
        Options Indexes FollowSymLinks
        AllowOverride All
        Require all granted
    </Directory>
</VirtualHost>
```

```bash
sudo a2ensite www-static-com.conf   # 建立符号链接启用站点
sudo service apache2 restart         # 重启生效
sudo gedit /etc/hosts                # 客户端加一行：127.0.0.1 www.static.com
```

**部署三步**：写配置文件 → `a2ensite` 启用 → hosts 指向 IP。实验里 www.static.com / www.dynamic.com / www.blog.com 三个站点就是同一台机器按此流程依次部署的。

### 3. 静态网站 vs 动态网站（必考对比）

| | 静态网站 | 动态网站 |
|---|---|---|
| 页面内容 | 写死的 HTML（最多带点 JS 特效） | 按请求实时生成（查数据库） |
| 技术 | HTML/CSS/JS | 后端语言 + 数据库 |
| 特点 | 快、简单、无法个性化 | 能注册登录、千人千面 |
| 本实验例子 | `index.html` 用 `document.write()` 输出标题 | 注册/登录/查库全套流程 |

### 4. 动态网站的数据库设计（实验代码提炼）

```sql
CREATE DATABASE loginsystem;
USE loginsystem;
CREATE TABLE users (
    id INT NOT NULL PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) NOT NULL UNIQUE,
    password VARCHAR(50) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
CREATE USER 'user'@'%' IDENTIFIED BY 'password';      -- 最小权限：应用账号≠root
GRANT ALL PRIVILEGES ON loginsystem.* TO 'user'@'%';
FLUSH PRIVILEGES;
```

```php
// config.php：统一数据库连接（所有页面 require 它）
$link = mysqli_connect('localhost', 'user', 'password', 'loginsystem');
```

**流程串起来**：建库建表 → config.php 连接 → register.php 注册写入 → login.php 查库验证 + session → main.php 主页面。**最小权限原则从这里就该养成**：给应用一个独立账号而不是用 root 连库——这正是后面 SQL 注入防御"Web 账号不连 root"的先例。

### 5. CMS 快速部署（WordPress 博客）

下载模板 → `tar -zxvf` 解压 → 复制到站点目录 → 建库建用户赋权 → 配虚拟主机 + hosts → 浏览器图形化安装向导 → 后台 `/wp-login.php`。

> 强制搭建 vs 一键安装的意义：亲手走一遍 LAMP 才能在出问题时知道是哪一层（服务/语法/权限/配置）出问题，这也是渗透测试里排查靶场的通用思路。

---

## 五、安全视角复盘（这份基础里埋着哪些雷）

| 代码/配置 | 问题 | 对应漏洞 |
|---|---|---|
| `"SELECT ... WHERE username='$user'"` 字符串拼 SQL | 用户输入直接进 SQL 语句 | SQL 注入 |
| 用户输入直接 `echo` 输出到页面 | 输入被浏览器当代码解析 | XSS |
| `$_SESSION['loggedin']=true` 后不换 session ID | 会话 ID 可被固定/预测 | 会话固定、弱会话 |
| 验证码/权限只做前端判断 | 后端没有真正校验 | 逻辑漏洞（CAPTCHA 绕过、越权） |
| `include($_GET['page'])` 动态包含 | 参数决定加载哪个文件 | 文件包含 |
| 上传目录在 Web 根目录内且可写 | 可执行文件被直接访问 | 文件上传 |

**一句话**：把"用户可控的任何东西"（输入、参数、文件名、URL）直接交给"执行类操作"（SQL、HTML 输出、include、执行命令），就产生了 Web 安全里绝大部分漏洞。**面试时把这份"地基"和攻击对应起来讲，比单背漏洞点强得多。**

---

## 六、面试速答卡

- **浏览器输入网址到显示页面经历了什么**：DNS 解析 → TCP 三次握手 → HTTP 请求 → 服务器处理 → HTTP 响应 → 四次挥手 → 浏览器渲染
- **DNS 解析流程**：本地 DNS → 根 → 顶级域（.com）→ 二级域 → 真实 IP，逐级向下查询
- **为什么三次握手**：双方各自确认"你发我能收、我发你能收"，两次不够四次浪费
- **为什么四次挥手**：TCP 全双工，每个方向单独完成关闭，各自要一次 FIN+ACK
- **静态 vs 动态网站**：内容写死 vs 按请求实时生成（查库），动态才能有注册登录
- **LAMP 是什么**：Linux + Apache + MySQL + PHP；Windows 用 XAMPP/PHPStudy 替代
- **虚拟主机是什么**：一台服务器按域名分发请求到不同目录，实现多站点与隔离
- **hosts 文件为什么能劫持域名**：本地解析优先于 DNS 查询，实验里手动把域名指向 127.0.0.1
- **前端安全的基本原则**：前端所有算法/校验对用户透明，安全边界必须放在后端
- **这份基础对应哪些漏洞**：SQL 拼接→SQLi、原样输出→XSS、动态包含→文件包含、不可信上传→WebShell