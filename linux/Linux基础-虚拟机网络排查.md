# Linux 基础：虚拟机网络排查

> 来源：实战排障记录（Kali Linux 2025 VMware 虚拟机断网修复，2026-08）
> 定位：虚拟化环境（VMware/VM 等）里"VM 没网"是最常见的环境问题，占了排障求助的大头。掌握从外到内的分层排查思路，5 分钟内定位断在哪一层；同时这套方法也是面试必考的"网络故障排查"标准答案。

---

## 一、排查思路：先分层，再动手

VM 没网 ≠ 一定是 VM 的问题。**网络是一层层叠起来的**，任何一层断了都表现为"没网"。正确姿势是从外到内逐层排除，而不是上来就乱敲命令。

**三层模型（从外到内）**：

| 层次 | 对应实体 | 核心问题 | 一句话口诀 |
|---|---|---|---|
| 第 1 层 | 宿主机物理网络 | 宿主机自己能不能上网 | 物理网线/路由 |
| 第 2 层 | VMware 虚拟网络层 | NAT/DHCP 服务在跑吗？VMnet8 正常吗 | 虚拟交换机 |
| 第 3 层 | VM 系统内部 | 网卡 UP 吗？有 IP 吗？路由/DNS 对吗 | 系统配置 |

**快速定位技巧**：先看宿主机是否正常（1 秒钟），再查 VMware 服务（1 秒钟），最后进 VM 里看 `ip a`（几秒钟）。哪一层找到异常，就在哪一层解决，不要越层瞎折腾。

> 本次案例：前两层全部正常，问题在第三层 —— Kali 网卡 `NO-CARRIER`（虚拟网线没插）。而"网线没插"的开关，在 VMware 设置里（第 2 层的配置项），不在 Kali 内部。这就是分层排查的价值：**知道去哪找，不乱试**。

---

## 二、第 1 层：宿主机物理网络排查（Windows）

```powershell
ipconfig          # 看物理网卡（WLAN/以太网）有没有 IPv4 地址
ping 223.5.5.5    # 能不能上外网（阿里公共 DNS，不依赖域名解析）
```

- 有 IP 且能 ping 通公网 → 宿主机正常，往下查
- 没 IP / ping 不通 → 物理网络问题（WiFi 断开、路由器故障），与 VM 无关

**坑**：`ipconfig` 里 VMware 的虚拟网卡（VMnet1/VMnet8）也会列出来，别把它们当成物理网卡。物理网卡是 WLAN（无线）或以太网（有线）。

---

## 三、第 2 层：VMware 虚拟网络层排查

### 3.1 VMware 核心服务（Windows）

```powershell
Get-Service | Where-Object { $_.Name -match "VMnet|VMware" }
# 关键看两个：
#   VMnetDHCP            —— 给 VM 分配 IP 的 DHCP 服务
#   VMware NAT Service   —— VM 通过它 NAT 上网
```

两者必须是 **Running**。停了就启动：

```powershell
Start-Service "VMnetDHCP"
Start-Service "VMware NAT Service"
```

### 3.2 虚拟网卡状态

```powershell
ipconfig
# VMware Network Adapter VMnet8（NAT 模式用）应有 IPv4，如 192.168.198.1
# VMware Network Adapter VMnet1（仅主机模式用）应有 IPv4，如 192.168.242.1
```

VMnet8 网段是多少，VM 里就该拿到同网段的 IP（如 192.168.198.x）。

### 3.3 网段扫描：VM 到底在不在线

宿主机扫 VMnet8 网段，看看 VM 是否在线（排查时能快速确认"VM 有没有拿到 IP"）：

```powershell
# 快速并行扫描（比逐 IP 串行 ping 快得多）
$tasks = 1..254 | ForEach-Object {
    $ip = "192.168.198.$_"
    $p = [System.Net.NetworkInformation.Ping]::new()
    $p.SendPingAsync($ip, 500)
}
[System.Threading.Tasks.Task]::WaitAll($tasks)
1..254 | ForEach-Object {
    if ($tasks[$_-1].Result.Status -eq "Success") { "192.168.198.$_" }
}
```

