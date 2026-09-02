# Git 和 GitHub 基础知识

## 一、Git 是什么？

Git 是一个**分布式版本控制系统**，用于追踪文件的变更历史，支持多人协作开发。

### 核心概念

| 概念 | 说明 |
|------|------|
| **工作区 (Working Directory)** | 你正在编辑的文件所在的目录 |
| **暂存区 (Staging Area)** | 用 `git add` 添加的文件，准备提交 |
| **本地仓库 (Local Repository)** | 用 `git commit` 提交后，存储在 `.git` 目录 |
| **远程仓库 (Remote Repository)** | GitHub、Gitee 等在线托管平台 |

### 工作流程

```
工作区 → git add → 暂存区 → git commit → 本地仓库 → git push → 远程仓库
```

---

## 二、Git 常用命令

### 1. 仓库初始化

```bash
# 初始化新仓库
git init

# 克隆远程仓库
git clone <仓库地址>
```

### 2. 文件操作

```bash
# 查看状态
git status

# 添加到暂存区
git add <文件名>      # 添加单个文件
git add .            # 添加所有文件
git add *.py         # 添加所有 .py 文件

# 提交到本地仓库
git commit -m "提交说明"

# 查看提交历史
git log
git log --oneline    # 简洁模式
```

### 3. 分支管理

```bash
# 查看分支
git branch           # 本地分支
git branch -a        # 所有分支（含远程）

# 创建分支
git branch <分支名>

# 切换分支
git checkout <分支名>
git switch <分支名>   # 新命令

# 创建并切换分支
git checkout -b <分支名>
git switch -c <分支名>

# 合并分支
git merge <分支名>

# 删除分支
git branch -d <分支名>
```

### 4. 远程操作

```bash
# 查看远程仓库
git remote -v

# 添加远程仓库
git remote add origin <地址>

# 推送到远程
git push origin main
git push -u origin main    # 首次推送，设置上游分支

# 拉取更新
git pull origin main

# 获取远程更新（不合并）
git fetch origin
```

### 5. 撤销操作

```bash
# 撤销工作区修改
git checkout -- <文件名>
git restore <文件名>

# 撤销暂存区
git reset HEAD <文件名>
git restore --staged <文件名>

# 修改最近一次提交
git commit --amend

# 回退到指定版本
git reset --hard <commit_id>
```

### 6. 暂存工作

```bash
# 暂存当前修改
git stash

# 恢复暂存
git stash pop

# 查看暂存列表
git stash list
```

---

## 三、GitHub 是什么？

GitHub 是一个基于 Git 的**在线代码托管和协作平台**，提供版本控制、项目管理、社交编程等功能。

### GitHub vs Git

| | Git | GitHub |
|--|-----|--------|
| 本质 | 版本控制工具 | 在线协作平台 |
| 安装 | 需要安装在本地 | 网页访问 |
| 功能 | 代码版本管理 | 代码托管 + 协作 + 社交 |

---

## 四、GitHub 核心功能

### 1. Repository（仓库）

- 代码存储的基本单位
- 每个仓库可以设置**公开 (Public)** 或 **私有 (Private)**
- 包含代码、README、License 等

### 2. Fork（复制仓库）

- 将别人的仓库复制到自己的账号下
- 用于修改后提交 PR，参与开源项目
- 不影响原仓库

### 3. Pull Request（PR，合并请求）

- 向原仓库提交代码合并申请
- 是代码审查 (Code Review) 的核心机制
- 流程：Fork → 修改 → 开 PR → 审查 → 合并

### 4. Issue（问题追踪）

- 用于报告 Bug、提出功能需求、讨论问题
- 支持标签、指派、里程碑管理

### 5. GitHub Actions（CI/CD）

- 自动化工作流：测试、构建、部署
- 配置文件：`.github/workflows/xxx.yml`

### 6. GitHub Pages（静态网站）

- 免费托管静态网站
- 访问地址：`https://用户名.github.io`
- 项目页面：`https://用户名.github.io/仓库名/`

---

## 五、GitHub Pages 搭建

### 1. 创建用户主页

```bash
# 1. 创建仓库，名字必须是：用户名.github.io
# 2. 在仓库中放 index.html 或 index.md
# 3. Push 到远程
# 4. 等待部署，访问 https://用户名.github.io
```

### 2. 创建项目页面

```bash
# 1. 创建任意名称的仓库
# 2. Push 代码
# 3. 在 Settings → Pages 中开启
# 4. 访问 https://用户名.github.io/仓库名/
```

---

## 六、Git 认证配置

