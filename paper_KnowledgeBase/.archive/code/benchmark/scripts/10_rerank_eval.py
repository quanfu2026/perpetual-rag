#!/usr/bin/env python3
"""
Stage 10: 兩階段檢索（T+ retrieval → Cross-encoder rerank）。

針對 §VI-D 之 E2「字面相似誘導」改進，加入 cross-encoder reranker：
  Stage A: T+ (BM25+BGE Hybrid α=0.1) 取 Top-50 候選
  Stage B: BGE-reranker-base 對 (query, doc) 配對重新評分
  Stage C: 取重排後 Top-K

預期 Hit@1 大幅提升（cross-encoder 對精確排序最有效）。
"""
import json
import time
from collections import defaultdict
from pathlib import Path

import numpy as np
import jieba
from rank_bm25 import BM25Okapi
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import CrossEncoder

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
KS = [1, 3, 5, 10]
ALPHA = 0.1
TOP_N_CANDIDATES = 50  # 第一階段保留前 50 候選
RERANKER_MODEL = "BAAI/bge-reranker-base"


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
    test = [q for q in queries if q["subset"] == "test"]
    doc_ids = [d["doc_id"] for d in corpus]
    doc_texts_full = [doc_text(d) for d in corpus]
    doc_text_dict = dict(zip(doc_ids, doc_texts_full))

    print(f"📚 corpus: {len(corpus)} docs")
    print(f"📋 test: {len(test)} queries")

    # ── Stage A: T+ retrieval (BM25 + BGE) ──
    print(f"\n🔬 Stage A: T+ 檢索取 Top-{TOP_N_CANDIDATES}...")
    cache = DATA / "embeddings"
    doc_emb = np.load(cache / "corpus_bge.npy")
    test_q_emb = np.load(cache / "test_queries_bge.npy")

    tokenized = [list(jieba.cut(t)) for t in doc_texts_full]
    bm25 = BM25Okapi(tokenized)

    t0 = time.time()
    candidates = []  # list of (query_text, gt, candidate_doc_ids)
    for i, q in enumerate(test):
        bm = bm25.get_scores(list(jieba.cut(q["query"])))
        if bm.max() > bm.min():
            bm = (bm - bm.min()) / (bm.max() - bm.min())
        cos = cosine_similarity([test_q_emb[i]], doc_emb)[0]
        s = ALPHA * bm + (1 - ALPHA) * cos
        idx = s.argsort()[::-1][:TOP_N_CANDIDATES]
        cand_ids = [doc_ids[j] for j in idx]
        candidates.append({
            "query": q["query"],
            "gt": q["expert_verification"]["final_gt"],
            "cand_ids": cand_ids,
        })
    print(f"   完成：{time.time()-t0:.1f}s")

    # ── Stage A baseline metrics（不重排）──
    print(f"\n📊 Stage A baseline (T+ 不重排):")
    for k in KS:
        h = sum(hit_at_k(c["cand_ids"], c["gt"], k) for c in candidates) / len(candidates)
        print(f"     Hit@{k:>2}: {h:.4f}")

    # ── Stage B: Cross-encoder rerank ──
    print(f"\n🤖 Stage B: 載入 {RERANKER_MODEL}（首次需下載 ~280MB）...")
    t0 = time.time()
    reranker = CrossEncoder(RERANKER_MODEL, max_length=512)
    print(f"   載入：{time.time()-t0:.1f}s")

    print(f"\n🎯 Stage B: 重排 {len(candidates)*TOP_N_CANDIDATES:,} 個 (query, doc) 配對...")
    t0 = time.time()
    reranked = []
    for i, c in enumerate(candidates):
        pairs = [(c["query"], doc_text_dict[did]) for did in c["cand_ids"]]
        scores = reranker.predict(pairs, batch_size=32, show_progress_bar=False)
        # sort by reranker score desc
        order = np.argsort(scores)[::-1]
        reranked_ids = [c["cand_ids"][j] for j in order]
        reranked.append(reranked_ids)
        if (i + 1) % 100 == 0:
            elapsed = time.time() - t0
            eta = elapsed / (i + 1) * (len(candidates) - i - 1)
            print(f"     {i+1}/{len(candidates)} ({elapsed:.0f}s, ETA {eta:.0f}s)")
    print(f"   完成：{time.time()-t0:.1f}s")

    # ── 重排後 metrics ──
    print(f"\n🏆 Stage C: 重排後（T++ rerank）結果:")
    metrics_rerank = {}
    correct_rerank_5 = []
    for k in KS:
        h = sum(hit_at_k(reranked[i], candidates[i]["gt"], k) for i in range(len(test))) / len(test)
        metrics_rerank[f"Hit@{k}"] = h
        print(f"     Hit@{k:>2}: {h:.4f}")
    metrics_rerank["MRR"] = sum(rr(reranked[i], candidates[i]["gt"]) for i in range(len(test))) / len(test)
    print(f"          MRR: {metrics_rerank['MRR']:.4f}")
    correct_rerank_5 = [hit_at_k(reranked[i], candidates[i]["gt"], 5) for i in range(len(test))]

    # ── 寫回 evaluation_results.json ──
    R = json.loads((DATA / "evaluation_results.json").read_text(encoding="utf-8"))
    label = "T++ (T+ → CrossEncoder rerank)"
    R["test_metrics"][label] = metrics_rerank
    R["per_query_correct_test"][label] = correct_rerank_5
    (DATA / "evaluation_results.json").write_text(
        json.dumps(R, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✅ 已併入 evaluation_results.json（新增 {label}）")
    print(f"   下一步：python scripts/5_statistics.py 重算統計")


if __name__ == "__main__":
    main()
