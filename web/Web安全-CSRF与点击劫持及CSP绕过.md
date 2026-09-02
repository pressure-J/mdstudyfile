# Web 安全：CSRF 与点击劫持及 CSP 绕过

> 来源：课程实验《CSP绕过攻击、CSRF攻击与点击劫持攻击》（DVWA 平台 + Burp Suite，2025-2026 第二学期）
> 定位：三类"信任型/旁路型"攻击——浏览器自动携带身份、浏览器被 UI 欺骗、浏览器策略被绕过；一线安全面试高频
> 实战场景：改密码、转账、发帖等一切"带 Cookie 的敏感操作"；任何靠 CSP 兜底 XSS 的站点

---

## 一、CSRF 原理（跨站请求伪造）

**一句话原理**：浏览器会自动携带目标网站的 Cookie 发起请求，服务器只认"这个请求带着合法 Cookie"，不认"这个请求是谁、在哪发起的"。于是攻击者构造一个页面，受害者**只要访问**，浏览器就替他向目标网站发出敏感操作请求。

**为什么能成功，三个条件缺一不可**：
1. 受害者已登录目标站点（浏览器里存着有效 Cookie）
2. 攻击者知道目标操作对应的 URL 结构（改密、转账等）
3. 目标站点的敏感操作**没有做额外验证**（无 token、无二次确认），或验证可被绕过

**与 XSS 的本质区别**（面试必问）：
- XSS 是攻击者在**受害者的浏览器里执行代码**（破坏的是"代码信任"）
- CSRF 是攻击者**借用受害者的身份发出请求**（破坏的是"请求来源信任"）——攻击者页面里只是放了一个请求，代码根本没在目标域执行

**危害**：改密码、转账、发表内容、修改资料——**一切受害者能做的操作，攻击者都能替他做**。GET 请求型 CSRF 尤其危险，因为 `<img>` 标签就能自动触发。

---

## 二、核心知识

### 攻击载荷三件套

```html
<!-- 1. GET 型：img 标签自动触发（杀伤力最大，无需用户交互） -->
<img src="http://目标站/vulnerabilities/csrf/?password_new=hack&password_conf=hack&Change=Change">

<!-- 2. POST 型：隐藏表单 + JS 自动提交 -->
<form action="http://目标站/change.php" method="POST" id="f">
  <input type="hidden" name="password" value="hack">
</form>
<script>document.getElementById('f').submit();</script>

<!-- 3. 诱惑点击：短链接/钓鱼页包装 -->
<a href="http://短链">点我领福利</a>
```

### 实验中的 GET 型实例（DVWA Low）

修改密码后观察 URL：

```
http://192.168.164.130/DVWA/vulnerabilities/csrf/?password_new=12341234&password_conf=12341234&Change=Change#
```

**改密码的全部参数都在 URL 里**——把这个 URL 发给受害者，他一旦点击，密码就被改了。实战中没人会点一长串可疑链接，所以要配合**短链接服务**或**HTML 钓鱼页面**包装。教训：**GET 请求绝不应该承载"修改类"操作**。

---

## 三、实操/利用流程（方法论）

1. **分析目标操作**：用 Burp 抓包看敏感操作的请求方法、参数结构（GET/POST、改密/转账的参数名）
2. **判断可行性**：请求是否只靠 Cookie 认证？有没有 token / Referer 校验 / 二次确认？
3. **选择载荷形态**：GET 请求用 `<img>`；POST 请求用隐藏表单自动提交；需要点击的用短链接+诱饵文案
4. **投放诱饵**：论坛发帖、聊天软件发链接、邮件钓鱼——受害者访问即中招
5. **验证效果**：用受害者 Cookie 确认操作已生效

---

## 四、绕过与进阶（DVWA 各难度）

### Medium：Referer 校验的绕过

后端校验请求头 `Referer` 必须来自本站。绕过思路：

- **把攻击文件放到目标站点服务器上**（如本实验：攻击 HTML 放 192.168.164.130 下），Referer 天然合法
- 程序直接访问（地址栏输入）时 Referer 为空——很多实现"空 Referer 直接放行"
- 部分实现只做"包含域名片段"的前缀匹配，构造 `http://target.com.attacker.com` 可绕过

**为什么 Referer 校验不可靠**：Referer 是客户端可自行设置的请求头，浏览器扩展/代理/脚本能随意伪造；且空 Referer、同源判断不严谨都会漏。

### High：Anti-CSRF Token 的绕过

后端引入 token 机制：每次访问改密页面，服务器返回随机 `user_token`，提交时必须带上且必须正确。

- **关键突破口**：token 在响应页面里，攻击者必须先**发起一次合法请求拿到 token**，再连同 token 一起提交攻击请求
- 工具化：安装 **Burp Suite 的 CSRF Token Tracker 插件**——抓包重放时插件自动从响应中提取新 token 并替换请求中的旧 token，循环往复即可打穿"token 每次失效"的防线
- 失败根源：**token 与用户会话绑定不牢 / token 可预测 / token 在 URL 或响应中泄露**，或服务器"先生效后校验"（先改密后验 token）

