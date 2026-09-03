"""阶段2：chunks.json → 向量索引（本地 embedding，完全离线）
依赖：Ollama 运行中 + bge-m3（embedding 模型）已拉取
输出：
  kb/vectors.npy     (N, dim) float32 —— 向量矩阵，第 i 行对应 meta 第 i 条
  kb/embed_meta.json {total, chunks[source, heading, text]}
用法：py kb/embed_index.py
可移植：改 OLLAMA_URL / MODEL / KB 即可接入其他项目（如 CyberStrikeAI）
"""
import json
import pathlib
import sys
import time
import urllib.request

OLLAMA_URL = 'http://localhost:11434/api/embed'
MODEL = 'bge-m3'
BATCH = 24            # 每批文本数（按模型负载调整）

KB = pathlib.Path(r'D:\mdstudyfile\kb')
CHUNKS = KB / 'chunks.json'
VECTORS = KB / 'vectors.npy'
META = KB / 'embed_meta.json'


def embed_batch(texts):
    body = json.dumps({'model': MODEL, 'input': texts}).encode('utf-8')
    req = urllib.request.Request(OLLAMA_URL, data=body,
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=600) as resp:
        data = json.loads(resp.read().decode('utf-8'))
    embs = data['embeddings']
    if len(embs) != len(texts):
        raise RuntimeError(f'embedding 数量不匹配: 请求 {len(texts)} 返回 {len(embs)}')
    return embs


def main():
    data = json.loads(CHUNKS.read_text(encoding='utf-8'))
    chunks = data['chunks']
    print(f'载入 {len(chunks)} 个块，向量化中（模型 {MODEL}）...', flush=True)

    vectors = []
    t0 = time.time()
    for i in range(0, len(chunks), BATCH):
        batch_texts = [c['text'] for c in chunks[i:i + BATCH]]
        embs = embed_batch(batch_texts)
        vectors.extend(embs)
        done = min(i + BATCH, len(chunks))
        print(f'  [{done}/{len(chunks)}] 用时 {time.time()-t0:.0f}s', flush=True)

    try:
        import numpy as np
        arr = np.asarray(vectors, dtype=np.float32)
        np.save(VECTORS, arr)
        saved_as = f'numpy .npy shape={arr.shape}'
    except ImportError:
        VECTORS.with_suffix('.json').write_text(json.dumps(vectors), encoding='utf-8')
        saved_as = 'json (numpy 不可用)'

    META.write_text(
        json.dumps({'total': len(chunks), 'chunks': chunks}, ensure_ascii=False, indent=1),
        encoding='utf-8')

    dim = len(vectors[0]) if vectors else 0
    print(f'完成: {len(vectors)} 条向量, 维度 {dim}, 存储: {saved_as}')
    print(f'向量文件: {VECTORS}  元数据: {META}')


if __name__ == '__main__':
    main()