"""阶段1：mdstudyfile 笔记 → 分块 → kb/chunks.json
零模型依赖（纯 Python 标准库），随时可跑。
阶段2 将用 embedding 为每个 chunk 建向量索引。

分块策略：
  1. 按 Markdown 标题（# ~ ####）切块，标题作为块的 heading
  2. 超长块（> MAX_CHUNK 字符）按空行分段切小
  3. 剥离 YAML frontmatter
排除目录：.git / 漏洞复现 / 安全运营 / kb（与 .gitignore 一致）
"""
import json
import pathlib
import re

ROOT = pathlib.Path(r'D:\mdstudyfile')
KB = ROOT / 'kb'
OUT = KB / 'chunks.json'
EXCLUDE_DIRS = {'.git', '漏洞复现', '安全运营', 'kb'}
EXCLUDE_FILES = {'web/Untitled.md'}  # 空草稿，与 .gitignore 一致
MAX_CHUNK = 800


def collect_md_files():
    files = []
    for p in ROOT.rglob('*.md'):
        rel = p.relative_to(ROOT)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if str(rel).replace('\\', '/') in EXCLUDE_FILES:
            continue
        files.append(p)
    return sorted(files)


def split_by_heading(lines):
    """按 Markdown 标题切块，返回 [(heading, [lines])]"""
    chunks = []
    cur_heading = '（无标题）'
    cur = []
    for ln in lines:
        m = re.match(r'^(#{1,4})\s+(.+)$', ln)
        if m:
            if cur:
                chunks.append((cur_heading, cur))
            cur_heading = m.group(2).strip()
            cur = []
        cur.append(ln)
    if cur:
        chunks.append((cur_heading, cur))
    return chunks


def split_long_text(text):
    """超长块按空行分段，合并成 <= MAX_CHUNK 的块；单段超长硬切"""
    paras = re.split(r'\n\s*\n', text)
    out, cur = [], ''
    for para in paras:
        if len(cur) + len(para) + 2 <= MAX_CHUNK:
            cur = f'{cur}\n\n{para}' if cur else para
        else:
            if cur:
                out.append(cur)
            while len(para) > MAX_CHUNK:
                out.append(para[:MAX_CHUNK])
                para = para[MAX_CHUNK:]
            cur = para
    if cur:
        out.append(cur)
    return out


def main():
    files = collect_md_files()
    chunks = []
    for f in files:
        try:
            raw = f.read_text(encoding='utf-8', errors='replace')
        except Exception as e:
            print(f'[skip] {f}: {e}')
            continue
        for heading, block_lines in split_by_heading(raw.splitlines()):
            text = '\n'.join(block_lines).strip()
            if not text:
                continue
            # 剥离 YAML frontmatter（每个文件第一个块通常以 --- 开头）
            if text.startswith('---'):
                parts = text.split('---', 2)
                if len(parts) == 3:
                    text = parts[2].strip()
                    if not text:
                        continue
            for piece in split_long_text(text):
                chunks.append({
                    'source': str(f.relative_to(ROOT)),
                    'heading': heading,
                    'text': piece,
                })

    KB.mkdir(exist_ok=True)
    OUT.write_text(
        json.dumps({'total': len(chunks), 'chunks': chunks},
                   ensure_ascii=False, indent=1),
        encoding='utf-8')

    sizes = [len(c['text']) for c in chunks]
    print(f'笔记文件数: {len(files)}')
    print(f'分块总数:   {len(chunks)}')
    if sizes:
        print(f'块大小:     平均={sum(sizes)//len(sizes)} 最小={min(sizes)} 最大={max(sizes)}')
    print(f'输出:       {OUT}')
    if chunks:
        c0 = chunks[0]
        print(f'样例块:     {c0["source"]} | 标题:{c0["heading"]} | {c0["text"][:50].replace(chr(10), " ")}')


if __name__ == '__main__':
    main()