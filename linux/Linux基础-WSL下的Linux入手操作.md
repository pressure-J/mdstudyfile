# Linux 基础：WSL 下的 Linux 入手操作

> 来源：本人实战记录（Win11 家庭版 26200 安装 WSL2 + Kali Linux 2026.2，2026-10）
> 定位：WSL 是 Windows 上最轻的 Linux 环境，秒级启停、不吃内存，适合当"命令行走廊"——跑 nmap、写脚本、编译 payload。但它不是 VMware 的替代品（没有独立网段、做不了内网横向），两者按任务分工，详见第六节。

---

## 一、WSL 是什么，和 VMware 差在哪

**一句话**：WSL2 是微软官方提供的轻量虚拟机，跑的是真实 Linux 内核，但由 Windows 深度托管——没有 BIOS、没有虚拟网卡配置界面、不用装系统、不用等开机。

和传统虚拟机最本质的三点差别：

| 维度 | VMware / VirtualBox | WSL2 |
|---|---|---|
| 系统安装 | 挂 ISO 走完整安装流程（分区、用户、GRUB） | 一条命令下载 rootfs 解包，1 分钟完成 |
| 资源占用 | 固定分配 2–4 GB 内存 | 按需增长，空闲时自动释放（~200 MB 起） |
| 网络 | 可加多块网卡、桥接/仅主机/NAT 随意组网 | **固定一张网卡，固定 NAT**，不能改拓扑 |
| 文件互通 | 靠共享文件夹 / SMB | `/mnt/c`、`/mnt/d` 原生挂载，双向直读 |
| 图形界面 | 完整桌面 | 无桌面（可用 WSLg 跑单个 GUI 程序） |

**判断用哪个**：

- 要"两个网段互通""桥接拿真实 IP""ARP 扫描二层发现" → **VMware**
- 要"快速敲命令""轻量编译""不占内存常驻" → **WSL**

---

## 二、安装：一条命令 + 一次重启

### 2.1 先认清那个 msi 文件

网上教程常让人下载 `wsl_update_x64.msi`（16 MB）双击安装。**这个文件在 Win11 上已经没用了。**

它是早期 Win10 的 WSL2 内核更新包，那时内核和系统组件分离分发。Win11 起 WSL 改成 Store 应用，内核随 WSL 包一起走，这个 MSI 装上也不会被任何组件引用。看到它可以直接删。

### 2.2 正确流程

**管理员** PowerShell 执行：

```powershell
wsl --install
```

它会自动做三件事：启用 `Microsoft-Windows-Subsystem-Linux` 和 `VirtualMachinePlatform` 两个可选功能、安装 Store 版 WSL2 主体、安装默认发行版 Ubuntu。

### 2.3 必须重启一次（关键）

`虚拟机平台`(VirtualMachinePlatform) 是内核级组件，对应的 `VmCompute` 驱动必须在系统启动时加载，**运行中启用不生效**。命令跑完会输出：

```
请求的操作成功。直到重新启动系统前更改将不会生效。
```

此时状态是这样的，容易误判成"装好了"：

```powershell
wsl --version        # ✅ 能打印版本 —— 但这只说明命令行框架在
wsl --status         # ❌ 报 "WSL2 无法启动，因为此计算机上未启用虚拟化"
wsl --list --online  # ✅ 能列出可装发行版
```

`wsl --version` 有输出 ≠ 能用。真正判断标准是 `wsl --status` 里有没有那句"无法启动，因为此计算机上未启用虚拟化"。**有 → 重启**。

重启后 `wsl --status` 应该只剩：

```
默认版本: 2
当前计算机配置不支持 WSL1。
```

"当前计算机配置不支持 WSL1" 是正常提示（家庭版没启用 WSL1 旧组件），不影响 WSL2。

### 2.4 装发行版

```powershell
wsl --list --online              # 看有哪些（Ubuntu-24.04 / kali-linux / Debian / archlinux ...）
wsl --install -d kali-linux      # 装 Kali
```

**坑 1：`--no-launch` 的副作用**

加 `--no-launch` 只下载不启动，装完 `wsl -l -v` 显示 `Stopped` 但进不去，还得手动跑 `wsl` 完成初始化。不加则装完自动进入并让你建用户名密码。**想省事就别加**。

**坑 2：`WININET_E_TIMEOUT`**

```
正在下载 https://raw.githubusercontent.com/microsoft/WSL/master/distributions/DistributionInfo.json
错误代码: Wsl/InstallDistro/WININET_E_TIMEOUT
```

