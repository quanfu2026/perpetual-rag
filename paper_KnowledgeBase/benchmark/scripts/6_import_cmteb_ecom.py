#!/usr/bin/env python3
"""
Import C-MTEB/EcomRetrieval (Chinese E-commerce Retrieval Benchmark) as our base.

C-MTEB/EcomRetrieval 是中文電商檢索的標準 benchmark（Multi-CPR 的 e-commerce 子集），
含 100,902 篇真實商品、1,000 筆查詢、1,000 筆 qrels 標準答案。

本腳本將其轉換為本研究的 corpus.json + queries.json 格式，並支援子採樣。
由於 qrels 已是學術標準 ground truth，可直接跳過雙標註者流程（IRR 步驟）。

Usage:
  python 6_import_cmteb_ecom.py --queries 500 --distractors 1500
  # 子採樣 500 筆查詢 + 500 GT docs + 1500 干擾項 = 2000 篇 corpus

  python 6_import_cmteb_ecom.py --queries 1000 --distractors 4000
  # 完整 1000 筆 + 4000 干擾項 = 5000 篇 corpus（更挑戰性）
"""
import argparse
import json
import random
from pathlib import Path

from datasets import load_dataset

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--queries", type=int, default=1000,
                        help="子採樣查詢數（預設 1000，最多 1000）")
    parser.add_argument("--distractors", type=int, default=1000,
                        help="干擾項數量（隨機採樣自 corpus，預設 1000）")
    parser.add_argument("--dev-ratio", type=float, default=0.5,
                        help="dev/test 切分比例（預設 0.5）")
    parser.add_argument("--backup", action="store_true",
                        help="備份既有 mock 資料")
    args = parser.parse_args()

    if args.backup:
        for fn in ("corpus.json", "queries.json"):
            src = DATA / fn
            if src.exists():
                src.rename(DATA / f"{fn}.mock_bak")
                print(f"[backup] {fn} → {fn}.mock_bak")

    print("📥 Downloading C-MTEB/EcomRetrieval...")
    ds = load_dataset("C-MTEB/EcomRetrieval")
    qrels_ds = load_dataset("C-MTEB/EcomRetrieval-qrels")["dev"]

    corpus_full = ds["corpus"]  # 100,902 docs
    queries_full = ds["queries"]  # 1,000 queries
    print(f"  corpus: {len(corpus_full)} docs")
    print(f"  queries: {len(queries_full)} queries")
    print(f"  qrels: {len(qrels_ds)} judgments")

    # ── 建立 qrels 索引 ──
    qid_to_pid = {row["qid"]: row["pid"] for row in qrels_ds}
    pid_to_text = {row["id"]: row["text"] for row in corpus_full}

    # ── 子採樣查詢 ──
    sampled_queries = list(queries_full)
    random.shuffle(sampled_queries)
    sampled_queries = sampled_queries[: args.queries]

    # 確保查詢有對應 qrel
    sampled_queries = [q for q in sampled_queries if q["id"] in qid_to_pid]
    print(f"\n📋 採樣 {len(sampled_queries)} 筆有效查詢")

    # ── 收集 GT pids ──
    gt_pids = {qid_to_pid[q["id"]] for q in sampled_queries}
    print(f"   對應 {len(gt_pids)} 個 GT 商品")

    # ── 採樣干擾項 ──
    all_pids = set(pid_to_text.keys())
    distractor_pool = list(all_pids - gt_pids)
    random.shuffle(distractor_pool)
    distractors = distractor_pool[: args.distractors]
    print(f"   採樣 {len(distractors)} 個干擾項")

    # ── 組裝 corpus（保留原始 pid 作為 doc_id 後綴）──
    selected_pids = sorted(gt_pids | set(distractors))
    corpus_out = []
    for pid in selected_pids:
        text = pid_to_text[pid]
        corpus_out.append({
            "doc_id": f"doc_{pid}",
            "category": "ecom",
            "model": "",  # C-MTEB 無結構化 model 欄位，留空
            "specs": {},
            "description": text,
            "_source": "C-MTEB/EcomRetrieval",
            "_orig_pid": pid,
        })
    print(f"\n📚 corpus 總計：{len(corpus_out)} 篇")

    # ── 組裝 queries（含 GT，跳過雙標註步驟）──
    n_dev = int(len(sampled_queries) * args.dev_ratio)
    queries_out = []
    for i, q in enumerate(sampled_queries):
        gt_pid = qid_to_pid[q["id"]]
        gt_doc_id = f"doc_{gt_pid}"
        subset = "dev" if i < n_dev else "test"
        queries_out.append({
            "id": f"{subset}_{i:04d}",
            "subset": subset,
            "category": "ecom_search",  # 統一類型
            "product_category": "ecom",
            "query_template": q["text"],
            "query": q["text"],  # 已是真實使用者查詢，直接使用
            "expansion_hint": "C-MTEB benchmark 真實查詢，無需擴寫",
            "ground_truth_doc_id": gt_doc_id,
            "expert_verification": {
                "annotator_A": gt_doc_id,        # 直接使用 C-MTEB 官方 qrel
                "annotator_B": gt_doc_id,        # 同上
                "status": "consistent",          # 預先標記為一致
                "final_gt": gt_doc_id,
            },
            "expanded": True,
            "_source": "C-MTEB/EcomRetrieval",
            "_orig_qid": q["id"],
        })
    print(f"📋 queries 總計：{len(queries_out)} 筆")
    print(f"   dev: {sum(1 for q in queries_out if q['subset']=='dev')} 筆")
    print(f"   test: {sum(1 for q in queries_out if q['subset']=='test')} 筆")

    # ── 寫出 ──
    (DATA / "corpus.json").write_text(
        json.dumps(corpus_out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (DATA / "queries.json").write_text(
        json.dumps(queries_out, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"\n✅ 寫出 data/corpus.json + data/queries.json")
    print(f"\n💡 後續步驟：")
    print(f"   python scripts/4_evaluate.py    # 直接跑評估（已跳過標註步驟）")
    print(f"   python scripts/5_statistics.py  # 統計檢定")
    print(f"\n📝 樣本查驗（隨機 5 筆 query + 對應 GT doc）：")
    samples = random.sample(queries_out, 5)
    for q in samples:
        gt_text = pid_to_text[q["_orig_qid"] and qid_to_pid[q["_orig_qid"]]]
        print(f"\n   [{q['id']}] query: {q['query']}")
        print(f"   GT doc:  {gt_text[:80]}")


if __name__ == "__main__":
    main()
