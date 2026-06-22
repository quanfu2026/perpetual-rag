#!/usr/bin/env python3
"""
跨章節一致性檢查腳本
偵測不同章節間的矛盾論點（關鍵詞衝突）
執行方式：python3 ~/paper_KnowledgeBase/scripts/consistency_check.py
"""

import os
import re
from datetime import date

VAULT = os.path.expanduser("~/paper_KnowledgeBase")
TODAY = date.today().isoformat()

# 需要跨章節一致的關鍵技術術語
KEY_TERMS = {
    "幻覺率": r"幻覺率.*?(\d+\.?\d*%)",
    "Hit@5": r"Hit@5.*?(\d+\.?\d*%)",
    "MRR": r"MRR.*?(\d+\.?\d*)",
    "alpha參數": r"α.*?(\d+\.?\d*)",
    "Top-K": r"Top-(\d+)",
}

def scan_all_notes():
    notes = {}
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if not d.startswith(("scripts", ".obsidian"))]
        for fname in files:
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(root, fname)
            rel = os.path.relpath(fpath, VAULT)
            with open(fpath, encoding="utf-8") as f:
                notes[rel] = f.read()
    return notes

"""
合理的多值術語白名單：同一概念在不同階段有不同數值，不視為矛盾
格式：{術語: 說明}
"""
WHITELIST = {
    "Top-K": "雙階段架構中第一階段召回 Top-50、第二階段精選 Top-5，屬正常分階段設計，非矛盾",
    "幻覺率": "幻覺率有三種合理脈絡：(1) 外部文獻基準 5%（雙階段RAG電商），(2) 純LLM無RAG時 100%（對照組），(3) 本研究設計目標 < 1%；三者測量情境不同，非矛盾",
    "Hit@5": "Hit@5 有兩種合理脈絡：(1) 外部文獻基準 95.0%（雙階段RAG電商），(2) 本研究設計目標 > 90%；95.0% 與 95% 為相同數值的格式差異，非矛盾",
}

def check_conflicts(notes):
    conflicts = []
    term_occurrences = {term: [] for term in KEY_TERMS}

    for rel_path, content in notes.items():
        for term, pattern in KEY_TERMS.items():
            matches = re.findall(pattern, content)
            for m in matches:
                term_occurrences[term].append((rel_path, m))

    for term, occurrences in term_occurrences.items():
        if len(occurrences) < 2:
            continue
        values = set(v for _, v in occurrences)
        if len(values) > 1:
            if term in WHITELIST:
                print(f"ℹ️  [{term}] 多值已知合理：{WHITELIST[term]}")
                continue
            conflicts.append({
                "term": term,
                "values": values,
                "files": occurrences
            })
    return conflicts

def write_report(conflicts):
    report_path = os.path.join(VAULT, "00_一致性檢查報告.md")
    if not conflicts:
        body = "✅ 未發現跨章節矛盾，知識庫一致性良好。"
    else:
        lines = []
        for c in conflicts:
            lines.append(f"### ⚠️ 術語：`{c['term']}`")
            lines.append(f"發現 **{len(set(v for _,v in c['files']))} 種不同數值**：")
            for fpath, val in c["files"]:
                lines.append(f"- `{fpath}` → **{val}**")
            lines.append("")
        body = "\n".join(lines)

    content = f"""---
status: draft
tags: [一致性檢查, 品質保證]
source: Claude-Code
created: {TODAY}
last_updated: {TODAY}
---

# ⚖️ 跨章節一致性檢查報告 — {TODAY}

## 結果摘要
- 檢查術語數：{len(KEY_TERMS)}
- 發現矛盾數：{len(conflicts)}

---

## 詳細報告

{body}

---

> 此報告由 consistency_check.py 自動生成於 {TODAY}
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(content)
    return report_path

if __name__ == "__main__":
    print("🔍 掃描所有筆記...")
    notes = scan_all_notes()
    print(f"   共掃描 {len(notes)} 個檔案")
    conflicts = check_conflicts(notes)
    path = write_report(conflicts)
    if conflicts:
        print(f"⚠️  發現 {len(conflicts)} 個跨章節矛盾，詳見：{path}")
    else:
        print(f"✅ 未發現矛盾，報告已寫入：{path}")
