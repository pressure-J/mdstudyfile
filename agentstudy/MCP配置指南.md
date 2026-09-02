# MCP（Model Context Protocol）配置指南

> 日期：2026-08-20
> 来源：Hermes Agent 桌面端实践

---

## 什么是 MCP？

MCP（Model Context Protocol）是一种协议，定义了 Agent 和服务器之间的通信规则：

- **服务器**：按 MCP 协议编写功能脚本，提供工具给 Agent
- **Agent**：按 MCP 协议调用服务器的工具完成功能
- **协议**：定义了工具发现、调用方式、通信格式

### 类比

```
Agent（Hermes）          MCP 协议           MCP 服务器
     │                    │                    │
     │  "你有什么工具？"   │ ──────────────────>│
     │                    │                    │
     │  "我有这些工具"     │ <──────────────────│
     │                    │                    │
     │  "调用工具A，参数X" │ ──────────────────>│
     │                    │                    │
     │  "工具A的结果Y"    │ <──────────────────│
```

---

## Hermes 内置工具 vs MCP

### 内置工具（已有）

| 工具 | 功能 |
|------|------|
| `terminal` | 执行命令 |
| `read_file` | 读取文件 |
| `write_file` | 写入文件 |
| `search_files` | 搜索文件 |
| `list_directory` | 列出目录 |
| `patch` | 编辑文件 |
| `get_file_info` | 获取文件信息 |
| `process` | 管理进程 |
| `todo` | 任务管理 |
| `memory` | 持久记忆 |
| `web` | 网页搜索 |
| `browser` | 浏览器自动化 |

### MCP 的真正价值

MCP 适合扩展**内置工具没有的能力**：

| 场景 | MCP 服务器 | 内置工具有吗？ |
|------|------------|----------------|
| 数据库操作 | `sqlite`、`postgres` | ❌ 没有 |
| GitHub API | `github` | ❌ 没有（只有 `gh` 命令行） |
| Notion | `notion` | ❌ 没有 |
| Docker | `docker` | ❌ 没有 |
| 专用 API | 自定义服务器 | ❌ 没有 |

---

## 配置方式

### 方式1：桌面端界面

桌面端 MCP 配置参数：

| 参数 | 说明 |
|------|------|
| **名称** | 服务器名称（自定义） |
| **URL** | stdio = 命令（如 `npx`），HTTP = 远程地址 |
| **传输方式** | `stdio` 或 `HTTP` |
| **环境变量** | 传递给服务器的变量 |

### 方式2：编辑 config.yaml

文件路径：`~/.hermes/config.yaml`

```yaml
mcp_servers:
  # 文件系统服务器
  filesystem:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-filesystem", "D:/mdstudyfile"]
    timeout: 30

  # GitHub 服务器（需要 Token）
  github:
    command: "npx"
    args: ["-y", "@modelcontextprotocol/server-github"]
    env:
      GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxx"
    timeout: 60
```

---

## 配置参数详解

### `command`
执行的命令，用于启动 MCP 服务器。

常用值：
- `"npx"` — Node.js 包管理器
- `"uvx"` — Python 包管理器
- `"node"` — 直接运行 Node.js 脚本

### `args`
传递给命令的参数列表。

示例：
```yaml
args: ["-y", "@modelcontextprotocol/server-filesystem", "D:/mdstudyfile"]
```

拆解：
- `-y` — 自动确认安装
- `@modelcontextprotocol/server-filesystem` — 包名
- `D:/mdstudyfile` — 允许访问的目录

### `env`
传递给 MCP 服务器的环境变量（可选）。

```yaml
env:
  GITHUB_PERSONAL_ACCESS_TOKEN: "ghp_xxxxxxxx"
```

### `timeout`
单次工具调用的超时时间（秒），默认 120。

### `connect_timeout`
初始连接和工具发现的超时时间（秒），默认 60。

---

## 工具命名规则

MCP 工具自动加上前缀：`mcp_{服务器名}_{工具名}`

例如：
- 服务器 `filesystem` + 工具 `read_file` → `mcp_filesystem_read_file`
- 服务器 `github` + 工具 `list-issues` → `mcp_github_list_issues`

---

## 传输类型

### 本地（stdio）
```yaml
command: "npx"
args: [...]
```

### 远程（HTTP）
```yaml
url: "https://example.com/mcp"
headers:
  Authorization: "Bearer sk-..."
```

两种不能同时存在。

---

## 常用 MCP 服务器

| 服务器 | 安装命令 | 用途 |
|--------|----------|------|
| `@modelcontextprotocol/server-filesystem` | `npx -y ...` | 文件系统 |
| `@modelcontextprotocol/server-github` | `npx -y ...` | GitHub 操作 |
| `@modelcontextprotocol/server-sqlite` | `npx -y ...` | SQLite 数据库 |
| `@modelcontextprotocol/server-time` | `npx -y ...` | 获取时间 |
| `@modelcontextprotocol/server-brave-search` | `npx -y ...` | 网页搜索 |

---

## 常用命令

```bash
hermes mcp list          # 查看已配置的 MCP 服务器
hermes mcp add NAME      # 添加服务器
hermes mcp remove NAME   # 删除服务器
hermes mcp test NAME     # 测试连接
hermes mcp configure NAME # 配置工具选择
```

---

## 注意事项

1. **环境变量安全** — stdio 模式不会传递完整 shell 环境，敏感信息需在 `env` 中显式指定
2. **重启生效** — 添加或删除服务器后需要重启 Hermes
3. **工具注入** — MCP 工具会自动注入到所有平台（CLI、Telegram、Discord 等）
4. **工具发现** — 服务器启动时自动发现工具，无需手动注册

---

## 总结

| 场景 | 建议 |
|------|------|
| 文件操作、搜索、执行命令 | 用内置工具 |
| 数据库、GitHub API、专用服务 | 用 MCP |
| 日常学习、CTF | 内置工具够用 |

MCP 的价值在于扩展内置工具没有的能力，而不是重复已有功能。
