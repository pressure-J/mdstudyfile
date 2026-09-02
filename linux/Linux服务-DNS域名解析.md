# Linux 服务：DNS 域名解析

> 来源：课程实验（Linux操作系统，CentOS 8.3，2025-2026 第一学期），老师版PDF为底料
> 定位：网络访问的第一道关口，"域名↔IP 转换"的基础设施。运维中任何 Web/邮件服务都依赖它；安全角度上 DNS 是内网侦察的重要信息来源（区域传送 AXFR 泄露内网主机名）、DDoS 反射放大攻击的放大器（开放递归），面试高频考点是资源记录类型与解析流程。

---

## 一、概念与原理

**DNS（Domain Name System）**：把"方便人记的域名"翻译成"机器可用的 IP 地址"，可理解为一张巨大的分布式电话本。它是一个**分布式数据库**，命名系统呈倒置树的层次结构，称为**域名空间**（树最大深度 127 层，节点最长 63 字符）。完整域名 FQDN 从节点到树根反向书写、用 `.` 分隔，如 `www.example.com.`（末尾的根域名平时省略）。

**域名层级**：主机名.次级域名(SLD).顶级域名(TLD).根域名 —— 即 `host.sld.tld.root`。

**DNS 服务器分类**：
1. **主 DNS 服务器**：维护所辖域的权威信息（正向/反向区域文件）；
2. **辅助 DNS 服务器**：从主服务器同步区域副本（区域传输），分担负载、提供冗余；
3. **转发 DNS 服务器**：把解析请求转发给上游（如公共 DNS），目前绝大多数 DNS 都是转发型；
4. **唯缓存 DNS 服务器**：不做区域维护，只负责查询并缓存结果，加快内网解析速度。

**正反向解析**：正向 = 域名→IP；反向 = IP→域名（PTR 记录），反向解析常用于服务器身份验证、反垃圾邮件。

**端口**：53（UDP 查询为主，TCP 用于区域传输和大响应）。

**常见资源记录（面试必背）**：
| 记录 | 全称 | 作用 |
|---|---|---|
| SOA | Start of Authority | 区域的起始授权记录，定义全局参数，一个区域只能有一条 |
| NS | Name Server | 指定该区域的权威服务器 |
| A | Address | 域名→IPv4 地址 |
| PTR | Pointer | IP 地址→域名（反向解析） |
| CNAME | Canonical Name | 域名别名（指向另一域名，设置后不能再设 A/MX） |
| MX | Mail eXchange | 指定邮件交换服务器 |

**解析工作流程（递归+迭代）**：客户端 → 本地 DNS 服务器；本地服务器依次查根服务器（.）→ 顶级域（.com）→ 次级域（example.com），最终拿到主机的 A 记录返回客户端。根服务器地址内置在 DNS 服务器中（/var/named/named.ca），全球共 13 组。TTL（Time To Live）表示缓存时间，TTL 内免重复查询。

**测试工具**：`dig`（完整查询过程，+short 简化、+trace 显示分级查询、-x 反查）、`host`（简化版）、`nslookup`（交互式）、`whois`（域名注册信息）。客户端 DNS 配置在 `/etc/resolv.conf`（nameserver 行）。

---

## 二、环境准备与安装

```bash
sudo dnf install bind bind-chroot -y    # BIND：最流行的开源 DNS 软件
sudo rpm -qa | grep bind && sudo rpm -qa | grep bind-chroot
sudo systemctl start named              # 服务名是 named
sudo systemctl enable named
sudo firewall-cmd --permanent --add-service=dns && sudo firewall-cmd --reload
sudo setenforce 0                       # 或 Permissive
```

**配置文件体系**：
- 主配置文件 `/etc/named.conf`（options 全局参数 + zone 区域声明 + include 引入区域文件）
- 区域配置文件 `/etc/named.rfc1912.zones`（localhost 等内置区域；可复制为自定义区域文件）
- 区域声明文件目录 `/var/named/`：`named.ca`（根区域）、`named.localhost`（正向样本）、`named.loopback`（反向样本）、`named.empty`

**配置流程**：按需配置 named.conf → 建立区域配置文件与正/反向区域声明文件 → 重启 named 使生效。

**named.conf 关键 options**：`listen-on port 53`（监听地址）、`directory "/var/named"`（区域文件路径）、`allow-query`（允许查询的客户端）、`dnssec-validation`。

---

## 三、配置详解（主 DNS 实例：long90.cn 域）

需求：DNS 服务器 dns.long90.cn = 192.168.137.4，为下列主机提供正反向解析，且 www 别名为 web：
dns→.4、mail→.5、slave→.6、www→.7、ftp→.8。

### 3.1 修改主配置文件 `/etc/named.conf`
```
options {
    listen-on port 53 { any; };     // 由 127.0.0.1 改为监听所有接口
    allow-query     { any; };       // 允许所有客户端查询
    dnssec-validation no;           // 实验环境关闭 DNSSEC 校验
};
/* 删除 include "/etc/named.rfc1912.zones"; 改为：*/
include "/etc/named.zones";
```

### 3.2 编辑区域配置文件 `/etc/named.zones`
```
sudo cp -p /etc/named.rfc1912.zones /etc/named.zones   # -p 保留属性和时间
zone "long90.cn" IN {
        type master;
        file "long90.cn.zone";       # 正向区域声明文件
        allow-update { none; };      # 禁止动态更新
};
zone "137.168.192.in-addr.arpa" IN { # 反向区域（网段倒写）
        type master;
        file "1.137.168.192.zone";   # 反向区域声明文件
        allow-update { none; };
};
```

