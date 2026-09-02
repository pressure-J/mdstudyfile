# Linux 基础：常用命令与文件系统

> 来源：Linux操作系统课程实验《Linux操作系统基础命令》（本人实验报告 docx 整理，2025-2026 第一学期，指导老师陶小结）
> 定位：一切渗透、运维操作都建立在命令行之上；面试必考基础，不会 ls/cd/权限/挂载等于不会 Linux。本文按"用户与系统 → 磁盘 → 目录 → 权限 → 链接 → 压缩"主线补全每个命令的完整用法

---

## 一、概述：Linux 的命令行哲学

**一句话原理**：Linux 遵循"**一切皆文件**"的设计思想——普通文件、目录、硬盘、键盘、网卡、进程，统统被抽象成文件，通过统一的命令进行操作。而"命令行"就是操作这些文件的工具箱：**每个命令是一个小程序，专注做一件事；通过管道 `|`、重定向 `>`、通配符把小程序组合起来，就能完成任意复杂的任务**。

文件系统则规定了这些文件怎么摆放。Linux 采用 FHS（文件系统层次标准），几个必须记住的顶级目录：

| 目录 | 存放内容 |
|---|---|
| `/` | 根目录，一切文件的起点 |
| `/bin`、`/sbin` | 系统最基本命令（ls、cat）与系统管理命令（fdisk） |
| `/etc` | 系统配置文件（passwd、fstab、yum.repos.d） |
| `/home` | 普通用户的家目录（`/home/用户名`，简写 `~`） |
| `/root` | root 用户的家目录 |
| `/dev` | 设备文件（`/dev/sda` 硬盘、`/dev/sda1` 分区） |
| `/mnt`、`/media` | 挂载点（临时挂载 U 盘、光盘） |
| `/tmp` | 临时文件 |
| `/var` | 日志、缓存等易变数据（`/var/log`） |

理解这两件事（一切皆文件 + 目录结构），后面所有命令就只是"在哪个目录对哪个文件做什么操作"。

---

## 二、核心命令速查

### 1. 用户与系统命令

| 命令 | 作用 | 常用形式 |
|---|---|---|
| `su` | 切换用户（默认切到 root，需要目标用户密码） | `su`、`su - root`（`-` 加载目标用户完整环境） |
| `sudo` | 以 root 权限执行单条命令（用自己密码授权） | `sudo apt install xxx` |
| `whoami` | 显示当前用户 | `whoami` |
| `ps` | 查看进程快照 | `ps -ef`（全格式）、`ps aux`（含 CPU/内存占比） |
| `kill` | 给进程发信号 | `kill -l`（列出所有信号）、`kill -9 PID`（强杀）、`kill PID`（默认 TERM 温和终止） |
| `df` | 查看磁盘整体使用情况 | `df -h`（人类可读 MB/GB） |
| `du` | 查看某个目录/文件占用空间 | `du -sh /var/log`（汇总单目录） |
| `uname` | 查看系统内核信息 | `uname -a` |

> 实验里的现象："输入 kill -l 出现了可用信号"——`kill -l` 列出的就是 64 个标准信号，最常用的三个：`SIGTERM(15)` 默认温和终止、`SIGKILL(9)` 强制杀死、`SIGHUP(1)` 挂断（常用来让守护进程重读配置）。

### 2. 目录与文件操作

| 命令 | 作用 | 例子 |
|---|---|---|
| `pwd` | 显示当前所在路径 | `pwd` |
| `ls` | 列出目录内容 | `ls -l`（长格式）、`ls -a`（含隐藏文件）、`ls -lh`（人性化大小） |
| `cd` | 切换目录 | `cd /etc`、`cd ..`（上一级）、`cd ~`（家目录） |
| `mkdir` | 创建目录 | `mkdir -p a/b/c`（递归创建） |
| `rmdir` | 删除**空**目录 | `rmdir emptydir` |
| `rm` | 删除文件或目录 | `rm -rf dir`（递归+强制，**极度危险慎用**） |
| `touch` | 创建空文件/更新时间戳 | `touch test.c` |
| `cp` | 复制 | `cp -r 源目录 目标`（复制目录必须 `-r`） |
| `mv` | 移动/剪切/重命名 | `mv a.txt b.txt`（重命名）、`mv file /tmp/` |
| `find` | 按条件查找文件 | `find / -name "*.conf"`、`find /home -user myth` |
| `cat` | 查看文件内容 | `cat /etc/passwd` |

