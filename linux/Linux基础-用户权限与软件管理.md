# Linux 基础：用户权限与软件管理

> 来源：Linux操作系统课程实验《Linux用户管理与软件管理》（本人实验报告 docx，2025-2026 第一学期，指导老师陶小结）
> 定位：Linux 安全的基础就是"谁能做什么、谁装了啥"。用户/组/权限模型是 CTF 提权、应急响应的底层知识；apt/yum 包管理是日常部署软件的第一道关。面试常问 SUID、UID/GID、dpkg 与 aptitude 的区别等

---

## 一、概述：用户模型与包管理两大流派

### 1. 用户与权限模型（Linux 安全的地基）

Linux 是多用户多任务系统，一切权限控制围绕三个身份展开：**用户（user）、用户组（group）、其他人（others）**。

- 每个用户有唯一 **UID**（用户 ID），root 的 UID 永远是 **0**，普通用户从 1000 开始。判断"是不是管理员"看的是 UID，不是名字。
- 用户归属某个**主组（primary group）**，还可以加入多个**附加组**。
- 账号数据存三个核心文件：
  - `/etc/passwd`：用户名、UID、GID、家目录、登录 shell（密码字段现在是 `x`，真正的密码挪走了）
  - `/etc/shadow`：加密后的密码哈希及有效期策略（**只有 root 能读**，这就是防破解的关键）
  - `/etc/group`：组名、GID、组成员

> 面试点：为什么密文在 shadow 而不在 passwd？因为 passwd 需要被所有程序读取（比如 ls -l 显示属主），把哈希放进去等于公开给暴力破解，所以拆出来单独用 600 权限保护。

### 2. 软件包管理两大流派

Linux 发行版分两大系，包格式和工具都不同：

| 体系 | 底层包格式 | 底层工具 | 前端工具 | 代表发行版 |
|---|---|---|---|---|
| Debian 系 | `.deb` | `dpkg` | `apt`（Ubuntu/Kali 用） | Ubuntu、Kali、Debian |
| Red Hat 系 | `.rpm` | `rpm` | `yum` / `dnf` | CentOS、Rocky、Fedora |

- **底层工具（dpkg/rpm）**：安装卸载单个包，**不会自动解决依赖**。
- **前端工具（apt/yum）**：从软件源仓库自动下载包并**解决依赖关系**，日常几乎都用前端。

**网安学生注意**：Kali 是 Debian 系，装工具用 `apt`；而很多安全工具的安装说明用的 CentOS 命令是 `yum`，别混。

---

## 二、核心命令速查

### 1. 用户管理

| 命令 | 作用 | 常用形式 |
|---|---|---|
| `useradd` | 创建用户 | `useradd myth`、`useradd -m -s /bin/bash myth`（-m 建家目录，-s 指定 shell，**强烈建议加**） |
| `passwd` | 设置/修改密码 | `passwd myth`（root 可以给任何人设密码） |
| `usermod` | 修改用户属性 | `usermod -aG docker myth`（-aG 追加到附加组，**不加 -a 会覆盖组列表**） |
| `userdel` | 删除用户 | `userdel -r myth`（-r 连家目录一起删） |
| `chage` | 管理密码有效期 | `chage -l myth`（查看）、`chage -E 2026-12-31 myth`（设过期） |
| `id` | 查看用户 UID/GID/所属组 | `id myth` |
| `who` / `w` | 查看当前登录用户 | `who` |

### 2. 用户组管理

| 命令 | 作用 | 常用形式 |
|---|---|---|
| `groupadd` | 创建组 | `groupadd devteam` |
| `groupmod` | 修改组（**改编号/名称**——实验内容） | `groupmod -g 2001 devteam`（改 GID）、`groupmod -n newname devteam`（改名） |
| `groupdel` | 删除组 | `groupdel devteam` |
| `gpasswd` | 管理组成员 | `gpasswd -a myth devteam`（加入）、`gpasswd -d myth devteam`（移出） |
| `groups` | 查看用户所属组 | `groups myth` |

