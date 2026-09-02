# Linux 服务：FTP 文件传输

> 来源：课程实验（Linux操作系统，CentOS 8.3，2025-2026 第一学期），老师版PDF为底料
> 定位：最常见的文件传输服务之一，运维中用于软件分发、网站内容上传维护、数据备份交换；安全角度上 FTP 明文传输密码+三种认证模式权限配置是高频考点，vsftpd 也是应急响应中排查后门上传/弱口令暴破的重点服务。

---

## 一、概念与原理

**FTP（File Transfer Protocol）**：文件传输协议，可靠性强、传输效率高，采用 **C/S 结构**，默认控制端口 **21**，数据通道端口为 **20（主动模式）**。

**工作原理（双通道）**：
1. 客户端动态打开一个大于 1024 的端口（如 1031），向服务器 21 端口发起连接请求，建立 FTP 会话连接（控制连接）。
2. 传输数据时，客户端再动态打开一个大于 1024 的端口（如 1032），与服务器 **20** 端口建立数据连接传输数据，传完即关闭。
3. 数据传输完毕如果不发拆除连接请求，则连接保持；客户端发送拆除请求并确认后断开，动态端口自动释放。

**两种工作模式（面试必问）**：
| 模式 | 数据连接方向 | 特点 |
|---|---|---|
| 主动模式 Active | 服务器 20 端口主动连客户端的高端口 | 客户端被防火墙/NAT 挡住时常失败 |
| 被动模式 Passive | 服务器开放一个随机端口，客户端主动连接 | 能穿透大多数防火墙，现代客户端默认 |

**匿名用户**：用统一用户名 `anonymous`（密码任意，惯例填邮箱格式），方便公开软件下载站点即开即用。

**本实验使用 vsftpd（Very Secure FTP Daemon）**，号称"非常安全的 FTP 守护进程"。三种认证模式：
1. **匿名开放模式**：最不安全，无须密码直接登录；
2. **本地用户模式**：用 Linux 系统账户密码认证，比匿名安全；但一旦账号泄露可登录远程终端，完全控制服务器；
3. **虚拟用户模式**：最安全。为 FTP 单独建立用户数据库，虚拟账号**在系统中不存在**，仅作认证用；即使泄露也无法登录系统终端，破坏范围最小。

---

## 二、环境准备与安装

```bash
sudo dnf install vsftpd ftp -y         # ftp 是客户端命令
sudo rpm -qa | grep vsftpd && sudo rpm -qa | grep ftp
sudo systemctl start vsftpd
sudo systemctl enable vsftpd
sudo firewall-cmd --permanent --add-service=ftp && sudo firewall-cmd --reload
sudo setsebool -P ftpd_full_access=on  # 或 sudo setenforce 0
```

**配置文件族**：
- 主配置文件：`/etc/vsftpd/vsftpd.conf`（127 行，多数是注释；可用 `grep -v "#"` 过滤出有效参数）
- PAM 认证配置：`/etc/pam.d/vsftpd`
- **ftpusers 黑名单**：文件内用户一律禁止访问（默认含 root、bin、daemon 等系统账号）
- **user_list**：配合 `userlist_deny` 决定是白名单还是黑名单（userlist_deny=NO 仅允许列表用户；=YES 默认值，拒绝列表用户）
- 服务目录：`/var/ftp`（含 pub 子目录，默认只读，仅 root 可写）

**常用参数速查**：`listen/listen_address/listen_port`（监听方式与端口）、`download_enable`、`userlist_enable/userlist_deny`、`max_clients`（最大连接数，0 不限）、`max_per_ip`（同 IP 最大连接数）、`anon_umask=022`、`anon_root=/var/ftp`（匿名根目录）、`anon_max_rate`（限速）、`local_root`、`chroot_local_user`（禁锢用户在 FTP 目录内）、`local_max_rate`。

---

## 三、配置详解（三种模式的完整实例）

### 3.1 匿名用户方式

需求：允许匿名上传下载，根目录 /var/ftp。

```bash
sudo touch /var/ftp/pub/sample.tar
sudo vim /etc/vsftpd/vsftpd.conf
```
```
anonymous_enable=YES              # 允许匿名登录
anon_root=/var/ftp                # 匿名根目录
anon_upload_enable=YES            # 允许上传
anon_mkdir_write_enable=YES       # 允许建目录
#anon_other_write_enable=YES      # 删除/重命名权限，本实例不开
```
⚠️ **语句前后不能有空格**，重复语句直接修改不要追加。重启后 Windows 资源管理器访问 `ftp://192.168.137.4` 能进 pub 但**无法新建文件夹**——原因是文件系统权限没放开：
```bash
sudo chmod o+w /var/ftp/pub       # 给其他用户写权限
sudo systemctl restart vsftpd
```

### 3.2 本地用户方式

需求：team1/team2 维护网站内容，仅限登录 FTP、不能登录本地系统，根目录锁定在 /web/www/html。

```bash
sudo useradd team1 && sudo useradd team2
sudo passwd team1 && sudo passwd team2
sudo cp /etc/vsftpd/vsftpd.conf /etc/vsftpd/vsftpd.conf.bak1   # 备份
sudo sh -c 'grep -v "#" /etc/vsftpd/vsftpd.conf.bak > /etc/vsftpd/vsftpd.conf'  # 恢复干净配置
sudo mkdir -p /web/www/html && sudo touch /web/www/html/test.sample
sudo chmod -R o+w /web/www/html
```
```
local_enable=YES
local_root=/web/www/html
chroot_local_user=NO              # 采用"列表内受限"方案（默认值）
chroot_list_enable=YES            # 激活 chroot 例外列表
chroot_list_file=/etc/vsftpd/chroot_list
allow_writeable_chroot=YES        # 启用 chroot 必须加，否则报错
```
`/etc/vsftpd/chroot_list` 文件写入 team1、team2（列表内用户被禁锢在根目录）。**chroot 两种实现**：① `chroot_local_user=YES`（列表内自由、列表外受限）；② `chroot_local_user=NO`（列表内受限、列表外自由）——本例用②。

