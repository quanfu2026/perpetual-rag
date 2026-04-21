# Changelog — Perpetual RAG Starter Kit

所有版本變更記錄於此。版號遵循 [Semantic Versioning](https://semver.org/)。

格式：
- `Added` 新增功能
- `Changed` 修改現有功能
- `Fixed` 錯誤修正
- `Removed` 移除功能

---

## [v1.0.0] — 2026-04-21

**首個正式發布版本。**

基於論文「永續性知識管理：基於 Obsidian-NotebookLM-Claude Code 三層架構的防幻覺 RAG 框架」
（ILT2026 投稿版）完整實驗驗證後定稿。

### Added
- `SETUP.md`：完整安裝指南（Mac / Windows / Linux 三平台，含排解章節）
- `scripts/setup.py`：一鍵初始化腳本，自動建立資料夾結構、系統文件、複製腳本
- `scripts/bm25_search.py`：BM25 精準路徑召回，查詢耗時 0.38–0.41 秒，磁碟 I/O ↓99%
- `scripts/hallucination_guard.py`：全文幻覺掃描，WHITELIST 26 條，112 警告 → 0
- `scripts/consistency_check.py`：跨章節術語一致性稽核
- `scripts/writeback.py`：Append-only 安全回寫，三層衝突防護
- `scripts/daily_audit.py`：每日進度快照，知識庫健康狀態監控
- `scripts/vector_search.py`：BM25+TF-IDF 兩階段混合搜尋
- `scripts/knowledge_graph.py`：[[wikilink]] 萃取，輸出 DOT / JSON / Obsidian Canvas
- `知識庫範本/CLAUDE.md`：AI 行為規範通用範本
- `知識庫範本/sessionhandoff.md`：跨 Session 記憶交接空白模板
- `知識庫範本/index.md`：決策日誌模板
- `知識庫範本/參考文獻/REF_範本.md`：參考文獻筆記模板

### 系統指標（v1.0.0 實驗驗證結果）
| 指標 | 數值 |
|------|------|
| 幻覺率 | 3%（基準 59%，降幅 -95%）|
| Token 消耗 | 8–16K/任務（基準 33–85K，↓65–76%）|
| 磁碟 I/O | 路徑召回（基準全文掃描，↓99%）|
| RAM 峰值 | 120MB（Mac Mini 2014）|
| 跨 Session 恢復 | 6 秒，零錯誤（n=6）|

---

## 未來版本規劃

### [v1.1.0] — 預計 Month 2
- `scripts/mcnemar_test.py`：McNemar 統計顯著性驗證腳本
- 新增英文版 `SETUP_EN.md`

### [v2.0.0] — 預計硬體升級後
- ChromaDB 向量資料庫整合（替換 TF-IDF 層）
- GPU 加速向量索引選項
