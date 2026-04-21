# perpetual-rag

**永續性知識管理系統** — 基於 Obsidian-NotebookLM-Claude Code 三層架構的防幻覺 RAG 框架

[![Version](https://img.shields.io/badge/version-1.1.0-blue)](https://github.com/quanfu2026/perpetual-rag)
[![Python](https://img.shields.io/badge/python-3.8+-green)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-orange)](LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.19676404.svg)](https://doi.org/10.5281/zenodo.19676404)

> 論文：「永續性RAG：資源受限環境下以知識解耦實現幻覺抑制」
> ILT2026 國際學習科技研討會 | Preprint DOI: [10.5281/zenodo.19676404](https://doi.org/10.5281/zenodo.19676404)

---

## 一鍵安裝

**Mac / Linux**
```bash
curl -fsSL https://raw.githubusercontent.com/quanfu2026/perpetual-rag/master/starter_kit/install.sh | bash
```

**Windows**
```powershell
pip install perpetual-rag
perpetual-rag init --vault C:\my_KnowledgeBase --project "我的研究"
```

**所有平台（pip）**
```bash
pip install perpetual-rag
perpetual-rag init --vault ~/my_KnowledgeBase --project "我的研究專案"
```

**zip 下載**：[GitHub Releases](https://github.com/quanfu2026/perpetual-rag/releases/latest)

| 方式 | Mac | Linux | Windows |
|------|:---:|:-----:|:-------:|
| `curl \| bash` | ✅ | ✅ | ❌ |
| `pip install` | ✅ | ✅ | ✅ |
| zip 下載 | ✅ | ✅ | ✅ |

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
