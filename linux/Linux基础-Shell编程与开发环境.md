# Linux 基础：Shell 编程与开发环境

> 来源：Linux操作系统课程实验《配置Linux编程开发环境（VSCode、Docker、Git）》（老师版 PDF 28 页，讲师 myth）＋《Linux编程环境、网络配置、Shell编程与正则表达式》（本人报告 docx）＋《Tmux使用》（老师版 PDF）
> 定位：从"会用 Linux"到"能用 Linux 干活"的跨越。写脚本自动化、Docker 快速部署靶机（如 DVWA）、Git 版本管理是网安学习和工作的日常；Shell 与正则更是渗透测试、日志分析的看家本领

---

## 一、概述：一条完整的 Linux 开发工作流

在 Linux 上开发，完整链条是：**编辑器写代码（Vim/VSCode）→ 编译器构建（GCC）→ 调试器排错（GDB）→ 构建工具管理多文件（Make）→ 容器化交付（Docker）→ 版本控制协作（Git）→ 终端复用提升效率（Tmux）→ 脚本自动化（Shell）**。

- **Shell（bash）** 是人与内核交互的解释器，把命令"翻译"给系统执行。**Shell 脚本 = 把一串命令 + 判断 + 循环写成文件**，实现自动化（批量部署、定时任务、提权 payload 都得靠它）。
- **正则表达式** 是"文本的模式描述语言"，配合 grep/sed/awk 完成搜索、替换、提取——分析日志、过滤流量包靠这套组合拳。
- **Docker** 把应用和依赖打包成镜像，一键跑成容器；网安用它三分钟拉起 DVWA、靶场环境。
- **Tmux** 解决"关窗口进程就死"的问题：会话与窗口解绑，SSH 断了重连也不丢任务。

---

## 二、核心知识

### 1. Vim 三模式（背熟切换键）

| 模式 | 作用 | 进入方式 | 常用命令 |
|---|---|---|---|
| 命令模式 | 移动光标、删除、复制 | 启动默认 / Esc | `dd` 删行、`yy` 复制、`p` 粘贴、`/xxx` 搜索 |
| 插入模式 | 编辑输入 | 命令模式按 `i` | 随便打字，Esc 退出 |
| 底行模式 | 保存退出、替换 | 命令模式按 `:` | `wq` 保存退出、`q!` 不保存退出、`%s/old/new/g` 全局替换 |

### 2. GCC 编译流程（四步，面试常问）

```bash
gcc test.c -o test    # 一步到位：编译 + 链接生成可执行文件 test
./test                # 运行
```

编译内部实际分四步：**预处理（去掉注释、展开头文件）→ 编译（C 转汇编 .s）→ 汇编（汇编转机器码 .o）→ 链接（把库合并成可执行文件）**。分步执行：

```bash
gcc -E test.c -o test.i        # 1 预处理
gcc -S test.i -o test.s        # 2 编译成汇编
gcc -c test.s -o test.o        # 3 汇编成机器码目标文件
gcc test.o -o test             # 4 链接成可执行文件
gcc -g test.c -o test          # 加 -g 生成调试信息（GDB 必需）
gcc -Wall test.c -o test       # 打开所有警告，养成好习惯
```

### 3. GDB 调试（断点→运行→单步→查变量）

```bash
gcc -g test.c -o test    # 必须带 -g 编译
gdb test                 # 进入调试器
(gdb) list               # 查看源码
(gdb) break 5            # 第 5 行设断点（break main 也行）
(gdb) run                # 运行到断点
(gdb) next               # 单步执行（不进入函数）
(gdb) step               # 单步（进入函数内部）
(gdb) print n            # 查看变量 n 的值
(gdb) quit               # 退出
```

### 4. Make 与 Makefile（多文件自动化编译）

Makefile 的规则格式：`目标: 依赖` + 下一行 Tab 缩进的命令——**依赖比目标新才执行命令**，实现了"只重新编译改过的文件"。

```makefile
# 例：两个源文件 a.c b.c 编译成 app
app: a.o b.o
		gcc a.o b.o -o app        # 注意：必须是 Tab 缩进，不能是空格
a.o: a.c
		gcc -c a.c
b.o: b.c
		gcc -c b.c
clean:
		rm -f *.o app
```

```bash
make          # 按依赖自动编译，缺哪个编哪个
make clean    # 执行 clean 目标清理
```

### 5. Shell 编程基础

**脚本三部曲**：编辑 → 加执行权限 → 运行：

```bash
vim test.sh                       # 第一行写 #!/bin/bash（声明用 bash 解释）
chmod +x test.sh                  # 加执行权限（见权限篇）
./test.sh                         # 当前目录运行
bash test.sh                      # 或用解释器直接跑（无需执行权限）
```

**变量与参数**：

