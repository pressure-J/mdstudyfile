# CTF工具集总结

基于 `example_agent/ctf_tools.py` 的学习笔记。

---

## 1. 脚本概述

这是一个**CTF（Capture The Flag）安全竞赛工具包**，提供了多种安全测试、密码学和文件分析工具。脚本采用模块化设计，每个工具都是独立的函数，可以单独调用。

---

## 2. 功能模块分类

### 2.1 Web安全工具

| 函数名 | 功能 | 依赖工具 | 参数 |
|--------|------|----------|------|
| `sqlmap_scan` | SQL注入扫描 | sqlmap | url, param, level |
| `dirb_scan` | 目录扫描 | dirb | url |
| `xss_test` | XSS测试 | requests | url, param |

**示例：**
```python
# SQL注入扫描
result = sqlmap_scan("http://target.com/page.php?id=1", param="id", level=2)

# 目录扫描
result = dirb_scan("http://target.com/")

# XSS测试
result = xss_test("http://target.com/search.php", "q")
```

### 2.2 Crypto工具

| 函数名 | 功能 | 说明 |
|--------|------|------|
| `base64_encode` | Base64编码 | 将文本转换为Base64 |
| `base64_decode` | Base64解码 | 将Base64转换为文本 |
| `hash_crack` | Hash类型识别 | 识别MD5/SHA1/SHA256 |
| `caesar_cipher` | 凯撒密码解密 | 支持任意偏移量 |
| `rot13` | ROT13解密 | 凯撒密码的特例（偏移13） |
| `hex_decode` | 十六进制解码 | 将十六进制转换为文本 |
| `xor_decode` | XOR解密 | 使用指定密钥解密 |

**示例：**
```python
# Base64解码
result = base64_decode("SGVsbG8gV29ybGQ=")  # 输出: Hello World

# Hash识别
result = hash_crack("5d41402abc4b2a76b9719d911017c592")
# 输出: 识别为: MD5

# 凯撒密码解密
result = caesar_cipher("Uryyb", 13)  # 输出: Hello

# ROT13解密
result = rot13("Uryyb")  # 输出: Hello

# 十六进制解码
result = hex_decode("48656c6c6f")  # 输出: Hello
```

### 2.3 Misc工具

| 函数名 | 功能 | 说明 |
|--------|------|------|
| `extract_strings` | 提取可读字符串 | 从二进制文件中提取，自动筛选flag相关内容 |

**示例：**
```python
# 从文件中提取字符串
result = extract_strings("suspicious_file.bin")
```

### 2.4 HTTP工具

| 函数名 | 功能 | 说明 |
|--------|------|------|
| `send_request` | 发送HTTP请求 | 支持GET/POST方法 |

**示例：**
```python
# GET请求
response = send_request("http://example.com")

# POST请求
response = send_request("http://example.com/login", 
                       method="POST", 
                       data="user=admin&pass=123")
```

---

## 3. 工具注册系统

脚本使用`CTF_TOOLS`字典统一管理所有工具：

```python
CTF_TOOLS = {
    "tool_name": {
        "func": function_reference,      # 实际函数
        "desc": "工具描述",              # 中文描述
        "params": {                      # JSON Schema格式参数
            "type": "object",
            "properties": {
                "param1": {"type": "string", "description": "参数说明"}
            },
            "required": ["param1"]       # 必需参数
        }
    }
}
```

**使用方式：**
```python
# 查看所有可用工具
for tool_name, tool_info in CTF_TOOLS.items():
    print(f"{tool_name}: {tool_info['desc']}")

# 动态调用工具
tool = CTF_TOOLS["base64_decode"]
result = tool["func"]("SGVsbG8=")
```

---

## 4. 技术特点

### 4.1 模块化设计
- 每个工具都是独立函数
- 可以单独导入使用
- 通过`CTF_TOOLS`字典统一管理

### 4.2 异常处理
- 所有函数都有try-except块
- 返回友好的错误信息
- 防止单个工具失败影响整体

### 4.3 实用功能
- **自动筛选**：`extract_strings`会自动过滤包含"flag"或"ctf"的内容
- **超时控制**：网络请求有超时限制（10-300秒）
- **结果截断**：避免返回过长的输出

### 4.4 密码学工具
- 支持常见的编解码格式
- 实现了经典的凯撒密码和ROT13
- 提供XOR解密功能

---

## 5. 使用方法

### 5.1 直接导入函数
```python
from ctf_tools import base64_decode, hash_crack

result = base64_decode("SGVsbG8=")
print(result)
```

### 5.2 使用CTF_TOOLS字典
```python
from ctf_tools import CTF_TOOLS

# 动态调用
tool = CTF_TOOLS["base64_decode"]
result = tool["func"]("SGVsbG8=")
```

### 5.3 批量测试
```python
from ctf_tools import xss_test

# 测试多个参数
params = ["q", "search", "input", "query"]
for param in params:
    result = xss_test("http://target.com/search.php", param)
    if "XSS" in result:
        print(f"发现漏洞: 参数 {param}")
        break
```

---

## 6. 注意事项

### 6.1 依赖安装
```bash
pip install requests
```

### 6.2 外部工具
- `sqlmap`：需要单独安装
- `dirb`：需要单独安装
- `strings`：Linux命令，Windows需要替代方案

### 6.3 Windows兼容性
- 部分命令（如strings）在Windows上可能不可用
- 需要调整路径分隔符
- 某些shell命令可能不兼容

### 6.4 安全考虑
- 网络请求有超时限制
- 文件操作有异常处理
- 避免执行危险的系统命令

---

## 7. 与agent_framework.py的关系

`ctf_tools.py`是`agent_framework.py`的**工具库**，为Agent提供具体的CTF工具函数。

**调用关系：**
```
agent_framework.py (Agent)
    ↓ 调用工具函数
ctf_tools.py (工具库)
    ↓ 执行具体操作
系统命令/网络请求/文件操作
```

**整合方式：**
```python
# 在agent_framework.py中注册CTF工具
from ctf_tools import CTF_TOOLS

for tool_name, tool_info in CTF_TOOLS.items():
    agent.register_tool(
        name=tool_name,
        description=tool_info["desc"],
        func=tool_info["func"],
        parameters=tool_info["params"]
    )
```

---

## 8. 扩展建议

### 8.1 添加更多工具
- 文件格式解析（PNG、PDF、ZIP等）
- 编码转换（URL编码、HTML实体等）
- 网络工具（端口扫描、子域名枚举等）

### 8.2 改进现有工具
- 增加更多XSS payload
- 支持更多hash类型
- 添加字典攻击功能

### 8.3 增强功能
- 并行执行多个工具
- 结果缓存机制
- 工具调用日志

---

## 9. 总结

`ctf_tools.py`是一个功能丰富的CTF工具集，提供了：

1. **Web安全测试**：SQL注入、目录扫描、XSS检测
2. **密码学工具**：编解码、hash识别、经典密码破解
3. **文件分析**：字符串提取、二进制分析
4. **HTTP工具**：灵活的请求发送

该脚本采用模块化设计，易于扩展和维护，是CTF竞赛中实用的自动化工具库。