# Web 渗透测试：DVWA 与 Burp Suite 与暴力破解

> 来源：课程实验《渗透测试DVWA平台、Burp Suite与Brute Force攻击》（Kali Linux，2025-2026 第二学期）
> 定位：渗透测试入门三件套——靶场搭建、代理抓包、口令爆破；是所有后续实验的地基，面试讲项目必提
> 实战场景：任何登录表单、后台入口的弱口令测试；Burp 是 Web 渗透的"瑞士军刀"

---

## 一、原理概述

### 暴力破解（Brute Force）为什么存在

**一句话原理**：登录认证的本质是"把用户输入的口令和数据库里存的比对，一样就放行"。只要口令空间是有限的、可枚举的，攻击者就能**逐个尝试**直到撞对一个——这就是暴力破解。它不依赖任何代码漏洞，**只要口令弱，协议再安全也没用**。

**为什么值得研究**：
- 大量站点的后台仍用弱口令（admin/admin123、123456），爆破成功率远高于想象
- 爆破不只是"撞密码"，还是**枚举用户名**（用户名错误和密码错误的提示不同）、**枚举 token/验证码**的手段
- 破解工具 = 字典（口令候选集）× 自动化发包引擎 × 结果判断（响应差异）

### Burp Suite 为什么能爆破

Burp 是**中间人代理**：浏览器把流量交给 Burp（默认监听 `127.0.0.1:8080`），Burp 看到、可以修改后再转发给服务器。因为攻击者的每个请求都要经过 Burp，Burp 就能**批量改参数、批量发包（Intruder）、批量重放（Repeater）**——爆破就是在 Intruder 里把"口令那一格"换成字典循环发送。

### DVWA 是什么

DVWA（Damn Vulnerable Web Application）是**故意留了一堆漏洞的 PHP 靶场**，每个漏洞都提供 Low / Medium / High / Impossible 四个安全级别，用来对比"有漏洞的写法"和"安全的写法"——是整个课程所有攻击实验的共同平台。

---

## 二、DVWA 靶场搭建（方法论）

1. **放代码**：解压 DVWA.zip，把整个 DVWA 文件夹放进 Web 根目录 `/var/www/html/`
2. **改配置**：`config/` 下把 `config.inc.php.dist` 重命名为 `config.inc.php`
3. **建库**：启动 MySQL，按 DVWA 要求创建数据库和用户
4. **调 PHP**：编辑 `/etc/php/8.x/apache2/php.ini`，消除 setup 页面标红的项（如 `allow_url_include`、GD 库扩展等）
5. **补依赖**：PHP module gd 缺失就 `apt install php-gd`（记得换国内源）；reCAPTCHA key 缺失就把官方示例 key 填进 config 的两个空字符串
6. **给写权限**：`hackable/uploads/` 和 `config/` 目录要对 www-data 可写（`chmod`/`chown`）
7. **验收**：访问 `/DVWA/setup.php`，所有红色项全消 → 登录默认账号 admin/password

> 常见坑：PHP 版本号因更新从 8.2 变 8.4，php.ini 路径要对上实际版本；所有"标红项"本质是权限/扩展/配置三类问题，逐个对症下药。

---

## 三、Burp Suite 核心模块（面试速记）

| 模块 | 作用 | 本实验用途 |
|---|---|---|
| **Proxy** | 拦截/查看/修改 HTTP 请求；`Open Browser` 起自带浏览器（自动走代理，省去手动配代理） | 抓登录包，看参数结构 |
| **Intruder** | 自动化批量请求：把参数标记为 payload 位置，循环发送字典 | 暴力破解核心工具 |
| **Repeater** | 手动重放/微调单个请求 | 测试 token、改数据试验 |
| **Decoder / Comparer** | 编解码 / 响应对比 | 辅助分析 |
| 插件体系 | 如 CSRF Token Tracker | 自动化处理动态 token |

---

## 四、实操/利用流程（方法论）

### 暴力破解五步（Low 级别）

1. **抓包定靶**：Proxy 开拦截（Intercept on），登录页随便输个账号密码点提交 → 抓到 POST 请求，确认参数名（实验里是 `username=admin&password=xxx`）
2. **送进 Intruder**：请求右键 → Send to Intruder；**Attack type 选 Cluster Bomb**（有两组独立字典要组合：用户名 × 密码，适合"用户名密码都不知道"的场景）
3. **标 payload 位置**：选中 `admin` 和 `password` 两个参数值，点 Add 变成 `§admin§`、`§password§`
4. **配字典**：Payload Sets 一（用户名）、二（密码）分别 Paste 粘贴或 Load 加载字典文件
5. **跑 & 判定**：Start attack → 看响应**长度/状态码/响应文本**的差异——实验里绝大多数结果长度是 4620，唯一一条 4663 的就是成功的那组（内容多出错/成功提示）

