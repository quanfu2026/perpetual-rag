#!/usr/bin/env python3
"""
Stage 9: BM25 + BGE 混合檢索 α 掃描，決定 T++ 最佳組態。

讀取 8_bge_eval.py 已快取的 BGE embeddings + 既有 BM25 索引，
計算 hybrid 分數並掃描 α，與 BGE-only 比較。
"""
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import jieba
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KS = [1, 3, 5, 10]
ALPHAS = [round(0.1 * i, 1) for i in range(11)]


def load():
    corpus = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))
    queries = json.loads((DATA / "queries.json").read_text(encoding="utf-8"))
    queries = [q for q in queries if q["expert_verification"].get("final_gt")]
    return corpus, queries


def doc_text(d):
    return f"{d.get('model','')} " + " ".join(d.get("specs", {}).values()) + " " + d.get("description", "")


def hit_at_k(p, gt, k):
    return 1 if gt in p[:k] else 0


def rr(p, gt):
    for i, x in enumerate(p, 1):
        if x == gt: return 1.0 / i
    return 0.0


def main():
    corpus, queries = load()
    dev = [q for q in queries if q["subset"] == "dev"]
    test = [q for q in queries if q["subset"] == "test"]
    doc_ids = [d["doc_id"] for d in corpus]

    print(f"📚 corpus: {len(corpus)} docs")
    print(f"📋 dev: {len(dev)} queries, test: {len(test)} queries")

    # ── 載入 BGE embeddings 快取 ──
    cache_dir = DATA / "embeddings"
    doc_emb = np.load(cache_dir / "corpus_bge.npy")

    # 編碼 dev queries（之前只算過 test）
    print(f"\n📥 載入 BGE 模型 + 編碼 dev 查詢...")
    from sentence_transformers import SentenceTransformer
    model = SentenceTransformer("BAAI/bge-small-zh-v1.5")
    dev_q_emb_path = cache_dir / "dev_queries_bge.npy"
    if dev_q_emb_path.exists():
        dev_q_emb = np.load(dev_q_emb_path)
    else:
        dev_q_emb = model.encode([q["query"] for q in dev], batch_size=32,
                                  convert_to_numpy=True, normalize_embeddings=True)
        np.save(dev_q_emb_path, dev_q_emb)
    test_q_emb = np.load(cache_dir / "test_queries_bge.npy")
    print(f"   dev: {dev_q_emb.shape}, test: {test_q_emb.shape}")

    # ── BM25 ──
    print(f"\n🔧 建立 BM25 索引...")
    tokenized = [list(jieba.cut(doc_text(d))) for d in corpus]
    bm25 = BM25Okapi(tokenized)

    def hybrid_topk(query_text, q_emb, alpha, k):
        bm = bm25.get_scores(list(jieba.cut(query_text)))
        if bm.max() > bm.min():
            bm = (bm - bm.min()) / (bm.max() - bm.min())
        cos = cosine_similarity([q_emb], doc_emb)[0]
        s = alpha * bm + (1 - alpha) * cos
        idx = s.argsort()[::-1][:k]
        return [doc_ids[i] for i in idx]

    # ── α 掃描 (dev) ──
    print(f"\n🔬 BM25 + BGE 混合 α 掃描（dev set, n={len(dev)}）")
    print(f"   {'α':>5}  {'Hit@1':>7}  {'Hit@3':>7}  {'Hit@5':>7}  {'Hit@10':>7}  {'MRR':>7}")
    sweep = {}
    t0 = time.time()
    for a in ALPHAS:
        m = defaultdict(list)
        for i, q in enumerate(dev):
            top = hybrid_topk(q["query"], dev_q_emb[i], a, max(KS))
            gt = q["expert_verification"]["final_gt"]
            for k in KS:
                m[f"Hit@{k}"].append(hit_at_k(top, gt, k))
            m["MRR"].append(rr(top, gt))
        agg = {k: sum(v) / len(v) for k, v in m.items()}
        sweep[a] = agg
        print(f"   {a:>5}  {agg['Hit@1']:>7.4f}  {agg['Hit@3']:>7.4f}  "
              f"{agg['Hit@5']:>7.4f}  {agg['Hit@10']:>7.4f}  {agg['MRR']:>7.4f}")

    best_alpha = max(sweep, key=lambda a: sweep[a]["Hit@5"])
    print(f"\n   ⭐ 最佳 α* = {best_alpha} (dev Hit@5 = {sweep[best_alpha]['Hit@5']:.4f})")
    print(f"   掃描耗時：{time.time()-t0:.0f}s")

    # ── test 評估 ──
    print(f"\n🎯 test set 評估（BM25+BGE α*={best_alpha}, n={len(test)}）")
    m = defaultdict(list)
    correct_at5 = []
    for i, q in enumerate(test):
        top = hybrid_topk(q["query"], test_q_emb[i], best_alpha, max(KS))
        gt = q["expert_verification"]["final_gt"]
        for k in KS:
            m[f"Hit@{k}"].append(hit_at_k(top, gt, k))
        m["MRR"].append(rr(top, gt))
        correct_at5.append(hit_at_k(top, gt, 5))
    agg = {k: sum(v) / len(v) for k, v in m.items()}
    for k, v in agg.items():
        print(f"     {k:>8}: {v:.4f}")

    # 寫回
    R = json.loads((DATA / "evaluation_results.json").read_text(encoding="utf-8"))
    label = f"T++ (BM25+BGE, α*={best_alpha})"
    R["test_metrics"][label] = agg
    R["per_query_correct_test"][label] = correct_at5
    R["bge_hybrid_alpha_sweep_dev"] = {str(a): sweep[a] for a in ALPHAS}
    R["best_alpha_bge_hybrid"] = best_alpha
    (DATA / "evaluation_results.json").write_text(
        json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✅ 已併入 evaluation_results.json（新增 {label}）")


if __name__ == "__main__":
    main()