```bash
name="alice"                      # 定义变量（= 两边不能有空格）
echo $name                        # $ 引用变量
echo ${name}abc                   # {} 隔离变量边界
echo $0 $1 $2                     # $0=脚本名 $1=第1个参数 $2=第2个参数
echo $#                           # 参数个数
echo $*                           # 所有参数
export PATH=$PATH:/opt/mybin      # 环境变量：把目录加进 PATH 全局搜索路径
read -p "输入:" input             # 从键盘读输入
echo $?                           # 上一条命令的返回值（0=成功，非0=失败）
```

**运算符与判断**（`expr` 用于算术，注意空格）：

```bash
expr 5 + 3                        # 算术：+ - \* / %（* 要转义）
[ 5 -gt 3 ] && echo yes           # test 简写 []，-gt 大于
[ "a" = "a" ] && echo equal       # 字符串相等
[ -d /tmp ] && echo "是目录"      # -d 判断目录、-f 判断文件、-e 判断存在
```

**流程控制四兄弟**：

```bash
# if-then
if [ $1 -gt 10 ]; then echo "大"; else echo "小"; fi

# case（多分支）
case $1 in
  start) echo "启动";;
  stop) echo "停止";;
  *) echo "未知";;
esac

# for 循环
for i in 1 2 3; do echo $i; done
for f in *.txt; do echo $f; done

# while 循环
n=1
while [ $n -le 5 ]; do echo $n; n=$((n+1)); done

# 函数
say_hello() { echo "Hello, $1"; }
say_hello world
```

**注释**：`#` 开头是注释（`#!` 是声明解释器的特殊行，不算普通注释）。

### 6. 正则表达式与文本三剑客

**元字符速记表**：

| 元字符 | 含义 | 反义 |
|---|---|---|
| `\w` | 字母、数字、汉字、下划线 | `\W` |
| `\b` | 单词边界（开头/结尾） | `\B` |
| `\s` | 空白符 | `\S` |
| `\d` | 数字 | `\D` |
| `^` / `$` | 行首 / 行尾 | — |
| `*` / `?` | 前一个字符 0~多次 / 0~1 次 | — |
| `{n}` | 前一个字符恰好 n 次 | — |
| `[a-z]` | 字符簇：任意小写字母 | — |

**文本三剑客**：

```bash
grep -E "^\d{3}" /var/log/xxx.log   # 按正则过滤行（ls 不支持正则，配合管道把输出交给 grep）
sed 's/old/new/g' file.txt          # 全局替换（s=替换，g=全部）
sed '/^#/d' file.txt                # 删除注释行（d=删除）
sed '2a 新行' file.txt              # 在第 2 行后追加（a=追加）
sed -n '5,10p' file.txt             # 只显示第 5-10 行（p=打印）
awk '{print $1}' file.txt           # 按空白拆列，打印第 1 列
awk '$3 > 50 {print $1}' file.txt   # 带逻辑条件：第3列>50 才打印第1列
```

> 经典组合拳：`ps aux | grep mysql | grep -v grep` 找进程；`cat access.log | awk '{print $1}' | sort | uniq -c | sort -rn` 统计访问最多的 IP。

### 7. Tmux 终端复用（最简工作流）

```bash
sudo apt install tmux               # 安装
tmux new -s mywork                  # 新建命名会话
# 会话里跑长任务...
Ctrl+b d                            # 分离（任务继续后台跑）
tmux ls                             # 列出会话
tmux attach -t mywork               # 重新接入，任务还在！
tmux kill-session -t mywork         # 杀死会话
```

快捷键速记（前缀都是 `Ctrl+b` 再按）：`d` 分离、`%` 左右分窗格、`"` 上下分窗格、`c` 新建窗口、`n/p` 切换窗口、`x` 关闭窗格、`z` 窗格全屏、`?` 帮助。**核心价值：SSH 断了、窗口关了，任务还在后台跑，重连即恢复**。

### 8. Docker：镜像与容器（类=实例的关系）

**镜像（Image）是只读模板（相当于"类"），容器（Container）是镜像运行时的实例（相当于"对象"）**，同一个镜像可生成多个容器。镜像拉取/构建 → 容器运行/停止，全流程命令：

