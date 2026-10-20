---
title: Python 与终端交互（subprocess 与 pty）
tags: [python, subprocess, 终端]
created: '2026-10-15T15:40:00.000Z'
modified: '2026-10-15T15:40:00.000Z'
---

# Python 与终端交互（`subprocess` 与 `pty`）

> 来源：问「Py 脚本能不能跟终端交互」。答案：**能**，但要分清三种"交互"——只要结果、喂输入、真·一步步对话。**本文所有代码在本机（py 3.12.6 / Win11）实测过**，包括踩出来的坑。

## 0. 结论速览

| 需求 | 用什么 | 难度 |
|---|---|---|
| 跑命令、拿输出 | `subprocess.run(..., capture_output=True)` | 一行 |
| 跑命令、给输入 | `run(input=b"...")` / `Popen.communicate()` | 一行 |
| 长时间任务、实时看输出 | `Popen` + `for line in p.stdout` | 简单 |
| 纯 Python 程序互相调用（subprocess） | `Popen` + `stdin.write/flush` | **本机踩坑，见 §4** |
| 真交互式程序（`input()` 一问一答、密码提示、ssh/ftp） | `pywinpty` 伪终端 | 需要驱动循环，见 §5 |

---

## 1. 只要结果：`subprocess.run`

```python
import subprocess
r = subprocess.run(["openssl", "version"], capture_output=True, text=True)
r.returncode     # 0
r.stdout         # 'OpenSSL 3.5.5 ...\n'
r.stderr         # ''
```
- `capture_output=True` = 收 stdout+stderr（不打印到屏幕）。
- `text=True` 让它按**系统默认编码**解码成 str → **Windows 上默认 GBK，中文输出会炸**（见 §3）。
- 想直接看输出就别加 `capture_output`。

密码题实战：
```python
# 一条命令把 n/e/d/p/q 全取回来
r = subprocess.run(["openssl", "rsa", "-in", "k.pem", "-noout", "-text"],
                   capture_output=True, text=True)
print(r.stdout)      # 实测 512 位密钥打印 2097 字符，直接正则抽 n/e/d
```
先分两步：①`subprocess.run` 拿文本；② `re` 抽参数 —— 比手工 `int(open().read())` 稳。

## 2. 给子进程喂输入：`input=` 和 `communicate`

```python
# ① 一次性喂完（推荐，官方最稳）
r = subprocess.run(["openssl", "dgst", "-sm3"], input=b"hello world", capture_output=True)
r.stdout.decode()
# 'SM3(stdin)= 44f0061e69fa6fdfc290c494654a05dc0c053da7e5c52b84ef93a9d67d3fff88'

# ② 多行输入
p = subprocess.Popen([sys.executable, "-c", "a=input();b=input();print('GOT',a,b)"],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, encoding="utf-8")
out, _ = p.communicate("one\ntwo\n")
out          # 'GOT one two\n'
```
**`input=` / `communicate` 会自己处理"写完关闭 stdin"，所以永远不会踩 §4 的坑。**

需要口令的命令，**别去交互**，用命令行选项一次给完（实测）：
```python
subprocess.run(["openssl", "genrsa", "-aes128", "-passout", "pass:123456",
                "-out", "enc.pem", "512"], capture_output=True)
r = subprocess.run(["openssl", "rsa", "-in", "enc.pem", "-passin", "pass:123456",
                    "-noout", "-text"], capture_output=True, text=True)
r.stdout.splitlines()[0]     # 'Private-Key: (512 bit, 2 primes)'
```
类似地有 `-b`（browser 密码）、`-certin` 等。**能一次性给参数就别开交互**，这是最省事的路线。

## 3. 编码坑：`text=True` 在 Windows 会炸

实测：
```python
subprocess.run(["cmd", "/c", "echo", "中文测试"], capture_output=True, text=True)
# UnicodeDecodeError: 'utf-8' codec can't decode byte 0xd6 in position 0
```
原因：Windows 下子进程按本地代码页（GBK）输出，`text=True` 却按 UTF-8 解。

三种解法（全部实测）：
```python
# ① 拿 bytes 自己解（最可控，知道对端编码就用这个）
r = subprocess.run([...], capture_output=True)
r.stdout.decode("gbk", "replace")      # → '中文测试'

# ② 明确指定编码
subprocess.run([...], capture_output=True, text=True, encoding="gbk")

# ③ 官方推荐的兜底写法（不炸）
subprocess.run([...], capture_output=True, text=True, encoding="utf-8", errors="replace")
# 内容是乱码但程序不会崩 —— 抓不到就看不出问题，适合"只关心 rc 和关键词"的场景
```
| 写法 | 结果 |
|---|---|
| `text=True`（默认） | GBK 字节 → **直接抛 UnicodeDecodeError** |
| `decode("gbk")` | `中文测试` ✅ |
| `text=True, encoding="gbk"` | `'中文测试'` ✅ |
| `text=True, encoding="utf-8", errors="replace"` | `'���Ĳ���'`（乱码但不崩） |

