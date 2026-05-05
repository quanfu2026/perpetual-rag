#!/usr/bin/env python3
"""
Stage 2: Export queries → annotator CSV / Import filled CSV → JSON.

Usage:
  python 2_annotate.py export   # 匯出 annotator_A.csv 與 annotator_B.csv
  python 2_annotate.py import   # 從填好的 CSV 匯入回 queries.json
"""
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ANNO = DATA / "annotations"
ANNO.mkdir(exist_ok=True)


def load_queries():
    return json.loads((DATA / "queries.json").read_text(encoding="utf-8"))


def save_queries(queries):
    (DATA / "queries.json").write_text(
        json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def export():
    queries = load_queries()
    corpus = json.loads((DATA / "corpus.json").read_text(encoding="utf-8"))
    candidates = "\n".join(f"  - {d['doc_id']}: {d['model']}" for d in corpus[:5])

    for ann in ("A", "B"):
        path = ANNO / f"annotator_{ann}.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "subset", "category", "query", "annotated_doc_id", "notes"])
            for q in queries:
                w.writerow([q["id"], q["subset"], q["category"], q["query"], "", ""])
        print(f"[export] 已寫出 {path.relative_to(ROOT)}")

    guide = ANNO / "annotation_instructions.md"
    guide.write_text(
        f"""# 標註指南

## 任務
對每筆查詢（query 欄位），從 200 篇商品語料庫（`data/corpus.json`）中
選出最符合該查詢之 ground truth 商品，將其 doc_id 填入 `annotated_doc_id` 欄位。

## 候選查詢範例
```
{candidates}
  - ...（共 200 筆，請參考 data/corpus.json）
```

## 規則
1. 每筆查詢必須有一個確定的 doc_id 答案
2. 若無任何商品符合，填寫 `NONE`
3. 若有多個合理候選，選**最匹配**者（依字面或語意）並在 notes 欄位簡述理由
4. 標註過程中**禁止與另一位標註者討論**

## 一致性目標
- Cohen's Kappa ≥ 0.75（substantial agreement）
- 若 κ < 0.75，需重新檢視標註指南並重標衝突部分

## 完成後
將填好的 CSV 放回 `data/annotations/annotator_{{A,B}}.csv`，
然後執行：`python scripts/2_annotate.py import`
""",
        encoding="utf-8",
    )
    print(f"[export] 標註指南：{guide.relative_to(ROOT)}")


def import_():
    queries = load_queries()
    by_id = {q["id"]: q for q in queries}

    for ann in ("A", "B"):
        path = ANNO / f"annotator_{ann}.csv"
        if not path.exists():
            print(f"[import] ⚠️  找不到 {path}，跳過")
            continue

        with path.open(encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                qid = row["id"]
                if qid not in by_id:
                    continue
                doc = row["annotated_doc_id"].strip() or None
                by_id[qid]["expert_verification"][f"annotator_{ann}"] = doc
                count += 1
        print(f"[import] {path.name}: {count} 筆")

    # 計算一致性狀態
    consistent = 0
    conflict = 0
    pending = 0
    for q in queries:
        a = q["expert_verification"]["annotator_A"]
        b = q["expert_verification"]["annotator_B"]
        if a is None or b is None:
            q["expert_verification"]["status"] = "pending"
            pending += 1
        elif a == b:
            q["expert_verification"]["status"] = "consistent"
            q["expert_verification"]["final_gt"] = a
            consistent += 1
        else:
            q["expert_verification"]["status"] = "conflict"
            conflict += 1

    save_queries(queries)
    total = len(queries)
    print(f"\n📊 標註狀態：")
    print(f"   一致：{consistent} ({consistent/total*100:.1f}%)")
    print(f"   衝突：{conflict} ({conflict/total*100:.1f}%)")
    print(f"   未完：{pending} ({pending/total*100:.1f}%)")
    print(f"\n下一步：python scripts/3_verify.py")


def main():
    if len(sys.argv) < 2 or sys.argv[1] not in ("export", "import"):
        print(__doc__)
        sys.exit(1)
    if sys.argv[1] == "export":
        export()
    else:
        import_()


if __name__ == "__main__":
    main()
