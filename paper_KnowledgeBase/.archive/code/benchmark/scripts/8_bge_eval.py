#!/usr/bin/env python3
"""
Stage 8: 加入 BGE / sentence-transformers neural embedding 對照組（T+）。

針對 §VI-D 局限性「E4 同義詞失配可由 neural encoder 改善」做實證補強。
新增條件 T+ (Hybrid + BGE) — 用 BGE neural embedding 取代 TF-IDF。

腳本流程：
  1. 載入 BGE-small-zh-v1.5（95MB，CPU 可跑）
  2. 編碼 corpus（2000 docs）+ test queries（500）
  3. 計算 BGE-only 與 BM25+BGE hybrid 兩個變體
  4. 與既有 B0/B1/B2/T 比較

執行需 ~5-10 分鐘（Mac Mini 2014）。
"""
import hashlib
import json
import time
from pathlib import Path

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

MODEL_NAME = "BAAI/bge-small-zh-v1.5"  # 95MB, 512-dim, Chinese-specific
KS = [1, 3, 5, 10]


def load():
    corpus = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))
    queries = json.loads((DATA / "queries.json").read_text(encoding="utf-8"))
    queries = [q for q in queries if q["expert_verification"].get("final_gt")]
    return corpus, queries


def doc_text(d):
    return f"{d.get('model','')} " + " ".join(d.get("specs", {}).values()) + " " + d.get("description", "")


def _texts_hash(texts):
    h = hashlib.sha256()
    for t in texts:
        h.update(t.encode("utf-8"))
        h.update(b"\x00")
    return h.hexdigest()


def encode_with_cache(model, texts, cache_path, name):
    hash_path = cache_path.with_suffix(".sha256")
    expected = _texts_hash(texts)
    if cache_path.exists() and hash_path.exists() and hash_path.read_text().strip() == expected:
        print(f"  📂 {name} 載入快取 ({cache_path.stat().st_size // 1024} KB, hash matched)")
        return np.load(cache_path)
    if cache_path.exists():
        print(f"  ⚠️  {name} 快取存在但 hash 不符，重新編碼...")
    print(f"  🧠 {name} 編碼中（{len(texts)} 個樣本，CPU）...")
    t0 = time.time()
    emb = model.encode(texts, batch_size=32, show_progress_bar=True,
                       convert_to_numpy=True, normalize_embeddings=True)
    dt = time.time() - t0
    print(f"  ✅ {name} 完成：{dt:.1f}s ({dt/len(texts)*1000:.1f} ms/sample)")
    np.save(cache_path, emb)
    hash_path.write_text(expected)
    return emb


def hit_at_k(predicted_ids, gt, k):
    return 1 if gt in predicted_ids[:k] else 0


def reciprocal_rank(predicted_ids, gt):
    for i, p in enumerate(predicted_ids, 1):
        if p == gt:
            return 1.0 / i
    return 0.0


def topk(scores, doc_ids, k):
    idx = scores.argsort()[::-1][:k]
    return [doc_ids[i] for i in idx]


def main():
    print(f"🤖 模型：{MODEL_NAME}\n")
    corpus, queries = load()
    test = [q for q in queries if q["subset"] == "test"]
    doc_ids = [d["doc_id"] for d in corpus]
    doc_texts = [doc_text(d) for d in corpus]
    query_texts = [q["query"] for q in test]
    gts = [q["expert_verification"]["final_gt"] for q in test]
    print(f"📚 corpus: {len(corpus)} docs")
    print(f"📋 test queries: {len(test)}")

    print(f"\n📥 載入模型（首次需下載 ~95MB）...")
    t0 = time.time()
    model = SentenceTransformer(MODEL_NAME)
    print(f"   載入完成：{time.time()-t0:.1f}s")

    # 編碼 corpus（含快取）
    print(f"\n🔬 編碼 corpus...")
    cache_dir = DATA / "embeddings"
    cache_dir.mkdir(exist_ok=True)
    doc_emb = encode_with_cache(model, doc_texts, cache_dir / "corpus_bge.npy", "corpus")
    query_emb = encode_with_cache(model, query_texts, cache_dir / "test_queries_bge.npy", "queries")

    # ── BGE-only 條件 (T_BGE) ──
    print(f"\n🎯 計算 cosine 相似度 + Top-K...")
    sim_matrix = cosine_similarity(query_emb, doc_emb)  # (500, 2000)

    metrics_bge = {f"Hit@{k}": [] for k in KS}
    metrics_bge["MRR"] = []
    correct_bge = []
    for i, gt in enumerate(gts):
        scores = sim_matrix[i]
        top_ids = topk(scores, doc_ids, max(KS))
        for k in KS:
            metrics_bge[f"Hit@{k}"].append(hit_at_k(top_ids, gt, k))
        metrics_bge["MRR"].append(reciprocal_rank(top_ids, gt))
        correct_bge.append(hit_at_k(top_ids, gt, 5))

    bge_results = {k: sum(v) / len(v) for k, v in metrics_bge.items()}
    print(f"\n   T+ (BGE-only):")
    for k, v in bge_results.items():
        print(f"     {k:>8}: {v:.4f}")

    # ── 寫回到既有 evaluation_results.json ──
    R = json.loads((DATA / "evaluation_results.json").read_text(encoding="utf-8"))
    label_bge = "T+ (BGE-only)"
    R["test_metrics"][label_bge] = bge_results
    R["per_query_correct_test"][label_bge] = correct_bge
    (DATA / "evaluation_results.json").write_text(
        json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✅ 已併入 evaluation_results.json（新增 {label_bge} 條件）")
    print(f"   下一步：python scripts/5_statistics.py 重新生成統計表")


if __name__ == "__main__":
    main()