### CSP 绕过（实验第二部分）

**CSP 是什么**：服务器通过 `Content-Security-Policy` 响应头告诉浏览器"脚本只能从哪些源加载"。它是 XSS 的**兜底防线**——XSS 注入了，但脚本不是白名单源，浏览器拒绝执行。

| 级别 | CSP 策略 | 绕过手法 | 原理 |
|---|---|---|---|
| Low | 允许列表含外部可信域名 | 到被允许的域名上放 JS（文本分享网站）+ JSONP 端点 | CSP 只限制"脚本从哪来"，不限制"脚本内容"；被信任的域名上能放任意内容 = 变成攻击者的脚本托管站 |
| Medium | `script-src 'nonce-xxx'` | 把响应里明文的 nonce 抄进自己的 `<script nonce="TmV2ZXIgZ29pbmcgdG8gZ2l2ZSB5b3UgdXA=">alert(/xss/)` | nonce 每次请求都由服务端生成并**原样出现在页面里**，且未设置过期/绑定，等于白送 |
| High | `script-src 'self'`（只信自己域名） | 利用同域有漏洞的 JSONP 端点：`source/jsonp.php?callback=solveNum` 未过滤回调参数，返回 `callback(...)` 形式的 JS | 自己的域名是白名单，在自己的域名上找到一个能"产出可控脚本"的接口，就借到了执行权 |

**CSP 绕过核心思想**：CSP 画了一个"可信源的圈"，攻击者要做的不是打破这个圈，而是**在圈内找到能让自己代码落地的点**——JSONP（回调可控）、开放 API、可上传内容的域名、可注入但无 CSP 覆盖的端点。面试说"CSP 不是万能的"时，就举 JSONP 和 nonce 泄露这两个例子。

### 点击劫持（ClickJacking）

**一句话原理**：攻击页面用 CSS 把目标网站包进一个**透明 iframe**，叠在诱饵按钮上；受害者看到的按钮是假的，实际点下去点中的是 iframe 里目标网站的按钮。

```html
<!-- 攻击者页面（重叠+透明） -->
<iframe src="http://目标站/转账页" style="opacity:0; position:absolute; top:0; left:0;"></iframe>
<button style="position:absolute; top:10px; left:10px;">点我抽奖!</button>
```

- 与 CSRF 区别：CSRF 是"浏览器自动帮我发请求"；点击劫持是"骗受害者亲手点击"（UI 层攻击，无法用 token 防住——token 是受害者自己带上的）
- 防御（面试必答）：响应头 **`X-Frame-Options: DENY / SAMEORIGIN`**；或 CSP 的 **`frame-ancestors 'none'/'self'`**；两者同时设置兼容新旧浏览器

---

## 五、防御（面试必答，对应原理）

| 攻击 | 防御 | 对应原理 |
|---|---|---|
| CSRF | **Anti-CSRF Token**：每个敏感操作带随机 token，且 token 与 session 强绑定、一次性 | 攻击者页面无法预知受害者会话的 token，请求带不齐 |
| CSRF | **SameSite Cookie 属性**（`Lax`/`Strict`） | 跨站请求不再自动携带 Cookie，从浏览器层断根 |
| CSRF | 敏感操作只用 POST + 校验 `Content-Type`/自定义请求头 | 增加攻击者构造跨站表单的难度 |
| CSRF | 二次验证（改密需旧密码、转账需短信码） | 即使请求伪造成功，缺少人类确认信息 |
| Referer 类 | 不依赖 Referer，或用精确同源匹配 + 空 Referer 拒绝 | Referer 可伪造、可缺失 |
| 点击劫持 | `X-Frame-Options` + `frame-ancestors` 双重设置 | 禁止页面被嵌入第三方 iframe |
| CSP 被绕 | nonce 每次刷新 + 与请求绑定；JSONP 接口过滤回调白名单；收紧可信域名列表 | 堵死"圈内落点" |

---

## 六、面试速答卡

- **CSRF 三条件**：受害者已登录、知道请求结构、无额外验证
- **CSRF 和 XSS 区别**：XSS 偷身份在受害者浏览器跑代码；CSRF 借 Cookie 替他发请求
- **为什么不建议 GET 改数据**：`<img>` 自动发 GET，零交互触发 CSRF
- **token 防 CSRF 的原理**：攻击者拿不到受害者会话对应的随机 token
- **Referer 校验为什么不可靠**：请求头可伪造；空 Referer 常被放行；前缀匹配可绕过
- **CSP 绕过思路**：在可信源圈内找落点——JSONP 回调可控、nonce 泄露、可信域名可上传内容
- **点击劫持防御**：`X-Frame-Options: DENY` / CSP `frame-ancestors`
- **CSRF 最完整防线**：SameSite Cookie + token + 自定义头 + 二次验证的组合