| 类别 | 命令 | 作用 |
|---|---|---|
| 镜像 | `docker pull ubuntu:22.04` | 从仓库（默认 Docker Hub）拉镜像 |
| | `docker image ls` | 列出本地镜像 |
| | `docker rmi 镜像ID/名` | 删除镜像 |
| | `docker build -t nginx:v3 .` | 按 Dockerfile 构建镜像 |
| | `docker save alpine -o alpine.tar` / `docker load -i alpine.tar` | 镜像导出/导入（换机器迁移） |
| 容器 | `docker run -it --rm ubuntu:22.04 bash` | 交互式启动容器（-i 交互、-t 终端、--rm 退出即删） |
| | `docker run -d -p 80:80 nginx:alpine` | 后台运行 + 端口映射（宿主机80→容器80） |
| | `docker ps` / `docker ps -a` | 查看运行中 / 所有容器 |
| | `docker stop 容器ID` / `docker start 容器ID` | 温和停止 / 重启已停止容器 |
| | `docker kill 容器ID` | 直接 SIGKILL 强杀 |
| | `docker rm 容器ID` | 删除容器（停着的也要占空间，记得删） |
| | `docker exec -it 容器ID bash` | 进入运行中容器（推荐；attach 退出会把容器也停掉） |
| | `docker logs 容器ID` | 查看容器输出日志 |

**Docker 与虚拟机的区别（高频面试题）**：虚拟机虚拟的是**硬件**（重量级，自带完整 OS）；Docker 虚拟的是**操作系统层**，容器与宿主机**共享内核**，只隔离进程/文件/网络命名空间——所以容器秒级启动、性能开销极低（几 MB vs 几 GB）。

**端口映射**：容器内应用要对外访问必须映射端口：`-p 宿主机端口:容器端口`（如 `-p 8000:80`）。网安常用来一键拉起靶场：`docker run -d -p 8080:80 vulnerables/web-dvwa`。

### 9. Git 版本控制（提交→推送闭环）

```bash
git config --global user.name "你的名字"       # 首次配置身份
git config --global user.email "你的邮箱"
ssh-keygen -t rsa -b 4096 -C "邮箱"            # 生成密钥，公钥(id_rsa.pub)贴到 GitHub → Settings → SSH Keys

git clone git@github.com:用户名/仓库名.git       # 克隆远程仓库
cd 仓库 && 写代码
git add .                            # 暂存所有改动
git commit -m "提交说明"              # 提交到本地
git push origin main                 # 推送到远程
```

> 面试小知识：`git add` 把改动放进**暂存区**，`commit` 固化到本地历史，`push` 才上远程——三者是三个不同区域。网络差导致 push 失败时，可把 git 端口从 22 改用 443（`ssh -T -p 443 git@ssh.github.com`）。

### 10. VSCode 远程开发（详见安装篇，这里补插件环节）

Remote-SSH 连上后，**插件要装到远程服务器上**（点插件右下角"SSH: 主机名"标识）；强烈推荐 **Code Runner** 插件，写代码后一键编译运行。经典组合：远程写好 `test.c` → 终端 `gcc test.c -o test && ./test`，或用 Code Runner 直接跑。

---

## 三、实操流程（老师版 PDF 主线）

### 任务 1：VSCode 远程开发闭环
1. 确保 SSH 服务已启动、已配静态 IP（见安装篇）。
2. VSCode 装 Remote-SSH → 连接 → 在远程打开 `/home/用户名` 作为工作目录（规范习惯）。
3. 远程安装 Python / C/C++ 插件 + Code Runner。
4. 新建 `test.c` 写 fork 小程序 → Ctrl+Shift+` 打开远程终端 → `gcc test.c -o test && ./test` 验证编译运行链路通畅。

### 任务 2：Docker 安装（Ubuntu docker-ce 版）
```bash
sudo apt update -y
sudo apt install ca-certificates curl -y
sudo install -m 0755 -d /etc/apt/keyrings
# 下载官方 GPG 密钥（网络差会报 curl: (35) SSL connect reset，改用阿里云）
sudo curl -fsSL https://mirrors.aliyun.com/docker-ce/linux/ubuntu/gpg \
    -o /etc/apt/keyrings/docker.asc
