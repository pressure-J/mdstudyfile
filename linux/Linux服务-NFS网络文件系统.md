# Linux 服务：NFS 网络文件系统

> 来源：课程实验（Linux操作系统，CentOS 8.3，2025-2026 第一学期），老师版PDF为底料
> 定位：Linux 服务器之间的文件共享标配（samba 负责跨 Windows，NFS 负责 Linux 内部）。运维中用于共享 home 目录、无盘工作站、集群共享存储；安全角度上 NFS 的 root_squash/export 权限配置错误是高危漏洞（越权读写、root 提权），应急响应中常见后门场景。

---

## 一、概念与原理

**NFS（Network File System，网络文件系统）**：让 Linux 客户端像访问本地磁盘一样访问远程服务器上的文件系统，本地工作站省磁盘空间、home 目录全网可用、光驱等存储设备可被多机共享。

**NFS 与 RPC 的关系（核心原理）**：
- 大部分网络服务端口固定，但 **NFS 端口不固定**——它由文件传输、身份验证等多个功能组成，每个功能服务时随机占用一个小于 1024 的端口；
- 因此需要 **RPC（远程进程调用）** 服务做"端口中介"，RPC 固定工作在 **111 端口**。

**工作流程（5 步）**：
1. NFS 启动时自动选择工作端口（如 1011），并向 111 端口的 RPC 汇报登记；
2. 客户端要访问 NFS，先向 RPC（111）查询"NFS 现在工作在哪个端口"；
3. RPC 回答：工作在 1011 端口；
4. 客户端直接访问 NFS 服务器的 1011 端口请求服务；
5. NFS 经过权限认证，允许客户端访问数据。

**守护进程组成（前 3 个必需）**：
| 进程 | 作用 |
|---|---|
| rpc.nfsd | 检查客户端登录权限，处理 NFS 请求 |
| rpc.mountd | 管理 NFS 文件系统（挂载管理） |
| rpcbind | 端口映射（111） |
| rpc.locked / rpc.stated | 文件锁定与崩溃恢复（可选） |
| rpc.quotad | NFS 与磁盘配额接口（可选） |

---

## 二、环境准备与安装

实验拓扑：Server1（CentOS 8.3，192.168.137.4）为 NFS 服务器；Client1（192.168.137.2，可为 Ubuntu/Kali）为客户端。

```bash
# 服务器端
sudo vim /etc/hosts        # 加入：192.168.137.4 Server1 / 192.168.137.2 Client1
sudo dnf install rpcbind nfs-utils -y        # 两个软件包缺一不可
sudo rpm -qa | grep rpcbind && sudo rpm -qa | grep nfs-utils

# 启动顺序不能变：rpcbind → nfs-utils → nfs-server
sudo systemctl start rpcbind && sudo systemctl enable rpcbind
sudo systemctl start nfs-utils
sudo systemctl start nfs-server && sudo systemctl enable nfs-server

# 防火墙（放行三个服务）
sudo firewall-cmd --permanent --add-service=rpc-bind
sudo firewall-cmd --permanent --add-service=mountd
sudo firewall-cmd --permanent --add-service=nfs
sudo firewall-cmd --reload
sudo setenforce 0                             # 或 Permissive
```

---

## 三、配置详解（/etc/exports，重点）

**NFS 的配置就是维护 /etc/exports**——定义"服务器上哪些目录、共享给谁、什么规则"。

先建共享目录测试文件，再编辑：
```bash
sudo mkdir /tmp1 /tmp2 /home/dir1 /pub
sudo touch /tmp1/f1 /tmp2/f2 /home/dir1/f3 /pub/f4
sudo vim /etc/exports
```

```
/           Server1(rw,no_root_squash)
/tmp1       *(rw) *.long90.cn(rw,sync)
/tmp2       192.168.137.0/24(ro)
/home/dir1  Client1(rw,all_squash,anonuid=1200,anongid=1200)
/pub        *(ro,insecure,all_squash)
```

**逐条解读**：
1. `/ Server1(rw,no_root_squash)`：Server1 上的用户访问 NFS 根目录时，以**服务器上同名用户的权限**操作根目录（相当于整个根导出，风险极大，仅教学演示）；
2. `/tmp1 *(rw) *.long90.cn(rw,sync)`：所有主机可读写；long90.cn 域的主机读写且**同步写入**（sync 保证数据一致性）；`*` 表示任意主机；
3. `/tmp2 192.168.137.0/24(ro)`：仅该网段的主机可访问，且**只读**；
4. `/home/dir1 Client1(rw,all_squash,anonuid=1200,anongid=1200)`：Client1 上所有用户可读写，所有访问用户 UID/GID **统一映射为 1200**（all_squash 防越权）；
5. `/pub *(ro,insecure,all_squash)`：类似 FTP 匿名功能，所有人自由访问但只读，且都由 all_squash **映射为 nobody 用户**。

