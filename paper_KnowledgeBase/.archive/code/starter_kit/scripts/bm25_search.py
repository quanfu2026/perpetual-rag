#!/usr/bin/env python3
"""
BM25 知識庫搜尋引擎
對 paper_KnowledgeBase 所有筆記建立 BM25 索引，支援加權關鍵字查詢
執行方式：
  ~/paper_KnowledgeBase/.venv/bin/python3 scripts/bm25_search.py "幻覺成因"
  ~/paper_KnowledgeBase/.venv/bin/python3 scripts/bm25_search.py "TF-IDF 召回" --top 5
"""

import os
import sys
import re
import jieba
from rank_bm25 import BM25Okapi

VAULT = os.path.expanduser("~/paper_KnowledgeBase")
EXCLUDE = {"scripts", ".venv", ".obsidian"}

def load_notes():
    notes = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in EXCLUDE and not d.startswith(".")]
        for fname in sorted(files):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, VAULT)
            with open(fpath, encoding="utf-8") as f:
                content = f.read()
            # 移除 YAML frontmatter
            content = re.sub(r"^---.*?---\n", "", content, flags=re.DOTALL)
            notes.append({"path": rel, "content": content})
    return notes

def tokenize(text):
    # 中文分詞 + 英文 token
    tokens = list(jieba.cut(text))
    tokens += re.findall(r"[a-zA-Z0-9]+", text)
    return [t.strip() for t in tokens if len(t.strip()) > 1]

def search(query, top_k=5, top_n=None, silent=False):
    """返回結構化搜尋結果列表（供模組呼叫）；silent=False 時同時印出結果。"""
    if top_n is not None:
        top_k = top_n  # 向後相容舊參數名

    notes = load_notes()
    corpus = [tokenize(n["content"]) for n in notes]
    bm25 = BM25Okapi(corpus)
    query_tokens = tokenize(query)
    scores = bm25.get_scores(query_tokens)

    ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)[:top_k]

    hits = []
    for rank, (idx, score) in enumerate(ranked, 1):
        if score < 0.01:
            continue
        note = notes[idx]
        snippet = ""
        for line in note["content"].split("\n"):
            if any(t in line for t in query_tokens):
                snippet = line.strip()[:80]
                break
        hits.append({"rank": rank, "score": round(score, 3), "path": note["path"], "snippet": snippet})

    if not silent:
        print(f"\n🔍 查詢：「{query}」")
        print(f"📚 索引筆記數：{len(notes)}\n")
        print("=" * 60)
        for h in hits:
            print(f"#{h['rank']}  分數：{h['score']:.3f}")
            print(f"    📄 {h['path']}")
            if h["snippet"]:
                print(f"    💬 ...{h['snippet']}...")
            print()
        print("=" * 60)

    return hits


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法：python3 bm25_search.py <查詢詞> [--top N | --top-k N]")
        sys.exit(1)

    query = sys.argv[1]
    top_k = 5
    for flag in ["--top", "--top-k"]:
        if flag in sys.argv:
            top_k = int(sys.argv[sys.argv.index(flag) + 1])

    search(query, top_k=top_k)
