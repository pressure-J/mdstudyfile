# FullAgent CTF解题Agent总结

基于 `example_agent/fullagent.py` 的学习笔记。

---

## 1. 脚本概述

这是一个**专业的CTF（Capture The Flag）解题Agent**，是`agent_framework.py`的升级版本。专注于CTF竞赛实战，具有自动检测flag并立即停止的特性。

---

## 2. 核心特性

### 2.1 FLAG自动检测机制
```python
def _has_flag(self, s):
    return re.search(r'flag\{.*?\}|NSSCTF\{.*?\}|ctf\{.*?\}', s, re.I) is not None
```

**支持的flag格式：**
- `flag{...}` - 通用格式
- `NSSCTF{...}` - NSSCTF平台格式
- `ctf{...}` - 其他CTF平台格式

**关键优势：** 一旦发现flag立即停止，避免无效循环，节省时间。

### 2.2 工具配置

| 工具名 | 功能 | 参数 | 超时 |
|--------|------|------|------|
| `send_request` | 发送HTTP请求 | url, method(GET/POST) | 10秒 |
| `execute_command` | 执行系统命令 | command | 30秒 |

---

## 3. 架构设计

### 3.1 类结构
```python
class CTFAgent:
    def __init__(self):
        self.client = OpenAI(...)      # LLM客户端
        self.tools = []                # 工具schema列表
        self.tool_funcs = {}           # 工具函数映射
        self._setup_tools()            # 初始化工具
```

### 3.2 工具注册系统
```python
tools_config = [
    {
        "name": "send_request",
        "desc": "发送HTTP请求",
        "func": self._send_request,
        "params": {...}
    },
    ...
]

# 自动注册工具
for tool in tools_config:
    self.tool_funcs[tool["name"]] = tool["func"]
    self.tools.append({
        "type": "function",
        "function": {
            "name": tool["name"],
            "description": tool["desc"],
            "parameters": tool["params"]
        }
    })
```

---

## 4. 核心解题流程

### 4.1 solve()方法
```python
def solve(self, task: str) -> str:
    messages = [
        {"role": "system", "content": "你是专业CTF选手..."},
        {"role": "user", "content": task}
    ]
    
    for i in range(50):  # 最多50轮
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        
        msg = response.choices[0].message
        
        if msg.tool_calls:
            # 执行工具调用
            for tc in msg.tool_calls:
                result = self.tool_funcs[name](**args)
                
                # 核心：检测flag
                if self._has_flag(result):
                    return result  # 发现flag立即返回
                
                messages.append({...})
        else:
            # 检测文本回复中的flag
            if self._has_flag(content):
                return content
```

### 4.2 流程图
```
用户输入目标网址
    ↓
Agent分析题目
    ↓
调用工具（HTTP请求/系统命令）
    ↓
检测结果是否包含flag
    ↓
发现flag → 立即返回 ✅
未发现 → 继续下一轮（最多50轮）🔄
    ↓
超时未找到 → 返回"未找到flag" ❌
```

---

## 5. 与agent_framework.py对比

| 特性 | agent_framework.py | fullagent.py |
|------|-------------------|--------------|
| **代码行数** | 196行 | 145行 |
| **工具数量** | 3个 | 2个 |
| **FLAG检测** | 无 | 有，发现即停止 |
| **最大轮数** | 30轮 | 50轮 |
| **系统提示** | 通用CTF助手 | 专业CTF选手 |
| **结果截断** | 无 | 2000字符 |
| **读取文件** | 支持 | 不支持 |
| **设计目标** | 教学演示 | 实战解题 |

---

## 6. 代码精简技巧

### 6.1 工具注册优化
```python
# agent_framework.py - 逐个注册，代码冗长
self.register_tool(name="execute_command", ...)
self.register_tool(name="send_request", ...)
self.register_tool(name="read_file", ...)

# fullagent.py - 列表配置，自动注册
tools_config = [...]
for tool in tools_config:
    self.tool_funcs[tool["name"]] = tool["func"]
```

