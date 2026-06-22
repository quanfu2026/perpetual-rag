#!/usr/bin/env python3
"""
Stage 4: α 參數調整 + Hit@K + MRR 評估。

執行：
  - 對 dev set（500 筆）掃描 α ∈ {0.0, 0.1, ..., 1.0}
  - 找出最佳 α*（依 dev Hit@5）
  - 用 α* 在 test set（500 筆）評估
  - 同時跑三組對照（B0 Pure LLM 留 stub / B1 Naive RAG / B2 BM25-only / T 本研究）
"""
import json
import math
from collections import defaultdict
from pathlib import Path

import random
try:
    import jieba
    from rank_bm25 import BM25Okapi
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError as e:
    print(f"⚠️  缺少依賴：{e.name}")
    print("   pip install rank_bm25 jieba scikit-learn")
    raise SystemExit(1)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

ALPHAS = [round(0.1 * i, 1) for i in range(11)]
KS = [1, 3, 5, 10]


# ── 載入語料 ────────────────────────────────────────────────────

def load():
    corpus = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))
    queries = json.loads((DATA / "queries.json").read_text(encoding="utf-8"))
    # 只用已仲裁完成且有 final_gt 的樣本
    queries = [q for q in queries if q["expert_verification"].get("final_gt")]
    return corpus, queries


def doc_text(d):
    return f"{d['model']} " + " ".join(d["specs"].values()) + " " + d["description"]


def tokenize(text):
    return list(jieba.cut(text))


# ── 檢索器 ──────────────────────────────────────────────────────

class RandomRetriever:
    """B0: 隨機檢索基準（statistical floor / chance level）。"""
    def __init__(self, corpus, seed=42):
        self.doc_ids = [d["doc_id"] for d in corpus]
        self.rng = random.Random(seed)

    def topk(self, query, alpha, k):
        ids = self.doc_ids.copy()
        self.rng.shuffle(ids)
        return ids[:k]


class HybridRetriever:
    def __init__(self, corpus):
        self.corpus = corpus
        self.doc_ids = [d["doc_id"] for d in corpus]
        texts = [doc_text(d) for d in corpus]

        # BM25（jieba tokenized）
        tokenized = [tokenize(t) for t in texts]
        self.bm25 = BM25Okapi(tokenized)

        # TF-IDF（character n-gram，輕量替代向量檢索）
        self.tfidf = TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4))
        self.tfidf_mat = self.tfidf.fit_transform(texts)

    def score(self, query, alpha):
        bm25_scores = self.bm25.get_scores(tokenize(query))
        # min-max normalize
        if bm25_scores.max() > bm25_scores.min():
            bm25_norm = (bm25_scores - bm25_scores.min()) / (bm25_scores.max() - bm25_scores.min())
        else:
            bm25_norm = bm25_scores

        q_vec = self.tfidf.transform([query])
        cos = cosine_similarity(q_vec, self.tfidf_mat)[0]

        return alpha * bm25_norm + (1 - alpha) * cos

    def topk(self, query, alpha, k):
        scores = self.score(query, alpha)
        idx = scores.argsort()[::-1][:k]
        return [self.doc_ids[i] for i in idx]


# ── 評估指標 ────────────────────────────────────────────────────

def hit_at_k(predicted, gt, k):
    return 1 if gt in predicted[:k] else 0


def reciprocal_rank(predicted, gt):
    for i, p in enumerate(predicted, 1):
        if p == gt:
            return 1.0 / i
    return 0.0


def evaluate_set(retriever, queries, alpha):
    metrics = defaultdict(list)
    for q in queries:
        gt = q["expert_verification"]["final_gt"]
        topk = retriever.topk(q["query"], alpha, max(KS))
        for k in KS:
            metrics[f"Hit@{k}"].append(hit_at_k(topk, gt, k))
        metrics["MRR"].append(reciprocal_rank(topk, gt))
    return {k: sum(v) / len(v) for k, v in metrics.items()}


