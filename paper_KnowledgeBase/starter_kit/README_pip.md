# perpetual-rag

**永續性知識管理系統** — 基於 Obsidian-NotebookLM-Claude Code 三層架構的防幻覺 RAG 框架

[![Version](https://img.shields.io/badge/version-1.0.0-blue)](https://github.com/YOUR/perpetual-rag)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)

> 論文：「永續性知識管理：基於 Obsidian-NotebookLM-Claude Code 三層防幻覺 RAG 框架」
> ILT2026 國際學習科技研討會

---

## 一鍵安裝

```bash
pip install perpetual-rag
perpetual-rag init --vault ~/my_KnowledgeBase --project "我的研究專案"
```

## 核心功能

```bash
perpetual-rag init    # 建立知識庫
perpetual-rag search "關鍵字"  # BM25 搜尋
perpetual-rag audit   # 防幻覺掃描
perpetual-rag graph   # 生成知識圖譜
perpetual-rag bump    # 版本升級
```

## 系統架構

```
Obsidian（儲存層）→ NotebookLM（理解層）→ Claude Code（執行層）
       ↑ 知識解耦（SoC 原則）↑
```

## 驗證結果

| 指標 | 數值 |
|------|------|
| 幻覺率 | **3%**（基準 59%，降幅 -95%）|
| Token 消耗 | **↓65–76%** |
| RAM 峰值 | **120MB**（Mac Mini 2014，無 GPU）|
| 跨 Session 恢復 | **6 秒，零錯誤** |
