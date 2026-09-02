# Linux 服务：DHCP 地址分配

> 来源：课程实验（Linux操作系统，CentOS 8.3，2025-2026 第一学期），老师版PDF为底料
> 定位：局域网 IP 自动分配基础设施，运维中一台 DHCP 服务替代几百台机器的手工配 IP；安全角度上 DHCP 是内网攻击的经典入口（DHCP 饿死攻击、伪造 DHCP 服务器劫持网关/DNS），面试必问 DORA 四步流程。

---

## 一、概念与原理

**DHCP（Dynamic Host Configuration Protocol，动态主机配置协议）**：自动管理局域网内主机的 IP 地址、子网掩码、网关、DNS 等参数，提升 IP 利用率、降低人工运维成本。

**端口**：服务器 67（UDP），客户端 68（UDP）。

**工作过程：DORA 四步（面试必背）**：
1. **D - Discover（IP 租用请求）**：客户端启动时 IP 为 0.0.0.0，向本地子网**广播** DHCP Discover 包（目标 UDP 67）；
2. **O - Offer（IP 租用提供）**：子网内每台 DHCP 服务器检查空闲地址，若有则以 DHCP Offer 包响应（发到 UDP 68）；
3. **R - Request（IP 租用选择）**：客户端**通常选择第一个** Offer，广播 DHCP Request 包回应；未被选中的服务器把保留地址放回地址池；
4. **A - Acknowledge（IP 租用确认）**：服务器收到 Request 后广播 DHCP Acknowledge 包，提供客户端要求的其他信息，租约成立。

**分配的两种 IP 类型**：
- **动态 IP**：每次租约可能不同，适合员工机等大量终端，IP 有限时最大化利用率（离线即收回）；
- **静态 IP（保留地址）**：记录特定 MAC 与 IP 的绑定，适合服务器等需要固定地址的设备。

**服务器工作细化流程**：客户端广播 → 服务器查主配置 dhcpd.conf → 先按 MAC 查是否有固定 IP 绑定，有则发固定 IP，无则从地址池取 → 客户端确认使用 → 服务器把租用信息写入**租用数据库文件**。

**关键文件**：主配置文件 `/etc/dhcp/dhcpd.conf`；租用数据库 `/var/lib/dhcpd/dhcpd.leases`（安装后为空文件，运行后记录每次租约）。

---

## 二、环境准备与安装

```bash
sudo dnf install dhcp-server -y
sudo rpm -qa | grep dhcp-server
sudo cp /usr/share/doc/dhcp-server/dhcpd.conf.example /etc/dhcp/dhcpd.conf   # 复制样例为正式配置
```

**搭建三步流程**：编辑主配置文件指定 IP 作用域 → 建立租用数据库文件（自动生成）→ 重启 dhcpd 生效。

**实验环境**：为虚拟机添加一张新网卡设为 Host Only（VMnet1），克隆出两台客户端虚拟机；服务器与客户端都连同一 Host Only 网络（本次实验网段 192.168.3.0/24）。

---

## 三、配置详解

### 3.1 配置文件语法三要素
| 要素 | 作用 | 示例 |
|---|---|---|
| parameters 参数 | 设置服务器/客户端动作 | `default-lease-time 600` |
| declarations 声明 | 指定作用域、地址池 | `subnet ... { }`、`range ...` |
| options 选项 | 配置客户端可选参数（都以 option 开头） | `option routers ...` |

常用项：
```
subnet 192.168.3.0 netmask 255.255.255.0 { ... }   # 定义作用域
range dynamic-bootp 192.168.3.100 192.168.3.200    # 动态地址池
option routers 192.168.3.254                       # 客户端默认网关
option subnet-mask 255.255.255.0                   # 客户端子网掩码
option domain-name-servers 192.168.3.1             # 客户端 DNS
option domain-name "localhost"                     # 域名后缀
option broadcast-address 192.168.3.255             # 广播地址
default-lease-time 600                             # 默认租期（秒）
max-lease-time 7200                                # 最大租期（秒）
```

**固定 IP 绑定（保留地址）**：
```
host computer1 {                    # host 声明，通常搭配 subnet 使用
    hardware ethernet 3a:b5:cd:32:65:12;   # 网卡类型+MAC
    fixed-address 192.168.3.105;           # 绑定的固定 IP
}
```

### 3.2 完整实例（网段 192.168.3.0/24）
需求：服务器地址 192.168.3.4/24，网关 192.168.3.1，客户端地址池 31~200（挖掉 105、107 两段），其中 192.168.3.105 固定给 Client2（MAC 00:0c:29:08:5b:ca）。