**结果解读**：只有 `.1`（宿主机虚拟网卡本身）响应、找不到 VM → **VM 没拿到 IP 或网卡没起来**，问题在 VM 端或 VMware 适配器配置。

**补充技巧**：`Get-NetNeighbor -InterfaceAlias "VMware Network Adapter VMnet8"` 看 ARP 缓存，能直接看到最近活跃的 VM。

> VMware 的「虚拟网络编辑器」（vmnetcfg）可以查看/重置各虚拟网络（VMnet0 桥接 / VMnet8 NAT / VMnet1 仅主机），一般不轻易动，除非确认虚拟网络配置坏了（如 NAT 网段被改乱）。

---

## 四、第 3 层：VM 内部排查（Kali/任何 Linux）

### 4.1 第一步永远先看 `ip a`

```bash
ip a
```

这是**整个排查最关键的一步**，看三件事：

| 看什么 | 正常 | 异常 |
|---|---|---|
| 网卡状态 | `state UP` | `state DOWN`（网卡没启用） |
| 载波标志 | 无 `NO-CARRIER` | `NO-CARRIER`（虚拟网线没插） |
| IPv4 地址 | `inet 192.168.x.x/24` | 只有 `inet6 fe80::`（link-local，没 DHCP） |

**`NO-CARRIER` 是重点**：含义是"物理层没有载波信号"——对虚拟化来说就是 **VMware 那一端没给这块网卡供电/插线**。这是 VMware 设置问题（见第五节），**在 VM 内部怎么改配置都没用**。

### 4.2 网卡是 DOWN：手动拉起

```bash
sudo ip link set eth0 up    # eth0 换成实际网卡名（ip a 里能看）
ip a                        # 再确认是否变 UP
```

### 4.3 UP 但没有 IP：手动申请 DHCP 地址

```bash
sudo dhclient eth0          # 向 DHCP 服务（VMnetDHCP）申请地址
ip a                        # 应出现 inet 192.168.x.x/24 dynamic
```

**为什么用 dhclient**：动态 IP 租约过期/网卡重启后可能不自动续租，手动触发一次 DHCP 请求（对应 DORA 流程的 Discover）即可拿到地址。

### 4.4 网络服务挂了：重启 NetworkManager

```bash
sudo systemctl restart NetworkManager
```

Kali（及多数桌面发行版）用 NetworkManager 管网络，它挂了网卡就起不来。

### 4.5 三层连通性验证（收尾必做）

```bash
ip route                    # ① 看默认路由（NAT 模式网关通常是 x.x.x.2 或 .1）
ping -c 3 192.168.198.1     # ② 内网：到 VMware 虚拟网关（宿主机）
ping -c 3 223.5.5.5         # ③ 外网 IP：阿里 DNS（不依赖域名解析）
ping -c 3 www.baidu.com     # ④ 外网域名：验证 DNS 解析
```

| 结果 | 判断 | 处理 |
|---|---|---|
| ②通 ③通 ④通 | 全通 | 完事 |
| ②通 ③不通 | NAT 出站问题 | 查 VMware NAT 服务 / 网关 |
| ③通 ④不通 | **DNS 问题**（很常见） | 改 `/etc/resolv.conf`（`nameserver 223.5.5.5`） |
| ②不通 | 内网链路问题 | 查网段匹配、VMnet8、网卡状态 |

**DNS 修复命令**：

```bash
sudo sh -c 'echo "nameserver 223.5.5.5" > /etc/resolv.conf'
```

---

## 五、本次故障完整复盘（现象 → 根因 → 修复）

**现象**：Kali 虚拟机突然完全没网，宿主机一切正常。

**排查过程**：
1. 宿主机：`Get-Service` 确认 VMnetDHCP / VMware NAT Service 均 Running；`ipconfig` 确认 VMnet8 = 192.168.198.1 正常
2. 扫 VMnet8 网段：只有 .1 响应，**VM 不在线** → 锁定 VM 端
3. VM 里 `ip a`：`eth0: <NO-CARRIER,BROADCAST,MULTICAST> state DOWN` —— **NO-CARRIER**，虚拟网线没插
4. `sudo ip link set eth0 up` 后仍 NO-CARRIER → 确认是 VMware 端问题，VM 内部无解

