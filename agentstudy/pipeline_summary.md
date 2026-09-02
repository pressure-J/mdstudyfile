# Pipeline流水线模式总结

基于 `example_agent/pipeline.py` 的学习笔记。

---

## 1. 脚本概述

这是一个**流水线（Pipeline）模式**的多Agent协作系统，用于按顺序执行多个专业Agent，通过上下文传递实现接力完成复杂任务。

---

## 2. 核心组件

### 2.1 BaseAgent类 - 基础Agent
```python
class BaseAgent:
    def __init__(self, name: str, system_prompt: str):
        self.name = name
        self.system_prompt = system_prompt
        self.client = OpenAI(...)
        self.tools = []
        self.tool_funcs = {}
    
    def register_tool(self, name, desc, func, params):
        """注册工具"""
        self.tool_funcs[name] = func
        self.tools.append({...})
    
    def think(self, task: str, context: dict = None) -> str:
        """Agent思考并执行"""
        # 支持上下文传递
        if context:
            messages.append({"role": "user", "content": f"已知信息:\n{json.dumps(context)}"})
```

**特点：**
- 支持工具注册和调用
- 支持上下文传递（来自前一个Agent的结果）
- 最多执行10轮工具调用

### 2.2 Pipeline类 - 流水线协调器
```python
class Pipeline:
    def __init__(self, agents: list):
        self.agents = agents
    
    def run(self, initial_task: str) -> dict:
        """执行流水线"""
        context = {"task": initial_task}
        results = {}
        
        for agent in self.agents:
            result = agent.think(
                task=f"基于上下文完成任务: {context.get('task', initial_task)}",
                context=context
            )
            
            results[agent.name] = result
            context[agent.name] = result
            context["task"] = f"基于 {agent.name} 的结果继续"
```

---

## 3. 工作流程

```
用户输入初始任务（如"扫描 http://example.com"）
    ↓
Agent 1（侦察Agent）执行
    ↓ 收集信息，传递给下一个
Agent 2（漏洞Agent）执行
    ↓ 分析漏洞，传递给下一个
Agent 3（利用Agent）执行
    ↓ 尝试利用漏洞
返回所有结果
```

---

## 4. 上下文传递机制

```python
# 初始上下文
context = {"task": "扫描 http://example.com"}

# Agent 1 执行后
context = {
    "task": "基于 侦察Agent 的结果继续",
    "侦察Agent": "发现3个开放端口：80, 443, 22..."
}

# Agent 2 执行后
context = {
    "task": "基于 漏洞Agent 的结果继续",
    "侦察Agent": "发现3个开放端口...",
    "漏洞Agent": "发现SQL注入漏洞在id参数..."
}

# Agent 3 执行后
context = {
    "task": "基于 利用Agent 的结果继续",
    "侦察Agent": "...",
    "漏洞Agent": "...",
    "利用Agent": "成功获取flag{...}"
}
```

---

## 5. 使用示例

### 5.1 基本流水线
```python
# 创建Agent
recon_agent = BaseAgent(
    name="侦察Agent",
    system_prompt="你是一个信息收集专家..."
)
recon_agent.register_tool("send_request", ...)

vuln_agent = BaseAgent(
    name="漏洞Agent",
    system_prompt="你是一个漏洞分析专家..."
)

exploit_agent = BaseAgent(
    name="利用Agent",
    system_prompt="你是一个漏洞利用专家..."
)
exploit_agent.register_tool("send_request", ...)

# 创建流水线
pipeline = Pipeline([recon_agent, vuln_agent, exploit_agent])

# 执行任务
results = pipeline.run("http://testphp.vulnweb.com/")
```

### 5.2 渗透测试流水线
```python
# 侦察 → 漏洞扫描 → 漏洞利用 → 权限提升
pipeline = Pipeline([
    recon_agent,      # 侦察
    scan_agent,       # 扫描
    exploit_agent,    # 利用
    post_agent        # 后渗透
])
```

### 5.3 代码审计流水线
```python
# 代码分析 → 漏洞识别 → 报告生成
pipeline = Pipeline([
    analysis_agent,   # 代码分析
    vuln_agent,       # 漏洞识别
    report_agent      # 报告生成
])
```

---

## 6. 为什么选择多Agent流水线？

### 6.1 专业分工 vs 全能选手

| 方面 | 单一Agent | 多Agent流水线 |
|------|----------|--------------|
| **角色** | 什么都做，但都不精通 | 每个Agent专注一个领域 |
| **提示词** | 很长，包含所有职责 | 短小精悍，只关注一件事 |
| **效果** | 容易混淆，质量不稳定 | 专业输出，质量稳定 |

**比喻：**
- 单一Agent = 一个全科医生（什么都会一点，但都不精通）
- 多Agent = 专家会诊（心脏科、神经科、骨科各司其职）

### 6.2 上下文管理优势

```python
# 单一Agent的上下文爆炸问题
messages = [
    {"role": "system", "content": "你是信息收集专家...漏洞分析专家...漏洞利用专家..."},
    # ... 大量工具调用和结果，上下文越来越长
]
# 问题：上下文太长，LLM容易遗忘早期信息，质量下降

# 多Agent流水线的上下文管理
# Agent 1: 只处理侦察，上下文短小
# Agent 2: 只处理漏洞分析，基于Agent 1的结果
# Agent 3: 只处理漏洞利用，基于Agent 2的结果
# 优势：每个Agent的上下文都很短，专注于当前任务
```

