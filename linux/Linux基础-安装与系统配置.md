# Linux 基础：安装与系统配置

> 来源：Linux操作系统课程实验《安装与配置Linux操作系统》（老师版 PDF 59 页，讲师 myth）+《CentOS8换源》+ 本人实验报告（docx，2025-2026 第一学期）
> 定位：网安学生搭建靶机/实验环境的必备技能，VMware + Ubuntu 是打 CTF、复现漏洞的标配玩法；SSH、静态 IP、免密登录是后续所有远程操作的地基

---

## 一、概述：虚拟机与虚拟化

**一句话原理**：虚拟化软件在一台物理电脑上，用软件"模拟"出 CPU、内存、硬盘、网卡等硬件，让多个操作系统互不干扰地同时运行，仿佛各自占有一台独立电脑。这样做的价值是：**资源复用、环境隔离、随手备份**——网安学习最需要的就是"随便折腾、坏了就还原"。

Windows 上常用的虚拟化软件有三类，选择建议直接记结论：

| 软件 | 特点 | 适合人群 |
|---|---|---|
| VMware Workstation | 功能最强、资料最多、博通收购后个人版免费；虚拟网络支持丰富 | **小白首选**（遇到问题能搜到大量教程） |
| Hyper-V | Windows 原生、性能好、稳定，但网络配置复杂，装 Linux 要关安全启动 | 技术强、追求性能的同学 |
| VirtualBox | 完全免费开源、跨平台，性能稍弱 | VMware 装不成的备选 |

**网安学生的核心场景**：用虚拟机装 Kali（攻击机）、Ubuntu/CentOS（靶机/服务器）、Windows（内网横向），构成一套完整的实验网。所以"装系统"不是点下一步那么简单，后面的网络规划、快照、SSH 都要会。

---

## 二、核心知识

### 1. ISO 镜像与哈希校验（老师强调"重要三遍"）

安装系统前先下载对应发行版的 ISO 镜像（如 `ubuntu-22.04.4-desktop-amd64.iso`）。**镜像是大文件，下载很容易不完整且自己察觉不到，装到一半报莫名奇妙的错**——所以下载后必须校验哈希：

```powershell
# Windows PowerShell 里校验（在镜像所在文件夹打开）
certutil -hashfile ubuntu-22.04.4-desktop-amd64.iso md5
```

把算出的值跟官网/老师给的 `.md5` 文件里的字符串比对，一致才说明下载完整。

### 2. 虚拟机的三种网络模式（面试常问的概念）

- **NAT 模式**：虚拟机通过宿主机的 IP 共享上网，外部看不到虚拟机——**最省事，默认推荐**。只要宿主机能上网，虚拟机就能上网。
- **桥接模式**：虚拟机直接"插"到真实局域网里，拥有独立 IP，外部可以直接访问（搭网站被别人访问就要用这个）。
- **仅主机模式（Host-Only）**：只能和宿主机互通，不能上外网，适合纯内网测试。

> 老师明确建议：**前期只使用 NAT 模式**，等熟悉了虚拟化网络再考虑桥接等模式，避免踩坑。

### 3. SSH 远程连接三件套

| 工具 | 用途 |
|---|---|
| VSCode + Remote-SSH 插件 | 远程写代码的主力，编辑器体验最好 |
| Xshell | 轻量远程终端，执行简单命令 |
| Xftp | 图形化文件传输，Windows ↔ Linux 互传文件 |

### 4. 快照 vs 检查点 vs 快照（不同厂商叫法不同）

| 平台 | 术语 | 作用 |
|---|---|---|
| VMware Workstation | 快照（Snapshot） | 保存虚拟机状态，坏了随时回滚 |
| Hyper-V | 检查点（Checkpoint） | 同上 |
| VirtualBox | 快照（Snapshot） | 同上 |

---

## 三、实操流程（老师版 PDF 步骤提炼）

### 第 1 步：下载镜像 + 校验哈希
官网或清华镜像站下载 ISO，用上面的 `certutil` 校验，确认完整后再动手。