sudo chmod a+r /etc/apt/keyrings/docker.asc
# 写入软件源（一行 exec；若报 Malformed entry 说明 docker.list 格式错，vim 改回单行）
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://mirrors.aliyun.com/docker-ce/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update -y
sudo apt install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
# 启动 + 开机自启 + 免 sudo（加 docker 组）
sudo systemctl start docker && sudo systemctl enable docker
sudo usermod -aG docker $USER && newgrp docker
docker --version        # 验证
```

> 备选方案：嫌 docker-ce 麻烦可直接 `sudo apt install docker.io`，Ubuntu/Kali/Debian 通吃（Debian 官方维护版）。Kali 装 Docker 走官网 Debian 教程。

### 任务 3：拉镜像、跑容器、配加速
```bash
docker run hello-world                        # 测试：能打印 Hello from Docker 即成功
docker pull ubuntu:22.04                      # 拉镜像
docker run -it --rm ubuntu:22.04 bash         # 进容器执行 cat /etc/os-release 看版本
```

**拉取超时（context deadline exceeded）→ 配国内镜像加速**：

```bash
sudo vim /etc/docker/daemon.json              # 写入：
# { "registry-mirrors": ["https://docker.nju.edu.cn","https://docker.m.daocloud.io",
#   "https://mirror.baidubce.com","https://hub-mirror.c.163.com"] }
sudo systemctl daemon-reload && sudo systemctl restart docker
docker run hello-world                        # 再试
```

进阶玩法：`docker build -t nginx:v3 .` 用 Dockerfile 定制镜像；`docker run -d -p 8000:80 wordpress` 式端口映射；`docker compose up -d` 一个 yml 文件拉起 WordPress+MySQL 多容器（网安可换成 LNMP 或 DVWA 靶场）。

### 任务 4：Git 从零推到 GitHub
注册 GitHub → 装 git → 配置 name/email → `ssh-keygen` 并把公钥贴进 GitHub → 网页建仓库 → `git clone` → 写文件 → `add` → `commit` → `push` → 网页刷新看到代码。选做：`username.github.io` 仓库 + GitHub Pages 免费托管个人静态网页；Hexo（`npm install hexo-cli -g` → `hexo init Myblog` → `hexo generate` → `hexo deploy`）搭博客。

### 任务 5：写一个实战 Shell 脚本（分词库：备份）
```bash
#!/bin/bash
# 备份脚本：把 /etc 打包并带时间戳
backup_dir="/home/$USER/backups"
mkdir -p $backup_dir
tar -czf $backup_dir/etc_$(date +%Y%m%d).tar.gz /etc 2>/dev/null
if [ $? -eq 0 ]; then
    echo "备份成功: $backup_dir"
else
    echo "备份失败"
fi
```

### 任务 6：Tmux 长任务工作流
SSH 登录 → `tmux new -s scan` → 在会话里跑长时间扫描/编译 → `Ctrl+b d` 分离 → 断网重连 → `tmux attach -t scan` 任务完好无损。

---

## 四、常见问题与排查

| 现象 | 原因 | 解决 |
|---|---|---|
| docker 安装时 `curl: (35) SSL connect reset` | download.docker.com 连接被重置 | GPG 密钥改用 `mirrors.aliyun.com/docker-ce` 下载 |
| apt 报 `E: Malformed entry ... docker.list` | 软件源文件格式错误 | vim 检查，改成单行、各字段空格分隔 |
| `docker run` 提示 `context deadline exceeded` | 连不上 Docker Hub | 配 /etc/docker/daemon.json 加速镜像源并重启 docker |
| docker 命令要加 sudo 很烦 | 用户不在 docker 组 | `sudo usermod -aG docker $USER` + `newgrp docker` 重新登录 |
| gcc 编译报 `fatal error: xxx.h: No such file` | 缺头文件（开发包） | `apt install build-essential`；缺库则装对应 `-dev` 包 |
| git push 失败（22 端口被墙） | 网络环境问题 | 用 https 地址 clone；或把 SSH 端口改 443 连接 ssh.github.com |
| VSCode 连不上报"过程试图写入的管道不存在" | 本地 .ssh 权限问题 | 见安装篇九步法；仍不行删 `~/.vscode-server` 重装 |
| 脚本运行报 `bash: ./test.sh: Permission denied` | 没加执行权限 | `chmod +x test.sh` 或 `bash test.sh` 运行 |
| 脚本里 `if [ ]` 报错 | 中括号两边必须有空格、变量要加引号 | `[ "$1" = "a" ]` 规范写法 |

---

## 五、面试速答卡

- **GCC 编译四步**：预处理 → 编译（C→汇编）→ 汇编（→机器码）→ 链接（→可执行文件）；加 `-g` 才能用 GDB
- **GDB 核心流程**：`gcc -g` → `break` 断点 → `run` → `next/step` 单步 → `print` 查变量
- **Makefile 规则三要素**：目标、依赖、Tab 缩进的命令；依赖新于目标才重新执行
- **Shell 脚本 `$?` 是什么**：上一条命令的退出码，0 成功非 0 失败，脚本里做错误判断神器
- **正则 `^` `$` `\d` `\w` `[a-z]` 各指什么**：行首、行尾、数字、字母数字下划线、小写字母簇
- **grep/sed/awk 分工**：grep 过滤行、sed 流式替换删除、awk 按列提取统计
- **Docker 镜像与容器区别**：镜像=只读模板（类），容器=运行实例（对象）；同一镜像可生成多个容器
- **Docker 为什么比虚拟机轻**：容器共享宿主机内核，只隔离用户态；虚拟机虚拟整套硬件和 OS
- **Tmux 解决什么问题**：会话与窗口解绑，SSH 断开任务不丢，重连 `tmux attach` 恢复现场
- **Git 三区**：工作区 → add 暂存区 → commit 本地仓库 → push 远程仓库