这是去 GitHub 拉分发列表时代理/网络不通。**直接重试**即可（微软有时也会同步到国内可达的 CDN）。注意 `wsl --install` 报这个错时退出码仍可能是 0，别被 `EXIT=0` 骗了，一定要用 `wsl -l -v` 验证。

**坑 3：重装/续装**

如果第一次只装上了 WSL 主体（`--no-distribution` 的效果），补装发行版直接再执行一次 `wsl --install -d <名字>`，不需要重装 WSL。

### 2.5 验证装好了没

```powershell
wsl -l -v
```
```
  NAME          STATE           VERSION
* kali-linux    Stopped         2
```

`VERSION=2` 才对（WSL1 网络行为完全不同）。再看内核：

```bash
wsl -d kali-linux -u root -- uname -r
# 6.18.54.1-microsoft-standard-WSL2
```

---

## 三、怎么用：三种进入方式

### 3.1 直接敲命令（最常用）

安装后 WSL 不是一个"应用"，而是 Windows 里的一个命令前缀：

```powershell
wsl                           # 进默认发行版，落在默认用户家目录
wsl ls -la                    # 不进交互，跑一条命令立刻返回
wsl nmap -sV 1.2.3.4          # 直接把 Linux 工具当 Windows 命令用
wsl -d kali-linux             # 指定发行版（多发行版时用）
wsl -u root                   # 以 root 身份进入（绕过默认用户）
wsl -- ls -la                 # 参数有歧义时用 -- 分隔
```

最后这条很实用：`wsl ls -la` 里的 `-la` 可能被 `wsl.exe` 自己吃掉，加 `--` 就明确"后面全给 Linux"。

### 3.2 开始菜单 / Windows Terminal

开始菜单里有 "Kali Linux" 图标，点开等同第一种方式。装了 Windows Terminal 后可以在下拉菜单里新建 Kali 标签页（`winget install Microsoft.WindowsTerminal`），比老 conhost 好用得多：多标签、UTF-8 正常、复制粘贴顺畅。

### 3.3 从 WSL 里调 Windows 程序

```bash
notepad.exe file.txt          # 用记事本打开（路径自动转换）
explorer.exe .                # 在资源管理器打开当前 Linux 目录
cmd.exe /c dir                # 调 cmd
```

反过来，WSL 里的路径可以直接被 Windows 访问：`\\wsl$\kali-linux\home\xj`（资源管理器地址栏）。

---

## 四、文件系统：两套盘怎么互通

### 4.1 Windows 盘挂到 `/mnt`

```bash
ls /mnt            # c  d  wsl  wslg
ls /mnt/d/mdstudyfile
ls /mnt/c/Users/徐利杰/Downloads
```

自动挂载，双向可读写。点目录名 `.` 开头的不会自动隐藏（Linux 没有隐藏属性）。

### 4.2 Linux 根文件系统在哪

真身是一个虚拟磁盘文件：

```
C:\Users\<用户>\AppData\Local\wsl\{GUID}\ext4.vhdx
```

**不要用 Windows 工具往这个目录里塞文件、不要用第三方分区软件去动它**，容易把 vhdx 搞坏导致整个发行版报废。要传文件走 `/mnt`，或者 `\\wsl$\` 路径。

### 4.3 性能坑：跨盘操作慢 5–10 倍

`/mnt/c`、`/mnt/d` 走的是 9P 协议（Windows 内核代理），每次文件操作都有跨 VM 边界的开销。

- 在 `/mnt/c` 里 `npm install`、`git clone`、编译 C 项目 → 慢到怀疑人生
- **正确做法**：代码放 Linux 家目录（`~/`），做完需要的产物再拷到 `/mnt` 

### 4.4 编码与换行

Windows 写的中文文件（GBK）在 WSL 里 `cat` 会乱码；`.sh` 脚本从 Windows 编辑过来带 CRLF 会让 bash 报 `$'\r': command not found`。

```bash
# 转 LF
sed -i 's/\r$//' script.sh
# 或
dos2unix script.sh
```

反过来，给 Windows 程序读的脚本要转回 CRLF。**用 shell 跑脚本时，优先直接在 Linux 里用 vim/nano 写**，省掉这层麻烦。

---

## 五、初始化配置（装完必做）

刚装好的 Kali WSL 默认**只有 root，没有普通用户**。直接拿 root 跑实验容易一个 `rm -rf` 玩坏自己（没任何拦截），建议先建普通用户。

### 5.1 建普通用户 + 配 sudo

```bash
# 以 root 进入
wsl -u root