**语法注意**：键值对（目录与主机、主机与主机）之间用空格分隔，**其余地方不能用空格**（如括号内不能加空格）。

**生效方式（不用重启服务）**：
```bash
sudo exportfs -a    # 全部加载 /etc/exports 的设置
sudo exportfs -r    # 重新加载 /etc/exports 的设置
sudo exportfs -u    # 卸载某一目录
sudo exportfs -v    # 在屏幕显示已共享的目录
sudo exportfs -r -v # 最常用：重加载并显示
```

**客户端配置**：
```bash
# 客户端安装（Ubuntu: nfs-common / CentOS: nfs-utils）
sudo apt install nfs-common -y        # 或 sudo dnf install nfs-utils -y
sudo showmount -e 192.168.137.4        # 查看服务器导出了哪些共享
sudo mkdir /nfstest                    # 确定挂载点
sudo mount -t nfs 192.168.137.4:/tmp1 /nfstest   # 挂载（数据物理位置在服务器）
cd /nfstest && ls                      # 应看到 f1
sudo umount /nfstest                   # 卸载
```
**永久挂载**：编辑 /etc/fstab 添加一行 `192.168.137.4:/tmp1 /nfstest nfs defaults 0 0`，然后 `sudo mount -a` 立即生效。

---

## 四、客户端验证

- `showmount -e <服务器IP>`：列出租出清单（也常被攻击者用来探测 NFS 共享）；
- `mount -t nfs 服务器IP:目录 本地目录` 后 `ls` 能看到服务器上的文件；
- `df -h` 可看到挂载的 NFS 文件系统；`mount` 无参数也列出挂载情况；
- 读写验证：在挂载目录创建/删除文件，回服务器端确认同步。

---

## 五、常见问题与排查（老师PDF里的坑）

1. **服务起不来**：确认 rpcbind 先于 nfs-server 启动（顺序不能变），两个软件包都装了才有效。
2. **客户端挂载失败**：防火墙要同时放行 rpc-bind、mountd、nfs 三个服务（NFS 动态端口，漏放 mountd 最典型）；SELinux 未放行也会拒绝。
3. **exports 改了不生效**：`exportfs -r` 重新加载即可，不需要重启 nfs-server。
4. **权限异常（无权限/看到文件不能写）**：检查 exports 的 rw/ro、all_squash 映射、以及共享目录的本地文件系统权限（NFS 与本地权限叠加生效）；insecure 参数允许客户端用高端口连接（老客户端挂载失败可加）。
5. **hosts 名字解析**：exports 里写主机名（如 Client1）时，服务器 /etc/hosts 必须能解析该名字。

---

## 六、安全加固要点

- **root_squash 极危险**：默认其实会 squash root（映射为 nobody），但配置中常被写成危险的 `no_root_squash`（客户端 root 在服务器上也以 root 操作文件）。生产环境**绝不使用 no_root_squash**，坚持默认 root_squash。
- **禁止导出 `/`**：把整个根导出=任何被授权的客户端都能看到全盘结构；只导出业务需要的子目录。
- **精确限制访问主机**：把 `*` 换成具体 IP/网段（如 192.168.137.0/24），配合 ro 只读；写权限只给确需的服务器。
- **all_squash + anonuid/anongid**：把匿名访问映射到低权限专用账号（如 nobody 或专用 UID），防止客户端 UID 越权读取其他用户文件。
- **网络层**：NFS 早期版本（v3 及以下）数据明文传输，只在可信内网使用；防火墙仅对 NFS 服务器放行必要端口；rpcbind 暴露在公网是常见的扫描目标。
- **版本**：优先 NFSv4（集成认证与加密选项）；关闭不需要的 rpc 守护进程。
- 应急/审计：用 `showmount -e` 自查对外暴露的共享，检查 exports 是否有异常新增条目。

---

## 七、面试速答卡

- **NFS 与 samba 区别**：NFS 用于 Linux↔Linux 文件共享，samba 用于跨 Windows/Linux（SMB 协议）。
- **NFS 为什么依赖 RPC**：NFS 端口动态分配，需要 rpcbind（111 端口）做端口映射，客户端先查 RPC 再访问实际端口。
- **exports 常用选项**：rw/ro、sync（同步写）、root_squash（root 降权）、all_squash（全部映射匿名）、anonuid/anongid（匿名映射的 UID/GID）、insecure（允许高端口连接）。
- **no_root_squash 为什么危险**：客户端 root 在服务器端也以 root 身份操作文件，等于把服务器权限交给客户端。
- **怎么让配置生效**：exportfs -r 重新加载，无需重启服务；客户端用 mount -t nfs 挂载、showmount -e 查看共享清单。
- **启动顺序**：rpcbind → nfs-utils → nfs-server，火墙放行 rpc-bind/mountd/nfs。