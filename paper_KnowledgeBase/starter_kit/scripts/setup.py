#!/usr/bin/env python3
"""
Perpetual RAG 永續性知識管理系統 — 一鍵初始化腳本

執行方式：
  python3 setup.py --vault ~/my_KnowledgeBase --project "我的研究專案"

選項：
  --vault       知識庫路徑（預設：~/my_KnowledgeBase）
  --project     專案名稱（用於 sessionhandoff.md 初始化）
  --check-only  僅檢查環境，不建立任何檔案
  --lang        介面語言：zh（預設）/ en
"""

import os
import sys
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import date

TODAY = date.today().isoformat()

# ── 必要套件清單 ──────────────────────────────────────────────────────────────
REQUIRED_PACKAGES = {
    "rank_bm25":  "rank-bm25",
    "jieba":      "jieba",
    "sklearn":    "scikit-learn",
    "yaml":       "pyyaml",
}

# ── 資料夾結構 ────────────────────────────────────────────────────────────────
FOLDER_STRUCTURE = [
    "第一章_緒論",
    "第二章_文獻回顧",
    "第三章_研究方法",
    "第四章_系統實作",
    "第五章_實驗結果",
    "第六章_結論",
    "參考文獻",
    "圖表",
    "scripts",
    ".obsidian",
]


def check_python_version():
    if sys.version_info < (3, 8):
        print("❌ 需要 Python 3.8 以上，目前版本：", sys.version)
        sys.exit(1)
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")


def check_packages():
    missing = []
    for module, package in REQUIRED_PACKAGES.items():
        try:
            __import__(module)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package}（未安裝）")
            missing.append(package)
    return missing


def install_packages(missing):
    if not missing:
        return True
    print(f"\n📦 安裝缺少的套件：{', '.join(missing)}")
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install"] + missing,
        capture_output=True, text=True
    )
    if result.returncode == 0:
        print("✅ 套件安裝完成")
        return True
    else:
        print("❌ 安裝失敗，請手動執行：")
        print(f"   pip install {' '.join(missing)}")
        return False


def create_folder_structure(vault: Path):
    print(f"\n📁 建立資料夾結構於：{vault}")
    vault.mkdir(parents=True, exist_ok=True)
    for folder in FOLDER_STRUCTURE:
        (vault / folder).mkdir(exist_ok=True)
        print(f"   ✅ {folder}/")


def copy_scripts(vault: Path, starter_kit_root: Path):
    scripts_src = starter_kit_root / "scripts"
    scripts_dst = vault / "scripts"

    # 複製 starter_kit/scripts 中的所有腳本（排除 setup.py 本身）
    copied = 0
    if scripts_src.exists():
        for script in scripts_src.glob("*.py"):
            if script.name == "setup.py":
                continue
            dst = scripts_dst / script.name
            if not dst.exists():
                shutil.copy2(script, dst)
                print(f"   ✅ scripts/{script.name}")
                copied += 1
            else:
                print(f"   ⏭  scripts/{script.name}（已存在，跳過）")

    if copied == 0 and not any(scripts_dst.glob("*.py")):
        print("   ⚠️  腳本未找到，請手動複製 scripts/*.py 到知識庫的 scripts/ 資料夾")