### 3.3 正向区域声明文件 `/var/named/long90.cn.zone`
```bash
su - root && cd /var/named
cp -p named.localhost long90.cn.zone
```
```
$TTL 1D
@       IN SOA  @ root.long90.cn. (
                                0       ; serial 序列号
                                1D      ; refresh
                                1H      ; retry
                                1W      ; expire
                                3H )    ; minimum
@               IN      NS              dns.long90.cn.
@               IN      MX      10      mail.long90.cn.
dns             IN      A               192.168.137.4
mail            IN      A               192.168.137.5
slave           IN      A               192.168.137.6
www             IN      A               192.168.137.7
ftp             IN      A               192.168.137.8
web             IN      CNAME           www.long90.cn.
```
⚠️ 记录行必须**顶格**（不能有前导空格）；域名都要带末尾 `.`（如 `dns.long90.cn.`）。

### 3.4 反向区域声明文件 `/var/named/1.137.168.192.zone`
```bash
cp -p named.loopback 1.137.168.192.zone
```
SOA/NS 同上，主机记录换成 PTR：
```
4   IN  PTR  dns.long90.cn.
5   IN  PTR  mail.long90.cn.
6   IN  PTR  slave.long90.cn.
7   IN  PTR  www.long90.cn.
8   IN  PTR  ftp.long90.cn.
```

### 3.5 辅助 DNS（区域冗余）
- 主服务器 zone 段加 `allow-update { 192.168.137.5; };`（或 allow-transfer 指定允许区域传输的服务器）；
- 辅助服务器（192.168.137.5）named.conf 中：
```
zone "long90.cn" IN {
       type   slave;                        // 辅助服务器
       file   "slaves/long90.cn.zone";      // 同步到 /var/named/slaves/
       masters { 192.168.137.4; };          // 主 DNS 地址
};
```
同步后 `ls -al /var/named/slaves/` 应看到两个 zone 文件；同步失败时查防火墙（必要时 stop firewalld 排错）并把文件属组改为 named（`chgrp named ...`）。

### 3.6 转发与唯缓存（选作）
- **完全转发**：options 中 `forwarders { 223.5.5.5; 8.8.8.8; };` + `forward only;`（全部转发，禁止本地解析）；
- **条件转发**：`zone "long90.cn" { type forward; forwarders { 192.168.137.4; }; };`（只转发指定域，其余照常）；
- **唯缓存**：`recursion yes;` + `forwarders {...};` + `forward first;`（优先转发，缓存结果加速后续查询）。

---

## 四、客户端验证

```bash
sudo vim /etc/resolv.conf     # nameserver 192.168.137.4
nslookup
> server 192.168.137.4        # 临时指定 DNS 服务器（NetworkManager 重置 resolv.conf 时用这招）
> www.long90.cn               # 正向：Name: www.long90.cn / Address: 192.168.137.7
> 192.168.137.6               # 反向：name = slave.long90.cn.
```
非交互式：`nslookup www.long90.cn 192.168.137.4`；`dig www.long90.cn @192.168.137.4`。

---

## 五、常见问题与排查（老师PDF里的坑）

1. **resolv.conf 改了又被重置**：NetworkManager 会自动改写 → 用 `nslookup` 交互模式里 `server IP` 临时指定，或配置静态 DNS。
2. **辅助服务器同步不过来**：查主服务器 allow-update/allow-transfer 是否放行、防火墙是否拦截（可临时 `systemctl stop firewalld` 验证）、同步文件属组是否为 named。
3. **解析失败先查配置语法**：`sudo systemctl status named` / `journalctl -xe`，常见错误：记录行有前导空格、域名漏写末尾点、反解网段写反。
4. **本机测 localhost 丢包/失败**：listen-on 与 allow-query 改 any 后要重启 named 才生效。

---

## 六、安全加固要点

- **限制 allow-query**：只允许内网网段查询，避免变成公网"免费递归解析器"——开放递归会被用来做 **DNS 反射放大攻击**（伪造源 IP 查大记录，放大倍数可达几十上百倍）。
- **限定区域传输**：allow-transfer 只写给辅助服务器，防止攻击者通过 **AXFR 区域传送**把整个内网主机名/域名清单拖走（内网侦察利器）。
- **关闭不必要功能**：内网私有域 `dnssec-validation no` 可接受；对外服务建议启用 DNSSEC 防缓存投毒；`allow-update { none; }` 防止动态更新被滥用。
- **主备分离**：主 DNS 与辅助 DNS 分开部署，单点故障时仍可解析。
- **日志监控**：named 日志记录查询来源，异常大量查询（放大攻击特征）及时封禁来源。
- hosts 文件管控：`/etc/hosts` 可先于 DNS 被查询，注意防篡改（恶意改 hosts 是经典钓鱼手法）。

---

## 七、面试速答卡

- **DNS 作用**：把域名解析成 IP 地址（正向），也能反查（反向 PTR）。
- **六种资源记录**：SOA（区域起始）、NS（权威服务器）、A（域名→IP）、PTR（IP→域名）、CNAME（别名）、MX（邮件服务器）。
- **解析流程**：客户端问本地 DNS → 本地 DNS 迭代查询根→顶级域→权威域，最终拿到 A 记录并缓存（TTL 控制缓存时长）。
- **主从同步机制**：辅助服务器通过区域传输（AXFR/IXFR）从主服务器拉取区域副本，主服务器上 allow-transfer 控制谁可以拉。
- **DNS 放大攻击原理**：攻击者伪造受害者 IP 向开放递归的 DNS 发送小查询，DNS 返回大响应打到受害者，放大流量。
- **BIND 服务名与配置文件**：服务 named，主配置 /etc/named.conf，区域文件在 /var/named/。