### 第 2 步：安装 VMware 并创建虚拟机
1. 官网（vmware.com，需注册博通账号选 personal use）下载安装，全程 Next。
2. 新建虚拟机 → 选择 ISO 镜像 → **输入用户名密码（记住！后面一直要用，建议全小写、好记）** → 选存放路径 → 磁盘容量（硬盘大就分大点，如 60G）。
3. 启动虚拟机开始装系统。

> **避坑**：装 Ubuntu 选内存时，少于 2GB（2048MB）会报 `initramfs unpacking failed: write error`，启动直接失败——**内存至少 2G，建议 4G**。

### 第 3 步：安装 Linux 系统（Ubuntu 为例）
1. 启动后选 "Try or Install Ubuntu" → Install Ubuntu。
2. 默认勾选"安装更新和第三方软件"即可（完整但慢）；想快可以勾最小化安装、去掉更新，后面自己装。
3. Install Now（新手直接用默认分区，熟悉后再自定义）。
4. 设置用户名密码 → 等待安装 → Restart Now。

### 第 4 步：安装后立即做快照（关键中的关键）
**装完系统第一件事就是备份**：右键虚拟机 → 快照 → 新建快照。不熟悉 Linux 很容易把系统搞崩，有快照就能秒回当初的状态，省去重装几小时。

### 第 5 步：安装并启用 SSH 服务
在虚拟机终端里执行（**Ubuntu 桌面版默认没装 SSH 服务端，这是连不上的头号原因**）：

```bash
sudo apt update -y              # 更新软件列表
sudo apt install openssh-server -y   # 安装 SSH 服务端
sudo systemctl start ssh        # 启动 ssh 服务
sudo systemctl enable ssh       # 开机自启
sudo systemctl status ssh       # 查看状态
```

然后在虚拟机里执行 `ip a` 查看 IP 地址并记下——这就是远程连接的地址。

### 第 6 步：SSH 客户端连接
- **VSCode**：装 Remote-SSH 插件 → 配置 `~/.ssh/config`：

```
Host ubuntu-vm          # 名字随意，能标识即可
HostName 192.168.x.x    # 虚拟机 IP，务必准确
User 你的用户名          # Ubuntu 用户名，务必准确
```

刷新 → Connect → Continue → 输密码 → Ctrl+Shift+` 打开远程终端。
- **Xshell**：新建会话填 IP、用户名、密码即可。
- **Xftp**：同 Xshell，连上后左边 Windows、右边 Linux，直接拖拽传文件。

### 第 7 步：配置静态 IP（进阶，让 SSH 地址固定不变）
动态 IP 每次重启可能变，SSH 配置就要跟着改，很烦。配静态 IP 后一劳永逸。

**VMware 的 NAT 模式（最简单）**：
1. 虚拟网络编辑器里查看 NAT 网段和网关（如网段 `172.30.73.0`、网关 `172.30.73.2`，**每台电脑不同**）。
2. 在 Ubuntu 的 Network 设置里手动配置：
   - IP：网段内未被占用的地址（避开网关和宿主机地址，如 `172.30.73.3`）
   - 掩码：`255.255.255.0`
   - 网关：`172.30.73.2`（填虚拟网络编辑器里记下的）
   - DNS：`223.5.5.5`（阿里）或 `8.8.8.8`（Google）
3. 应用后把有线网络关掉再打开使其生效，`ip a` 验证。

**Hyper-V 要点**：新建"内部"类型虚拟交换机 → 给虚拟机新增一块网卡接该交换机 → 在宿主机控制面板给该网卡设 IP → 虚拟机里配静态 IP（可加一张 Default Switch 网卡保外网）。
**VirtualBox 要点**：Host-Only 管内网（配静态 IP 供 SSH），NAT 管外网（自动分配）——**两块网卡都要有，否则要么连不上要么上不了网**。

### 第 8 步：VSCode 免密登录（公私钥）
每次都输密码麻烦，用密钥对实现免密（安全且方便）：

```bash
# Windows 上打开 Git Bash 生成密钥对
ssh-keygen          # 一路回车
# 生成的 id_rsa（私钥，勿外传）与 id_rsa.pub（公钥）在 C:\Users\你的用户名\.ssh\