useradd -m -s /bin/bash -G sudo xj
passwd xj                       # 输入密码（不回显，看不到星号是正常的）
id xj                           # 确认在 sudo 组
```

验证 sudo 权限：

```bash
sudo -l -U xj
# 应看到 (ALL : ALL) ALL
```

### 5.2 改默认用户（省掉每次 `-u root`）

编辑 `/etc/wsl.conf`：

```ini
[boot]
systemd=true

[user]
default=xj
```

改完**必须重启 WSL 才生效**：

```powershell
wsl --shutdown      # 等价于"关掉整台 Linux 虚拟机"
```

> `wsl --shutdown` 是高频命令：改 `wsl.conf`、改网络模式、改 `.wslconfig`、内存异常飙高，都靠它。它会把**所有**发行版一起关掉，未保存的进程全被杀。

重启后 `wsl` 进去就是 `xj`，`echo $HOME` → `/home/xj`。需要 root 时显式 `wsl -u root`。

### 5.3 换 apt 源（国内必做）

Kali 的源配置在 `/etc/apt/sources.list.d/kali.sources`（新版 deb822 格式，不是老的 `sources.list`）：

```bash
cat /etc/apt/sources.list.d/kali.sources
```
```
Types: deb
URIs: http://http.kali.org/kali/
Suites: kali-last-snapshot
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/kali-archive-keyring.gpg
```

换成阿里云前**先备份**，再写入：

```bash
cp /etc/apt/sources.list.d/kali.sources /etc/apt/sources.list.d/kali.sources.bak

cat > /etc/apt/sources.list.d/kali.sources <<'EOF'
Types: deb
URIs: http://mirrors.aliyun.com/kali/
Suites: kali-rolling
Components: main contrib non-free non-free-firmware
Signed-By: /usr/share/keyrings/kali-archive-keyring.gpg
EOF

apt update
```

**两个要注意的点**：

1. **`Suites` 从 `kali-last-snapshot` 改成了 `kali-rolling`**。last-snapshot 是固定快照（保守、可复现），rolling 跟随最新滚动版本。日常实验用 rolling；要做可复现实验就还原 backup 文件。
2. 阿里云 Kali 镜像只有 `kali-rolling`、`kali-bleeding-edge`、`kali-dev` 等几个 suite，**没有** `kali-last-snapshot`——所以换源时必须同步改 suite，否则 `apt update` 直接 404。

Ubuntu/Debian 的源文件是另一个格式（一行式 `deb http://... noble main restricted`），位置在 `/etc/apt/sources.list`，别搞混。

### 5.4 装常用工具

WSL 的 rootfs 是精简版，连 nmap、gcc 都没有。一次装齐（`--no-install-recommends` 避免拉一堆无用依赖，能省一半体积）：

```bash
sudo apt install -y --no-install-recommends \
  nmap ncat socat tcpdump whois dnsutils \
  gcc g++ make python3-pip python3-venv pipx \
  gobuster dirb sqlmap jq \
  net-tools iputils-ping
```

| 工具 | 用途 |
|---|---|
| nmap | 端口/服务扫描 |
| ncat / socat | 网络连接、端口转发、反弹 shell（Kali 自带 `nc` 是 openbsd 版） |
| tcpdump | 命令行抓包 |
| whois / dig | 域名与 DNS 查询 |
| gcc / g++ / make | 编译 C 程序、写 pwn 题 exp |
| pip3 / pipx | Python 包 |
| gobuster / dirb | 目录爆破 |
| sqlmap | SQL 注入自动化 |
| jq | JSON 处理（调 API 必备） |

### 5.5 pip 的 PEP 668 坑

直接 `pip3 install requests` 会报：

```
error: externally-managed-environment
```

这是 Debian 13 系起的保护机制（禁止 pip 污染系统 Python）。两种解法：

```bash
pip3 install requests --break-system-packages   # 简单粗暴，装进系统 Python
pipx install <工具名>                            # 推荐：自动建隔离 venv 并加进 PATH
```

做项目时更规范的是 `python3 -m venv ~/venv && source ~/venv/bin/activate`。

---

## 六、网络：WSL 和 VMware 的根本差异

这是两者差距最大、也最容易踩坑的地方。

