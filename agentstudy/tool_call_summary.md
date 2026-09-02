# Tool Calling工具调用总结

基于 `example_agent/tool_call.py` 的学习笔记。

---

## 1. 脚本概述

这是一个**Tool Calling（工具调用）**的基础示例，展示了如何让LLM调用自定义工具。这是Agent框架的核心功能之一。

---

## 2. 核心组件

### 2.1 工具函数
```python
def calculate(expression: str) -> str:
    """计算器工具"""
    try:
        result = eval(expression)
        return f"计算结果是：{expression}={result}"
    except Exception as e:
        return f"计算错误：{e}"
```

### 2.2 工具Schema（JSON格式）
```python
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "用于计算数学表达式",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "要计算的数学表达式"
                    }
                },
                "required": ["expression"]
            }
        }
    }
]
```

---

## 3. 核心循环

```python
def chat_with_tools(task: str) -> str:
    messages = [{"role": "user", "content": task}]
    
    for iteration in range(10):
        # 调用LLM，告诉它有哪些工具
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=messages,
            tools=tools,           # 告诉AI有哪些工具
            tool_choice="auto"    # 让AI自己决定是否调用工具
        )
        
        assistant_message = response.choices[0].message
        
        # 检查AI是否要调用工具
        if assistant_message.tool_calls:
            # AI要调用工具！
            for tool_call in assistant_message.tool_calls:
                function_name = tool_call.function.name
                arguments = json.loads(tool_call.function.arguments)
                
                # 执行工具
                result = calculate(arguments["expression"])
                
                # 把工具结果返回给AI
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })
        else:
            # AI没有调用工具，直接回复
            return assistant_message.content
```

---

## 4. 工作流程

```
用户输入："帮我算一下 (15 + 27) * 3 - 100/5"
    ↓
LLM分析任务
    ↓
LLM决定：需要调用calculate工具
    ↓
返回tool_calls：{"name": "calculate", "arguments": {"expression": "(15 + 27) * 3 - 100/5"}}
    ↓
执行工具：calculate("(15 + 27) * 3 - 100/5") = 106
    ↓
将结果返回给LLM
    ↓
LLM生成最终回复："计算结果是：(15 + 27) * 3 - 100/5 = 106"
```

---

## 5. 关键参数解析

### 5.1 `tools` 参数
```python
# 告诉LLM有哪些工具可用
tools = [
    {
        "type": "function",
        "function": {
            "name": "calculate",          # 工具名称
            "description": "用于计算数学表达式",  # 工具描述
            "parameters": {               # 参数schema
                "type": "object",
                "properties": {
                    "expression": {"type": "string"}
                },
                "required": ["expression"]
            }
        }
    }
]
```

### 5.2 `tool_choice` 参数
```python
tool_choice="auto"  # 让LLM自己决定是否调用工具
# 其他选项：
# "none" - 强制不调用工具
# "required" - 强制调用工具
# {"type": "function", "function": {"name": "calculate"}} - 强制调用指定工具
```

### 5.3 工具调用结果格式
```python
# LLM返回的工具调用
assistant_message.tool_calls = [
    {
        "id": "call_xxx",
        "function": {
            "name": "calculate",
            "arguments": "{\"expression\": \"(15 + 27) * 3 - 100/5\"}"
        }
    }
]

# 将结果返回给LLM
messages.append({
    "role": "tool",
    "tool_call_id": "call_xxx",
    "content": "计算结果是：(15 + 27) * 3 - 100/5 = 106"
})
```

---

## 6. 测试示例

```python
# 测试1：简单计算
chat_with_tools("帮我算一下 (15 + 27) * 3 - 100/5 等于多少")
# LLM会调用calculate工具，返回结果

# 测试2：需要多步计算
chat_with_tools("先算 123 * 456，然后把结果除以7")
# LLM可能需要多轮调用工具
```

---

## 7. 与其他文件的关系

### 这是Agent的核心基础

| 文件 | Tool Calling | 说明 |
|------|--------------|------|
| **tool_call.py** | ✅ 基础示例 | 展示Tool Calling原理 |
| agent_framework.py | ✅ 完整实现 | Agent = LLM + Tool Calling + 循环 |
| fullagent.py | ✅ 优化实现 | 专注CTF的Tool Calling |
| pipeline.py | ✅ 多Agent | 每个Agent都有Tool Calling |
| parallel.py | ❌ 无 | 只有LLM调用，无工具 |
| supervisior.py | ✅ 路由 | Supervisor路由到专家Agent |

### 演进关系
```
tool_call.py（基础示例）
    ↓ 添加系统提示、循环控制
agent_framework.py（基础Agent）
    ↓ 优化flag检测、精简代码
fullagent.py（专业CTF Agent）
    ↓ 多个Agent协作
pipeline.py（流水线模式）
parallel.py（并行模式）
supervisior.py（监督者模式）
```

---

## 8. 安全注意事项

```python
# ⚠️ 危险：使用eval()执行任意代码
def calculate(expression: str) -> str:
    result = eval(expression)  # 如果用户输入"__import__('os').system('rm -rf /')"就危险了

# ✅ 安全改进：使用ast.literal_eval()或白名单
import ast
def safe_calculate(expression: str) -> str:
    # 只允许数学表达式
    tree = ast.parse(expression, mode='eval')
    # 检查是否只包含数学操作
    ...
```

---

## 9. 总结

`tool_call.py`是**Tool Calling的基础示例**，展示了：

1. **工具定义**：函数 + JSON Schema
2. **工具调用**：LLM决定是否调用、调用哪个、传什么参数
3. **结果返回**：将工具结果返回给LLM
4. **循环控制**：最多10轮，直到LLM给出最终回复

**核心价值：** 这是Agent框架的基石。所有Agent（agent_framework、fullagent、pipeline等）都基于这个原理。

**一句话总结：** Tool Calling让LLM从"只能聊天"变成"能干活"，是Agent的核心能力。