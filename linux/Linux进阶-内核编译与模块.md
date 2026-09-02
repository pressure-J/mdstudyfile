# Linux 进阶：内核编译与内核模块

> 来源：课程实验（Linux操作系统，Ubuntu 22.04，2025-2026 第一学期），老师版PDF为底料
> 定位：Linux 系统管理的高阶内容，运维中掌握内核编译可做性能优化、安全补丁定制、驱动适配；安全角度上内核模块（LKM）是 rootkit 和提权利用的经典载体（如隐藏进程/端口），应急响应查内核模块列表是标配动作。

---

## 一、概念与原理

**Linux 内核**：操作系统的核心，管理进程调度、内存、文件系统、设备驱动、网络协议栈。发行版预编译的内核是通用配置，企业常按需裁剪/优化，或打安全补丁。

**内核版本**：`uname -r` 查看（如 Ubuntu 22.04 为 6.8.0-45-generic）。与内核发布版（上游版本号 6.10.13）不同，发行版会带后缀（-generic 等）。内核及配置文件位于 /boot/：`vmlinuz-*`（内核镜像）、`config-*`（内核配置）、`initrd.img-*`（初始内存盘）。

**内核模块（LKM，Loadable Kernel Module）**：可在运行时动态加载/卸载的"内核插件"，用于扩展驱动和功能，免去每次改动都重编译内核。对应文件为 `.ko`（kernel object），存放在 `/lib/modules/$(uname -r)/` 下。

**模块管理命令**：`insmod`（加载，按文件路径）、`rmmod`（卸载，按模块名）、`modprobe`（智能加载/卸载，自动处理依赖）、`lsmod`（查看已加载模块）、`dmesg`（查看内核日志，printk 输出在这里）。

---

## 二、环境准备（源码下载与依赖）

```bash
uname -r                                   # 6.8.0-45-generic
# 选一个接近的稳定版本，如 6.10.13（建议官网下载，国内镜像可能不完整）
wget https://cdn.kernel.org/pub/linux/kernel/v6.x/linux-6.10.13.tar.xz
tar -Jxvf linux-6.10.13.tar.xz
sudo apt update -y && sudo apt upgrade -y
sudo apt install git fakeroot build-essential ncurses-dev xz-utils gcc make \
  libncurses5-dev openssl libssl-dev pkg-config libc6-dev bison flex \
  libelf-dev bc dwarves -y
```

---

## 三、配置详解（.config）

**官方源码不带配置**，需要从当前系统复制一份做底子再更新：

```bash
cd linux-6.10.13
cp /boot/config-$(uname -r) .config      # 以当前内核配置为蓝本
make olddefconfig                         # 用新内核默认值补齐缺失的配置项
```

**两组必改项**（新版内核要求签名证书，发行版证书路径在源码环境里不存在，编译安装会失败）：
```bash
./scripts/config --file .config --set-str SYSTEM_TRUSTED_KEYS ''
./scripts/config --file .config --set-str SYSTEM_REVOCATION_KEYS ''
# 等价于 vim .config 把 CONFIG_SYSTEM_TRUSTED_KEYS 与 CONFIG_SYSTEM_REVOCATION_KEYS 置空
```

**交互式配置**：`make menuconfig`（文本图形界面，可逐项选择"启用/禁用/编译为模块"）。

**改源码验证自己内核**：编辑 `init/main.c`，在内核启动函数 `start_kernel()`（约 903 行）里加一行：
```c
printk(KERN_ALERT "Hello, World! This is my custom kernel!\n");
```
重启后能看到自己内核打的第一条日志，验证"我的内核真的被编译了"。

---

## 四、编译与安装

```bash
sudo make -j8            # 并行编译，-j$(nproc) 按 CPU 核数加速；第一次编译非常久（6核约7小时）
sudo make INSTALL_MOD_STRIP=1 modules_install   # 安装内核模块（去掉调试符号减小体积）
sudo make install        # 安装内核镜像与 initrd
sudo update-grub         # 更新引导程序，识别新内核
sudo shutdown now        # 关机重启
```
重启时长按 Shift 进 Grub → "Advanced options for ubuntu" → 选择自编译的 6.10.13 内核。验证：
```bash
uname -r                                  # 应显示 6.10.13
sudo dmesg | grep "Hello, World"          # 应看到 [0.000000] Hello, World! This is my custom kernel!
```

---

## 五、内核模块编写（Hello, Kernel! 完整流程）

