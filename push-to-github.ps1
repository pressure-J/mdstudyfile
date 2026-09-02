# ============================================
# 一键推送学习笔记到 GitHub 私有仓库 mdstudyfile
# 用法：右键 -> 使用 PowerShell 运行（或在终端执行）
# 安全：token 不落盘，运行时从 Hermes config 动态读取
# ============================================
$ErrorActionPreference = 'Stop'
Set-Location D:\mdstudyfile

# 1. 读取 token（Hermes 的 GitHub MCP 配置）
$cfgPath = 'C:\Users\徐利杰\AppData\Local\Hermes Agent CN Desktop\data\hermes-home\config.yaml'
$line = (Get-Content $cfgPath) | Where-Object { $_ -match 'GITHUB_PERSONAL_ACCESS_TOKEN' } | Select-Object -First 1
if (-not $line) {
    Write-Host '[!] 未找到 GitHub token，请先确认 Hermes config.yaml 配置' -ForegroundColor Red
    exit 1
}
$token = ($line -split ':\s*', 2)[1].Trim().Trim('"').Trim("'")
$b64 = [Convert]::ToBase64String([Text.Encoding]::ASCII.GetBytes("pressure-J:$token"))

# 2. 有改动才提交
$changes = git status --porcelain
if (-not $changes) {
    Write-Host '[=] 没有新改动，无需推送' -ForegroundColor Yellow
    exit 0
}

# 3. 提交 + 推送
git add -A
git commit -m "update: $(Get-Date -Format 'yyyy-MM-dd HH:mm')"
git -c http.extraheader="AUTHORIZATION: basic $b64" push origin main

Write-Host '[√] 推送完成' -ForegroundColor Green