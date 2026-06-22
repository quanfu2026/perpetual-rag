#!/usr/bin/env python3
"""
GitHub Release zip 打包腳本

執行方式：
  cd ~/paper_KnowledgeBase
  python3 starter_kit/scripts/build_release.py

輸出：
  starter_kit/dist/perpetual-rag-v1.0.0.zip
  starter_kit/dist/perpetual-rag-v1.0.0-scripts-only.zip
"""

import os
import zipfile
import shutil
from pathlib import Path
from datetime import date

STARTER_KIT = Path(__file__).parent.parent
DIST_DIR = STARTER_KIT / "dist"
VERSION_FILE = STARTER_KIT / "VERSION"

# 完整包：包含所有檔案
FULL_INCLUDE = [
    "VERSION",
    "CHANGELOG.md",
    "CONTRIBUTORS_LOG.md",
    "SETUP.md",
    "pyproject.toml",
    "README_pip.md",
    "install.sh",
    "scripts/setup.py",
    "scripts/bump_version.py",
    "scripts/bm25_search.py",
    "scripts/hallucination_guard.py",
    "scripts/consistency_check.py",
    "scripts/writeback.py",
    "scripts/daily_audit.py",
    "scripts/vector_search.py",
    "scripts/knowledge_graph.py",
    "知識庫範本/CLAUDE.md",
    "知識庫範本/sessionhandoff.md",
    "知識庫範本/index.md",
    "知識庫範本/參考文獻/REF_範本.md",
]

# 腳本精簡包：只含核心腳本
SCRIPTS_ONLY_INCLUDE = [
    "VERSION",
    "SETUP.md",
    "install.sh",
    "scripts/setup.py",
    "scripts/bm25_search.py",
    "scripts/hallucination_guard.py",
    "scripts/consistency_check.py",
    "scripts/writeback.py",
    "scripts/daily_audit.py",
    "scripts/vector_search.py",
    "scripts/knowledge_graph.py",
]


def read_version() -> str:
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def build_zip(version: str, name_suffix: str, include_list: list) -> Path:
    zip_name = f"perpetual-rag-{version}{name_suffix}.zip"
    zip_path = DIST_DIR / zip_name

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path in include_list:
            src = STARTER_KIT / rel_path
            if src.exists():
                # zip 內部路徑：perpetual-rag-v1.0.0/檔名
                arc_name = f"perpetual-rag-{version}/{rel_path}"
                zf.write(src, arc_name)
                print(f"   + {rel_path}")
            else:
                print(f"   ⚠️  找不到：{rel_path}（跳過）")

    size_kb = zip_path.stat().st_size // 1024
    return zip_path, size_kb


def write_release_notes(version: str, dist_dir: Path):
    """生成 GitHub Release 說明文字"""
    notes_path = dist_dir / f"RELEASE_NOTES_{version}.md"
    today = date.today().isoformat()
    notes_path.write_text(
        f"## Perpetual RAG Starter Kit {version}\n\n"
        f"發布日期：{today}\n\n"
        f"### 安裝方式\n\n"
        f"**方式一：Shell 腳本（Mac/Linux）**\n"
        f"```bash\nbash install.sh --vault ~/my_KnowledgeBase --project \"我的研究\"\n```\n\n"
        f"**方式二：pip 套件**\n"
        f"```bash\npip install perpetual-rag\nperpetual-rag init --vault ~/my_KnowledgeBase\n```\n\n"
        f"**方式三：下載 zip 解壓**\n"
        f"1. 下載 `perpetual-rag-{version}.zip`\n"
        f"2. 解壓後執行：`python3 scripts/setup.py --vault ~/my_KnowledgeBase`\n\n"
        f"### 系統需求\n"
        f"- Python 3.8+\n- Node.js 18+（Claude Code CLI 需要）\n"
        f"- Obsidian（免費）\n- NotebookLM（免費，Google 帳號）\n\n"
        f"### 驗證指標（實驗結果）\n"
        f"| 指標 | 數值 |\n|------|------|\n"
        f"| 幻覺率 | 3%（基準 59%，-95%）|\n"
        f"| Token 消耗 | ↓65–76% |\n"
        f"| RAM 峰值 | 120MB（Mac Mini 2014）|\n"
        f"| 跨 Session 恢復 | 6 秒，零錯誤 |\n\n"
        f"**論文**：「永續性知識管理：基於 Obsidian-NotebookLM-Claude Code 三層架構的防幻覺 RAG 框架」\n"
        f"**投稿**：ILT2026 國際學習科技研討會\n",
        encoding="utf-8"
    )
    print(f"   ✅ RELEASE_NOTES_{version}.md")
    return notes_path


def main():
    version = read_version()
    print(f"\n📦 打包 Perpetual RAG Starter Kit {version}")
    print("=" * 60)

    DIST_DIR.mkdir(exist_ok=True)

    # 完整包
    print(f"\n🗜️  完整包：perpetual-rag-{version}.zip")
    zip_full, size_full = build_zip(version, "", FULL_INCLUDE)
    print(f"   ✅ {zip_full.name}（{size_full} KB）")

    # 精簡包
    print(f"\n🗜️  腳本精簡包：perpetual-rag-{version}-scripts-only.zip")
    zip_slim, size_slim = build_zip(version, "-scripts-only", SCRIPTS_ONLY_INCLUDE)
    print(f"   ✅ {zip_slim.name}（{size_slim} KB）")

    # Release Notes
    print(f"\n📝 生成 Release Notes：")
    write_release_notes(version, DIST_DIR)

    print(f"\n{'=' * 60}")
    print(f"✅ 打包完成！輸出位置：{DIST_DIR}")
    print(f"\n   完整包    {zip_full.name}  ({size_full} KB)")
    print(f"   精簡包    {zip_slim.name}  ({size_slim} KB)")
    print(f"\n上傳到 GitHub Release：")
    print(f"   gh release create {version} \\")
    print(f"     {zip_full} \\")
    print(f"     {zip_slim} \\")
    print(f"     --title 'Perpetual RAG Starter Kit {version}' \\")
    print(f"     --notes-file {DIST_DIR}/RELEASE_NOTES_{version}.md")


if __name__ == "__main__":
    main()
