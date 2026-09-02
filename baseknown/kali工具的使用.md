---
title: kali工具的使用
tags: [Import-d4ea]
created: '2026-07-04T07:17:32.592Z'
modified: '2026-07-04T11:31:55.677Z'
---

# kali工具的使用

## nmap使用

### 主机存活扫描

``` shell
nmap <目标ip或目标网段>
nmap 192.168.1.1
nmap 192.168.1.1/24
nmap 192.168.1.1-100
```

### 端口存活扫描

``` sh
nmap -sS -p <端口号> <目标主机或目标网段> ——>需要root权限
nmap -sT -p <端口号> <目标主机或目标网段>
nmap -sU -p <端口号> <目标主机或目标网段>
nmap -p- <目标主机或目标网段>
```

### 其他服务探测与功能

``` sh
nmap -sV <目标主机或目标网段> 查看服务版本（如80，22，3306等信息）
nmap -O <目标主机或目标网段> 查看操作系统信息（硬件信息）
nmap -oN result.txt <目标> 将结果输出
```

### 绕防火墙选项

``` sh
nmap -T0 <目标主机或目标网段> 间隔扫描，T0~T5，T0接近5分钟一个包
nmap -f <目标主机或目标网段> 分片扫描，还有-ff
nmap --mtu <8的倍数> <目标主机或目标网段> 自定义分片
```

### 最常用的选项

``` sh
nmap -sS -sV -A <目标> 最常用的综合扫描命令，适合快速获取目标信息
```

## dirb使用

### 目录文件爆破

``` sh
dirb <目标站点> <字典> -o <输出结果文件名>
```

### 绕过防火墙

```sh
dirb <目标站点> <字典> -z <毫秒数> -t <并发数>
```

![image-20260625164642227](C:\Users\Cohen\AppData\Roaming\Typora\typora-user-images\image-20260625164642227.png)

## hashcat和john

### hashcat

![image-20260628230804566](C:\Users\Cohen\AppData\Roaming\Typora\typora-user-images\image-20260628230804566.png)

``` sh
\\hashcat使用
hashcat -b 		hashcat破解测速

hashcat -m [类型码] -a [攻击模式] [哈希文件] [字典/掩码] [选项]
//常用的类型码：
0    → MD5
1000 → NTLM
1800 → SHA-512 (Linux shadow)
1400 → SHA-256
//攻击模式
0 → 字典攻击	纯跑字典，最普通的模式
1 → 组合攻击	两本字典组合攻击
3 → 掩码攻击	无需字典，只需要掩码
6 → 字典+掩码组合	字典+掩码组合攻击，还有7即掩码+字典攻击
```

![image-20260628231337190](C:\Users\Cohen\AppData\Roaming\Typora\typora-user-images\image-20260628231337190.png)

### john

```sh
john password.txt
```



## hydra

```sh
服务类爆破
hydra -l [用户名] -p [密码] [选项] ip [服务名]
```

## msf

```sh
查找模块	search xxx
进入利用模块	use xxx
查看选项模块	options
填充选项模块	set [选项] xxx
运行	run
//msf默认的payload是反弹shell【linux/x64/meterpreter/reverse_tcp】成执行指令：
set payload cmd/windows/generic			set payload cmd/unix/generic
set CMD xxx
back 返回  exit 退出

python3 -c "import pty;pty.spawn('/bin/bash')"   改成交互式shell

靶场drupal【不适合设置cmd】	
靶场struct2 s02-045		exploit/multi/http/struts2_content_type_ognl
```





# 靶场实战

## 靶场下载地址

https://download.vulnhub.com/w1r3s/w1r3s.v1.0.1.zip

作业：
https://www.vulnhub.com/entry/lampiao-1%2C249/【提权使用脏牛	msf模块搜索 dirty ，	exp需编译执行】

拿到www-data用户权限60																										

拿到root用户权限80分

拿到flag得100分
