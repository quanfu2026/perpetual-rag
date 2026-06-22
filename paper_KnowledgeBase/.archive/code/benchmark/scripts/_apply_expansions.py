#!/usr/bin/env python3
"""
合併 _expansions.json 中的擴寫結果回 queries.json。

_expansions.json 格式：{"dev_0001": "擴寫後的句子", ...}
"""
import json
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "data"

queries = json.loads((DATA / "queries.json").read_text(encoding="utf-8"))
expansions = json.loads((DATA / "_expansions.json").read_text(encoding="utf-8"))
by_id = {q["id"]: q for q in queries}

applied = 0
for qid, expanded in expansions.items():
    if qid not in by_id:
        continue
    by_id[qid]["query"] = expanded
    by_id[qid]["expanded"] = True
    applied += 1

(DATA / "queries.json").write_text(
    json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8"
)
total_expanded = sum(1 for q in queries if q.get("expanded"))
print(f"✅ 套用 {applied} 筆；累計已擴寫 {total_expanded}/{len(queries)}")