def generate_claude_md(vault: Path, project: str):
    dst = vault / "CLAUDE.md"
    if dst.exists():
        print("   ⏭  CLAUDE.md（已存在，跳過）")
        return

    content = f"""# CLAUDE.md — AI Agent 行為準則

---

## 一、授權目錄

工作目錄：{vault}

所有讀取、分析與編寫操作，嚴格限制在此目錄之內。

---

## 二、專案資訊

- 專案名稱：{project}
- 知識庫路徑：{vault}
- 初始化日期：{TODAY}

---

## 三、回寫與同步規則

- 完成任務後：同步更新 sessionhandoff.md 和 index.md
- 新建筆記時：加入 YAML frontmatter（title / type / status / tags）
- 收工時：將進度完整寫入 sessionhandoff.md

---

## 四、命名規範

| 類型 | 格式 |
|------|------|
| 參考文獻 | REF_作者年份_關鍵詞.md |
| 章節筆記 | 第X章_主題/節號_標題.md |
| 系統報告 | 00_報告名稱.md（排除於知識圖譜之外）|

---

## 五、禁止行為

- 禁止產生孤立文件（新文件必須在 index.md 登記）
- 禁止刪除 index.md 歷史記錄
- 禁止在未讀取 sessionhandoff.md 前開始工作

---

## 六、任務分派等級（L1–L4）

| 等級 | Token 預算 | 適用任務 |
|------|-----------|---------|
| L1 | 1–3K | 快速查詢、單檔修改 |
| L2 | 3–10K | 章節撰寫、腳本執行 |
| L3 | 5–15K | 跨章節整合、多檔操作 |
| L4 | 10–30K | 全稿稽核、系統重構 |

---

## 七、五層防幻覺規範

1. 攝取時：NotebookLM 來源必須是原始文件
2. 撰寫時：數據聲明必須附 [[REF_來源]] 雙向連結
3. 完成後：執行 python3 scripts/hallucination_guard.py
4. 跨章節：執行 python3 scripts/consistency_check.py
5. 收工前：零警告才可標記 status: final
"""
    dst.write_text(content, encoding="utf-8")
    print(f"   ✅ CLAUDE.md（專案：{project}）")


def generate_sessionhandoff(vault: Path, project: str):
    dst = vault / "sessionhandoff.md"
    if dst.exists():
        print("   ⏭  sessionhandoff.md（已存在，跳過）")
        return

    content = f"""---
title: sessionhandoff.md — 記憶交接中樞
type: log
status: active
tags: [記憶交接, 系統]
version: 1.0.0
created: {TODAY}
last_updated: {TODAY}
---

# sessionhandoff.md — 記憶交接中樞

> 每次「收工」時由 Claude Code 自動更新此檔案。
> 每次「開工」時必須先讀取此檔案再開始工作。

---

## 最後更新
- 日期：{TODAY}（第 1 次，系統初始化）
- 狀態：初始化完成 ✅

---

## 專案資訊

| 項目 | 內容 |
|------|------|
| 專案名稱 | {project} |
| 知識庫路徑 | {vault} |
| 初始化日期 | {TODAY} |

---

## 當前章節狀態

| 章節 | 狀態 | 備注 |
|------|------|------|
| 第一章 | draft | 待撰寫 |
| 第二章 | draft | 待撰寫 |
| 參考文獻 | draft | 持續累積 |

---

## 待辦清單

### 下次開工從這裡繼續
- [ ] 建立第一篇 REF_ 參考文獻筆記
- [ ] 將文獻 PDF 上傳到 NotebookLM
- [ ] 開始撰寫第一章草稿
- [ ] 執行 python3 scripts/daily_audit.py 確認系統正常

---

## 工作日誌

### 第 1 次（{TODAY}）— 系統初始化
- 完成：starter_kit 部署、資料夾結構建立、系統文件生成
- 待辦：開始建立知識庫內容

---
"""
    dst.write_text(content, encoding="utf-8")
    print(f"   ✅ sessionhandoff.md")


