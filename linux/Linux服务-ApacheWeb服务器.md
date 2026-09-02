# Linux 服务：Apache Web 服务器

> 来源：课程实验（Linux操作系统，CentOS 8.3，2025-2026 第一学期，含 LAMP 与 WordPress 部署），老师版PDF为底料
> 定位：全球使用最广的开源 Web 服务器，运维中承载企业官网/业务系统，常与 PHP+MySQL 组成 LAMP 架构；安全角度上 Web 服务器是攻击面最大的入口，目录权限、虚拟主机隔离、上传漏洞、WebShell 都是笔试面试高频点。

---

## 一、概念与原理

**WWW 与 HTTP**：WWW 采用客户/服务器结构，浏览器（Chrome/Firefox 等）是 HTTP 客户端，Apache/IIS 是 HTTP 服务器软件。HTTP 默认端口 **80**（默认可省略），改其他端口（如 8080）必须写明：`http://www.smile.com:8080/`。

**Apache HTTP Server**：Apache 软件基金会维护的开源网页服务器，牢靠、可信，曾占据绝大多数热门站点。CentOS/RHEL 的服务名是 **httpd**，Ubuntu/Debian 是 apache2。

**LAMP 架构**：Linux + Apache + MySQL/MariaDB + PHP，Web 动态网站（如 WordPress 博客）的经典组合。Apache 负责接收 HTTP 请求，PHP 处理动态逻辑，MariaDB 存数据。

**关键文件位置表**：
| 内容 | 位置 |
|---|---|
| 服务目录 | /etc/httpd |
| 主配置文件 | /etc/httpd/conf/httpd.conf |
| 网站数据目录 | /var/www/html |
| 访问日志 | /var/log/httpd/access_log |
| 错误日志 | /var/log/httpd/error_log |

**主配置常用参数**：ServerRoot（服务目录）、ServerAdmin（管理员邮箱）、User/Group（运行服务用户/组）、ServerName（服务器域名）、**DocumentRoot**（文档根目录，默认 /var/www/html）、**Directory**（目录权限）、**Listen**（监听 IP:端口）、**DirectoryIndex**（默认首页，默认 index.html）、ErrorLog/CustomLog（错误/访问日志）、Timeout（超时，默认 300s）。

---

## 二、环境准备与安装

```bash
sudo dnf install httpd -y
sudo rpm -qa | grep httpd
sudo systemctl start httpd && sudo systemctl enable httpd
sudo firewall-cmd --permanent --add-service=http && sudo firewall-cmd --reload
sudo setenforce 0                # 或 Permissive
```
验证：浏览器访问虚拟机 IP（本机可 http://127.0.0.1），看到 Apache 测试页即成功。⚠️ **setenforce 是临时的，重启后失效**；想长期生效就改 `/etc/sysconfig/selinux`（SELINUX=Permissive 或 Enforcing）。

默认首页替换（立即生效）：
```bash
sudo sh -c 'echo "Welcome To MyWebSite" > /var/www/html/index.html'
```

---

## 三、配置详解（六大实例）

### 3.1 实例1：设置文档根目录和首页
```bash
sudo mkdir /home/www
sudo sh -c 'echo "The Web'"'"'s DocumentRoot Test" > /home/www/myweb.html'
sudo cp /etc/httpd/conf/httpd.conf /etc/httpd/conf/httpd.conf.bak
```
改 httpd.conf 三处：`DocumentRoot "/home/www"`、`<Directory "/home/www">`、`DirectoryIndex index.html myweb.html`（注意实例里顺序是 `index.html myweb.html`）。重启并浏览器访问测试。

### 3.2 实例2：用户个人主页（/~username）
URL 格式 `http://域名/~用户名`，用户名必须是 Linux 合法用户。
```bash
sudo useradd long && sudo passwd long
sudo chmod 705 /home/long            # 家目录给其他用户读+执行权限
sudo mkdir /home/long/public_html
sudo sh -c 'echo "Welcome To Long WebSite" > /home/long/public_html/index.html'
```
编辑 `/etc/httpd/conf.d/userdir.conf`：把 `UserDir disabled` 注释掉（#），去掉 `UserDir public_html` 的注释（指定个人主页目录名）。访问 `http://127.0.0.1/~long`。

### 3.3 实例3：虚拟目录（Alias 别名）
虚拟目录 = 位于主目录之外、但看起来像主目录下子目录的目录，通过别名访问。
```bash
sudo mkdir -p /virdir
sudo sh -c 'echo "This Is Virtual Directory Sample" > /virdir/index.html'
sudo chmod 705 /virdir -R
```
httpd.conf 添加：
```
Alias /test "/virdir"
<Directory "/virdir">
   AllowOverride None
   Require all granted
</Directory>
```
访问 `http://127.0.0.1/test`。

### 3.4 实例4：基于 IP 的虚拟主机（多个 IP 多个站）
服务器绑两个 IP（192.168.137.4 与 .5，图形界面网络设置里加第二个 IP），建目录 /var/www/ip1、/var/www/ip2 及首页，编辑 `/etc/httpd/conf.d/vhost.conf`：
```
<Virtualhost 192.168.137.4>
    DocumentRoot /var/www/ip1
</Virtualhost>
<Virtualhost 192.168.137.5>
    DocumentRoot /var/www/ip2
</Virtualhost>
```
并在 httpd.conf 中为两个目录加 `<Directory>` 权限块（AllowOverride None + Require all granted）。访问不同 IP 看到不同站点。

