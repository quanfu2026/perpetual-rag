#!/usr/bin/env python3
"""
Perpetual RAG Starter Kit — 版本升級工具

執行方式：
  cd ~/paper_KnowledgeBase
  python3 starter_kit/scripts/bump_version.py

功能：
  1. 詢問升版類型（patch / minor / major）
  2. 詢問變更類型與異動元件
  3. 詢問修改者姓名
  4. 預覽所有將要變更的內容
  5. 人工確認後自動執行：
     - 更新 VERSION
     - 寫入 CHANGELOG.md（用戶可見）
     - 寫入 CONTRIBUTORS_LOG.md（內部責任追溯）
     - 更新 SETUP.md 頁首版號
     - git add + git commit + git tag
"""

import os
import re
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

STARTER_KIT = Path(__file__).parent.parent
VERSION_FILE    = STARTER_KIT / "VERSION"
CHANGELOG_FILE  = STARTER_KIT / "CHANGELOG.md"
CONTRIB_FILE    = STARTER_KIT / "CONTRIBUTORS_LOG.md"
SETUP_FILE      = STARTER_KIT / "SETUP.md"

TZ_TAIPEI = timezone(timedelta(hours=8))

CHANGE_TYPES = {
    "1": "新增功能",
    "2": "修改功能",
    "3": "刪除功能",
    "4": "錯誤修正",
    "5": "文件更新",
}

COMPONENTS = [
    "bm25_search.py",
    "hallucination_guard.py",
    "consistency_check.py",
    "writeback.py",
    "daily_audit.py",
    "vector_search.py",
    "knowledge_graph.py",
    "setup.py",
    "bump_version.py",
    "SETUP.md",
    "CLAUDE.md（範本）",
    "sessionhandoff.md（範本）",
    "REF_範本.md",
    "starter_kit（全部）",
    "其他（自行輸入）",
]


# ── 工具函式 ──────────────────────────────────────────────────────────────────

def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def bump(version: str, level: str) -> str:
    major, minor, patch = map(int, version.lstrip("v").split("."))
    if level == "major":
        return f"v{major + 1}.0.0"
    elif level == "minor":
        return f"v{major}.{minor + 1}.0"
    else:
        return f"v{major}.{minor}.{patch + 1}"


def git_user() -> str:
    try:
        result = subprocess.run(
            ["git", "config", "user.name"],
            capture_output=True, text=True, cwd=STARTER_KIT
        )
        return result.stdout.strip()
    except Exception:
        return ""


def run_git(args: list, cwd=None) -> bool:
    result = subprocess.run(args, capture_output=True, text=True, cwd=cwd or STARTER_KIT.parent)
    if result.returncode != 0:
        print(f"  ❌ git 錯誤：{result.stderr.strip()}")
        return False
    return True


def separator(char="─", width=60):
    print(char * width)


# ── 互動步驟 ──────────────────────────────────────────────────────────────────

def ask_bump_level(current: str) -> str:
    print(f"\n  當前版號：{current}")
    print()
    print("  請選擇升版類型：")
    print("    1) patch  — 錯誤修正、文件微調（例：v1.0.0 → v1.0.1）")
    print("    2) minor  — 新增功能、新增腳本（例：v1.0.0 → v1.1.0）")
    print("    3) major  — 架構重組、破壞性更動（例：v1.0.0 → v2.0.0）")
    print()
    while True:
        choice = input("  輸入 1 / 2 / 3：").strip()
        if choice == "1": return "patch"
        if choice == "2": return "minor"
        if choice == "3": return "major"
        print("  請輸入 1、2 或 3。")


def ask_change_type() -> str:
    print("\n  變更類型：")
    for key, label in CHANGE_TYPES.items():
        print(f"    {key}) {label}")
    print()
    while True:
        choice = input("  輸入 1–5：").strip()
        if choice in CHANGE_TYPES:
            return CHANGE_TYPES[choice]
        print("  請輸入 1 到 5。")


