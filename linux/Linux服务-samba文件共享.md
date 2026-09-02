# Linux 服务：Samba 文件共享

> 来源：课程实验（Linux操作系统，CentOS 8.3，2025-2026 第一学期），老师版PDF为底料
> 定位：Windows 与 Linux 混合环境下的文件/打印机共享主力服务。运维中常用于内网文件服务器的搭建；安全角度上，Samba 是内网横向渗透的高价值目标（弱口令暴破、永恒之蓝 SMB 漏洞、匿名共享数据泄露），应急响应常需排查 /etc/samba/smb.conf 是否被篡改、是否有异常共享。

---

## 一、概念与原理

**Samba 是什么**：在 Linux 上实现 SMB/CIFS 协议的开源软件，让 Linux 可以无缝参与 Windows 局域网资源共享。SMB 协议（Server Message Block）可看作局域网上共享文件和打印机的一种协议。

**应用环境**：
- 文件和打印机共享：Samba 的主要功能
- 身份验证和权限设置
- 名称解析：通过 nmbd 服务搭建 NBNS（NetBIOS Name Service）服务器
- 浏览服务：Samba 服务器可成为本地主浏览服务器（LMB）

**两大进程**：Samba 服务由 **nmbd**（NetBIOS 名称解析）和 **smbd**（文件/打印共享）两个进程组成。

**访问的四步握手（面试常问）**：
| 步骤 | 报文指令 | 说明 |
|---|---|---|
| ① 协议协商 | negprot | 客户端告知自己支持的 SMB 类型，服务器选择最优 SMB 版本回应 |
| ② 建立连接 | session setup | 客户端提交账号密码，通过验证后服务器为用户分配唯一 **UID** |
| ③ 访问共享 | tree connect | 服务器为每个"客户端-共享资源"连接分配 **TID**，客户端开始访问 |
| ④ 断开连接 | tree disconnect | 使用完毕客户端主动关闭共享连接 |

**端口**：139（SMB over NetBIOS）、445（SMB over TCP，现代 Windows 主力）、137/138（NetBIOS 名称解析）。

**配置文件位置**：主配置文件 `/etc/samba/smb.conf`（日志文件、共享定义、权限均在此），用户数据库由 tdbsam 后端管理（`smbpasswd` 命令维护）。

**配置工作流程**：编辑 smb.conf 指定共享目录及共享权限 → 指定日志文件 → 设置共享目录的**本地系统权限** → 重新加载/重启服务 → 放行防火墙、处理 SELinux。

---

## 二、环境准备与安装

```bash
sudo dnf install samba -y              # 安装
sudo rpm -qa | grep samba              # 检查安装组件
sudo systemctl start smb               # 注意服务名是 smb 不是 samba
sudo systemctl enable smb              # 开机自启
sudo cp /etc/samba/smb.conf /etc/samba/smb.conf.bak   # 先备份主配置文件
sudo cat /etc/samba/smb.conf           # 查看默认内容（~706 字节）
```

默认 smb.conf 关键内容：`[global]` 中 `workgroup = SAMBA`、`security = user`（默认用户级安全）、`passdb backend = tdbsam`，另有 `[homes]`（用户家目录共享）、`[printers]`、`[print$]` 三个内置段。

---

## 三、配置详解（重点）

### 3.1 匿名访问方式

需求：共享目录 /share（共享名 public），全员可下载、禁止上传。

```bash
sudo mkdir /share
sudo touch /share/test_share.tar
sudo chmod 777 /share -R              # 本地系统权限也要放开
sudo vim /etc/samba/smb.conf
```

```ini
[global]
        map to guest = bad user        # 匿名用户映射为 guest，实现匿名访问

[public]
        comment=public
        path=/share
        guest ok=yes                   # 允许匿名（guest）访问
        browseable=yes                 # 客户端可见该共享
        public=yes                     # 等同 guest ok = yes
        read only=yes                  # 只读，禁止上传
```

### 3.2 用户访问方式

需求：销售部资料放 /companydata/sales，仅销售组可写。要点：**Samba 账号不能直接建立，必须先建立同名 Linux 系统账号**。

```bash
sudo mkdir -p /companydata/sales
sudo touch /companydata/sales/test_share.tar
sudo groupadd sales                    # 建立销售组
sudo useradd -g sales sale1            # 用户属于 sales 组
sudo useradd -g sales sale2
sudo useradd test_user1                # 对照组：不属于 sales 组
sudo passwd sale1 && sudo passwd sale2
sudo smbpasswd -a sale1                # 添加 samba 账号（smbpasswd -a）
sudo smbpasswd -a sale2
sudo chmod 770 /companydata/sales -R   # 本地权限：组内可读写
sudo chown :sales /companydata/sales -R
```

```ini
[global]
        workgroup = Workgroup
        server string = File Server

[sales]
        comment=sales
        path=/companydata/sales
        writable = yes
        browseable = yes
        valid users = @sales           # @前缀表示组，仅 sales 组成员可访问
```

