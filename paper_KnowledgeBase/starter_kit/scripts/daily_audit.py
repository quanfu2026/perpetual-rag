#!/usr/bin/env python3
"""
每日知識審計腳本
掃描 paper_KnowledgeBase 中所有章節狀態，產生每日待辦清單
執行方式：python3 ~/paper_KnowledgeBase/scripts/daily_audit.py
"""

import os
import re
from datetime import date

VAULT = os.path.expanduser("~/paper_KnowledgeBase")
TODAY = date.today().isoformat()

def get_status(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"^status:\s*(.+)$", content, re.MULTILINE)
    return match.group(1).strip() if match else "未設定"

def get_tags(filepath):
    with open(filepath, encoding="utf-8") as f:
        content = f.read()
    tags = re.findall(r"^\s+-\s+(.+)$", content[:500], re.MULTILINE)
    return tags[:3]

def scan_chapters():
    results = {"draft": [], "review": [], "final": [], "未設定": []}
    chapter_dirs = sorted([
        d for d in os.listdir(VAULT)
        if os.path.isdir(os.path.join(VAULT, d)) and d.startswith(("第", "參考"))
    ])
    for chapter in chapter_dirs:
        chapter_path = os.path.join(VAULT, chapter)
        for fname in sorted(os.listdir(chapter_path)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(chapter_path, fname)
            status = get_status(fpath)
            rel_path = f"{chapter}/{fname}"
            results.setdefault(status, []).append(rel_path)
    return results

def count_refs():
    ref_dir = os.path.join(VAULT, "參考文獻")
    if not os.path.exists(ref_dir):
        return 0
    return len([f for f in os.listdir(ref_dir) if f.endswith(".md")])

def write_todo(results):
    todo_path = os.path.join(VAULT, "00_每日待辦.md")
    draft_list = "\n".join(f"- [ ] {p}" for p in results.get("draft", []))
    review_list = "\n".join(f"- [ ] {p}" for p in results.get("review", []))
    final_list = "\n".join(f"- [x] {p}" for p in results.get("final", []))
    ref_count = count_refs()

    content = f"""---
status: draft
tags: [每日待辦, 審計]
source: Claude-Code
created: {TODAY}
last_updated: {TODAY}
---

# 📋 每日知識審計報告 — {TODAY}

## 統計總覽
| 狀態 | 數量 |
|------|------|
| 🔲 draft（待寫） | {len(results.get('draft', []))} |
| 🔍 review（審閱中） | {len(results.get('review', []))} |
| ✅ final（完成） | {len(results.get('final', []))} |
| 📚 參考文獻 | {ref_count} 篇 |

---

## 🔲 待寫章節（優先處理）

{draft_list if draft_list else "- 無"}

---

## 🔍 審閱中（需確認內容）

{review_list if review_list else "- 無"}

---

## ✅ 已完成

{final_list if final_list else "- 無"}

---

> 此報告由 daily_audit.py 自動生成於 {TODAY}
"""
    with open(todo_path, "w", encoding="utf-8") as f:
        f.write(content)
    return todo_path

if __name__ == "__main__":
    print(f"🔍 掃描 {VAULT} ...")
    results = scan_chapters()
    path = write_todo(results)
    print(f"✅ 審計完成，報告已寫入：{path}")
    print(f"   draft: {len(results.get('draft',[]))} 篇")
    print(f"   review: {len(results.get('review',[]))} 篇")
    print(f"   final: {len(results.get('final',[]))} 篇")
