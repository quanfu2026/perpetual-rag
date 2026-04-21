# Perpetual RAG 永續性知識管理系統 — 完整安裝指南

**版本：v1.0.0** | 發布日期：2026-04-21 | [查看更新記錄](CHANGELOG.md)

> **目標**：從零到完整可用，預計 30–45 分鐘。
> **環境需求**：任何 Mac / Windows / Linux，不需 GPU，不需雲端伺服器。
> **已在 Mac Mini 2014（4GB RAM）上完整驗證。**

---

## 安裝概覽

```
第一步  安裝 Obsidian          （5 分鐘）  儲存層
第二步  開通 NotebookLM        （5 分鐘）  理解層
第三步  安裝 Claude Code CLI   （10 分鐘） 執行層
第四步  安裝 Python 套件       （5 分鐘）  腳本環境
第五步  一鍵初始化知識庫       （2 分鐘）  建立知識庫
第六步  第一次啟動             （3 分鐘）  開始工作
```

---

## 一鍵安裝（快速通道）

> 熟悉命令列的用戶可跳過後面的逐步說明，直接使用以下指令。

### Mac / Linux

```bash
curl -fsSL https://raw.githubusercontent.com/quanfu2026/perpetual-rag/master/starter_kit/install.sh | bash
```

腳本會自動完成：偵測 OS → 安裝 Python 套件 → 安裝 Claude Code CLI → 建立知識庫 → 驗證安裝。

### Windows

```powershell
pip install perpetual-rag
perpetual-rag init --vault C:\my_KnowledgeBase --project "我的研究"
```

### 所有平台（通用）

```bash
# 方式一：pip 套件（Mac / Linux / Windows 均適用）
pip install perpetual-rag
perpetual-rag init --vault ~/my_KnowledgeBase --project "我的研究"

# 方式二：下載 zip 解壓後執行
# https://github.com/quanfu2026/perpetual-rag/releases/latest
python3 scripts/setup.py --vault ~/my_KnowledgeBase --project "我的研究"
```

| 方式 | Mac | Linux | Windows | 需要 Python |
|------|:---:|:-----:|:-------:|:-----------:|
| `curl \| bash`（Shell 腳本）| ✅ | ✅ | ❌（需 WSL）| 自動安裝 |
| `pip install perpetual-rag` | ✅ | ✅ | ✅ | 需先安裝 |
| zip 下載解壓 | ✅ | ✅ | ✅ | 需先安裝 |

> **不熟悉命令列？** 請繼續閱讀下方逐步說明。

---

## 第一步：安裝 Obsidian（儲存層）

**Obsidian 是本系統的知識儲存核心。** 所有筆記、參考文獻、章節都存放在這裡。

### 1-1 下載並安裝