### 6.3 错误隔离

```python
# 单一Agent：一个环节出错，整个任务失败
# 例如：侦察阶段出错，后续漏洞分析和利用都会受影响

# 多Agent流水线：错误可以被隔离和处理
if agent1失败:
    # 可以重试agent1，或者使用备用策略
    # 不影响其他Agent的设计
```

### 6.4 可维护性和可调试性

```python
# 单一Agent：代码臃肿，难以调试
def solve(task):
    # 100行信息收集逻辑
    # 100行漏洞分析逻辑
    # 100行漏洞利用逻辑
    # 难以定位问题在哪里

# 多Agent流水线：模块化，易于调试
pipeline = Pipeline([
    recon_agent,    # 独立调试
    vuln_agent,     # 独立调试
    exploit_agent   # 独立调试
])
```

---

## 7. 技术优势

### 7.1 提示词优化
```python
# 单一Agent的提示词（很长）
system_prompt = """你是专业的渗透测试专家。
你需要完成以下任务：
1. 信息收集：使用nmap扫描端口，使用dirb扫描目录...
2. 漏洞分析：检查SQL注入、XSS、命令注入...
3. 漏洞利用：编写payload，测试漏洞...
4. 权限提升：如果需要的话...
5. 报告生成：整理结果..."""

# 多Agent的提示词（每个都很短）
recon_prompt = "你是信息收集专家，只关注收集目标的基本信息。"
vuln_prompt = "你是漏洞分析专家，只关注识别安全漏洞。"
exploit_prompt = "你是漏洞利用专家，只关注获取flag。"
```

### 7.2 工具管理
```python
# 单一Agent：需要注册所有工具
agent.register_tool("nmap扫描", ...)
agent.register_tool("目录扫描", ...)
agent.register_tool("SQL注入测试", ...)
agent.register_tool("XSS测试", ...)
# 工具太多，LLM可能选择错误的工具

# 多Agent：每个Agent只注册需要的工具
recon_agent.register_tool("nmap扫描", ...)
recon_agent.register_tool("目录扫描", ...)

vuln_agent.register_tool("SQL注入测试", ...)
vuln_agent.register_tool("XSS测试", ...)
```

---

## 8. 与其他模式的对比

| 特性 | Pipeline（流水线） | Parallel（并行） | 单Agent |
|------|-------------------|-----------------|---------|
| **执行方式** | 顺序执行 | 并行执行 | 单独执行 |
| **上下文传递** | 支持，自动传递 | 无，各自独立 | 无需 |
| **结果依赖** | 前后依赖 | 互不依赖 | 无 |
| **适用场景** | 多步骤任务 | 多维度分析 | 简单任务 |
| **效率** | 串行，较慢 | 并行，较快 | 最快 |
| **协作性** | 强，接力完成 | 中，各自贡献 | 无 |

---

## 9. 适用场景

### 9.1 适合流水线的场景
- **复杂多步骤任务**：渗透测试、安全审计
- **需要专业知识**：不同领域专家协作
- **长上下文任务**：避免上下文爆炸
- **可维护性要求高**：模块化设计

### 9.2 不适合流水线的场景
- **简单任务**：单一Agent更快
- **独立任务**：并行模式更高效
- **实时性要求高**：流水线有延迟

---

## 10. 实际案例

### 10.1 CTF竞赛
```python
pipeline = Pipeline([
    recon_agent,      # 侦察题目类型
    strategy_agent,   # 制定解题策略
    exploit_agent     # 执行解题
])
```

### 10.2 安全审计
```python
pipeline = Pipeline([
    network_agent,    # 网络层审计
    web_agent,        # Web应用审计
    code_agent,       # 代码审计
    report_agent      # 报告生成
])
```

### 10.3 渗透测试
```python
pipeline = Pipeline([
    recon_agent,      # 信息收集
    scan_agent,       # 漏洞扫描
    exploit_agent,    # 漏洞利用
    post_agent        # 后渗透
])
```

---

## 11. 总结

`pipeline.py`是一个**流水线模式的多Agent协作系统**，通过：

1. **顺序执行**：按顺序执行多个Agent
2. **上下文传递**：自动传递前一个Agent的结果
3. **专业化分工**：每个Agent专注特定领域
4. **结果收集**：自动收集所有结果

**核心价值：** 实现多步骤、多阶段的任务协作，形成完整的工作流。

**为什么选择多Agent流水线？**
- **专业分工**：每个Agent专注一件事，做得更好
- **上下文管理**：避免上下文爆炸，提高准确性
- **错误隔离**：一个环节出错不影响整体
- **可维护性**：模块化设计，易于调试和扩展
- **质量稳定**：分工明确，输出质量更可控

**适用场景：** 渗透测试、代码审计、安全响应等需要多阶段协作的复杂任务。

**一句话总结：** 多Agent流水线通过"专业化分工"和"上下文隔离"，在复杂任务中实现比单一Agent更好的效果。