### 3. 磁盘配额（quota）

配额=限制用户/组能占用的磁盘空间，防止一人占满全盘（多用户服务器必备）。

```bash
# 流程：改内核参数 → 重挂载 → 生成配额数据库 → 设限额 → 开启配额
vim /etc/fstab          # 在目标分区的挂载选项加 usrquota,grpquota
mount -o remount /home  # 按新参数重挂载
quotacheck -cug /home   # 生成 aquota.user / aquota.group 数据库
edquota -u myth         # 交互式设置 myth 的软/硬限额（soft 超限警告、hard 硬顶）
quotaon /home           # 开启配额
quota -u myth           # 查看该用户配额使用情况
```

> 概念区分：**软限制（soft）**允许超限但警告、宽限期后仍超就拒绝；**硬限制（hard）**是绝对上限，到了直接拒绝写入。

### 4. 权限深入：SUID/SGID/粘滞位（面试加分项）

普通 `rwx` 之外还有三种特殊权限位：

| 特殊位 | 符号 | 作用 | 典型例子 |
|---|---|---|---|
| SUID | `s`（所有者位） | 执行该程序时**临时获得文件属主的权限** | `/usr/bin/passwd`（普通用户借此写 shadow） |
| SGID | `s`（组位） | 执行时获得属组权限；目录上设置后新建文件自动继承属组 | `/usr/bin/write` |
| 粘滞位 | `t` | 目录里的文件**只能被属主/root 删除** | `/tmp`（人人都能写，但不能删别人的） |

```bash
chmod u+s file   # 加 SUID；ls -l 显示 -rwsr-xr-x
chmod g+s dir    # 加 SGID
chmod +t dir     # 加粘滞位；/tmp 显示 drwxrwxrwt
```

> **网安重点**：SUID 提权是经典攻击面——找全盘 `find / -perm -4000` 列出 SUID 程序，找到配置错误的（如可写的 SUID 脚本）就是提权路径。面试深挖"R 用户如何提权"必答这条。

### 5. 软件包管理命令

**Debian 系（dpkg + apt）**：

| 命令 | 作用 |
|---|---|
| `dpkg -i 包.deb` | 安装本地 deb 包（不解决依赖） |
| `dpkg -r 包名` / `dpkg -P 包名` | 卸载（-P 连配置文件一起删） |
| `dpkg -l` / `dpkg -L 包名` | 列出已装包 / 查看包装了哪些文件 |
| `apt update` | 更新软件源索引（换源后必做第一步） |
| `apt upgrade` | 升级所有可升级软件 |
| `apt install 包名` / `apt remove 包名` | 装/卸载（自动解依赖） |
| `apt search 关键字` | 搜索软件 |

**Red Hat 系（rpm + yum）**：

| 命令 | 作用 |
|---|---|
| `rpm -ivh 包.rpm` | 安装本地 rpm 包 |
| `rpm -qa` / `rpm -ql 包名` | 列出全部已装包 / 查看包文件列表 |
| `rpm -e 包名` | 卸载 |
| `yum install 包名` / `yum remove 包名` | 装/卸载（自动解依赖） |
| `yum repolist` | 查看当前软件源 |
| `yum clean all && yum makecache` | 清缓存并重建索引（换源后必做） |

**apt 换源**（Ubuntu，国内加速）：

```bash
sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak   # 备份
sudo sed -i 's/archive.ubuntu.com/mirrors.aliyun.com/g' /etc/apt/sources.list
# 或直接编辑文件，把源地址换成清华/阿里镜像
sudo apt update
```

> 换源原理：distro 默认源的域名（archive.ubuntu.com / mirrors.aliyun.com…）在国外或已 EOL 失效，替换成国内镜像站的域名，下载速度立刻起飞。

---

## 三、实操流程（实验主线走一遍）

