# arXiv 投稿資訊表單

> 投稿前逐欄填入 arXiv 網站，複製貼上即可。

---

## 基本資訊

| 欄位 | 內容 |
|------|------|
| **Title** | Perpetual RAG: Hallucination Suppression via Knowledge Decoupling in Resource-Constrained Environments |
| **Authors** | Wenzhong Chen |
| **Affiliation** | Department of Intelligent Robotics Engineering, Kun Shan University |
| **Email** | b0963118770@gmail.com |

---

## 分類（Categories）

| 類型 | 代碼 | 說明 |
|------|------|------|
| **Primary** | `cs.IR` | Information Retrieval（主類別）|
| Secondary | `cs.AI` | Artificial Intelligence |
| Secondary | `cs.HC` | Human-Computer Interaction |

> arXiv 路徑：Computer Science → Information Retrieval (cs.IR)

---

## 摘要（直接複製貼上）

```
This study proposes a "Perpetual RAG" architecture employing a trinity
tool-chain of Obsidian, NotebookLM, and Claude Code to address two structural
challenges in the era of large language models: knowledge fragmentation and
hallucination generation. The core design principle is Knowledge Decoupling:
Obsidian serves as the local factual anchor for structured knowledge;
NotebookLM applies a Source-grounded mechanism to ensure every proposition
carries paragraph-level source citations; and Claude Code acts as an agentic
executor driving the entire knowledge feedback loop.

The architecture is fully deployed and validated in a resource-constrained
local environment (Mac Mini 2014, without GPU, vector database, or cloud
workflow). Experimental results demonstrate: hallucination rate dropped from
59% to 3% (−95%); citation completeness improved from 67% to 100%; six
cross-session recoveries completed without errors at an average of 6 seconds;
Token consumption reduced by 65–76%. These results support the central thesis:
the fundamental solution to hallucination lies not in model enhancement, but
in the structural upgrade of knowledge architecture.

Open-source implementation: https://quanfu2026.github.io/perpetual-rag/
```

---

## 關鍵詞（Comments 欄位填入）

```
6 pages, 5 tables. Submitted to ILT2026 (International Conference on Learning Technologies). Keywords: Perpetual RAG, Knowledge Decoupling, Hallucination Suppression, Agentic RAG, Knowledge Compound Interest. Open-source: https://github.com/quanfu2026/perpetual-rag
```

---

## 上傳檔案清單

| 檔案 | 說明 | 必要性 |
|------|------|--------|
| `ILT2026_arXiv.tex` | LaTeX 主檔 | ✅ 必要 |
| `references.bib` | BibTeX 參考文獻 | ✅ 必要 |
| `IEEEtran.cls` | IEEE 樣式檔（需另下載）| ✅ 必要 |

> **取得 IEEEtran.cls**：
> ```bash
> curl -O https://raw.githubusercontent.com/XiangyunHuang/ElegantLaTeX/master/elegantpaper/elegantpaper.cls
> ```
> 或直接至 https://ctan.org/pkg/ieeetran 下載後放入同資料夾。

---

## 投稿步驟（逐步操作）

1. **登入** https://arxiv.org → 右上角 **Login**（沒帳號請先註冊）
2. **新投稿** → 點擊 **Submit** → **New Submission**
3. **Agreement** → 勾選授權聲明 → **Next**
4. **Classification**：
   - Primary: `cs.IR`
   - Cross-list: `cs.AI`, `cs.HC`
5. **Upload Files**：
   - 選擇 **TeX/LaTeX**
   - 上傳 `ILT2026_arXiv.tex` + `references.bib` + `IEEEtran.cls`
   - 等待系統編譯，確認 PDF 預覽正確
6. **Metadata**：
   - Title：貼上上方 Title
   - Authors：`Wenzhong Chen`
   - Abstract：貼上上方摘要
   - Comments：貼上上方 Comments
7. **Preview** → 確認 PDF 排版正確
8. **Submit** → 系統分配 arXiv ID（格式如 arXiv:2504.XXXXX）
9. **等待審核**：通常 1–2 個工作天後上線

---

## 注意事項

- ⚠️ **[1] [2] 兩篇引用** arXiv ID 為佔位符，投稿前需確認實際論文資訊
- ⚠️ ILT2026 會議若有**版權限制**，預印本發布前請先確認投稿規定
- arXiv 上線後會取得永久 DOI：`10.48550/arXiv.XXXX.XXXXX`
- 可在 GitHub README 加入 arXiv badge：
  ```markdown
  [![arXiv](https://img.shields.io/badge/arXiv-XXXX.XXXXX-b31b1b.svg)](https://arxiv.org/abs/XXXX.XXXXX)
  ```

---

---

## 已發布資訊

| 平台 | DOI | 狀態 |
|------|-----|------|
| Zenodo | [10.5281/zenodo.19676404](https://doi.org/10.5281/zenodo.19676404) | ✅ 已發布 2026-04-21 |

*產生時間：2026-04-21*