### 3.3 虚拟用户方式（最安全）

需求：虚拟账号 user2/user3 登录，仅可查看 /var/ftp/vuser，禁止上传修改。

```bash
sudo mkdir /vftp && sudo vim /vftp/vuser.txt     # 每行"用户名/密码"：user2/12345678、user3/12345678
sudo db_load -T -t hash -f /vftp/vuser.txt /vftp/vuser.db   # 明文文件转 db 数据库
sudo chmod 700 /vftp/vuser.db
```
**配置 PAM**（/etc/pam.d/vsftpd，把原有内容全部 # 注释）：
```
auth    required    pam_userdb.so   db=/vftp/vuser
account required    pam_userdb.so   db=/vftp/vuser
```
**创建映射的系统用户**：
```bash
sudo useradd -d /var/ftp/vuser vuser
sudo chown vuser.vuser /var/ftp/vuser
sudo chmod 555 /var/ftp/vuser
sudo touch /var/ftp/vuser/file1 && sudo mkdir /var/ftp/vuser/dir1
```
**vsftpd.conf 要点**：`anonymous_enable=NO`（关匿名）、`local_enable=YES`、`chroot_local_user=YES`、`allow_writeable_chroot=YES`、`write_enable=NO`（禁写入）、`guest_enable=YES`、`guest_username=vuser`（虚拟账号统一映射到 vuser）、`pam_service_name=vsftpd`。

---

## 四、客户端验证

**Windows**：资源管理器输入 `ftp://192.168.137.4`，直接浏览/上传下载（匿名需先 `chmod o+w`）。

**Linux**：
```bash
ftp 192.168.137.4
Name: team1 / Password: ****   # 230 Login successful
ftp> pwd                        # 显示 "/"，实际是 /web/www/html
ftp> mkdir testteam1            # 建目录（本地用户可写）
ftp> get test.sample test1111.sample   # 下载并改名
ftp> put test1111.sample test00.sample # 上传并改名
```

---

## 五、常见问题与排查（老师PDF里的坑）

1. **匿名用户无法新建文件夹**：文件系统权限不足 → `chmod o+w /var/ftp/pub` 后重启。
2. **chroot 报错**：`500 OOPS: vsftpd: refusing to run with writable root inside chroot()` → 在配置中加入 `allow_writeable_chroot=YES`（只要启用 chroot 就必须加）。
3. **配置不生效/服务异常**：检查语句前后是否误带空格、是否有重复参数（重复项删除或覆盖，不要追加多份）；`grep -v "#"` 恢复干净配置后从零改。
4. **用户能访问系统其他目录**：确认 chroot 生效路径（chroot_list 文件写对用户、对应 chroot_local_user 取值方案）。
5. 排错命令：`sudo journalctl -xe`、`ss -tlnp | grep 21`、`tail -f /var/log/vsftpd.log`。

---

## 六、安全加固要点

- **优先虚拟用户模式**：虚拟账号不映射系统用户，即使密码泄露也无法登录服务器终端——这是三种模式里安全设计的关键。
- **禁止匿名写**：匿名模式只用于公开下载，`anon_upload_enable`、`anon_mkdir_write_enable`、`anon_other_write_enable` 默认不开放；确需上传的目录单独隔离并限速（`anon_max_rate`/`local_max_rate`）。
- **chroot 禁锢**：所有本地用户 `chroot_local_user=YES` 锁在 home 或指定目录，防止越权浏览系统文件。
- **系统账号保护**：把 root、bin 等留在 /etc/vsftpd/ftpusers；用 user_list 白名单（userlist_deny=NO）只放行业务账号。
- **最小权限**：只读优先；`write_enable` 按需开关；上传目录禁止执行（配合 httpd 时防 WebShell 上传执行链）。
- **网络层**：控制端口 21+被动端口范围用防火墙精确放行来源 IP；FTP 明文传输密码，重要场景建议改 FTPS（TLS）或 SFTP。
- 日志常查：`/var/log/vsftpd.log` 记录登录与传输，应急响应时核对异常登录 IP 与上传文件。

---

## 七、面试速答卡

- **FTP 端口**：控制连接 21，数据连接主动模式 20（被动模式随机端口）。
- **主动/被动模式区别**：主动是服务器连客户端数据端口，被动是客户端连服务器开放的随机端口；NAT/防火墙环境下被动模式更可靠。
- **vsftpd 三种认证模式**：匿名（最不安全）、本地用户（系统账号）、虚拟用户（独立用户库，最安全）。
- **chroot 的作用与两种实现**：把用户禁锢在指定目录；chroot_local_user=YES 时列表内自由/列表外受限，=NO 时列表内受限/列表外自由。
- **为什么虚拟用户最安全**：虚拟账号在系统中不存在，即使密码泄露也无法登录服务器终端。
- **ftpusers 与 user_list 区别**：ftpusers 是硬黑名单；user_list 由 userlist_deny 决定是黑名单还是白名单。