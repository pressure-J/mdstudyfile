# Workflow工作流引擎总结

基于 `example_agent/workflow.py` 的学习笔记。

---

## 1. 脚本概述

这是一个**工作流引擎**，用于定义和执行复杂的任务流程。它实现了可视化、可配置的工作流系统，支持节点连接、条件分支、并行执行和结果合并。

---

## 2. 核心组件

### 2.1 NodeType枚举 - 节点类型
```python
class NodeType(Enum):
    AGENT = "agent"         # Agent节点
    CONDITION = "condition" # 条件分支
    PARALLEL = "parallel"   # 并行执行
    MERGE = "merge"         # 合并结果
```

### 2.2 Node类 - 工作流节点
```python
class Node:
    def __init__(self, id: str, type: NodeType, config: dict):
        self.id = id
        self.type = type
        self.config = config
        self.next_nodes = []  # 下一个节点列表
    
    def connect(self, node, condition: str = None):
        """连接到下一个节点"""
        self.next_nodes.append({
            "node": node,
            "condition": condition
        })
    
    def execute(self, state: dict) -> str:
        """执行节点（根据类型分发）"""
        if self.type == NodeType.AGENT:
            return self._execute_agent(state)
        elif self.type == NodeType.CONDITION:
            return self._evaluate_condition(state)
        elif self.type == NodeType.PARALLEL:
            return self._execute_parallel(state)
        elif self.type == NodeType.MERGE:
            return self._merge_results(state)
```

### 2.3 Workflow类 - 工作流控制器
```python
class Workflow:
    def __init__(self, name: str):
        self.name = name
        self.nodes = {}
        self.start_node = None
    
    def add_node(self, node: Node):
        """添加节点"""
        self.nodes[node.id] = node
    
    def set_start(self, node_id: str):
        """设置起点"""
        self.start_node = self.nodes[node_id]
    
    def execute(self, initial_state: dict = None) -> dict:
        """执行工作流"""
        state = initial_state or {}
        current_node = self.start_node
        
        while current_node:
            # 1. 执行当前节点
            result = current_node.execute(state)
            
            # 2. 存储结果
            state[f"result_{current_node.id}"] = result
            
            # 3. 寻找下一个节点
            current_node = self._next_node(current_node, state)
        
        return state
```

---

## 3. 四种节点类型

### 3.1 AGENT节点 - 执行Agent任务
```python
def _execute_agent(self, state: dict) -> str:
    agent = self.config["agent"]
    task = self.config.get("task", "完成任务")
    context = state.get("context", {})
    return agent.think(task, context)
```

### 3.2 CONDITION节点 - 条件判断
```python
def _evaluate_condition(self, state: dict) -> str:
    condition = self.config["condition"]
    if eval(condition, {"state": state}):
        return "true"
    return "false"
```

### 3.3 PARALLEL节点 - 并行执行
```python
def _execute_parallel(self, state: dict) -> str:
    import concurrent.futures
    agents = self.config["agents"]
    task = self.config.get("task", "完成任务")
    results = {}
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(agents)) as executor:
        futures = {
            executor.submit(agent.think, task): name
            for name, agent in agents.items()
        }
        for future in concurrent.futures.as_completed(futures):
            name = futures[future]
            results[name] = future.result()
    
    return json.dumps(results, ensure_ascii=False)
```

### 3.4 MERGE节点 - 合并结果
```python
def _merge_results(self, state: dict) -> str:
    results = []
    for key, value in state.items():
        if key.startswith("result_"):
            results.append(f"### {key}\n{value}")
    return "\n\n".join(results)
```

---

## 4. 工作流程图

```
┌─────────────┐
│ recon_node  │ (开始)
└──────┬──────┘
       ↓
┌─────────────┐
│ check_node  │ (条件判断)
└──────┬──────┘
       ↓
   ┌───┴───┐
   │       │
 true    false
   │       │
   ↓       ↓
┌──────┐  ┌─────┐
│ vuln │  │结束 │
└──┬───┘  └─────┘
   ↓
┌─────────────┐
│exploit_node │
└─────────────┘
```

---

## 5. 使用示例