**结论**：抓中文用 `encoding="gbk"`，抓英文/机器信息用 `text=True` 默认即可。

## 4. ⚠️ 逐行写 `p.stdin`：本机实测有个"要么翻车要么秒过"的分界

想让 Python 脚本**一步步**和子进程对话（读提示符 → 应答 → 再读）时，直觉写法是：

```python
p = subprocess.Popen(CHILD, stdin=PIPE, stdout=PIPE, stderr=STDOUT, text=True, encoding="utf-8")
prompt = p.stdout.readline()     # 阻塞读到提示符
p.stdin.write("xu\n")
p.stdin.flush()                  # ← 问题在这
```

**实测结果（同一份代码，只改读提示符的方式）**：

| 读提示符的方式 | 结果 |
|---|---|
| `p.stdout.readline()`（阻塞读） | `write` **成功**，紧接着 `flush` 抛 `OSError: [Errno 22] Invalid argument`；子进程卡死，只能 kill |
| 先 `time.sleep(0.5)`，再非阻塞 `os.read(p.stdout.fileno(), n)` | `write OK` + `flush OK`，应答正常 `b'HI xu\r\n'`，`rc=0` ✅ |

两种读法拿到的提示符内容完全一样（都是 `b'N? '`），**差别只在"读完之后管道状态"**。对子进程是 `-c "..."` 字符串还是脚本文件、是不是 `text=True`、`bufsize=0`，都不改变这个结论。

**内网/环境差异提醒**：同一条 `p.stdout.readline()` 版本，在无头/服务化环境里也可能直接正常（我这边在 git-bash 前台 PTY 下能跑通、在 `execute_code` 内核里会挂）。所以**别指望"我的机器能跑"**——写成不阻塞的读法最保险。

### 4.1 可靠的两种写法

**写法一（推荐）：不阻塞读提示符**

```python
import subprocess, sys, os, time

p = subprocess.Popen([sys.executable, "-u", "-c", "n=input('N? '); print('HI '+n)"],
                     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
time.sleep(0.5)
os.set_blocking(p.stdout.fileno(), False)     # 关掉阻塞
prompt = p.stdout.read()                      # 拿到 b'N? '
os.set_blocking(p.stdout.fileno(), True)

p.stdin.write(b"xu\n")
p.stdin.flush()                               # ✅ 实测 OK
time.sleep(0.5)
os.set_blocking(p.stdout.fileno(), False)
print(p.stdout.read())                        # b'HI xu\r\n'
p.wait()
```
要点：`-u`（子进程不缓冲）、`sleep` 给子进程启动时间、非阻塞读避免卡死。密码学脚本里想驱动外部程序就用这个。

**写法二（最省事）：不要逐行，直接 `communicate`**

```python
p = subprocess.Popen(CHILD, stdin=PIPE, stdout=PIPE)
out, _ = p.communicate(b"xu\n")      # 内部：写 → 关 stdin → 读全部
```
只要你不需"看一句答一句"，就用它。**90% 的场景它够了。**

### 4.2 什么时候必须逐行

| 场景 | 说明 |
|---|---|
| 长任务进度 | `for line in p.stdout:`（配合 `python -u`），实测能实时打时间戳 |
| 输出很大 | 边读边处理，避免 `communicate` 把几十 MB 堆内存 |
| 一问一答协议 | 程序按提示符分步问 → 见 §5，真交互建议上 pty |

实测流式读：
```python
p = subprocess.Popen([sys.executable, "-u", "-c",
                      "import time\nfor i in range(3):\n    print('进度', i, flush=True); time.sleep(0.3)"],
                     stdout=subprocess.PIPE, text=True, encoding="utf-8")
for line in p.stdout:
    print(line.strip())
# 进度 0 / 进度 1 / 进度 2，每 0.3 秒一条
```
`python -u` 或子进程里 `flush=True` 是必须的，否则 Python 子进程缓冲到结束才吐。

## 5. 真交互式程序 → 伪终端（pty）

**为什么普通管道不够用**：`input()` 这类程序会判 `sys.stdin.isatty()`，发现不是终端就改行为（提示符不打、回显关闭、有时直接报错退出）；`getpass`、`ssh`、`ftp`、`mysql` 更是硬要求有 tty。

- Linux/macOS：标准库 `pty` 直接可用（`pty.spawn`/`pexpect`）。
- **Windows：标准库没有 `pty`**（实测 `import pty` → ModuleNotFoundError），需要第三方。

### 5.1 装 `pywinpty`（本机已装 3.0.5）

```bash
py -m pip install pywinpty
```
实测 API：
```python
from winpty import PtyProcess
p = PtyProcess.spawn(["D:\\徐利杰\\python.exe", "-u", "child.py"], dimensions=(24, 80))
p.write(...)      # 写入（写到终端，不是管道）
p.read(4096)      # 读（**阻塞**，没有数据会挂住 → 必须放后台线程）
p.isalive()
p.terminate(force=True)
```

### 5.2 ⚠️ 两个实测致命坑

**坑 1：必须发 `\r`（CR），不能只发 `\n`**