# 方式一：一键上传（推荐）
ssh-copy-id 用户名@IP      # 如 ssh-copy-id myth@172.30.73.29，输一次密码

# 方式二：手动粘贴
# 打开 Linux 的 ~/.ssh/authorized_keys，把 id_rsa.pub 内容粘进去保存
```

之后 VSCode/Xshell 连接就不用再输密码了。

### 第 9 步：CentOS8 换源（国内加速 + 处理 EOL）
CentOS 8 已停止维护（EOL），原软件源失效；且默认源在国外，下载慢。换阿里云源：

```bash
cd /etc/yum.repos.d/
sudo mkdir backup
sudo mv *repo backup                                  # 备份原配置
sudo wget -O /etc/yum.repos.d/CentOS-Linux-BaseOS.repo \
    https://mirrors.aliyun.com/repo/Centos-8.repo     # 下载阿里源
sudo yum clean all && sudo yum makecache              # 重建缓存
```

换源的本质：**把 `/etc/yum.repos.d/` 里指向国外的 .repo 文件，替换成指向国内镜像站的**。Ubuntu 同理（换 `/etc/apt/sources.list` 为清华/阿里源）。

---

## 四、常见问题与排查（全是老师 PDF 里标注的坑）

| 现象 | 原因 | 解决 |
|---|---|---|
| 启动报 `initramfs unpacking failed: write error` | 虚拟机内存给太小 | 调大内存至 2G+ |
| Windows 能 ping 通虚拟机，但 SSH 连不上 | Linux 没装 SSH 服务端 | 执行第 5 步四条 systemctl 命令 |
| Windows 与虚拟机互相 ping 不通 | 网络模式有问题/虚拟机没网 | 检查 NAT 配置，先保证虚拟机内能上网 |
| VSCode 连不上，日志报"过程试图写入的管道不存在" | Windows 侧 `~/.ssh` 文件夹权限被继承污染 | 按九步法重置：`.ssh` 属性 → 安全 → 高级 → 禁用继承 → 删除所有继承权限 → 添加自己的用户为所有者 |
| VSCode 配置正确还是连不上 | `known_hosts` 里的旧密钥记录冲突 | 删掉 `C:\Users\你的用户名\.ssh\known_hosts` 对应行或整个文件重连 |
| VSCode 服务端程序损坏 | 远程端 `~/.vscode-server` 缓存坏 | `sudo rm -rf ~/.vscode-server` 后重装 VSCode 重连 |
| Hyper-V 装 Linux 报错 | 第二代虚拟机默认开启了"安全启动"，Linux 不支持 | 虚拟机设置 → 安全 → **取消勾选"启用安全启动"** |
| 静态 IP 配置后不生效 | 没重启网络 | 图形界面把有线网络开关一次，或 `sudo systemctl restart network` |

---

## 五、面试速答卡

- **虚拟化是什么**：软件模拟硬件，多 OS 并行运行于一台物理机，资源隔离复用
- **NAT/桥接/仅主机区别**：NAT 借宿主机上网且外部不可见；桥接有独立局域网 IP 外部可访问；仅主机只能与宿主机互通
- **为什么下载 ISO 要校哈希**：大文件下载易损坏，损坏镜像装系统会莫名报错，校验防"装到一半崩溃"
- **Ubuntu 默认能 SSH 连接吗**：桌面版默认没装 openssh-server，需 `apt install openssh-server` 并 `systemctl start/enable ssh`
- **SSH 免密登录原理**：本地生成公私钥对，公钥放进远端 `~/.ssh/authorized_keys`，连接时用私钥签名验证
- **快照的作用**：保存虚拟机状态，系统搞坏后一键回滚，省去重装
- **换源为什么能加速**：把包管理器的软件源从海外官方服务器换成国内镜像站，网络延迟和带宽大幅改善
- **静态 IP 配置四要素**：IP 地址、子网掩码、网关、DNS——IP 与网关属于同一网段且不与已有设备冲突