> **判定技巧**：爆破成果不看"响应 200"，看**长度异常值**（成功页比错误页内容多）、**状态码分组**、以及响应体关键词（Welcome/Login failed）。先跑小字典看基线，再放大字典。

---

## 五、绕过与进阶（各难度）

### Medium：加了延迟照样爆

后端代码只是做了人为延迟（sleep），**参数结构没变**——用和 Low 一样的方法爆即可，只是**慢很多**。要点：Intruder 里可以调线程数、设超时，耐心等。

### High：Anti-CSRF Token 防重放的正面硬刚（重点）

**难点**：登录请求里多了一个 `user_token`，每次请求页面 token 都变，且服务器**先验 token 再验口令**——直接把抓包的旧 token 循环发，全部被拒。**核心矛盾：每次尝试新密码前，都必须先"重新请求一次登录页"拿到最新 token。**

**工具化四步（记住这个流程，面试讲得出来）**：

1. **Attack type 改 Pitchfork**（两组 payload 并行逐一配对）：payload 位置标记 `password` 和 `user_token` 两个参数
2. **Resource pool 里把并发（Maximum concurrent requests）设为 1** —— 必须串行：每次尝试都是"先取 token 再试密码"，并发会导致 token 错位
3. **Settings → Grep - Extract**：配置从响应中提取 `user_token` 的值（正则抓 `<input type='hidden' name='user_token' value='(.*)' />`）——这是"新一轮 token 从哪来"
4. **第二个 Payload 类型选 Recursive grep**：把最初抓包得到的 token 值填进 initial payload——之后每轮自动用"上一轮响应里提取的新 token"替换，形成"取 token→试密码→再取新 token"闭环

跑起来后 Intruder 每一轮都先 GET 页面拿新 token 再 POST 尝试，token 防线被自动化击穿。

**这段的本质**：token 把"无状态爆破"变成了"有状态爆破"——工具必须像真人一样"每次都先刷新页面"。脚本/工具能做到，只是麻烦了一点。**防御价值在于：token + 失败次数锁定 + 速率限制叠加后，爆破成本才会高到不划算。**

---

## 六、防御（面试必答）

| 攻击点 | 防御 | 说明 |
|---|---|---|
| 批量枚举 | **失败次数锁定**：连续 N 次失败冻结账号/IP 一段时间 | 直接掐断"无限尝试" |
| 自动化请求 | **验证码/CAPTCHA**（且校验必须在服务端、不可预测） | 拦自动化，不拦真人 |
| 高速穷举 | **速率限制**：同一 IP/账号单位时间限请求次数 | 把爆破速度降到不可用 |
| 撞库成功 | **双因素认证（2FA）** | 口令只是第一道门 |
| 弱口令本身 | 强口令策略 + 定期改密 + **密码库泄露检测**（Have I Been Pwned API） | 从根上减少"候选集命中" |
| 事后发现 | 登录日志 + 异常告警（异地/高频失败） | 让爆破行为可被发现 |

**终极一句话**：爆破防不住"口令本身弱"，防御的核心是 **"让尝试变得又慢又贵 + 让弱口令不存在"**。

---

## 七、面试速答卡

- **Burp 代理原理**：浏览器流量经 127.0.0.1:8080 中转，Burp 可看可改再转发
- **Intruder 四种模式**：Sniper（单字典逐位替换）、Battering ram（同值多位）、Pitchfork（多字典并行配对）、Cluster Bomb（多字典笛卡尔积组合）
- **用户名密码都不知道时**：Cluster Bomb；只知道密码时：Sniper
- **怎么判断爆破成功**：响应长度/状态码/响应关键词的差异，不是看 200
- **token 为什么难爆**：每次请求 token 都变，必须"先取 token 再尝试"，有状态爆破
- **Pitchfork + Recursive grep 是干嘛的**：并行配对两组字典 + 每轮自动从响应提取新 token 替换
- **爆破的防御组合**：锁定 + 验证码 + 限速 + 2FA + 强口令策略
- **DVWA 的四个级别**：Low（无防护）/ Medium（有简单防护）/ High（较强防护）/ Impossible（正确代码，用于学习防御）