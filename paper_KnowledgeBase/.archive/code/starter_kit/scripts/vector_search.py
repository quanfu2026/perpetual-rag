#!/usr/bin/env python3
"""
語意搜尋引擎（TF-IDF + Cosine Similarity）
Intel Mac 相容版：使用 sklearn TF-IDF 向量化，無需 GPU。

未來升級路徑：
  當硬體升級後，可將 build_tfidf_index() 替換為 ChromaDB + nomic-embed-text。

與 bm25_search.py 形成兩階段搜尋：
  BM25 Top-20（稀疏召回）→ TF-IDF 重排序 Top-5（語意精選）

執行方式：
  source ~/paper_KnowledgeBase/.venv/bin/activate
  python3 scripts/vector_search.py "查詢文字" [--top-k 5] [--mode tfidf|bm25|hybrid]

依賴：
  pip install scikit-learn jieba
"""

import os
import sys
import re
import argparse
import pickle
import hashlib
import yaml
import jieba
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

VAULT = os.path.expanduser("~/paper_KnowledgeBase")
INDEX_CACHE = os.path.join(VAULT, ".tfidf_index.pkl")

EXCLUDE_DIRS = {".venv", ".obsidian", "scripts", ".git", "node_modules", "_archive", "audio_files", ".chromadb"}
EXCLUDE_PREFIXES = ["00_", "CLAUDE", "session", "index", "只需說", "一句話", "交談內容", "開發思考"]


# ── 文件載入 ──────────────────────────────────────────────────────────────────

def load_markdown_files(include_drafts=False):
    docs, paths, titles = [], [], []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            if any(fname.startswith(p) for p in EXCLUDE_PREFIXES):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, VAULT)
            try:
                with open(fpath, encoding="utf-8") as f:
                    content = f.read()
            except UnicodeDecodeError:
                continue

            fm = {}
            if content.startswith("---"):
                end = content.find("---", 3)
                if end != -1:
                    try:
                        fm = yaml.safe_load(content[3:end]) or {}
                    except Exception:
                        pass
                    content = content[end + 3:].strip()

            status = fm.get("status", "draft")
            if status == "archive":
                continue
            if status == "draft" and not include_drafts:
                continue

            docs.append(content)
            paths.append(rel)
            titles.append(str(fm.get("title", fname)))
    return docs, paths, titles


def tokenize_for_tfidf(text):
    """中文 jieba 分詞 + 英文 token，供 TF-IDF analyzer 使用。"""
    tokens = list(jieba.cut(text))
    tokens += re.findall(r"[a-zA-Z0-9]+", text)
    return [t.strip() for t in tokens if len(t.strip()) > 1]


# ── 索引建立與快取 ──────────────────────────────────────────────────────────────

def build_tfidf_index(force_rebuild=False):
    """建立（或從快取載入）TF-IDF 索引。"""
    docs, paths, titles = load_markdown_files()

    # 計算語料庫 hash，若內容有變則重建
    corpus_hash = hashlib.md5("".join(paths).encode()).hexdigest()

    if not force_rebuild and os.path.exists(INDEX_CACHE):
        with open(INDEX_CACHE, "rb") as f:
            cached = pickle.load(f)
        if cached.get("hash") == corpus_hash:
            print(f"  載入快取索引（{len(paths)} 份文件）")
            return cached["vectorizer"], cached["matrix"], paths, titles

    print(f"  建立 TF-IDF 索引：{len(docs)} 份文件...")
    vectorizer = TfidfVectorizer(
        analyzer=tokenize_for_tfidf,
        max_features=20000,
        sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform(docs)

    with open(INDEX_CACHE, "wb") as f:
        pickle.dump({"hash": corpus_hash, "vectorizer": vectorizer, "matrix": matrix,
                     "paths": paths, "titles": titles}, f)
    print(f"  ✅ 索引完成（{matrix.shape[0]} 份文件，{matrix.shape[1]} 個特徵詞）")
    return vectorizer, matrix, paths, titles


# ── 搜尋函數 ───────────────────────────────────────────────────────────────────

def tfidf_search(query, top_k=5, force_rebuild=False):
    vectorizer, matrix, paths, titles = build_tfidf_index(force_rebuild=force_rebuild)
    q_vec = vectorizer.transform([query])
    scores = cosine_similarity(q_vec, matrix)[0]
    ranked_idx = np.argsort(scores)[::-1][:top_k]

    hits = []
    for rank, idx in enumerate(ranked_idx, 1):
        if scores[idx] < 0.01:
            continue
        hits.append({
            "rank": rank,
            "score": round(float(scores[idx]), 4),
            "path": paths[idx],
            "title": titles[idx],
        })
    return hits


def bm25_search(query, top_k=5):
    import importlib.util
    bm25_path = os.path.join(VAULT, "scripts", "bm25_search.py")
    spec = importlib.util.spec_from_file_location("bm25_search", bm25_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.search(query, top_k=top_k, silent=True)


def hybrid_search(query, bm25_top_k=20, final_top_k=5, force_rebuild=False):
    """兩階段：BM25 稀疏召回 → TF-IDF 語意重排序。"""
    bm25_hits = bm25_search(query, top_k=bm25_top_k)
    bm25_paths = {h["path"] for h in bm25_hits}

    # TF-IDF 全量搜尋
    all_tfidf = tfidf_search(query, top_k=50, force_rebuild=force_rebuild)

    # 只保留 BM25 候選集中的結果（交集重排序）
    reranked = [h for h in all_tfidf if h["path"] in bm25_paths]

    # 若交集太少，補充純 TF-IDF 結果
    if len(reranked) < final_top_k:
        existing = {h["path"] for h in reranked}
        for h in all_tfidf:
            if h["path"] not in existing:
                reranked.append(h)
            if len(reranked) >= final_top_k:
                break

    for i, h in enumerate(reranked[:final_top_k]):
        h["rank"] = i + 1
    return reranked[:final_top_k]


# ── 輸出格式化 ─────────────────────────────────────────────────────────────────

def print_results(hits, mode, query):
    mode_label = {"tfidf": "TF-IDF 語意", "bm25": "BM25 稀疏", "hybrid": "兩階段混合"}
    print(f"\n=== 搜尋結果 [{mode_label.get(mode, mode)}]：「{query}」===")
    for h in hits:
        print(f"  {h['rank']}. [{h['score']:.4f}] {h['path']}")
        if h.get("title"):
            print(f"       {h['title']}")
    print()


# ── 主程式 ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="語意搜尋引擎（TF-IDF / BM25 / 混合）")
    parser.add_argument("query", help="搜尋查詢")
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--mode", choices=["tfidf", "bm25", "hybrid"], default="tfidf")
    parser.add_argument("--rebuild", action="store_true", help="強制重建索引快取")
    args = parser.parse_args()

    print(f"🔍 查詢：「{args.query}」（模式：{args.mode}）")

    if args.mode == "tfidf":
        hits = tfidf_search(args.query, top_k=args.top_k, force_rebuild=args.rebuild)
    elif args.mode == "bm25":
        hits = bm25_search(args.query, top_k=args.top_k)
        for i, h in enumerate(hits):
            h.setdefault("rank", i + 1)
    else:
        hits = hybrid_search(args.query, bm25_top_k=args.top_k * 4, final_top_k=args.top_k, force_rebuild=args.rebuild)

    print_results(hits, args.mode, args.query)


if __name__ == "__main__":
    main()