### 3. 磁盘管理全流程（实验核心）

磁盘从"物理盘"到"能用"要过三关：**分区 → 格式化 → 挂载**。

| 命令 | 作用 | 例子 |
|---|---|---|
| `fdisk` | 分区工具 | `fdisk /dev/sdb`（进入交互界面，`n` 新建分区、`w` 保存） |
| `mkfs` | 格式化（建立文件系统） | `mkfs.ext4 /dev/sdb1` |
| `mount` | 挂载（把分区接到某个目录上） | `mount /dev/sdb1 /mnt/data` |
| `umount` | 卸载 | `umount /mnt/data` |
| `df` | 查看已挂载磁盘用量 | `df -h` |
| `du` | 查看目录占用 | `du -sh *` |

> **为什么要有"挂载"**：磁盘分区本身只是一块"空白空间"，Linux 必须把它接到目录树的某个位置（挂载点）才能读写。挂载是临时性的，**重启后会失效**；要永久生效需写入 `/etc/fstab` 配置文件。

### 4. 权限管理

```bash
chmod 权限 文件       # 修改权限 rwx
chown 用户:组 文件     # 修改文件所属用户和组
chgrp 组 文件          # 只改所属组
```

权限的三位组合：`-rwxr-xr--` 分成三段——**所有者 / 所属组 / 其他人**，每段 r=读(4)、w=写(2)、x=执行(1)。

| 数字 | 含义 |
|---|---|
| `chmod 755 file` | 所有者 rwx，组 r-x，其他 r-x（脚本/程序常用） |
| `chmod 644 file` | 所有者 rw-，组 r--，其他 r--（普通文件默认） |
| `chmod 777 file` | 所有人全部权限（**危险，慎用**） |

`chown myth:myth test.txt` 把文件所有者改成 myth、组改成 myth。

### 5. 链接：ln（软链接 vs 硬链接，高频考点）

```bash
ln 源文件 链接名          # 硬链接
ln -s 源文件 链接名       # 软链接（符号链接）
```

| 特性 | 硬链接 | 软链接（符号链接） |
|---|---|---|
| 本质 | 同一个 inode 的另一个名字，两个名字指向同一份数据 | 一个记录目标路径的特殊文件（相当于快捷方式） |
| 删原文件 | 链接仍可用（数据还在） | 链接失效（变成红色断链） |
| 跨文件系统 | **不可以** | 可以 |
| 对目录 | 不可以 | 可以 |
| 命令形式 | `ln a b` | `ln -s a b` |

面试一句话：**硬链接共享 inode、删源文件还能用；软链接是指向路径的快捷方式、源没了就失效**。

### 6. 压缩打包

```bash
tar -czvf 包名.tar.gz 目录    # 打包并用 gzip 压缩（c=创建 z=gzip v=显示 f=文件）
tar -xzvf 包名.tar.gz         # 解压
tar -tzvf 包名.tar.gz         # 只查看不解压
zip -r 包.zip 目录             # zip 压缩
unzip 包.zip                   # zip 解压
```

> Linux 下最常见的 `.tar.gz` = tar 完成"打包" + gzip 完成"压缩"两步；`.tar` 本身只打包不压缩。

---

## 三、实操流程（按实验主线走一遍）

### 任务 1：用户切换与进程管理
```bash
whoami                # 当前普通用户
su                    # 输入 root 密码切换为 root
ps -ef | head -20     # 查看进程列表（结合管道只显示前 20 行）
kill -l               # 查看可用信号，理解 9/15 的区别
kill -9 <PID>         # 强制结束不听话的进程
df -h                 # 看磁盘整体用量
du -sh ~              # 看自己家目录占了多少
```

### 任务 2：给系统加一块新硬盘（从裸盘到使用）
```bash
# 1. 虚拟化软件里给虚拟机"添加硬盘"（如 VMware 添加 10G SCSI 盘）
lsblk                 # 发现多了 /dev/sdb（原系统盘是 sda）
fdisk /dev/sdb        # 交互式分区：n → p → 回车默认 → w 保存，生成 /dev/sdb1
mkfs.ext4 /dev/sdb1   # 格式化 sdb1 为 ext4 文件系统
mkdir /mnt/data       # 创建挂载点
mount /dev/sdb1 /mnt/data   # 挂载
cd /mnt/data && touch hello.txt && ls   # 在"新盘"上创建文件并查看
cd .. && umount /mnt/data      # 用完卸载（文件不会丢，只是暂时不可见）
df -h                 # df 验证：挂载时能看到 sdb1，卸载后消失
du -sh /mnt/data      # 查看目录占用
```

