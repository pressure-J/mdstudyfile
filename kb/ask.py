"""阶段3：本地 RAG 问答（完全离线）
流程：问题 → bge-m3 向量化 → 与 vectors.npy 余弦相似度 → Top-K 块 → qwen2.5:7b 生成
用法：py kb/ask.py "你的问题" [top_k]
可移植：改 KB / EMBED_MODEL / CHAT_MODEL 即可接入其他项目
"""
import json
import pathlib
import sys
import urllib.request

KB = pathlib.Path(r'D:\mdstudyfile\kb')
OLLAMA_URL = 'http://localhost:11434/api/embed'
OLLAMA_CHAT = 'http://localhost:11434/api/chat'
EMBED_MODEL = 'bge-m3'
CHAT_MODEL = 'qwen2.5:7b'
TOP_K = 4


def embed_one(text):
    body = json.dumps({'model': EMBED_MODEL, 'input': text}).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode('utf-8'))['embeddings'][0]


def cosine(a, b):
    import numpy as np
    a = np.asarray(a, dtype=np.float32)
    b = np.asarray(b, dtype=np.float32)
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))


def chat(messages):
    body = json.dumps({'model': CHAT_MODEL, 'messages': messages, 'stream': False}).encode('utf-8')
    req = urllib.request.Request(OLLAMA_CHAT, data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as resp:
        return json.loads(resp.read().decode('utf-8'))['message']['content']


def main():
    if len(sys.argv) < 2:
        print('用法: py kb/ask.py "你的问题" [top_k]')
        sys.exit(1)
    question = sys.argv[1]
    top_k = int(sys.argv[2]) if len(sys.argv) > 2 else TOP_K

    import numpy as np
    vectors = np.load(KB / 'vectors.npy')
    meta = json.loads((KB / 'embed_meta.json').read_text(encoding='utf-8'))['chunks']
    if len(vectors) != len(meta):
        print(f'错误: 向量 {len(vectors)} 条 vs 元数据 {len(meta)} 条，请重建索引')
        sys.exit(1)

    print('向量化问题...', flush=True)
    qv = embed_one(question)
    sims = [cosine(qv, v) for v in vectors]
    order = sorted(range(len(sims)), key=lambda i: sims[i], reverse=True)[:top_k]

    print(f'Top-{top_k} 相关笔记块:')
    ctx = []
    for idx in order:
        c = meta[idx]
        print(f'  [{sims[idx]:.3f}] {c["source"]} | {c["heading"]}')
        ctx.append(f'来源: {c["source"]} 标题: {c["heading"]}\n{c["text"]}')
    context = '\n\n---\n\n'.join(ctx)

    messages = [
        {'role': 'system',
         'content': '你是网络安全学习助手。严格基于提供的笔记内容回答问题；'
                    '笔记中没有的内容，明确说"笔记里没有"，不要编造。'},
        {'role': 'user',
         'content': f'以下是从我的学习笔记中检索到的相关内容：\n\n{context}\n\n问题：{question}'},
    ]
    print(f'调用 {CHAT_MODEL} 生成回答...\n', flush=True)
    print(chat(messages))


if __name__ == '__main__':
    main()