**根因**：VMware 虚拟机设置里网卡的**「已连接」（Connected）勾选框被取消/失效**（挂起/恢复后偶发），相当于虚拟交换机上网线被拔了。

**修复**：
1. VMware → 虚拟机设置 → 网络适配器 → 重新勾选「已连接」→ 确定
2. Kali 里 `sudo dhclient eth0` 重新拿 IP → `inet 192.168.198.128/24`
3. 验证：ping 外网 IP ✅、ping 域名 ✅（网关 ping 不通是 Windows 防火墙默认禁 ICMP，见下）

**重要认知**：NAT 模式下网关 `192.168.198.1` 是**宿主机的 Windows 网卡**，Windows 防火墙默认**不响应 ping**（ICMP），所以"ping 不通网关"是**正常的**，不代表内网坏了——数据转发（TCP/UDP）不受影响，外网能通就说明链路是好的。

---

## 六、预防与加固要点

1. **不要随意取消 VMware 网卡「已连接」**；挂起/恢复虚拟机后若断网，先检查这个勾选框
2. **优先级排序**：VM 没网先查宿主机 → 再查 VMware 服务 → 再看 `ip a`，别一上来就改 VM 网络配置
3. **记住 `NO-CARRIER` 这个关键词**：见到它直接去 VMware 设置找原因，省掉 90% 的无效操作
4. **DNS 单独配置**：建议把 `nameserver 223.5.5.5`（阿里）/ `119.29.29.29`（腾讯 DNSPod）写进 resolv.conf，国内访问更快更稳
5. **排查命令记熟**：`ip a`、`ip route`、`ping 网关 → ping 公网 IP → ping 域名`，这套三步验证法通用所有 Linux 环境
6. 安全视角：DHCP 饿死/伪造 DHCP 服务器可让 VM/内网主机拿到恶意 IP，企业环境应开 DHCP Snooping（交换机防 DHCP 伪造），与本次排查同属"IP 怎么来"的问题

---

## 七、面试速答卡

- **Q：虚拟机没网，你怎么排查？**
  A：分层排查。①宿主机物理网络正不正常（ipconfig + ping 公网）；②VMware 虚拟网络层（VMnetDHCP/VMware NAT Service 是否 Running、VMnet8 网卡有没有 IP、扫网段看 VM 在不在线）；③VM 内部（`ip a` 看网卡 state 和有没有 IP、`ip route` 看路由、分层 ping 网关/公网 IP/域名）。哪层断在哪层修。

- **Q：`ip a` 显示 `NO-CARRIER` 是什么意思？**
  A：物理层无载波信号。物理机场景是网线没插/交换机端口不通；虚拟机场景是虚拟网卡没连到虚拟交换机，通常去 VMware 设置检查网卡「已连接」是否勾选，VM 内部改配置无效。

- **Q：网卡 UP 但只有 IPv6 link-local 地址（fe80::），怎么办？**
  A：说明没拿到 IPv4 地址，DHCP 没成功。手动 `sudo dhclient eth0` 触发 DHCP 申请；还不行就 `sudo systemctl restart NetworkManager` 或检查 DHCP 服务（VMnetDHCP）是否在运行。

- **Q：ping 得通 IP 但 ping 不通域名，问题出在哪？**
  A：DNS 解析问题（三层验证法的第③步）。检查 `/etc/resolv.conf` 的 nameserver，改成 `223.5.5.5` 等公共 DNS 重试。IP 通说明路由和网关正常。

- **Q：Windows 宿主机上 VM 的网关 ping 不通，但外网能上，正常吗？**
  A：正常。NAT 模式下网关是宿主机的虚拟网卡（如 192.168.198.1），Windows 防火墙默认丢弃 ICMP ping 请求，但不影响 TCP/UDP 数据转发，所以外网正常。判断内网是否正常应看能否 ping 通公网 IP。

- **Q：Linux 里排查网络常用的命令有哪些？**
  A：`ip a`（网卡状态/IP）、`ip route`（路由表）、`ping`（连通性）、`dhclient`（手动 DHCP）、`ss`/`netstat`（端口监听）、`traceroute`（路由追踪，定位断点）、`dig`/`nslookup`（DNS 查询）、`tcpdump`（抓包分析）。