### 任务 1：创建用户与配置密码
```bash
useradd -m -s /bin/bash myth     # 创建用户 myth，带家目录和 bash shell
passwd myth                      # root 为用户设密码（输入两次）
id myth                          # 验证 UID/GID
su - myth                        # 切换到新用户验证能登录
whoami
```

### 任务 2：用户组管理（改编号、改名）
```bash
groupadd devteam                  # 创建组
groupmod -g 2001 devteam          # 把 GID 改为 2001
groupmod -n securl devteam        # 组改名为 securl
usermod -aG securl myth           # 把 myth 加入该组（注意 -a 保留原有组）
groups myth                       # 验证
gpasswd -d myth securl            # 移出组
```

### 任务 3：磁盘配额
按上文 quota 流程：改 fstab → remount → quotacheck → edquota 设置 myth 软/硬限额 → quotaon → `dd if=/dev/zero of=/home/myth/bigfile bs=1M count=300` 超限验证。

### 任务 4：dpkg / rpm 本地包管理
```bash
# Debian 系：下载一个 .deb（如 vim 离线包）演示
dpkg -i vim_xxx.deb
dpkg -l | grep vim
dpkg -r vim

# Red Hat 系
rpm -ivh package.rpm
rpm -qa | grep 关键词
rpm -e 包名
```

### 任务 5：yum 换源（CentOS 8，已在安装篇详述）
```bash
cd /etc/yum.repos.d/ && mkdir backup && mv *repo backup
wget -O CentOS-Linux-BaseOS.repo https://mirrors.aliyun.com/repo/Centos-8.repo
yum clean all && yum makecache
yum install -y vim      # 安装测试
```

---

## 四、常见问题与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `useradd` 后用户没有家目录 | 忘了 `-m` 参数 | `usermod -m -d /home/myth myth` 补建 |
| 用户能登录但 shell 不对/不能执行命令 | 没指定 shell，默认 /bin/sh 或 nologin | `usermod -s /bin/bash myth` |
| `usermod -G` 后用户原本的组全没了 | **-G 是覆盖不是追加**，用 `-aG` | 用 `usermod -aG 组名 用户` 追加 |
| 删不掉的用户：`userdel` 报进程占用 | 该用户进程还在跑 | `pkill -u myth` 后删除 |
| 改完组成员不生效 | 组关系在登录时加载 | 重新登录（`su - myth`）或 `newgrp 组名` |
| apt/yum 报"源连不上 / EOL 源失效" | 默认源在国外或被停维护 | 换国内镜像源 + `clean all && makecache` |
| `dpkg -i` 报依赖缺失 | dpkg 不自动解决依赖 | 用 `apt install -f` 修复，日常直接 `apt install` |
| 提权失败：普通用户执行需要 root 的程序失败 | 权限不够 | 管理员分配 sudo 权限（加入 sudo 组）或配置 /etc/sudoers |

---

## 五、面试速答卡

- **root 的 UID 是多少**：0；普通用户一般 1000+；判断管理员看 UID 而非用户名
- **passwd 和 shadow 的分工**：passwd 存公开信息（UID/GID/家目录），shadow 存加密密码（仅 root 可读），避免哈希泄露被破解
- **useradd 与 adduser 区别**：useradd 是底层命令不建家目录，adduser 是交互式脚本自动建家目录配置完善（Debian 系）
- **apt 与 dpkg 区别**：dpkg 只管单个 .deb、不查依赖；apt 基于软件源自动拉取并解决依赖，日常用 apt
- **yum 与 rpm 区别**：对应 Red Hat 系，rpm 管本地包不解决依赖，yum 从软件源安装自动解依赖
- **SUID 是什么、有什么风险**：执行时以属主身份运行；若 SUID 程序可被利用（如存在漏洞或可写脚本），普通用户可借此提权——`find / -perm -4000` 排查
- **粘滞位的作用**：共享目录（如 /tmp）内文件只能属主或 root 删除，防止互删
- **磁盘配额软硬限制区别**：soft 超限警告可宽限，hard 是绝对上限直接拒绝