### 6.1 WSL2 默认是 NAT，只有一张网卡

实测数据（同一台机器）：

```
WSL:     eth0 = 172.22.80.234/20   网关 172.22.80.1   DNS 10.255.255.254
Windows: vEthernet (WSL (Hyper-V firewall)) = 172.22.80.1   ← 这就是 WSL 的网关
         WLAN (Intel Wi-Fi 6 AX203) = 10.47.10.28           ← 真实外网出口
VMware:  VMnet8 = 192.168.198.1 (NAT)   VMnet1 = 192.168.242.1 (仅主机)
```

链路是：`eth0 → vEthernet(WSL) → Windows NAT 转换 → WLAN → 路由器`。

那个 `172.22.80.0/20` 网段里**只有 WSL 自己和网关（Windows）两个成员**，不像 VMnet8 是个真的虚拟交换机，能挂多台机器。

### 6.2 能力对照

| 能力 | WSL2（默认 NAT） | VMware |
|---|---|---|
| 网卡数量 | 固定 1 张 | 可加多张 |
| 多网段隔离实验 | ❌ | ✅（VMnet1 + VMnet8 两个网段） |
| 桥接拿局域网真实 IP | ❌ | ✅ |
| 被局域网其他机器访问 | ❌ | ✅（桥接） |
| 从 Windows 访问服务 | ✅ `localhost:端口` 自动转发 | 要确认网段和防火墙 |
| **ARP 扫描 / netdiscover** | ❌ 基本无效 | ✅ |
| 模拟断网 / 换网段 | ❌ | ✅ |
| 抓包（干净流量） | 抓 vEthernet，源地址已被 NAT 改写 | 抓 VMnet，原始流量 |

### 6.3 三条实际影响

**① `arp-scan` / `netdiscover` 在 WSL 里没有意义**

ARP 不跨 NAT 边界。在 WSL 里扫 `172.22.80.0/20`，只能发现网关一台。要扫真实局域网 → 用 VMware Kali。扫远程公网/CTF 目标 → nmap TCP 扫描照样好使。

**② DNS 的坑不同**

WSL 的 `/etc/resolv.conf` 由 Windows 自动生成，内容是 `nameserver 10.255.255.254`（一个指向 Windows 解析器的代理）。没有 dhclient、没有 NetworkManager，所以不会出现"装个软件把 resolv.conf 覆盖掉导致 DNS 挂掉"的事故。

要自己接管 DNS，在 `/etc/wsl.conf` 加：

```ini
[network]
generateResolvConf=false
```

然后手动写 `/etc/resolv.conf`。

**③ 端口转发自动做**

WSL 里起的服务（如 `python3 -m http.server 8000`），Windows 上 `localhost:8000` 直接能访问，不用配转发。这是 NAT 模式的便利；反过来 Windows 的 `10.47.10.28:8000` 局域网访问不到它。

### 6.4 想要"桥接效果"：mirrored 模式

Win11 22H2+ 支持 `mirrored` 网络模式，WSL **直接共享 Windows 的网卡**，拿到和 Windows 一样的 IP（`10.47.10.28`），能看到真实局域网，`arp-scan` 也能用了。

在 `C:\Users\<用户>\.wslconfig` 写：

```ini
[wsl2]
networkingMode=mirrored
```

然后 `wsl --shutdown` 再生效。

代价：失去独立网络环境，WSL 和 Windows 共用 IP 和端口，某些"两个 IP 互相通信"的实验效果消失。需要独立 IP 时改回 NAT。

### 6.5 `.wslconfig` vs `/etc/wsl.conf`

两个文件容易搞混：