def generate_index(vault: Path, project: str):
    dst = vault / "index.md"
    if dst.exists():
        print("   ⏭  index.md（已存在，跳過）")
        return

    content = f"""---
title: index.md — 決策日誌
type: index
status: active
tags: [決策, 索引]
created: {TODAY}
---

# {project} — 決策日誌 & 知識庫索引

---

## 知識庫文件索引

### 章節筆記
| 文件 | 狀態 | 最後更新 |
|------|------|---------|
| （新增文件時在此登記） | — | — |

### 參考文獻
| 文件 | 作者年份 | 核心主張 |
|------|---------|---------|
| （每篇 REF_ 文件在此摘要） | — | — |

---

## 架構決策記錄（ADR）

### ADR-001：採用三層知識解耦架構
- **決策**：Obsidian（儲存）+ NotebookLM（理解）+ Claude Code（執行）
- **原因**：SoC 原則，降低幻覺率，無需 GPU
- **日期**：{TODAY}

---

## 系統狀態
```
初始化日期：{TODAY}
防幻覺警告：0
術語不一致：0
孤兒節點：0
```
"""
    dst.write_text(content, encoding="utf-8")
    print("   ✅ index.md")


def generate_requirements(vault: Path):
    dst = vault / "requirements.txt"
    if dst.exists():
        print("   ⏭  requirements.txt（已存在，跳過）")
        return
    content = "rank-bm25>=0.2.2\njieba>=0.42.1\nscikit-learn>=1.0.0\npyyaml>=6.0\n"
    dst.write_text(content, encoding="utf-8")
    print("   ✅ requirements.txt")


def print_next_steps(vault: Path, project: str):
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║       🎉  Perpetual RAG 知識庫初始化完成！                    ║
╚══════════════════════════════════════════════════════════════╝

📂 知識庫位置：{vault}
📋 專案名稱：{project}

━━━━ 接下來三步 ━━━━

1. 在 Obsidian 開啟此資料夾作為 Vault：
   File → Open folder as vault → 選擇 {vault}

2. 對 Claude Code 說：
   開工。我的知識庫在 {vault}，請讀取 sessionhandoff.md 了解當前進度。

3. 建立第一篇參考文獻：
   在 參考文獻/ 資料夾建立 REF_作者年份_關鍵詞.md（使用範本）

━━━━ 常用指令 ━━━━

搜尋知識庫：  python3 scripts/bm25_search.py "關鍵字"
防幻覺掃描：  python3 scripts/hallucination_guard.py
每日快照：    python3 scripts/daily_audit.py
知識圖譜：    python3 scripts/knowledge_graph.py

━━━━ 更多說明 ━━━━

完整啟動指南：starter_kit/SETUP.md
論文（原始研究）：https://github.com/（待補充）
""")


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Perpetual RAG 永續性知識管理系統 — 一鍵初始化"
    )
    parser.add_argument("--vault", default="~/my_KnowledgeBase",
                        help="知識庫路徑（預設：~/my_KnowledgeBase）")
    parser.add_argument("--project", default="我的研究專案",
                        help="專案名稱")
    parser.add_argument("--check-only", action="store_true",
                        help="僅檢查環境，不建立任何檔案")
    args = parser.parse_args()

    vault = Path(args.vault).expanduser().resolve()
    starter_kit_root = Path(__file__).parent.parent  # starter_kit/

    print("=" * 60)
    print("  Perpetual RAG 永續性知識管理系統 — 環境檢查")
    print("=" * 60)

    # 1. 環境檢查
    print("\n🔍 Python 版本：")
    check_python_version()

    print("\n📦 套件檢查：")
    missing = check_packages()

    if args.check_only:
        if missing:
            print(f"\n⚠️  待安裝套件：pip install {' '.join(missing)}")
        else:
            print("\n✅ 環境檢查通過，可以開始初始化！")
        return

    # 2. 安裝缺少套件
    if missing:
        install_packages(missing)

    # 3. 建立知識庫
    print(f"\n🏗️  初始化知識庫：{vault}")
    create_folder_structure(vault)

    print("\n📄 生成系統文件：")
    generate_claude_md(vault, args.project)
    generate_sessionhandoff(vault, args.project)
    generate_index(vault, args.project)
    generate_requirements(vault)

    # 4. 複製腳本
    print("\n🔧 複製自動化腳本：")
    copy_scripts(vault, starter_kit_root)

    # 5. 完成提示
    print_next_steps(vault, args.project)


if __name__ == "__main__":
    main()
