---
title: 實驗 Protocol（論文 §IV 草稿）
type: research
status: draft
tags: [protocol, methodology]
source: Claude-Code
project: paper_KnowledgeBase
created: 2026-05-03
last_updated: 2026-05-03
version: 0.1.0
---

# §IV. EXPERIMENTAL PROTOCOL（草稿，可直接寫入論文）

## A. 實驗設計與資料集說明

### 1) 資料集構建（Dataset Construction）

為真實反映電子商務客服場景中查詢型態之多樣性與語意複雜度，本研究構建包含 1,000 筆查詢–回應配對之基準資料集。資料依實驗需求劃分為兩部分：500 筆作為**開發集（development set）**，用於模型開發與融合權重 α 之調整；其餘 500 筆作為**獨立測試集（held-out test set）**，僅在最終評估階段使用一次，以確保結果之客觀性與外部有效性。

### 2) 查詢類型設計（Query Taxonomy）

依電商客服實務中常見之查詢模式，本研究將查詢分為兩類，各佔 50%：

- **精確規格查詢（exact specification queries, EXS）**：涉及產品型號、技術參數、規格數值之查詢（如「型號 XYZ-9000 的最大續航時間？」）。此類查詢對檢索系統的**字面匹配能力**要求最高，輕微字面偏差即可能召回錯誤產品。

- **意圖導向查詢（intent-oriented queries, INT）**：模糊描述、產品比較、選購建議等需語意理解之查詢（如「適合海邊強風環境拍照的空拍機」）。此類查詢對**語意泛化能力**要求高，純關鍵字檢索容易召回失敗。

此雙路徑分類設計呼應 [4]、[11] 之檢索評估慣例，並能對 BM25 / TF-IDF 與向量檢索之相對優勢進行**分層分析**。

### 3) 商品語料庫（Product Corpus）

語料庫包含 200 篇商品文檔（doc_001 至 doc_200），均勻分布於三個產品類別：
- 空拍機 / 無人機（70 篇）
- 農業機具與感測器（70 篇）
- 智慧家電與 IoT 設備（60 篇）

每篇文檔含結構化欄位（型號、規格、適用情境、價格區間）與自由文字描述（150–400 字），模擬真實電商產品頁面之資訊密度。

### 4) 真值標註（Ground Truth Annotation）

所有 1,000 筆測試樣本之 ground truth 由兩位具備電子商務領域知識之專家獨立人工標註：

- **標註者 A**：資工背景研究生，熟悉 RAG / 檢索系統
- **標註者 B**：電商客服資深從業者（≥3 年經驗），熟悉產品分類

雙方在不知對方答案之情況下，對每筆查詢標註其最佳 ground truth doc_id（候選自 200 篇商品語料庫）。

### 5) 交叉驗證機制（Cross-Verification）

- **一致性檢驗**：以 Cohen's Kappa 計算雙標註者一致性，要求 κ ≥ 0.75（substantial agreement，依 Landis & Koch 1977 標準）。
- **衝突解決**：對於不一致樣本（status = "conflict"），由第三位獨立仲裁者裁定最終 ground truth。所有衝突樣本與仲裁過程記錄於 `data/annotations/conflict_resolution.json`。
- **標註可重現性**：所有標註指南、衝突案例、仲裁理由均開源於本研究 GitHub 倉庫，供後續研究複現。

## B. α 參數調整與檢索評估

### 6) 混合檢索架構（Hybrid Retrieval）

本研究檢索層採用稀疏 + 稠密混合分數：

```
score(q, d) = α · BM25(q, d) + (1 − α) · DenseSim(q, d)
```

其中 α ∈ [0, 1] 為融合權重。以開發集 500 筆樣本掃描 α ∈ {0.0, 0.1, 0.2, ..., 1.0}（11 個取樣點），對每個 α 計算 Hit@5 與 MRR；選擇使開發集 Hit@5 最佳之 α* 作為測試集評估參數。

### 7) 評估指標

- **Hit@K**（K=1, 3, 5, 10）：Top-K 候選中包含 ground truth 之比例
- **MRR（Mean Reciprocal Rank）**：1/rank_gt 之平均，rank_gt 為 ground truth 在候選列表中之排名
- **無來源論點比例**：生成回應中未附段落級引用之聲明比例（透過 `hallucination_guard.py` 自動偵測）

### 8) 對照組設計（Baseline Conditions）

| 對照組 | 系統 | 描述 |
|--------|------|------|
| **B0** | Pure LLM | 直接以 LLM 回答查詢，無外部知識增強 |
| **B1** | Naive RAG | 純向量檢索（單一階段，無混合，α=0） |
| **B2** | BM25 only | 純關鍵字檢索（α=1） |
| **T**  | **Perpetual RAG（本研究）** | 混合檢索（最佳 α*）+ Source-grounded 生成 + 防幻覺審計 |

四組均在獨立測試集 500 筆上評估。

## C. 統計顯著性檢定

### 9) McNemar Test（配對檢定）

對於每筆測試樣本，記錄兩系統之回答是否正確（{對, 錯} × {對, 錯} 四象限）。使用 McNemar 配對檢定比較：
- T vs B0（Perpetual RAG vs Pure LLM）
- T vs B1（Perpetual RAG vs Naive RAG）
- T vs B2（Perpetual RAG vs BM25 only）

顯著性水準：α = 0.05（雙尾）；p < 0.05 視為達顯著差異。

### 10) 95% 信賴區間

對於 Hit@K 與 MRR 等比例 / 連續指標，分別以：
- Wilson score interval（比例型）
- Bootstrap with 1000 resamples（連續型）

計算 95% 信賴區間，作為點估計之區間化呈現。

### 11) 效應量（Effect Size）

對於 McNemar 顯著之比較，補報 odds ratio 與 95% CI，避免僅依賴 p-value 之常見批評（依 APA 統計報告慣例）。

## D. 可重現性聲明（Reproducibility Statement）

- 所有資料、標註、腳本、隨機種子均開源於 `https://github.com/[user]/perpetual-rag-benchmark`
- Python 3.12.x、固定 random seed = 42、依賴版本鎖定於 `requirements.txt`
- 評估流程可一鍵執行：`make all` 或 `bash run_full_pipeline.sh`
- 所有報告數據均可透過 `python scripts/5_statistics.py` 重現產生

## E. 已知限制（Limitations）

1. **資料規模**：1,000 筆相對於業界部署規模仍屬小型；外部有效性需更大規模驗證
2. **標註者偏差**：雙標註者均為中文母語者；對英文 / 跨語言場景之外推需謹慎
3. **領域窄化**：本基準聚焦電商客服；其他垂直領域（如法律、醫療）之適用性需獨立驗證
4. **動態知識更新**：本基準為靜態快照，無法反映知識庫隨時間演化之效應