### 3.5 实例5：基于域名的虚拟主机（一个 IP 多个站，主流方式）
```bash
sudo vim /etc/hosts     # 加：192.168.137.4 www.mywebsite1.com / 192.168.137.4 www.mywebsite2.com
sudo mkdir /var/www/www1 /var/www/www2   # 各自写不同首页
```
vhost.conf 中 **ServerName** 区分：
```
<Virtualhost 192.168.137.4>
    DocumentRoot /var/www/www1
    ServerName www.mywebsite1.com
</Virtualhost>
<Virtualhost 192.168.137.4>
    DocumentRoot /var/www/www2
    ServerName www.mywebsite2.com
</Virtualhost>
```
浏览器分别访问两个域名，看到不同页面。生产环境用 DNS 解析，测试用 hosts 文件。

### 3.6 实例6：基于端口的虚拟主机
```bash
sudo mkdir /var/www/8088 /var/www/8089   # 各写首页
```
httpd.conf 加 `Listen 8088`、`Listen 8089`；vhost.conf 用 `<Virtualhost 192.168.137.4:8088>` 区分。**坑**：防火墙默认只放行 80，访问 `http://IP:8088` 会失败 → 手动放行端口：
```bash
sudo firewall-cmd --permanent --zone=public --add-port=8088/tcp
sudo firewall-cmd --permanent --zone=public --add-port=8089/tcp
sudo firewall-cmd --reload
```

### 3.7 安装 PHP 与 MariaDB（LAMP 完整体）
```bash
sudo dnf install php                  # PHP 7.2
php -version
sudo vim /var/www/html/info.php       # <?php phpinfo(); ?>
# 注意：先按实例1把 DocumentRoot 改回 /var/www/html 才能访问
sudo dnf install php-mysqlnd mariadb-server mariadb
sudo systemctl start mariadb && sudo systemctl enable mariadb
sudo mysql_secure_installation         # 设 root 密码、删除匿名用户、移除 test 库
sudo mysql -u root -p
```
```sql
CREATE DATABASE webdb;
CREATE USER 'webuser'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON webdb.* TO 'webuser'@'localhost';
FLUSH PRIVILEGES;
```
建 testdb.php 用 mysqli 连接测试（"Connected successfully"）。**WordPress 部署**：下载 wordpress-5.0.18-zh_CN.tar.gz 解压到 /var/www/html、`chmod 777 wordpress`、建 wordpress 库与 wpuser 用户，浏览器访问 `http://IP/wordpress` 图形化安装，后台 `wp-login.php`。

---

## 四、客户端验证与排错

- 浏览器/curl 访问 `http://IP`、`http://IP:8088`、`http://域名` 看各自首页；
- **服务起不来第一反应**：`sudo systemctl status httpd` + `sudo journalctl -xe`，例：`Invalid command 'this'` → httpd.conf 第 1 行附近有写错的指令，vim 里 `:set nu` 看行号改掉即可；
- 访问不了：先查 `firewall-cmd --list-all`（80/8088/8089 是否放行）和 SELinux。

---

## 五、安全加固要点

- **目录权限最小化**：只给需要 Web 服务的目录 `Require all granted`（如 /var/www），其他目录默认拒绝；主目录下**别开写权限**（防上传 WebShell）。
- **用户隔离**：Apache 以低权限用户（apache）运行；虚拟主机之间互不可读写；个人主页权限 705（别人只能进 public_html）。
- **中间件加固**：隐藏版本号（ServerTokens Prod/ServerSignature Off）；删除默认测试页；限制 HTTP 方法；上传目录禁止执行 PHP（php_admin_flag engine off 或禁用 CGI）。
- **LAMP 安全**：数据库账号最小权限（webuser 只授权 webdb.*，不用 root 连库）；MariaDB root 禁止远程登录（mysql_secure_installation 时选禁远程）；wpx 类 CMS 及时更新、别用弱口令 admin/123456，禁用危险插件。
- **日志与 WAF**：access_log/error_log 常查异常扫描与注入请求；有条件上 ModSecurity/WAF。
- **SELinux 与防火墙**：生产环境按布尔值精确放行（httpd_* ），端口只开需要的；`setenforce 0` 只用于实验。

---

## 六、面试速答卡

- **Apache 默认端口与配置文件**：80；CentOS 主配置 /etc/httpd/conf/httpd.conf，网站根目录 /var/www/html，首页 DirectoryIndex index.html。
- **DocumentRoot 与 Directory 关系**：DocumentRoot 定义网站数据路径，Directory 定义该路径的访问权限（AllowOverride、Require all granted）。
- **三种虚拟主机**：基于 IP（多 IP 多站）、基于域名（同 IP 靠 ServerName 区分，主流）、基于端口（Listen 不同端口 + Virtualhost IP:端口）。
- **用户个人主页**：/~用户名，靠 /etc/httpd/conf.d/userdir.conf 开启，家目录 public_html 放网页。
- **LAMP 是什么**：Linux+Apache+MySQL/MariaDB+PHP 的 Web 架构组合。
- **服务起不来怎么排查**：systemctl status httpd + journalctl -xe，多半是配置文件语法错误或防火墙未放行端口。