### 3.3 高级配置

**① 用户账号映射**（虚拟账号登录，隐藏真实系统账号名）：
```ini
[global]
        username map = /etc/samba/smbusers
```
`/etc/samba/smbusers` 写入：
```
sale1=suser1 myuser1
sale2=suser2
```
客户端只需输入 suser1 即可访问，实际对应 sale1，防止真实账号泄露。

**② 客户端访问控制**（禁止 192.168.137.0/24 网段访问但放行 .1）：
```ini
[sales]
        hosts deny = 192.168.137.
        hosts allow = 192.168.137.1
```
注意：配置了访问控制后，连本机 localhost 都可能无法测试，需用同网段真实机器验证。

**③ 打印共享**（了解）：`[printers]` 段 `path=/var/spool/samba`、`writable=no`、`guest ok=yes`，并安装 CUPS（`dnf install cups`）。

### 3.4 放行与生效

```bash
sudo firewall-cmd --permanent --add-service=samba && sudo firewall-cmd --reload
sudo setenforce 0                      # 实验环境关闭 SELinux（生产建议按第六节处理）
sudo systemctl restart smb             # 或 systemctl reload smb 热加载
```

---

## 四、客户端验证

**Windows**：资源管理器地址栏输入 `\\192.168.137.4`（IP 用 `ip a` 查自己虚拟机的），匿名模式用户名填 `Anonymous`、密码留空；也可右键"添加一个网络位置"映射网络驱动器，像本地盘一样访问。

**Linux**：
```bash
sudo dnf install samba-client cifs-utils -y
sudo smbclient //192.168.137.4/public -U Anonymous   # 浏览测试，进入 smb: \> 交互界面
sudo mkdir -p /home/myth/linuxcourse/samba/public
sudo mount -t cifs //192.168.137.4/public /home/myth/linuxcourse/samba/public -o username=Anonymous
```

---

## 五、常见问题与排查（老师PDF里的坑）

1. **Windows 10/11 匿名访问失败**：提示"你不能访问此共享文件夹"。原因：新版 Windows 默认禁用匿名来宾访问。解决：`gpedit.msc` → 计算机配置 → 管理模板 → 网络 → Lanman 工作站 → 启用"**启用不安全的来宾登录**"，重启后再测。
2. **多账号连接冲突**：Windows 提示"不允许同一用户使用不同用户名同时连接"。解决：`net use` 查看连接，`net use * /delete` 全部断开，或用 `net use \\servername\sharename /delete` 断开指定连接后重连。
3. **权限不生效**：Samba 共享权限与文件系统权限是**叠加关系**，两边都要放开（共享里 writable=yes、系统里 chmod/chown 也要对）。
4. **访问不了先查防火墙和 SELinux**：`firewall-cmd --list-all` 确认 samba 服务放行；`getenforce` 查看状态。

---

## 六、安全加固要点

- **默认 `security = user`**，不要随意开放 guest；只有需要公开下载的目录才用匿名共享，且必须 `read only = yes`。
- **匿名共享风险**：全员可读=敏感数据泄露面。生产环境把共享目录放到独立分区、按部门分割（valid users 限定组），避免 `chmod 777`，用 770 + 属组控制。
- **弱口令暴破**：smbpasswd 密码独立于系统密码，复杂度要求要落地；配合 `fail2ban` 封禁反复认证失败 IP；关注永恒之蓝（MS17-010，445端口）类 SMB 漏洞补丁。
- **账号映射**（username map）隐藏真实系统账号名，降低被针对性利用的风险。
- **客户端访问控制**：`hosts allow` 只放行办公网段，杜绝公网直接访问 445。
- **SELinux**：生产建议开启 Enforcing 并放行 `samba_*` 布尔值，而不是 `setenforce 0` 一刀切。
- 日志审计：日志文件位置在 smb.conf 指定，常查异常登录与访问记录；应急响应时核对是否有新增的恶意共享段。

---

## 七、面试速答卡

- **Samba 是什么**：Linux 上实现 SMB/CIFS 协议的开源软件，用于跨 Windows/Linux 的文件与打印机共享。
- **smbd 和 nmbd 区别**：smbd 提供文件/打印共享与认证，nmbd 负责 NetBIOS 名称解析和浏览服务。
- **访问 Samba 的四步协议流程**：negprot 协议协商 → session setup 建立连接（分配UID）→ tree connect 访问共享（分配TID）→ tree disconnect 断开。
- **匿名共享的关键参数**：`map to guest = bad user` + `guest ok = yes`/`public = yes`，且目录文件系统权限要放开。
- **Samba 账号与系统账号关系**：先建同名 Linux 系统账号，再用 `smbpasswd -a` 添加 Samba 账号，两者密码相互独立。
- **Samba 常用端口**：445（SMB）、139（NetBIOS over SMB）、137/138（名称解析）。