| 文件 | 位置 | 管什么 | 生效 | 作用域 |
|---|---|---|---|---|
| `.wslconfig` | `C:\Users\<用户>\` | 虚拟机资源（内存/CPU/交换分区/内核/网络模式） | `wsl --shutdown` | 所有发行版 |
| `wsl.conf` | Linux 内 `/etc/wsl.conf` | 该发行版的 boot/systemd、默认用户、挂载、DNS 行为 | `wsl --shutdown` | 单个发行版 |

限制内存的写法（16 GB 机器建议给 WSL 上限 4–6 GB）：

```ini
# C:\Users\徐利杰\.wslconfig
[wsl2]
memory=6GB
processors=4
swap=2GB
```

---

## 七、常用命令速查

### Windows 侧

| 命令 | 作用 |
|---|---|
| `wsl` | 进入默认发行版 |
| `wsl -l -v` | 列出所有发行版 + 状态 + 版本 |
| `wsl --list --online` | 列出可安装的发行版 |
| `wsl --install -d <名字>` | 安装指定发行版 |
| `wsl -d <名字>` | 进入指定发行版 |
| `wsl -u root` | 以 root 进入 |
| `wsl --shutdown` | **关掉所有 WSL 虚拟机**（改配置后必用） |
| `wsl --terminate <名字>` | 只关某一个发行版 |
| `wsl --set-default-version 2` | 新装发行版默认用 WSL2 |
| `wsl --export <名字> D:\backup.tar` | 备份整个发行版 |
| `wsl --import <名字> D:\dir backup.tar` | 从备份恢复 |
| `wsl --unregister <名字>` | **彻底删除**（数据全没，慎用） |
| `wsl --update` | 更新 WSL 本体 |
| `wsl --version` | 看 WSL/内核/WSLg 版本 |

### Linux 侧（和普通 Linux 完全一致）

| 命令 | 作用 |
|---|---|
| `whoami` / `id` | 当前用户 / 完整身份 |
| `ip -4 a` | 查看 IP（WSL 里 `ifconfig` 需装 net-tools） |
| `ip route` | 看网关 |
| `df -h /` | 磁盘用量 |
| `sudo -l` | 当前用户能 sudo 哪些命令 |
| `cat /etc/wsl.conf` | 看发行版配置 |

---

## 八、踩坑清单

| 现象 | 原因 | 解决 |
|---|---|---|
| `wsl --version` 有输出但进不去 | 虚拟机平台组件未生效 | **重启电脑**，再看 `wsl --status` |
| `WSL2 无法启动，因为此计算机上未启用虚拟化` | 同上 / BIOS 虚拟化没开 | 重启；或 `dism /online /enable-feature /featurename:VirtualMachinePlatform /all` 后重启 |
| `wsl --install` 报 `WININET_E_TIMEOUT`，退出码却是 0 | 拉 GitHub 分发列表超时 | 重试；别信退出码，用 `wsl -l -v` 验证 |
| 装完 `wsl -l -v` 为空 | 用了 `--no-launch`，或只装了主体 | 再跑一次 `wsl --install -d <名字>` |
| 改 `wsl.conf` 不生效 | 没重启 WSL | `wsl --shutdown` |
| `pip3 install` 报 `externally-managed-environment` | PEP 668 保护 | 加 `--break-system-packages` 或用 pipx |
| `.sh` 报 `$'\r': command not found` | Windows 编辑产生 CRLF | `sed -i 's/\r$//' file.sh` |
| `/mnt/c` 里跑 npm/git 极慢 | 9P 协议跨 VM 开销 | 代码放 `~/`，产物再拷出去 |
| 换源后 `apt update` 404 | 阿里云没有 `kali-last-snapshot` | suite 改成 `kali-rolling` |
| 内存占用飙高不释放 | WSL 虚拟机常驻 | `wsl --shutdown`；或 `.wslconfig` 限 `memory=6GB` |
| `arp-scan` 扫不到任何设备 | NAT 边界挡住 ARP | 换 VMware，或启用 mirrored 模式 |
| 默认用户还是 root | `[user] default=` 未生效 | 检查 `wsl.conf` 语法，`wsl --shutdown` 后重进 |

---

## 九、和现有环境的定位

本机同时有 **VMware Kali** 和 **WSL Kali**，两者互补而非替代：

| 场景 | 用哪个 |
|---|---|
| 跑 nmap 扫公网 / CTF 目标 | WSL（秒启、不占内存） |
| 写 exploit、编译 payload、跑 Python 脚本 | WSL |
| 内网横向、两个网段通信 | VMware（VMnet1/8 组网） |
| 当服务器被局域网访问、做钓鱼/中间人实验 | VMware 桥接 |
| ARP 扫描、二层发现 | VMware |
| 抓包分析（干净原始流量） | VMware 抓 VMnet |

补充：WSL2 和 VMware 的兼容性——VMware 15.5 之前版本与 Hyper-V/WSL2 不能共存（开 WSL2 后 VMware 报"不支持嵌套虚拟化"），15.5+ 已支持共存，可同时运行。

参考：WSL 网络排查思路与 VMware 类似，都走"宿主机 → 虚拟网络层 → VM 内部"三层排除，详见 `Linux基础-虚拟机网络排查.md`。