# ── 主流程 ──────────────────────────────────────────────────────

def main():
    corpus, queries = load()
    if not queries:
        print("⚠️  沒有已標註完成的查詢。請先完成 stage 2 + 3。")
        return

    dev = [q for q in queries if q["subset"] == "dev"]
    test = [q for q in queries if q["subset"] == "test"]
    print(f"📚 corpus: {len(corpus)} docs")
    print(f"📋 dev:    {len(dev)} queries")
    print(f"📋 test:   {len(test)} queries")

    print("\n🔧 建立檢索器...")
    retriever = HybridRetriever(corpus)

    # ── α 掃描（dev） ──
    print(f"\n🔬 α 掃描（dev set, n={len(dev)}）")
    print(f"   {'α':>5}  {'Hit@1':>7}  {'Hit@3':>7}  {'Hit@5':>7}  {'Hit@10':>7}  {'MRR':>7}")
    sweep = {}
    for a in ALPHAS:
        m = evaluate_set(retriever, dev, a)
        sweep[a] = m
        print(f"   {a:>5}  {m['Hit@1']:>7.4f}  {m['Hit@3']:>7.4f}  "
              f"{m['Hit@5']:>7.4f}  {m['Hit@10']:>7.4f}  {m['MRR']:>7.4f}")

    best_alpha = max(sweep, key=lambda a: sweep[a]["Hit@5"])
    print(f"\n   ⭐ 最佳 α* = {best_alpha} (dev Hit@5 = {sweep[best_alpha]['Hit@5']:.4f})")

    # ── test 評估 + 對照組（含 B0 Random）──
    print(f"\n🎯 test set 評估（n={len(test)}）")
    random_retriever = RandomRetriever(corpus)

    print(f"   {'condition':<35}  {'Hit@1':>7}  {'Hit@3':>7}  {'Hit@5':>7}  {'Hit@10':>7}  {'MRR':>7}")
    test_metrics = {}
    per_query_correct = {}

    # B0 Random
    m = evaluate_set(random_retriever, test, 0.0)
    test_metrics["B0 (Random)"] = m
    per_query_correct["B0 (Random)"] = [
        hit_at_k(random_retriever.topk(q["query"], 0, 5),
                 q["expert_verification"]["final_gt"], 5)
        for q in test
    ]
    print(f"   {'B0 (Random)':<35}  {m['Hit@1']:>7.4f}  {m['Hit@3']:>7.4f}  "
          f"{m['Hit@5']:>7.4f}  {m['Hit@10']:>7.4f}  {m['MRR']:>7.4f}")

    # B1, B2, T
    conditions = {
        "B1 (Naive RAG, α=0)": 0.0,
        "B2 (BM25 only, α=1)": 1.0,
        f"T  (Perpetual RAG, α*={best_alpha})": best_alpha,
    }
    for name, a in conditions.items():
        m = evaluate_set(retriever, test, a)
        test_metrics[name] = m
        per_query_correct[name] = [
            hit_at_k(retriever.topk(q["query"], a, 5),
                     q["expert_verification"]["final_gt"], 5)
            for q in test
        ]
        print(f"   {name:<35}  {m['Hit@1']:>7.4f}  {m['Hit@3']:>7.4f}  "
              f"{m['Hit@5']:>7.4f}  {m['Hit@10']:>7.4f}  {m['MRR']:>7.4f}")

    # ── 寫出結果 ──
    out = {
        "best_alpha": best_alpha,
        "alpha_sweep_dev": sweep,
        "test_metrics": test_metrics,
        "per_query_correct_test": per_query_correct,
        "test_query_ids": [q["id"] for q in test],
    }
    (DATA / "evaluation_results.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✅ 結果已寫入 data/evaluation_results.json")
    print(f"   下一步：python scripts/5_statistics.py")


if __name__ == "__main__":
    main()