| 发送内容 | 子进程是否收到 |
|---|---|
| `"xu\n"` | ❌ 卡在提示符，`input()` 不返回 |
| `"xu\r\n"` | ✅ `HI xu` |
| `"xu\r"` | ✅ `HI xu` |

终端里回车是 CR。**只发 `\n` 会被终端吞掉**——这是交互式驱动最容易卡住的地方。

**坑 2：`read()` 会阻塞，必须后台线程持续读**

主线程"发一句 → 读一句"很容易在等待时死锁。正确结构（实测可跑通）：

```python
import threading, time, re
from winpty import PtyProcess

class Driver:
    def __init__(self, argv):
        self.buf, self.lock = "", threading.Lock()
        self.p = PtyProcess.spawn(argv)
        self.alive = True
        threading.Thread(target=self._reader, daemon=True).start()

    def _reader(self):                       # 后台不停收
        while self.alive:
            try:
                c = self.p.read(4096)
            except Exception:
                break
            if c:
                with self.lock:
                    self.buf += c

    def wait_for(self, pattern, timeout=8):  # 主线程按正则等
        t0 = time.time()
        while time.time() - t0 < timeout:
            with self.lock:
                if re.search(pattern, self.buf):
                    return True
            time.sleep(0.05)
        return False

    def send(self, s):
        self.p.write(s)

    def clean(self):                          # 去掉 ANSI 控制序列
        with self.lock:
            return re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", self.buf)

    def close(self):
        self.alive = False
        self.p.terminate(force=True)
```
用法：
```python
d = Driver([r"D:\徐利杰\python.exe", "-u", "_child.py"])
d.wait_for("请输入名字")      # 等提示
d.send("徐利杰\r")            # ★ CR
d.wait_for("HI")
print(d.clean())              # 干净文本
d.close()
```

实测跑通的两个场景：
- 普通 `input()` 提示符 → 应答 → 回显 `HI 徐利杰`
- `getpass.getpass('Password: ')`（**不回显的密码提示**）→ 送 `s3cret\r` → `len = 6` ✅

原始读到的东西长这样（含终端控制码，所以必须 `clean()`）：
```
'\x1b[1t\x1b[c\x1b[?1004h\x1b[?9001hPass: \r\r\nLEN 6\r\n'
```

## 6. 杂项（都实测过）

```python
subprocess.call([...])                     # 只要退出码，输出直接进屏幕
subprocess.check_output([...], text=True)  # 非 0 抛 CalledProcessError（可当"这命令成功了吗"用）
subprocess.getoutput("echo hi | tr a-z A-Z")  # 字符串命令 + 管道，返回 str（最省事，2 秒上手）
os.system("...")                           # 老式，只能拿退出码
```
```python
# 注入环境变量
subprocess.run(["cmd", "/c", "echo", "%MYVAR%"], capture_output=True, text=True,
               env={**os.environ, "MYVAR": "injected"})     # → 'injected'

# 指定工作目录
subprocess.run(["cmd", "/c", "cd"], capture_output=True, text=True, cwd="C:/")  # → 'C:\\'

# 超时（卡住的命令必须设，别让它吊死脚本）
try:
    subprocess.run([...], capture_output=True, timeout=1)
except subprocess.TimeoutExpired:
    print("超时了")

# 自定义管道计数器（pycryptodome CTR 用）
from Crypto.Util import Counter
Counter.new(128, initial_value=0)     # 键名: counter_len / initial_value / prefix / suffix / little_endian
```
- `shell=True` + 字符串才能用管道/重定向；否则一律传**列表**（避免路径带空格出问题）。
- `p.kill()` 只杀直接子进程，孙进程可能残留（Windows 上用 `taskkill /T /F /PID` 或 `psutil`）。

## 7. 直接跑的例子

`D:\python\CTF工具箱\misc\终端交互demo.py`（本文 A/B/C/D 四个场景的可运行版）：
```bash
py "D:\python\CTF工具箱\misc\终端交互demo.py"
```
输出（实测）：
```
[A] 调外部命令拿输出      rc = 0 | OpenSSL 3.5.5 ...
[B] 喂 stdin             SM3(stdin)= 44f0061e...
[C] 实时流式读输出        [0.0s] 进度 0 / [0.3s] 进度 1 / [0.6s] 进度 2
[D] 驱动交互式程序        等到提示符: True | 子进程回应: True | HI 徐利杰
                        交互式口令: True | len = 6
```

## 8. 一句话选型

> **能一次给完参数（`input=`/`communicate`）就别交互；要读进度用 `Popen` + `for line in stdout`；非交互不可（`input()`/密码/ssh）才上 `pywinpty`，且记住发 `\r`、后台线程收。**

---

## 相关

- [Python 数据加密编码函数大全](Python-数据加密编码函数大全.md) —— 里面用 `subprocess` 调 openssl 的部分
- [str 与 bytes 编码](Python3-str与bytes编码.md) —— §3 的编码坑延伸
- 密码学常用函数速查：`D:\mdstudyfile\密码学\常用函数.md`（§9 命令行工具）
