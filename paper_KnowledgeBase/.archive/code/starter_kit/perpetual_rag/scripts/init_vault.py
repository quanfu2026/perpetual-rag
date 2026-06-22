#!/usr/bin/env python3
"""pip 套件版的知識庫初始化 — 從 package 內嵌模板建立知識庫"""

import shutil
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()

FOLDERS = [
    "第一章_緒論", "第二章_文獻回顧", "第三章_研究方法",
    "第四章_系統實作", "第五章_實驗結果", "第六章_結論",
    "參考文獻", "圖表", "scripts",
]

SCRIPTS_TO_COPY = [
    "bm25_search.py", "hallucination_guard.py", "consistency_check.py",
    "writeback.py", "daily_audit.py", "vector_search.py",
    "knowledge_graph.py", "bump_version.py",
]

PACKAGE_ROOT = Path(__file__).parent.parent
TEMPLATES_DIR = PACKAGE_ROOT / "templates"
SCRIPTS_SRC   = PACKAGE_ROOT.parent / "scripts"  # starter_kit/scripts/


def run(vault: str = "~/my_KnowledgeBase", project: str = "我的研究專案"):
    vault_path = Path(vault).expanduser().resolve()

    print(f"\n🏗️  初始化知識庫：{vault_path}")
    vault_path.mkdir(parents=True, exist_ok=True)

    # 資料夾
    for folder in FOLDERS:
        (vault_path / folder).mkdir(exist_ok=True)
        print(f"   ✅ {folder}/")

    # 模板文件
    print("\n📄 生成系統文件：")
    _write_claude_md(vault_path, project)
    _write_sessionhandoff(vault_path, project)
    _write_index(vault_path, project)
    _write_requirements(vault_path)

    # 複製腳本
    print("\n🔧 複製自動化腳本：")
    scripts_dst = vault_path / "scripts"
    for script_name in SCRIPTS_TO_COPY:
        src = SCRIPTS_SRC / script_name
        dst = scripts_dst / script_name
        if src.exists() and not dst.exists():
            shutil.copy2(src, dst)
            print(f"   ✅ scripts/{script_name}")
        elif dst.exists():
            print(f"   ⏭  scripts/{script_name}（已存在）")

    print(f"\n🎉 完成！知識庫位置：{vault_path}")
    print(f"\n接下來：")
    print(f"  1. 在 Obsidian 開啟 {vault_path}")
    print(f"  2. cd {vault_path} && claude")
    print(f"  3. 輸入：開工")


def _write_claude_md(vault: Path, project: str):
    dst = vault / "CLAUDE.md"
    if dst.exists():
        print("   ⏭  CLAUDE.md"); return
    dst.write_text(
        f"# CLAUDE.md — AI Agent 行為準則\n\n"
        f"工作目錄：{vault}\n專案：{project}\n初始化：{TODAY}\n\n"
        f"## 規則\n- 收工時更新 sessionhandoff.md\n"
        f"- 新建筆記加 YAML frontmatter\n"
        f"- 數據聲明附 [[REF_來源]] 雙向連結\n",
        encoding="utf-8"
    )
    print("   ✅ CLAUDE.md")


def _write_sessionhandoff(vault: Path, project: str):
    dst = vault / "sessionhandoff.md"
    if dst.exists():
        print("   ⏭  sessionhandoff.md"); return
    dst.write_text(
        f"---\ntitle: sessionhandoff.md\ntype: log\nstatus: active\n"
        f"created: {TODAY}\nlast_updated: {TODAY}\n---\n\n"
        f"# 記憶交接中樞\n\n## 專案\n- 名稱：{project}\n- 路徑：{vault}\n\n"
        f"## 第 1 次（{TODAY}）— 初始化\n- 完成：知識庫建立\n- 待辦：建立第一篇 REF_ 筆記\n",
        encoding="utf-8"
    )
    print("   ✅ sessionhandoff.md")


def _write_index(vault: Path, project: str):
    dst = vault / "index.md"
    if dst.exists():
        print("   ⏭  index.md"); return
    dst.write_text(
        f"---\ntitle: 決策日誌\ntype: index\nstatus: active\ncreated: {TODAY}\n---\n\n"
        f"# {project} — 決策日誌\n\n## 文件索引\n（新增文件時在此登記）\n\n"
        f"## ADR-001：採用三層知識解耦架構\n- Obsidian + NotebookLM + Claude Code\n- 日期：{TODAY}\n",
        encoding="utf-8"
    )
    print("   ✅ index.md")


def _write_requirements(vault: Path):
    dst = vault / "requirements.txt"
    if dst.exists():
        print("   ⏭  requirements.txt"); return
    dst.write_text("rank-bm25>=0.2.2\njieba>=0.42.1\nscikit-learn>=1.0.0\npyyaml>=6.0\n",
                   encoding="utf-8")
    print("   ✅ requirements.txt")