> 实验报告里"创建一个 initrd 并挂载"是同款操作——`mount` 把某个设备/文件系统接到目录，`umount` 摘除，`df/du` 一宏观一微观地检查空间。

### 任务 3：目录与文件操作
```bash
mkdir projects && cd projects    # 建目录进入
touch a.c b.c                    # 建两个空文件
cp a.c a.c.bak                   # 复制
mkdir backup && cp -r a.c.bak backup/   # 复制到目录（注意 -r）
mv a.c.bak renamed.c             # 移动=重命名
find /home -name "*.c"           # 全盘找自己写的 C 源码
ln -s /etc/passwd mypasswd       # 建软链接，cat mypasswd 即可读
cd .. && rmdir projects          # 删除空目录（有内容时用 rm -rf）
```

### 任务 4：权限实验
```bash
chmod 755 script.sh      # 让脚本可执行
chmod 644 file.txt       # 恢复普通只读权限
chown myth:myth file.txt # 改变属主属组
ls -l                    # 查看权限位变化
# 对比：所有者 rwx、组 r-x、其他 r-x，逐位对应 r=4 w=2 x=1
```

### 任务 5：压缩打包
```bash
tar -czvf mybackup.tar.gz /etc          # 把配置目录打包压缩
tar -tzvf mybackup.tar.gz | head        # 查看包内容
tar -xzvf mybackup.tar.gz -C /tmp/restore # 解压到指定目录
```

---

## 四、常见问题与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| `umount` 报 `device is busy` | 还有进程在使用该挂载点（如 shell 的当前目录在里面） | `cd` 离开该目录后再卸载；`lsof /mnt/data` 看占用进程 |
| 新加的磁盘在系统里看不到内容 | 只加了盘没走完"分区→格式化→挂载"三关 | `lsblk` 检查；分区用 `fdisk`，格式化 `mkfs.ext4`，再 `mount` |
| 挂载的分区重启后又消失了 | mount 是临时挂载 | 把挂载项写入 `/etc/fstab`：`/dev/sdb1 /mnt/data ext4 defaults 0 0` |
| 硬链接创建报错 | 试图跨文件系统或对目录建硬链接 | 换软链接 `ln -s` |
| `rm -rf` 删错东西 | 手滑/路径写错——**这是 Linux 最经典的翻车现场** | 无解，养成习惯：删除前先 `ls` 确认、用 `rm -i` 交互确认、重要目录先备份 |
| `find /` 权限报错刷屏 | 普通用户无权限访问其他用户目录 | 用 `find / -name xxx 2>/dev/null` 丢弃错误输出 |
| `kill -9` 杀不掉进程 | 进程处于不可中断的 D 状态（如等待 IO） | 等 IO 完成或重启系统；平时优先 `kill` / `kill -15` |

---

## 五、面试速答卡

- **Linux 的设计哲学**：一切皆文件 + 短小命令通过管道/重定向组合
- **文件权限 rwx 对应数字**：r=4、w=2、x=1，`chmod 755`=所有者全权限、组和其他人只读+执行
- **硬链接和软链接区别**：硬链接共享 inode 删源文件不影响；软链接是指向路径的快捷方式，源文件消失即失效；软链接可跨文件系统
- **磁盘使用四步骤**：分区（fdisk）→ 格式化（mkfs.ext4）→ 挂载（mount）→ 使用；写 /etc/fstab 才永久生效
- **df 和 du 的区别**：df 看整个文件系统的用量（宏观、含已删但被占用的空间），du 看具体目录文件占用（微观）
- **kill 和 kill -9 区别**：kill 默认发 SIGTERM(15) 让程序自己清理退出；kill -9 发 SIGKILL 直接强杀，可能丢数据
- **tar -czvf 各字母含义**：c=创建、z=gzip 压缩、v=显示过程、f=指定文件名；解压为 -xzvf
- **为什么挂载点必须是空目录**：mount 会把原目录内容暂时隐藏，非空目录挂载后原文件不可见（数据不丢）