### 方式一：HTTPS + Token（推荐新手）

```bash
# 1. 在 GitHub 生成 Personal Access Token
# Settings → Developer settings → Personal access tokens → Generate new token

# 2. 配置凭据管理器
git config --global credential.helper store

# 3. 首次 push 时输入用户名和 Token（代替密码）
```

### 方式二：SSH Key（推荐）

```bash
# 1. 生成 SSH 密钥
ssh-keygen -t ed25519 -C "your_email@example.com"

# 2. 复制公钥内容
cat ~/.ssh/id_ed25519.pub

# 3. 在 GitHub 添加公钥
# Settings → SSH and GPG keys → New SSH key

# 4. 使用 SSH 地址克隆
git clone git@github.com:username/repo.git
```

---

## 七、`.gitignore` 文件

用于指定 Git 忽略的文件和目录：

```gitignore
# 忽略所有 .log 文件
*.log

# 忽略 build 目录
build/

# 忽略 node_modules
node_modules/

# 忽略 .env（包含敏感信息）
.env

# 忽略 IDE 配置
.vscode/
.idea/

# 忽略 OS 文件
.DS_Store
Thumbs.db
```

---

## 八、分支策略

### Git Flow

```
main        ─── 稳定版本
  │
  └── develop ─── 开发分支
        │
        ├── feature/xxx ─── 功能分支
        ├── feature/yyy ─── 功能分支
        │
        └── release/1.0 ─── 发布分支
              │
              └── hotfix/xxx ─── 紧急修复
```

### 简化流程

```
main        ─── 稳定版本
  │
  └── dev    ─── 开发分支
        │
        └── feature-xxx ─── 功能分支
              │
              └── 完成后合并到 dev
```

---

## 九、常用 Git 别名

```bash
git config --global alias.st status
git config --global alias.co checkout
git config --global alias.br branch
git config --global alias.ci commit
git config --global alias.lg "log --oneline --graph --all"
```

---

## 十、常见问题

### 1. 合并冲突怎么办？

```bash
# 冲突文件会显示：
<<<<<<< HEAD
你的代码
=======
别人的代码
>>>>>>> branch-name

# 手动编辑文件，选择保留哪部分，然后：
git add <文件名>
git commit
```

### 2. 忘记 add 就 commit 了？

```bash
git add <文件名>
git commit --amend
```

### 3. 提交了敏感信息？

```bash
# 使用 BFG 工具清理
# https://rtyley.github.io/bfg-corrupter/
bfg --passwords my-password.txt
```

### 4. push 被拒绝？

```bash
# 先拉取再推送
git pull origin main
git push origin main
```

---

## 十二、origin 与 upstream：开源协作流程

### 1. 概念与区别

| 名称 | 含义 | 谁拥有 |
|------|------|--------|
| **origin** | 自己 clone / push 的远程仓库（通常是自己 fork 的仓库） | 你本人 |
| **upstream** | fork 出来的源头仓库（原作者的项目） | 别人 / 团队 |

> origin 和 upstream 只是"远程仓库的别名"，不是 Git 强制规则，只是社区约定俗成的命名。克隆下来的仓库默认只有 origin，upstream 需要手动添加。

### 2. Fork 工作流（参与开源项目的标准套路）

```
GitHub 原作者仓库 alice/CyberStrikeAI  ← upstream
      │ fork（复制到自己账号）
你/CyberStrikeAI                        ← origin
      │ clone（下载到本地）
本地仓库
```

### 3. 完整命令流程

```bash
# 添加 upstream（指向原作者仓库）
git remote add upstream https://github.com/原作者/仓库.git

# 同步原作者更新：先 fetch 再 merge（避免未提交改动直接冲突）
git fetch upstream
git checkout main
git merge upstream/main

# 切功能分支开发，推到自己 fork
git checkout -b fix-login-bug
git push origin fix-login-bug

# 到 GitHub 你的 fork 页面 → Compare & pull request
# 合并方向：你/fix-login-bug → 原作者/main（注意别反了）
```

### 4. 常见坑

- `git pull` 默认拉 origin，不是 upstream
- upstream 只拉不推（无推送权限）；origin 是你的地盘，随便推
- PR 提交后如需修改，再 push 到同一分支，PR 自动更新，不用重新开

### 5. upstream 的第二个含义

`git push -u origin main`（-u = --set-upstream）是给分支绑定**跟踪关系**，绑定后直接 `git push` / `git pull` 不用带参数。这是"跟踪分支"概念，与"upstream 远程仓库"无关，注意区分：
- "添加一个 upstream 远程仓库" → 原作者仓库
- "分支的 upstream 是 origin/main" → 分支跟踪关系

