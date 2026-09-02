# Agent Framework 核心知识

基于 `example_agent/agent_framework.py` 的学习笔记。

---

## 1. Agent 的最小定义

```
Agent = LLM + 工具 + 循环（感知 → 思考 → 行动 → 观察）
```

三要素缺一不可：
- **LLM** — 大脑，做决策
- **工具** — 手脚，对外界产生影响
- **循环** — 多轮自主迭代，不是一次问答

---

## 2. 整体架构

```
用户输入题目 ──→ LLM 分析 ──→ LLM 决定调用工具？
                                  │
                    ┌──────────────┤
                    否（有文字回复）  是（tool_calls）
                    │              │
                  返回答案      执行工具函数
                                  │
                               结果送回 LLM
                                  │
                              下一轮循环 ──→ ...
```

---

## 3. 导入的六个库

| 库 | 类型 | 用途 |
|---|------|------|
| `openai` | 第三方 | LLM 客户端，调用 DeepSeek API |
| `dotenv` | 第三方 | 从 `.env` 文件加载环境变量 |
| `os` | 内置 | 读取环境变量 `os.getenv()` |
| `json` | 内置 | 解析 LLM 返回的 JSON 字符串为 Python 字典 |
| `subprocess` | 内置 | 执行系统命令（nmap、sqlmap 等） |
| `requests` | 第三方 | 发送 HTTP 请求 |

---

## 4. 类的结构

### 4.1 初始化 `__init__`

```python
def __init__(self):
    self.client = OpenAI(...)          # LLM 客户端
    self.tools = []                    # 工具 schema 列表（给 LLM 看）
    self.tools_functions = {}          # 工具名 → 函数映射（本地执行）
    self.system_prompt = "..."         # Agent 角色设定
    self._register_builtin_tools()     # 注册内置工具
```

### 4.2 工具注册系统

```python
def register_tool(self, name, description, func, parameters):
    self.tools_functions[name] = func  # 本地函数映射
    self.tools.append({                # LLM 能看到的 JSON Schema
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": parameters
        }
    })
```

**关键设计**：`tools`（schema）和 `tools_functions`（函数）分离。
- LLM 只看 schema，不知道函数实现
- 本地通过字典映射执行真正的 Python 函数

### 4.3 三个内置工具

| 工具 | 功能 | 实现 |
|------|------|------|
| `execute_command` | 执行系统命令 | `subprocess.run(shell=True, timeout=60)` |
| `send_request` | 发 HTTP 请求 | `requests.get()` / `requests.post()` |
| `read_file` | 读取文件 | `open(path, 'r')` |

### 4.4 核心循环 `solve`

```python
def solve(self, task):
    messages = [
        {"role": "system", "content": self.system_prompt},
        {"role": "user", "content": task}
    ]

    for iteration in range(30):          # 最多 30 轮，防止死循环

        # ① 发消息给 LLM
        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=self.tools,
            tool_choice="auto"
        )
        assistant_message = response.choices[0].message

        # ② 判断：LLM 要调工具吗？
        if assistant_message.tool_calls:
            messages.append(assistant_message)
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)

                # ③ 执行工具
                result = self.tools_functions[function_name](**arguments)

                # ④ 结果送回 LLM
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            # ⑤ 没有工具调用 → 返回最终答案
            return assistant_message.content
```

伪代码：
```
循环 {
    发消息给 LLM →
    if LLM 要调工具:
        执行工具 → 结果加到消息列表 → 继续循环
    else:
        返回文字回复 → 结束
}
```

---

## 5. 核心知识点

| 概念 | 对应实现 |
|------|---------|
| **Agent = LLM + 工具 + 循环** | `solve()` 方法 |
| **Function Calling** | `tools` schema + `tool_choice="auto"` |
| **ReAct 模式** | 思考 → 行动 → 观察 → 思考（循环体） |
| **消息历史** | `messages` 列表不断 append |
| **工具注册** | `register_tool()` 做 schema 和函数的绑定 |

---

## 6. 环境配置

### `.env` 文件

项目只有 `.env.example` 模板，需手动创建 `.env`：

```
DEEPSEEK_API_KEY=sk-你的真实key
DEEPSEEK_BASE_URL=https://api.deepseek.com
```

`load_dotenv()` 从当前工作目录查找 `.env` 并加载为环境变量。

### 运行方式

```bash
cd d:\ctf-agent
python example_agent/agent_framework.py
```

---

## 7. 与生产级 Agent 的差距

| 维度 | 基础 Agent（本脚本） | 生产级 Agent |
|------|-------------------|-------------|
| 记忆 | 仅当次对话 | 跨会话持久化记忆 |
| 规划 | 临时决策 | 先规划再执行（Plan & Execute） |
| 多 Agent | 一个干所有 | Supervisor + 多专家协作 |
| 反思 | 无 | Critic/Validator 模块 |
| 安全 | 直接执行任意命令 | 权限控制、命令白名单、沙箱 |
| 工具扩展 | 启动时固定 3 个 | MCP 协议动态发现新工具 |

---

## 8. 依赖安装

```bash
pip install openai python-dotenv requests
```