### 6.2 系统提示精简
```python
# agent_framework.py - 详细说明
"""你是专业CTF选手。你有以下工具可用：
1. execute_command: 执行系统命令，如nmap、sqlmap等
2. send_request: 发送HTTP请求
3. read_file: 读取文件内容
请根据题目要求，合理使用工具解题。"""

# fullagent.py - 精简实战
"""你是专业CTF选手。
只要得到flag，立刻停止，输出flag。
必须调用工具获取结果。"""
```

### 6.3 核心功能强化
```python
# 用10行代码实现关键的flag检测
def _has_flag(self, s):
    return re.search(r'flag\{.*?\}|NSSCTF\{.*?\}|ctf\{.*?\}', s, re.I) is not None

# 在工具执行后立即检测
if self._has_flag(result):
    print("\n🎉🎉🎉 成功拿到FLAG！！！")
    return result
```

---

## 7. 使用方法

### 7.1 环境准备
```bash
# 安装依赖
pip install openai python-dotenv requests

# 配置.env文件
DEEPSEEK_API_KEY=sk-你的真实key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

### 7.2 运行方式
```bash
python example_agent/fullagent.py

# 输入目标网址
请输入CTF目标网址：http://target.com/challenge.php?id=1
```

### 7.3 使用示例
```python
# 作为模块导入
from fullagent import CTFAgent

agent = CTFAgent()
result = agent.solve("目标网址：http://target.com，找到flag")
print(result)
```

---

## 8. 设计哲学

### 8.1 "少即是多"
- **更少的代码**：145行 vs 196行
- **更少的工具**：2个 vs 3个
- **更强的功能**：自动flag检测
- **更高的效率**：发现即停止

### 8.2 专注核心
- 去掉`read_file`工具（CTF主要靠网络交互）
- 专注HTTP请求和系统命令执行
- 强化flag检测机制

### 8.3 实战导向
- 精简系统提示，减少token消耗
- 增加最大轮数（50轮），适应复杂题目
- 结果截断（2000字符），避免输出过长

---

## 9. 优势分析

### 9.1 效率优势
- **自动停止**：发现flag立即返回，不浪费时间
- **减少轮数**：避免无效的工具调用
- **节省token**：精简提示，降低API成本

### 9.2 实用优势
- **支持多平台**：兼容不同CTF平台的flag格式
- **错误处理**：网络请求和命令执行都有超时控制
- **结果过滤**：自动截断过长的输出

### 9.3 性能优势
- **更快响应**：更少的代码意味着更快的执行
- **更低延迟**：精简的提示减少LLM处理时间
- **更少资源**：内存和CPU占用更低

---

## 10. 扩展建议

### 10.1 增强flag检测
```python
# 支持更多flag格式
patterns = [
    r'flag\{.*?\}',
    r'NSSCTF\{.*?\}',
    r'ctf\{.*?\}',
    r'FLAG\{.*?\}',
    r'key\{.*?\}',
    r'secret\{.*?\}'
]
```

### 10.2 添加工具
- 文件分析工具（二进制、图片、文档）
- 密码学工具（编解码、hash破解）
- 网络工具（端口扫描、子域名枚举）

### 10.3 智能优化
- 根据题目类型自动选择工具
- 历史记录和学习机制
- 多Agent协作解题

---

## 11. 总结

`fullagent.py`是一个**精简高效的CTF解题Agent**，通过：

1. **精简设计**：更少的代码，更强的功能
2. **专注核心**：只保留CTF必需工具
3. **自动检测**：发现flag立即停止
4. **实战优化**：支持多平台flag格式

**核心优势：** 用更少的资源实现更高的效率，是CTF竞赛中的实用工具。

**适用场景：** CTF竞赛实战、安全挑战、自动化解题。