def ask_component() -> str:
    print("\n  異動元件（哪支腳本或哪份文件？）：")
    for i, name in enumerate(COMPONENTS, 1):
        print(f"    {i:2d}) {name}")
    print()
    while True:
        choice = input(f"  輸入 1–{len(COMPONENTS)}：").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(COMPONENTS):
                component = COMPONENTS[idx]
                if component == "其他（自行輸入）":
                    return input("  請輸入元件名稱：").strip()
                return component
        print(f"  請輸入 1 到 {len(COMPONENTS)} 的數字。")


def ask_description() -> str:
    print()
    desc = input("  變更說明（一句話，例：新增 mcnemar_test.py 統計顯著性驗證）：").strip()
    while not desc:
        desc = input("  說明不可為空，請重新輸入：").strip()
    return desc


def ask_modifier() -> str:
    default = git_user()
    hint = f"（Enter 直接使用 git 設定：{default}）" if default else ""
    print()
    name = input(f"  修改者姓名 {hint}：").strip()
    if not name and default:
        return default
    while not name:
        name = input("  修改者姓名不可為空：").strip()
    return name


def ask_detail_notes() -> str:
    print()
    print("  詳細說明（可留空，按 Enter 跳過；支援多行，輸入 END 結束）：")
    lines = []
    while True:
        line = input("  > ")
        if line.strip().upper() == "END":
            break
        if not line and not lines:
            break
        lines.append(line)
    return "\n".join(lines)


# ── 預覽 ──────────────────────────────────────────────────────────────────────

def preview(current: str, new_ver: str, change_type: str, component: str,
            description: str, modifier: str, now_str: str):
    separator()
    print("  預覽：以下變更將被執行")
    separator()
    print(f"  VERSION          {current} → {new_ver}")
    print(f"  CHANGELOG.md     新增 [{new_ver}] 區塊")
    print(f"  CONTRIBUTORS_LOG 新增一筆責任記錄")
    print(f"  SETUP.md         頁首版號更新為 {new_ver}")
    print()
    print(f"  變更類型：{change_type}")
    print(f"  異動元件：{component}")
    print(f"  說明    ：{description}")
    print(f"  修改者  ：{modifier}")
    print(f"  時間    ：{now_str}")
    print()
    print(f"  git commit：chore: 升版至 {new_ver} — {description}")
    print(f"  git tag   ：{new_ver}")
    separator()


def confirm() -> bool:
    while True:
        ans = input("  確認執行？輸入 yes 繼續，no 取消：").strip().lower()
        if ans == "yes": return True
        if ans == "no":  return False
        print("  請輸入 yes 或 no。")


# ── 執行變更 ──────────────────────────────────────────────────────────────────

def update_version_file(new_ver: str):
    VERSION_FILE.write_text(new_ver + "\n", encoding="utf-8")
    print(f"  ✅ VERSION → {new_ver}")


def update_setup_md(new_ver: str, today: str):
    text = SETUP_FILE.read_text(encoding="utf-8")
    updated = re.sub(
        r"\*\*版本：v[\d\.]+\*\* \| 發布日期：[\d\-]+",
        f"**版本：{new_ver}** | 發布日期：{today}",
        text
    )
    SETUP_FILE.write_text(updated, encoding="utf-8")
    print(f"  ✅ SETUP.md 版號 → {new_ver}")


def update_changelog(new_ver: str, change_type: str, component: str,
                     description: str, today: str, detail_notes: str):
    text = CHANGELOG_FILE.read_text(encoding="utf-8")

    detail_block = ""
    if detail_notes:
        detail_block = "\n" + "\n".join(f"> {line}" for line in detail_notes.split("\n")) + "\n"

    new_entry = (
        f"\n## [{new_ver}] — {today}\n\n"
        f"### {change_type}\n"
        f"- **{component}**：{description}\n"
        f"{detail_block}"
        f"\n---\n"
    )

    # 插入在第一個 ## [v 之前
    insert_pos = text.find("\n## [v")
    if insert_pos == -1:
        insert_pos = text.find("\n## 未來")
    if insert_pos == -1:
        text += new_entry
    else:
        text = text[:insert_pos] + new_entry + text[insert_pos:]

    CHANGELOG_FILE.write_text(text, encoding="utf-8")
    print(f"  ✅ CHANGELOG.md → 新增 [{new_ver}] 區塊")