1. 前往 [https://obsidian.md](https://obsidian.md) → 點擊 **Download**
2. 選擇你的作業系統版本：
   - **Mac**：下載 `.dmg`，拖曳到 Applications
   - **Windows**：下載 `.exe`，直接安裝
   - **Linux**：下載 `.AppImage` 或使用 `.deb`
3. 開啟 Obsidian，選擇 **Create new vault**（先建一個測試用的，之後會換）

### 1-2 安裝必要外掛

開啟 Obsidian 後：

1. 點擊左下角齒輪圖示 → **Settings**
2. 左側選單 → **Community plugins**
3. 關閉 **Restricted mode**（允許社群外掛）
4. 點擊 **Browse** → 搜尋並安裝以下兩個外掛：

| 外掛名稱 | 用途 |
|---------|------|
| **Templater** | 快速建立筆記模板 |
| **Dataview** | 用查詢語法統計筆記狀態 |

5. 安裝後分別點擊 **Enable** 啟用

---

## 第二步：開通 NotebookLM（理解層）

**NotebookLM 是本系統的語意問答層。** 上傳 PDF 論文後，它會綁定來源進行問答，大幅降低幻覺。

### 2-1 開通帳號

1. 前往 [https://notebooklm.google.com](https://notebooklm.google.com)
2. 使用 **Google 帳號** 登入（免費，無需付費）
3. 點擊 **New notebook** 建立第一個筆記本

### 2-2 上傳第一份來源

1. 在 Notebook 頁面點擊 **+ Add sources**
2. 選擇 **Upload**，上傳你的 PDF 論文或參考文獻
3. 上傳完成後即可在右側對話框提問

> **重要**：每次提問請選擇「引用來源」模式，確保每個答案都附有段落級來源標注。這是本系統第一層防幻覺機制。

---

## 第三步：安裝 Claude Code CLI（執行層）

**Claude Code 是本系統的 AI 代理核心。** 它會讀取你的知識庫、執行腳本、更新記憶交接檔。

### 3-1 確認前置需求：Node.js

Claude Code CLI 需要 Node.js 18 以上版本。

**檢查是否已安裝：**
```bash
node --version
```

如果顯示 `v18.x.x` 或更高，跳到 3-2。

**如果未安裝，請先安裝 Node.js：**

- **Mac（推薦用 Homebrew）**：
  ```bash
  # 先安裝 Homebrew（如果沒有）
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

  # 再安裝 Node.js
  brew install node
  ```

- **Windows**：
  前往 [https://nodejs.org](https://nodejs.org) → 下載 **LTS 版本** → 執行安裝程式

- **Linux（Ubuntu/Debian）**：
  ```bash
  curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
  sudo apt-get install -y nodejs
  ```

安裝完成後確認：
```bash
node --version   # 應顯示 v18.x.x 或更高
npm --version    # 應顯示版本號
```

### 3-2 安裝 Claude Code CLI

```bash
npm install -g @anthropic-ai/claude-code
```

安裝完成後確認：
```bash
claude --version
```

### 3-3 取得 Anthropic API Key

1. 前往 [https://console.anthropic.com](https://console.anthropic.com)
2. 註冊或登入帳號
3. 點擊左側 **API Keys** → **Create Key**
4. 複製金鑰（格式為 `sk-ant-...`）

### 3-4 設定 API Key

**方法 A：環境變數（推薦）**

- **Mac / Linux**，在終端機執行：
  ```bash
  # 加入 ~/.zshrc 或 ~/.bashrc，讓每次開啟終端機都自動載入
  echo 'export ANTHROPIC_API_KEY="sk-ant-你的金鑰"' >> ~/.zshrc
  source ~/.zshrc
  ```

- **Windows（PowerShell）**：
  ```powershell
  [System.Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-你的金鑰", "User")
  ```

**方法 B：首次執行時輸入**

直接執行 `claude`，程式會提示你輸入 API Key 並儲存到本機設定檔。

### 3-5 驗證 Claude Code 可以正常使用

```bash
claude
```

如果看到互動式提示符（`>`），表示安裝成功。輸入 `/exit` 離開。

---

## 第四步：安裝 Python 套件（腳本環境）

本系統的七支自動化腳本需要 Python 3.8 以上。

### 4-1 確認 Python 版本

```bash
python3 --version
```

應顯示 `Python 3.8.x` 或更高。

**如果版本過低或未安裝：**
- **Mac**：`brew install python3`
- **Windows**：前往 [https://python.org](https://python.org) 下載安裝
- **Linux**：`sudo apt-get install python3 python3-pip`

### 4-2 安裝必要套件

```bash
# 進入你的知識庫目錄（初始化後執行）
cd ~/my_KnowledgeBase

# 安裝所有依賴
pip3 install -r requirements.txt
```

`requirements.txt` 內容：
```
rank-bm25>=0.2.2    # BM25 搜尋引擎
jieba>=0.42.1       # 中文分詞
scikit-learn>=1.0.0 # TF-IDF 混合搜尋
pyyaml>=6.0         # YAML 解析
```

### 4-3 驗證安裝

```bash
python3 -c "import rank_bm25, jieba, sklearn, yaml; print('✅ 所有套件就緒')"
```

---

## 第五步：一鍵初始化知識庫

### 5-1 下載 starter_kit

**方法 A：從 GitHub 下載（推薦）**
```bash
git clone https://github.com/（待補充）/perpetual-rag-starter.git
cd perpetual-rag-starter
```

**方法 B：直接複製現有 starter_kit 資料夾**
```bash
cp -r starter_kit/ ~/my_KnowledgeBase/
```

### 5-2 執行初始化腳本

```bash
python3 starter_kit/scripts/setup.py \
  --vault ~/my_KnowledgeBase \
  --project "你的研究專案名稱"
```

**參數說明：**
- `--vault`：知識庫要建立在哪個路徑（預設：`~/my_KnowledgeBase`）
- `--project`：你的研究專案名稱（會寫入 `CLAUDE.md` 和 `sessionhandoff.md`）

**執行後自動完成：**
```
✅ 建立標準資料夾結構（第一章 ～ 第六章 / 參考文獻 / 圖表 / scripts）
✅ 生成 CLAUDE.md（含你的專案名稱和知識庫路徑）
✅ 生成 sessionhandoff.md（記憶交接初始狀態）
✅ 生成 index.md（決策日誌）
✅ 複製七支自動化腳本到 scripts/
✅ 生成 requirements.txt
```

### 5-3 在 Obsidian 開啟知識庫

1. 開啟 Obsidian
2. 點擊 **Open folder as vault**
3. 選擇剛才建立的 `~/my_KnowledgeBase/` 資料夾
4. 點擊 **Trust and open**

左側面板應出現：第一章\_緒論、第二章\_文獻回顧 等資料夾，以及 `CLAUDE.md`、`sessionhandoff.md`。

---

## 第六步：第一次啟動

### 6-1 在終端機進入知識庫目錄

```bash
cd ~/my_KnowledgeBase
```

### 6-2 啟動 Claude Code

```bash
claude
```

### 6-3 輸入開工指令

```
開工。我的知識庫在 ~/my_KnowledgeBase/，請讀取 sessionhandoff.md 了解當前進度。
```

Claude Code 會自動：
1. 讀取 `sessionhandoff.md` 了解你的研究現況
2. 讀取 `CLAUDE.md` 了解行為規範
3. 回報當前待辦事項，準備開始工作

### 6-4 建立第一篇參考文獻（測試系統）

對 Claude Code 說：
```
請在參考文獻資料夾建立一篇新的參考文獻筆記，作者是 Gao，年份 2024，主題是 RAG Survey。
```

Claude Code 會依照 `REF_範本.md` 的格式，在 `參考文獻/` 資料夾建立 `REF_Gao2024_RAG_Survey.md`。

在 Obsidian 中應該立即看到這個新文件出現在左側面板。

---

## 日常操作速查

### 每天開工
```
開工
```

### 每天收工
```
收工
```

### 七支腳本指令

```bash
# 搜尋知識庫（最常用）
python3 scripts/bm25_search.py "關鍵字" --top 5

# 寫完章節後：掃描幻覺
python3 scripts/hallucination_guard.py

# 跨章節術語一致性檢查
python3 scripts/consistency_check.py

# 每日進度快照
python3 scripts/daily_audit.py

# 生成知識圖譜（Obsidian Canvas 可視化）
python3 scripts/knowledge_graph.py

# 混合搜尋（語意 + 關鍵字）
python3 scripts/vector_search.py "問題描述"
```

---

## 資料夾結構說明

```
my_KnowledgeBase/
│
├── CLAUDE.md              ← AI 行為規範（不可刪除）
├── sessionhandoff.md      ← 跨 Session 記憶交接中樞
├── index.md               ← 決策日誌（不可刪除歷史記錄）
├── requirements.txt       ← Python 套件清單
│
├── 第一章_緒論/           ← 每章一個資料夾
│   └── 1.1_研究背景.md
├── 第二章_文獻回顧/
├── 參考文獻/              ← 格式：REF_作者年份_關鍵詞.md
│   └── REF_Gao2024_RAG_Survey.md
│
├── 圖表/                  ← 系統自動生成的視覺化文件
│   ├── 知識圖譜.canvas    ← Obsidian 互動圖
│   └── 知識圖譜.json      ← D3.js 網頁圖
│
└── scripts/               ← 七支自動化腳本
    ├── setup.py
    ├── bm25_search.py
    ├── hallucination_guard.py
    ├── consistency_check.py
    ├── writeback.py
    ├── daily_audit.py
    ├── vector_search.py
    └── knowledge_graph.py
```

---

## 命名規範（系統自動辨識的關鍵）

| 類型 | 格式 | 範例 |
|------|------|------|
| 參考文獻 | `REF_作者年份_關鍵詞.md` | `REF_Gao2024_RAG_Survey.md` |
| 章節筆記 | `第X章_主題/節號_標題.md` | `第一章_緒論/1.1_研究背景.md` |
| 系統報告（自動生成）| `00_報告名稱.md` | `00_防幻覺檢查報告.md` |
| 圖表 | 放在 `圖表/` 資料夾 | `圖表/三大流程圖.md` |

---

## 五層防幻覺框架（核心創新）

| 層次 | 時機 | 機制 | 執行方式 |
|------|------|------|---------|
| 第一層 | 攝取時 | Source-grounded 來源綁定 | 用 NotebookLM 問答，不直接問 ChatGPT |
| 第二層 | 檢索時 | BM25 詞彙精確召回 | `python3 scripts/bm25_search.py "關鍵字"` |
| 第三層 | 寫入時 | CLAUDE.md 行為約束 | 每次開工自動載入規範 |
| 第四層 | 審計時 | 全文幻覺掃描 | `python3 scripts/hallucination_guard.py` |
| 第五層 | 一致性 | 跨節點術語稽核 | `python3 scripts/consistency_check.py` |

**實驗驗證結果：幻覺率 59% → 3%（降幅 -95%）**

---

## 常見問題排解

**Q：`claude` 指令找不到**
```bash
# 確認 npm 全域安裝路徑是否在 PATH 中
npm config get prefix
# 將上面路徑的 /bin 加入 PATH，例如：
export PATH="$PATH:$(npm config get prefix)/bin"
```

**Q：`python3` 指令找不到（Windows）**
Windows 安裝 Python 時勾選 **Add Python to PATH**，或使用 `python` 而非 `python3`。

**Q：套件安裝失敗（權限問題）**
```bash
pip3 install --user -r requirements.txt
```

**Q：`ModuleNotFoundError: No module named 'rank_bm25'`**
```bash
# 確認你在正確的 Python 環境
which python3
python3 -m pip install rank-bm25 jieba scikit-learn pyyaml
```

**Q：Obsidian 打開後看不到 Canvas 圖形**
Canvas 需要 Obsidian 1.1 以上版本（內建，無需安裝外掛）。確認 Obsidian 已更新到最新版。

**Q：沒有 GPU，跑得動嗎？**
完全可以。本系統不使用任何神經網路推理，所有腳本均為純 CPU 計算。RAM 峰值僅 120MB。

---

## 系統需求摘要

| 項目 | 最低需求 | 建議 |
|------|---------|------|
| 作業系統 | Mac 10.15 / Win 10 / Ubuntu 20.04 | 最新版本 |
| RAM | 2GB | 4GB 以上 |
| 硬碟空間 | 500MB | 2GB（含 PDF 文獻）|
| Python | 3.8 | 3.10 以上 |
| Node.js | 18.x | 20.x（LTS）|
| GPU | 不需要 | — |

---

*論文來源：「永續性知識管理：基於 Obsidian-NotebookLM-Claude Code 三層架構的防幻覺 RAG 框架」*
*ILT2026 國際學習科技研討會 投稿版*
