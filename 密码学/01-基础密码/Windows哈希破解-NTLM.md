---
tags: [crypto, windows, hash]
title: Windows哈希破解-NTLM
created: '2026-09-05T12:00:00.000Z'
modified: '2026-09-05T12:00:00.000Z'
---

# Windows哈希破解（NTLM）

## 题型识别（一眼看出）
题目给一段形如以下格式的账户数据（来自内存取证/mimikatz dump / SAM 导出）：

```
Administrator:500:aad3b435b51404eeaad3b435b51404ee:31d6cfe0d16ae931b73c59d7e0c089c0:::
ctf:1002:06af9108f2e1fecf144e2e8adef09efd:a7fcb22a88038f35a8f39d503e7f0062:::
```

**格式**：`用户名:RID:LM哈希:NTLM哈希`

| 段 | 含义 | 处理 |
|---|---|---|
| 用户名 | 账户名 | 锁定目标（通常非内置账户） |
| RID | 用户 ID，500=Administrator，501=Guest，>1000=普通用户 | 出题人新建的账户 RID 通常 >1000 |
| LM 哈希 | `aad3b435b51404eeaad3b435b51404ee` 是**空 LM**（Vista 后不存 LM） | 直接忽略 |
| NTLM 哈希 | 真正的密码哈希 | 🎯 破解目标 |

**直接排除法**（秒杀大半行）：
- `31d6cfe0d16ae931b73c59d7e0c089c0` = **空密码**的 NTLM 固定值（Administrator/Guest 常为它）
- `aad3b435b51404eeaad3b435b51404ee` = 空 LM，忽略
- `bef14eee40dffbc345eeb3f58e290d56` = SUPPORT_388945a0 内置账户固定哈希

**本质**：NTLM 是无盐哈希，`NTLM(pw) = MD4(UTF-16LE(pw))` → 可逆向（查表/字典/暴力）。

## 破解优先级（按成本从低到高）
1. **本地弱密码脚本**（秒级）：常见弱口令 + 用户名变体，见 `NTLM破解-弱密码测试.py`
2. **在线查表站**（秒级）：crackstation.net / cmd5.com / somd5.com / md5decrypt.net
   - ⚠️ 用**浏览器**打开（脚本 UA 会被 403）
   - ⚠️ 哈希类型**必须选 NTLM**（选错查不到）
   - ⚠️ 单条查，批量会被限流
3. **hashcat + rockyou 字典**（正规军）：
   ```bash
   echo 'a7fcb22a88038f35a8f39d503e7f0062' > hash.txt
   hashcat -m 1000 hash.txt /usr/share/wordlists/rockyou.txt
   hashcat -m 1000 hash.txt rockyou.txt -r /usr/share/hashcat/rules/best64.rule   # 无果加规则
   ```
4. **纯数字暴力**（少位数可行）：见 `NTLM破解-数字暴力.py`（1~6 位纯数字分钟级）

## 实战记录
- 目标 `a7fcb22a88038f35a8f39d503e7f0062`（ctf 用户）→ crackstation 查到密码 **`good-luck`**
- 验证：`MD4('good-luck'.encode('utf-16-le')).hexdigest()` == 目标 ✅
- 738 个常见弱密码 + 1~6 位纯数字未命中 → 说明密码在弱口令和纯数字之外，查表站命中

## 易错点
1. **LM 哈希不是目标**：`aad3b435b51404eeaad3b435b51404ee` 出现不代表有 LM 密码，Vista 后系统默认不存 LM，这是空值占位
2. **空密码有固定 NTLM**：`31d6cfe0d16ae931b73c59d7e0c089c0` 直接识别，不用破
3. **在线站选错类型**：贴 MD5/SHA256 格式的哈希去 NTLM 模式查 = 永远查不到
4. **查表结果要验证**：用 MD4 重算比对，防止站给错/你抄错
5. **crackstation 脚本访问被 403**：必须真实浏览器访问 + 带正常 UA

## 相关脚本
- `NTLM破解-弱密码测试.py`：738 个常见弱密码 + 用户名变体秒测
- `NTLM破解-数字暴力.py`：1~6 位纯数字 + ctf 相关变体暴力