def update_contributors_log(new_ver: str, modifier: str, now_str: str,
                            change_type: str, component: str, description: str):
    text = CONTRIB_FILE.read_text(encoding="utf-8")

    new_row = (
        f"| {new_ver} | {modifier} | {now_str} "
        f"| {change_type} | {component} | {description} |\n"
    )

    # 插入在表格最後一行之後（找最後一個以 | 開頭的行）
    lines = text.splitlines(keepends=True)
    last_table_line = -1
    for i, line in enumerate(lines):
        if line.startswith("|") and not line.startswith("| 版本"):
            last_table_line = i

    if last_table_line == -1:
        text += new_row
    else:
        lines.insert(last_table_line + 1, new_row)
        text = "".join(lines)

    CONTRIB_FILE.write_text(text, encoding="utf-8")
    print(f"  ✅ CONTRIBUTORS_LOG.md → {modifier} / {now_str}")


def git_commit_and_tag(new_ver: str, description: str):
    vault_root = STARTER_KIT.parent

    files_to_add = [
        str(STARTER_KIT / "VERSION"),
        str(STARTER_KIT / "CHANGELOG.md"),
        str(STARTER_KIT / "CONTRIBUTORS_LOG.md"),
        str(STARTER_KIT / "SETUP.md"),
    ]

    ok = run_git(["git", "add"] + files_to_add, cwd=vault_root)
    if not ok: return False

    commit_msg = f"chore: 升版至 {new_ver} — {description}\n\nCo-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
    ok = run_git(["git", "commit", "-m", commit_msg], cwd=vault_root)
    if not ok: return False

    ok = run_git(["git", "tag", "-a", new_ver, "-m", f"Perpetual RAG Starter Kit {new_ver}"], cwd=vault_root)
    if not ok: return False

    print(f"  ✅ git commit + tag {new_ver} 完成")
    return True


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    separator("═")
    print("  Perpetual RAG Starter Kit — 版本升級工具")
    separator("═")

    current = read_version()
    now = datetime.now(TZ_TAIPEI)
    now_str = now.strftime("%Y-%m-%dT%H:%M:%S+08:00")
    today = now.strftime("%Y-%m-%d")

    # 蒐集資訊
    level       = ask_bump_level(current)
    new_ver     = bump(current, level)
    change_type = ask_change_type()
    component   = ask_component()
    description = ask_description()
    modifier    = ask_modifier()
    detail      = ask_detail_notes()

    # 預覽 + 確認
    print()
    preview(current, new_ver, change_type, component, description, modifier, now_str)

    if not confirm():
        print("\n  ❌ 已取消，未做任何變更。")
        return

    # 執行
    separator()
    print("  執行中...")
    separator()
    update_version_file(new_ver)
    update_setup_md(new_ver, today)
    update_changelog(new_ver, change_type, component, description, today, detail)
    update_contributors_log(new_ver, modifier, now_str, change_type, component, description)
    success = git_commit_and_tag(new_ver, description)

    separator("═")
    if success:
        print(f"  🎉 升版完成：{current} → {new_ver}")
        print(f"  修改者：{modifier}  |  時間：{now_str}")
        print()
        print("  若要推送到遠端：")
        print(f"    git push origin master --tags")
    else:
        print("  ⚠️  檔案已更新，但 git 操作失敗，請手動執行：")
        print(f"    git add starter_kit/VERSION starter_kit/CHANGELOG.md starter_kit/CONTRIBUTORS_LOG.md starter_kit/SETUP.md")
        print(f"    git commit -m 'chore: 升版至 {new_ver}'")
        print(f"    git tag -a {new_ver} -m 'Perpetual RAG Starter Kit {new_ver}'")
    separator("═")


if __name__ == "__main__":
    main()