---

## 十三、主分支与功能分支

### 1. fork ≠ 分支

fork 复制的是**整个仓库**（包含它所有分支），不是切一条分支。fork 出来的仓库里，main 依然是主分支。

| 概念 | 是什么 | 类比 |
|------|--------|------|
| 仓库（Repo） | 完整代码库，包含所有分支 | 整棵树 |
| 分支（Branch） | 树上的某条枝干 | 树干 vs 侧枝 |
| fork | 把整棵树复制一份到自己的账号 | 克隆一棵新树 |

### 2. 主分支 vs 功能分支

```
main ───────── 主干道，稳定可发布
  ├── fix-login-bug  功能分支：修 bug 临时切出，改完合并回 main 再删
  └── crypto-tools   功能分支：开发新功能临时切出
```

- **主分支（main）**：项目主干道，保持能跑、能发布的状态
- **功能分支（feature branch）**：从主干临时切出去的"小路"，专门开发某个功能/修 bug，完成后合并回主干再删除（类似 Git Flow 的 feature/xxx）

### 3. 在自己的 fork 里切功能分支

```
你/CyberStrikeAI
  ├── main            ← 主分支（fork 后依然是主分支，不是功能分支）
  └── crypto-tools    ← 功能分支（git checkout -b crypto-tools 创建）
```

> 功能分支不是"fork 出来的那条"，而是你在自己的 fork 里**另外切出**的一条新线。

### 4. 为什么推功能分支开 PR，而不是推 main？

- main 保持干净，可继续同步 upstream
- 一个功能一个分支，同时开多个 PR 互不干扰
- 直接推 main 开 PR，main 会和上游分叉，后续同步全是坑

---

## 十四、分支的本质

### 1. 分支 = 指向提交的指针

创建分支的那一刻，新指针指向当前提交（包含整个项目全部文件快照），所以分支天生是一份**完整项目**：

```
main          → [提交C]   ← main 指针
crypto-tools  → [提交C]   ← 新指针指向同一提交
```

之后两个分支独立演进：main 上的提交不影响分支，反之亦然——像从存档点复制了一份完整存档，两边是**平行的完整世界**。

### 2. 合并是增量叠加，不是替代

```
main    ── C ────────── M（合并提交）
            ↘        ↗
crypto-tools  D（新功能）

合并后 main = C 原有功能 + D 新功能，旧代码与历史全保留
```

- 普通开发：新功能是**增补**进主干，原有功能一条不少
- 接近"替代"的情况只有重构 / 修 bug（旧实现被新版本换掉）
- 但 Git 历史里旧版本永远在，可随时回退——本质是"演进"而非"替代"
- 开源贡献规范：小改动、增量式贡献，避免用大 PR 重写别人存量代码

---

## 十五、Git 合并原理：三路合并与冲突解决

### 1. 三路合并（three-way merge）

Git 合并不直接拼两份文件，而是对比**三份**：

```
        [B] 分叉点（merge base）← 两边代码相同的起点
       /     \
      /       \
[主干的新代码] [分支的新代码]
       \       /
      [合并结果]
```

### 2. 三种情况

| 情况 | 结果 |
|------|------|
| 两边改的是不同位置 | 自动合并，互不影响 |
| 一边改了、另一边没动 | 自动合并，直接采用改动方 |
| 两边改了同一处（同一函数/同一行） | **冲突**，需要人工裁决 |

### 3. 冲突标记与解决

冲突会直接写进文件：

```
<<<<<<< HEAD
    return check_token(token) and check_expire(token)     ← 主干版本
=======
    return check_token(token) or allow_white_list(token)  ← 分支版本
>>>>>>> crypto-tools
```

解决步骤：

```bash
# 1. 手动编辑冲突区域，保留/合并成最终版本
# 2. 处理完标记解决并提交
git add <文件名>
git commit
```

### 4. 关键认知

- 实际项目约 80% 的合并静默完成，冲突多发生在两边改动到同一函数/同一行时
- 冲突不是事故，是 Git 强制"开发者确认两边改了什么、由谁拍板"的机制
- VS Code / PyCharm 提供可视化三方合并界面，可以图形化解决冲突

---

## 十一、学习资源

- [Git 官方文档](https://git-scm.com/doc)
- [GitHub 官方文档](https://docs.github.com)
- [Pro Git 中文版](https://git-scm.com/book/zh/v2)
- [GitHub Skills](https://skills.github.com)

---

*最后更新：2026年8月29日*
