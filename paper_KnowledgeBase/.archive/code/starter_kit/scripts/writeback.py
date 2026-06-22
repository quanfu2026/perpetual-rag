#!/usr/bin/env python3
"""
執行後自動回寫腳本
將任務完成記錄追加至對應章節筆記，並更新 sessionhandoff.md
執行方式：python3 ~/paper_KnowledgeBase/scripts/writeback.py "章節路徑" "完成內容"
範例：python3 writeback.py "第一章_緒論/1.1_研究背景.md" "補充了幻覺成因分類表格"
"""

import os
import sys
from datetime import datetime

VAULT = os.path.expanduser("~/paper_KnowledgeBase")

def append_to_note(rel_path, content):
    full_path = os.path.join(VAULT, rel_path)
    if not os.path.exists(full_path):
        print(f"❌ 找不到檔案：{full_path}")
        return False
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"\n---\n## [{timestamp}] 執行記錄\n{content}\n"
    with open(full_path, "a", encoding="utf-8") as f:
        f.write(entry)
    print(f"✅ 已回寫至：{rel_path}")
    return True

def update_sessionhandoff(rel_path, content):
    handoff_path = os.path.join(VAULT, "sessionhandoff.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    entry = f"- [{timestamp}] ✅ {rel_path}：{content}\n"
    with open(handoff_path, "r", encoding="utf-8") as f:
        text = f.read()
    text = text.replace(
        "## ✅ 上次完成的事項\n",
        f"## ✅ 上次完成的事項\n{entry}"
    )
    with open(handoff_path, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"✅ sessionhandoff.md 已同步更新")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法：python3 writeback.py <章節路徑> <完成內容描述>")
        sys.exit(1)
    rel_path = sys.argv[1]
    content = sys.argv[2]
    ok = append_to_note(rel_path, content)
    if ok:
        update_sessionhandoff(rel_path, content)