```python
# 1. 创建Agent
recon_agent = BaseAgent("侦察", "信息收集专家")
vuln_agent = BaseAgent("漏洞", "漏洞分析专家")
exploit_agent = BaseAgent("利用", "漏洞利用专家")

# 2. 创建节点
recon_node = Node("recon", NodeType.AGENT, {"agent": recon_agent, "task": "收集目标信息"})
check_node = Node("check", NodeType.CONDITION, {"condition": "len(state.get('result_recon', '')) > 100"})
vuln_node = Node("vuln", NodeType.AGENT, {"agent": vuln_agent, "task": "分析漏洞"})
exploit_node = Node("exploit", NodeType.AGENT, {"agent": exploit_agent, "task": "利用漏洞获取flag"})

# 3. 连接节点
recon_node.connect(check_node)                  # 侦察完 → 判断
check_node.connect(vuln_node, condition="true") # 判断为真 → 漏洞分析
check_node.connect(None, condition="false")     # 判断为假 → 结束
vuln_node.connect(exploit_node)                 # 漏洞分析完 → 利用

# 4. 创建工作流
workflow = Workflow("CTF解题")
workflow.add_node(recon_node)
workflow.add_node(check_node)
workflow.add_node(vuln_node)
workflow.add_node(exploit_node)
workflow.set_start("recon")

# 5. 执行
final_state = workflow.execute({"target": "http://example.com"})
```

---

## 6. 状态管理

```python
# 全局状态示例
state = {
    "target": "http://example.com",           # 初始输入
    "result_recon": "【侦察 - 信息收集专家】已完成：收集目标信息",
    "result_check": "true",                   # 条件判断结果
    "result_vuln": "【漏洞 - 漏洞分析专家】已完成：分析漏洞",
    "result_exploit": "【利用 - 漏洞利用专家】已完成：利用漏洞获取flag",
    "context": {                              # 上下文
        "recon": "...",
        "vuln": "...",
        "exploit": "..."
    }
}
```

---

## 7. 与其他模式的对比

| 特性 | Workflow（工作流） | Pipeline（流水线） | Supervisor（监督者） |
|------|-------------------|-------------------|---------------------|
| **流程定义** | 可视化节点连接 | 固定顺序列表 | 动态路由 |
| **条件分支** | ✅ 支持 | ❌ 不支持 | ✅ 支持（LLM决策） |
| **并行执行** | ✅ 支持（PARALLEL节点） | ❌ 不支持 | ✅ 支持 |
| **结果合并** | ✅ 支持（MERGE节点） | ❌ 无 | ✅ 支持 |
| **灵活性** | ⭐⭐⭐⭐⭐ 最高 | ⭐⭐ 低 | ⭐⭐⭐⭐ 高 |
| **可视化** | ✅ 容易可视化 | ❌ 不容易 | ❌ 不容易 |

---

## 8. 优势分析

### 8.1 可视化流程
- 节点连接清晰
- 容易理解和调试
- 可以画出流程图

### 8.2 灵活配置
- 支持条件分支
- 支持并行执行
- 支持结果合并

### 8.3 状态管理
- 全局状态贯穿整个流程
- 每个节点的结果自动存储
- 上下文可以传递

### 8.4 可扩展性
- 易于添加新节点类型
- 易于添加新Agent
- 易于修改流程

---

## 9. 扩展应用

### 9.1 CTF自动解题
```python
# 侦察 → 判断 → 漏洞分析 → 利用 → 合并结果
workflow = build_ctf_workflow()
workflow.execute({"target": "http://ctf.example.com"})
```

### 9.2 安全审计
```python
# 网络扫描 → Web扫描 → 代码审计 → 合并报告
workflow = build_audit_workflow()
workflow.execute({"target": "192.168.1.0/24"})
```

### 9.3 渗透测试
```python
# 侦察 → 漏洞扫描 → 漏洞利用 → 权限提升 → 报告生成
workflow = build_pentest_workflow()
workflow.execute({"target": "http://target.com"})
```

---

## 10. 总结

`workflow.py`是一个**可视化工作流引擎**，通过：

1. **节点化设计**：将任务分解为节点
2. **可视化连接**：通过connect()连接节点
3. **条件分支**：支持if/else逻辑
4. **并行执行**：支持多Agent同时工作
5. **状态管理**：全局状态贯穿整个流程

**核心价值：** 将复杂的多步骤任务转化为可视化、可配置的工作流，易于理解和维护。

**适用场景：** 需要复杂流程控制、条件分支、并行执行的任务，如CTF解题、安全审计、渗透测试等。