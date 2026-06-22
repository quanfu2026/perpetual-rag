## Perpetual RAG Starter Kit v1.0.0

發布日期：2026-04-21

### 安裝方式

**方式一：Shell 腳本（Mac/Linux）**
```bash
bash install.sh --vault ~/my_KnowledgeBase --project "我的研究"
```

**方式二：pip 套件**
```bash
pip install perpetual-rag
perpetual-rag init --vault ~/my_KnowledgeBase
```

**方式三：下載 zip 解壓**
1. 下載 `perpetual-rag-v1.0.0.zip`
2. 解壓後執行：`python3 scripts/setup.py --vault ~/my_KnowledgeBase`

### 系統需求
- Python 3.8+
- Node.js 18+（Claude Code CLI 需要）
- Obsidian（免費）
- NotebookLM（免費，Google 帳號）

### 驗證指標（實驗結果）
| 指標 | 數值 |
|------|------|
| 幻覺率 | 3%（基準 59%，-95%）|
| Token 消耗 | ↓65–76% |
| RAM 峰值 | 120MB（Mac Mini 2014）|
| 跨 Session 恢復 | 6 秒，零錯誤 |

**論文**：「永續性知識管理：基於 Obsidian-NotebookLM-Claude Code 三層架構的防幻覺 RAG 框架」
**投稿**：ILT2026 國際學習科技研討會