### 5.1 编写 hello_module.c
```c
#include <linux/module.h>   // 模块核心头文件
#include <linux/kernel.h>   // 内核相关头文件
#include <linux/init.h>     // 模块初始化/清理宏

static int __init hello_init(void) {
    printk(KERN_INFO "Hello, Kernel!\n");   // 加载时打印到内核日志
    return 0;                               // 返回 0 表示加载成功
}
static void __exit hello_exit(void) {
    printk(KERN_INFO "Goodbye, Kernel!\n"); // 卸载时打印
}
module_init(hello_init);        // 指定初始化函数
module_exit(hello_exit);        // 指定清理函数
MODULE_LICENSE("GPL");          // 许可证（必需，否则内核报 taint）
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("A simple hello world Linux kernel module");
MODULE_VERSION("1.0");
```

### 5.2 编写 Makefile
```make
obj-m += hello_module.o     # 把 hello_module.o 编成内核模块
all:
    make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules
clean:
    make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
```
`-C` 指定进入内核源码构建目录，`M=$(PWD)` 表示编译当前目录的模块。

### 5.3 编译→加载→验证→卸载→清理
```bash
make                          # 生成 hello_module.ko（编译好的内核模块）
sudo insmod hello_module.ko   # 加载模块
sudo dmesg | tail             # 看到 [104146.705925] Hello, Kernel!
sudo rmmod hello_module       # 卸载（用模块名，不带 .ko）
sudo dmesg | tail             # 看到 [104192.111439] Goodbye, Kernel!
make clean                    # 清理编译产物
```

---

## 六、常见问题与排查

1. **编译报错 `the compiler differs from the one used to build the kernel`**：内核源码比当前 gcc 新 → `sudo apt install gcc-12` 装对应版本再编。
2. **安装失败 `No such file or directory` / 证书相关**：多半是 SYSTEM_TRUSTED_KEYS/SYSTEM_REVOCATION_KEYS 没置空，用 scripts/config 命令处理。
3. **编译时间超长**：正常现象，用 `make -j$(nproc)` 并行；虚拟机建议给足 CPU 核数（实验 6 核约 7 小时）。
4. **重启后没进新内核**：确认 update-grub 执行过，Grub 里 Advanced options 手动选；也可改 /etc/default/grub 设默认启动项。
5. **模块加载失败 `Invalid module format`**：模块与当前运行内核版本不匹配（insmod 必须在编译该模块的同一内核下使用）。
6. **dmesg 看不到输出**：printk 级别（KERN_INFO）低于 console_loglevel 时终端不显示但日志里有，用 `dmesg | tail` 查。

---

## 七、安全加固要点（内核视角）

- **LKM 是 rootkit 经典载体**：恶意模块可隐藏进程/文件/端口、开后门。应急响应必查：`lsmod` 对比基线、`dmesg` 找异常加载记录、检查 /lib/modules 下可疑 .ko、用 rkhunter/chkrootkit 扫描。
- **禁用未签名模块**：启用内核模块签名校验（CONFIG_MODULE_SIG_FORCE + `module.sig_enforce=1`），只加载可信厂商签名模块，阻止恶意 LKM 注入。
- **lockdown 模式**：`lockdown=confidentiality` 内核参数限制 /dev/mem、kexec 等敏感接口，防内核级提权利用。
- **及时更新内核**：内核漏洞（如脏牛 Dirty COW、Dirty Pipe）影响面大，云服务器直接升级内核补 CVE。
- **系统硬化基线**：sysctl 加固（禁 IP 转发、防 SYN 洪水）、关无用内核参数；生产内核编译时裁剪不需要的功能模块，缩小攻击面。
- 编译环境与生产环境分离：不要在公网裸奔编译机；内核源码完整性校验（校验和/签名）。

---

## 八、面试速答卡

- **Linux 内核编译流程**：下载源码 → 复制现有 config（cp /boot/config-$(uname -r) .config）→ make olddefconfig → 改配置（menuconfig/scripts/config）→ make -j$(nproc) 编译 → modules_install + make install → update-grub → 重启选内核。
- **内核模块四个头文件/宏的作用**：module.h（核心）、init.h（__init/__exit 宏）、kernel.h（printk 等）；module_init/module_exit 注册加载卸载函数，MODULE_LICENSE("GPL") 声明许可证。
- **insmod/rmmod/modprobe/lsmod 区别**：insmod/rmmod 按路径/名字加载卸载、不做依赖处理；modprobe 自动处理依赖；lsmod 列已加载模块。
- **.ko 与 printk/dmesg**：.ko 是编译出的内核模块；模块里 printk 输出进内核日志，用 dmesg 查看。
- **为什么模块比重编内核方便**：LKM 运行时热插拔，改驱动/加功能不用重编译整个内核。
- **内核模块安全风险**：恶意 LKM 可提权、隐藏痕迹（rootkit），用模块签名（module.sig_enforce=1）和 lsmod/dmesg 审计防御。