```
ddns-update-style none;             # 不做 DDNS 动态更新
log-facility local7;                # 日志设施
subnet 192.168.3.0 netmask 255.255.255.0 {
  range 192.168.3.31 192.168.3.104;     # 地址池前段
  range 192.168.3.106 192.168.3.106;    # 挖掉 .105 后的独立段（注意 range 写法）
  range 192.168.3.108 192.168.3.200;    # 挖掉 .107 后的独立段
  option domain-name-servers 192.168.3.4;
  option domain-name "localhost";
  option routers 192.168.3.1;
  option subnet-mask 255.255.255.0;
  option broadcast-address 192.168.3.255;
  default-lease-time 600;
  max-lease-time 7200;
}
host Client2 {
  hardware ethernet 00:0c:29:08:5b:ca;  # MAC 小写，按自己虚拟机网卡改
  fixed-address 192.168.3.105;
}
```
⚠️ 网段/IP 必须按自己虚拟机（Host Only 网段）对应修改；配置是严格语法（分号、大括号都不能少）。

### 3.3 启动与管理

```bash
sudo systemctl start dhcpd
sudo systemctl enable dhcpd
sudo systemctl status dhcpd
sudo firewall-cmd --permanent --add-service=dhcp && sudo firewall-cmd --reload
sudo setenforce 0                     # 或 Permissive
```

**启动失败常见原因（背下来）**：
1. 配置文件语法错误（如少个分号），或声明的子网与掩码不匹配；
2. 主机 IP 与声明的子网不在同一网段；
3. 主机根本没配置 IP 地址。

排错：`sudo dhcpd`（前台运行直接报错）或 `sudo journalctl -xe`。

---

## 四、客户端验证

```bash
sudo dhclient -r       # 释放当前 IP
sudo dhclient          # 重新获取 IP
ip a                   # 查看是否拿到池内 IP（如 192.168.3.x）
```
- Client1（普通客户端）应拿到 31~200 池内的**随机动态 IP**；
- Client2（MAC 绑定）每次都应拿到 192.168.3.105（**静态 IP**）。
- 服务器端核验：`sudo cat /var/lib/dhcpd/dhcpd.leases`（租约记录）、`sudo tail -f /var/log/messages`（分配日志）。

---

## 五、常见问题与排查（老师PDF里的坑）

1. **客户端拿到不符合预期的 IP**（如 192.168.79.123）：**VMware 的 VMnet1 自带 DHCP 服务**与你自己搭的 DHCP 冲突，谁先抢到算谁的 → 在虚拟网络编辑器里关闭 VMnet1 的 DHCP 服务。
2. **实验完成后**：最后关闭自己搭的 DHCP 服务器，恢复用虚拟化软件自带的 DHCP 分配 IP，否则后续可能无法上网。
3. **dhcpd 启动即失败**：按上面三个常见原因逐项检查（语法/同网段/主机有 IP），`sudo dhcpd` 前台运行看直接报错最快。
4. **客户端释放/获取**：先 `dhclient -r` 再 `dhclient`，别只执行一个。

---

## 六、安全加固要点

- **DHCP 饿死攻击（DHCP Starvation）**：攻击者伪造海量 MAC 发送 Discover 请求，耗尽地址池，导致合法客户端无法获取 IP（DoS）；防御：交换机上启用 **DHCP Snooping**（只信任接 DHCP 服务器的端口）并限制端口 MAC 数量，配合地址池监控告警。
- **伪造 DHCP 服务器（Rogue DHCP）**：内网插入一台恶意 DHCP，提供恶意网关/DNS，把流量劫持到攻击者机器（中间人）——这是 Wi-Fi 钓鱼的经典手法；防御：DHCP Snooping + 802.1X 接入认证，客户端侧核对分配的网关与 DNS。
- **静态绑定关键设备**：服务器、网络设备用 host+MAC 绑定，防止地址冲突与劫持。
- **日志审计**：定期查 dhcpd.leases 与 /var/log/messages，发现陌生 MAC 大量租约要警惕。
- 只在可信网络段部署 DHCP；防火墙限制 UDP 67/68 只对目标网段开放。

---

## 七、面试速答卡

- **DHCP 四步流程**：Discover（广播找服务器）→ Offer（服务器提供地址）→ Request（客户端确认选择）→ Acknowledge（服务器确认，租约成立）。
- **DHCP 端口**：服务器 UDP 67，客户端 UDP 68。
- **动态与静态 IP 的区别**：动态从地址池随机分配、租约到期回收；静态通过 MAC 绑定固定地址，适合服务器。
- **怎么给固定 IP**：`host 主机名 { hardware ethernet MAC; fixed-address IP; }`。
- **DHCP 饿死攻击原理**：海量伪造 MAC 请求耗尽地址池，造成合法用户无法获取 IP——用 DHCP Snooping 防御。
- **租用数据库文件**：/var/lib/dhcpd/dhcpd.leases，记录每次 IP 租用情况。