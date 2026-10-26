# Web安全 · 1024 许愿池 HTTP 请求构造 WriteUp（DASCTF 环境）

- **题目**：1024 许愿池（`http://<hash>.http-ctf2.dasctf.com/`）
- **类型**：校验 / 逻辑类（非注入）——服务端校验 HTTP 请求的三个条件
- **难度**：入门，考点全在「能不能把一个 HTTP 请求**按字节精确**发对」

## 一、信息收集

```bash
curl -s -i 'http://<host>/'
```

`Server: openresty`，页面自述规则（考点直接写在页面上）：

| # | 条件 | 内容 |
|---|------|------|
| 1 | 方法+路径 | `POST /wish` |
| 2 | 头部 | `Content-Type: text/plain` |
| 3 | 请求体 | **正好 1024 字节**，以 `WISH:` 开头、`:1024` 结尾，中间随意 |

三个条件全过才给 flag，差一个会提示差在哪。

## 二、构造请求（每一步的为什么）

最终 body 形状：

```
WISH: + 'A'*1014 + :1024     →  5 + 1014 + 5 = 1024 字节
```

用 Python 生成并数长度，**不能靠肉眼数**：

```python
body = b"WISH:" + b"A"*1014 + b":1024"
print(len(body))   # 1024
open("wish_body.bin","wb").write(body)
```

发送：

```bash
curl -s -i -X POST \
  -H 'Content-Type: text/plain' \
  --data-binary @wish_body.bin \
  'http://<host>/wish'
```

三个容易翻车的点（都是构造时真实排除过的，本题一次通过）：

1. **不能用 `curl -d '...'` 直接发**：`-d` 的默认 `Content-Type` 是 `application/x-www-form-urlencoded`，条件 2 直接挂；而且表单编码模式会把 body 里的 `&`、`=` 等按表单语义处理。要发「纯字节流」用 `--data-binary`，再显式补 `-H 'Content-Type: text/plain'`。
2. **结尾换行 = 第 1025 个字节**：`@file` 方式 curl 会把文件**原样整读**，编辑器/`echo` 写出的文件末尾常带一个 `\n`，长度就变 1025。所以用 Python `open(...,"wb")` 写、`len()` 验过再发，别用文本编辑器手造文件。
3. **字节 ≠ 字符**：服务端按**字节**数。中间填充故意用 `A`（1 字节/字符）而不是中文或 emoji（UTF-8 下 3~4 字节/字符），让「字符数=字节数」避开编码坑。本题没有过滤规则要绕，填充内容随便选，选 `A` 纯粹是为了让长度可数。

## 三、结果

```
HTTP/1.1 200 OK
Content-Type: text/plain; charset=utf-8

DASCTF{0fb81f65-5b4e-437f-b6d3-d1a43624c143}
```

**flag：`DASCTF{0fb81f65-5b4e-437f-b6d3-d1a43624c143}`**

## 知识点沉淀

- HTTP 请求 = 请求行 + 头部 + 空行 + **body（纯字节序列）**。所谓"校验类"题，考的就是你能不能把这三段按服务端的声明精确发对。
- `Content-Type` 是发送方给 body 贴的**解析说明书**：服务端照着声明选解析器。声明 `text/plain` 就是"别解析，当原文"。声明错了，轻则校验不过，重则 body 被改写（表单编码）。
- curl 发 body 的三个姿势：`-d`（表单模式，会动 body）、`--data-urlencode`（主动 URL 编码，body 必被改）、`--data-binary`（字节原样，本题唯一正确选项）。
- 一切"长度必须等于 N"的校验，先问一句：**按字节还是按字符？** 然后**用代码数**，不用眼睛数。

## 关联

- 同环境：`Web安全-UnicornShop单字符与Unicode数字解析WriteUp.md`（同为校验类，那题考多解释器口径不一致，本题考请求本身构造）
- 机制延伸：`Web基础-站点搭建与HTTP工作原理.md`
