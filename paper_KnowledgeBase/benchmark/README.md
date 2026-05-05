# Perpetual RAG Benchmark

> Reproducible empirical evaluation infrastructure for the Perpetual RAG architecture
> on the C-MTEB EcomRetrieval Chinese e-commerce benchmark.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![C-MTEB](https://img.shields.io/badge/benchmark-C--MTEB%20EcomRetrieval-green.svg)](https://huggingface.co/datasets/C-MTEB/EcomRetrieval)

This repository provides the complete experimental infrastructure for evaluating the **Perpetual RAG** architecture proposed in our paper. All scripts, configurations, and intermediate artifacts are open-sourced under MIT License to support full reproducibility.

---

## 🎯 Headline Results

Evaluation on **C-MTEB EcomRetrieval** (2,000-document subset, 500 held-out test queries):

| Condition | Hit@5 (95% CI) | MRR | Significance vs T+ |
|-----------|----------------|-----|---------------------|
| B0 Random | 0.8% [0.31%, 2.04%] | 0.0000 | p < 0.001 *** |
| B2 BM25 only | 73.6% [69.6%, 77.3%] | 0.6331 | p < 0.001 *** |
| B1 TF-IDF only | 83.6% [80.1%, 86.6%] | 0.7098 | p < 0.001 *** |
| T (TF-IDF Hybrid, CPU fallback) | 84.8% [81.4%, 87.7%] | 0.7383 | p < 0.001 *** |
| **T+ (BGE Hybrid, proposed)** | **93.6% [91.1%, 95.4%]** | **0.8697** | **—** |

McNemar paired test (n=500). Random seed = 42 for full reproducibility.

**Key finding**: Replacing TF-IDF with BGE-small-zh-v1.5 in the same hybrid architecture (α=0.1) yields a statistically significant 8.8 percentage point improvement (T+ vs T, p < 0.001), empirically validating that the Perpetual RAG architecture is **retriever-agnostic**.

---

## 📦 Installation

```bash
# Clone the repository
git clone https://github.com/quanfu2026/perpetual-rag.git
cd perpetual-rag-benchmark

# Create virtual environment
python3.12 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

**Hardware tested**: Mac Mini 2014 Intel (i5 4-core, 8GB RAM, no GPU). Runtime ~10 minutes for full pipeline.

---

## 🚀 Quick Start

```bash
# 1. Import C-MTEB EcomRetrieval benchmark (downloads ~50MB)
python scripts/6_import_cmteb_ecom.py

# 2. Run TF-IDF Hybrid evaluation (T condition)
python scripts/4_evaluate.py

# 3. Run BGE-based evaluation (T+ proposed method, downloads ~95MB BGE model)
python scripts/8_bge_eval.py
python scripts/9_bge_hybrid_eval.py

# 4. Run cross-encoder reranking (optional, T++ further improvement)
python scripts/10_rerank_eval.py

# 5. Generate statistical reports
python scripts/5_statistics.py

# 6. Generate publication figures
python scripts/7_plot.py
```

All outputs land in `data/`:
- `data/evaluation_results.json` — full numerical results
- `data/final_report.md` — Wilson CI + McNemar tables
- `data/figures/` — Fig. 1 (α sweep) and Fig. 2 (5-condition bar chart) in PNG + PDF

---

## 📁 Repository Structure

```
benchmark/
├── README.md                        # this file
├── requirements.txt                 # Python dependencies
├── .env.example                     # template for ANTHROPIC_API_KEY (optional)
├── docs/
│   ├── protocol.md                  # full experimental protocol (paper §IV draft)
│   ├── manual_verification.md       # 7-step QA verification guide
│   └── paper_section_VI.md          # paper §VI Empirical Evaluation draft
├── data/
│   ├── corpus.json                  # 2,000-doc product corpus (C-MTEB subset)
│   ├── queries.json                 # 1,000 queries (500 dev + 500 test) with qrels
│   ├── evaluation_results.json      # all numerical results
│   ├── final_report.md              # statistical report (auto-generated)
│   ├── error_samples.json           # 76 misclassified samples for error analysis
│   ├── embeddings/                  # cached BGE embeddings
│   │   ├── corpus_bge.npy
│   │   ├── dev_queries_bge.npy
│   │   └── test_queries_bge.npy
│   └── figures/                     # publication-ready figures (PNG + PDF)
└── scripts/
    ├── 1_generate.py                # mock corpus (deprecated, kept for history)
    ├── 2_annotate.py                # annotation export/import workflow
    ├── 3_verify.py                  # Cohen's Kappa + conflict resolution
    ├── 4_evaluate.py                # TF-IDF Hybrid + 4 baselines
    ├── 5_statistics.py              # McNemar + Wilson 95% CI + Bootstrap
    ├── 6_import_cmteb_ecom.py       # C-MTEB EcomRetrieval import
    ├── 7_plot.py                    # matplotlib figure generation
    ├── 8_bge_eval.py                # BGE-small-zh-v1.5 evaluation (BGE-only)
    ├── 9_bge_hybrid_eval.py         # BM25 + BGE hybrid α sweep
    └── 10_rerank_eval.py            # CrossEncoder reranking (T++ optional)
```

---

## 🔬 Experimental Design

### Dataset

| Attribute | Value |
|-----------|-------|
| Source benchmark | C-MTEB EcomRetrieval (Multi-CPR e-commerce subset) |
| Corpus size | 2,000 documents (1,000 ground-truth + 1,000 distractors) |
| Query count | 1,000 (500 dev + 500 held-out test) |
| Ground truth | Human-annotated qrels (academic standard) |
| Language | Chinese (Mandarin), real e-commerce search queries |

### Retrieval Architecture

The hybrid retrieval score:

```
score(q, d) = α · BM25(q, d) + (1 − α) · DenseSim(q, d)
```

We instantiate `DenseSim()` two ways:

- **T (CPU fallback)**: TF-IDF character-level n-gram (n=2-4) — for resource-constrained deployment
- **T+ (proposed)**: BGE-small-zh-v1.5 neural embedding (512-dim, 95MB) — primary configuration

Both share the same hybrid framework with α* = 0.1 (tuned on dev set).

### Baselines

- **B0 Random** (statistical floor)
- **B1 TF-IDF only** (α = 0)
- **B2 BM25 only** (α = 1)
- **T TF-IDF Hybrid** (CPU fallback ablation)

### Statistical Tests

- **Wilson 95% Score Interval** for binomial proportions (Hit@K)
- **Bootstrap 95% CI** for continuous metrics (MRR, 1,000 resamples)
- **McNemar paired test** for system comparison (binary correctness)
- All comparisons against significance level α = 0.05 (two-tailed)

---

## 🛠 Reproducibility

- **Random seed**: 42 (fixed throughout pipeline)
- **Python version**: 3.12.x
- **Dependencies pinned**: see `requirements.txt`
- **Hardware tested**: Mac Mini 2014 (Intel i5, 8GB, no GPU); should work on any modern CPU
- **Total runtime**: ~10 minutes end-to-end

To re-verify our results:

```bash
make all          # or
bash run_all.sh   # if Makefile not available
```

The output should match `data/evaluation_results.json` byte-for-byte modulo float precision.

---

## 📚 Citation

If you use this benchmark or its findings, please cite:

```bibtex
@inproceedings{chen2026perpetual,
  title     = {Perpetual Knowledge Management:
               Implementing a Low-Cost RAG System via a Trinity Architecture
               of Obsidian, NotebookLM, and Claude Code},
  author    = {Chen, Wen-Chung},
  booktitle = {Proceedings of [VENUE TBD]},
  year      = {2026},
  note      = {Code: https://github.com/quanfu2026/perpetual-rag/tree/master/paper_KnowledgeBase/benchmark}
}
```

We also acknowledge the foundational benchmarks our work builds upon:

```bibtex
@article{xiao2023cpack,
  title   = {C-Pack: Packed Resources For General Chinese Embeddings},
  author  = {Xiao, Shitao and Liu, Zheng and Zhang, Peitian and Muennighoff, Niklas},
  journal = {arXiv preprint arXiv:2309.07597},
  year    = {2023}
}

@inproceedings{long2022multicpr,
  title     = {Multi-CPR: A Multi Domain Chinese Dataset for Passage Retrieval},
  author    = {Long, Dingkun and Gao, Qiong and Zou, Kun and others},
  booktitle = {Proceedings of SIGIR 2022},
  year      = {2022}
}
```

---

## 📜 License

This codebase is released under the **MIT License** — see [LICENSE](LICENSE).

The C-MTEB benchmark data is governed by its original license (see [C-MTEB/EcomRetrieval](https://huggingface.co/datasets/C-MTEB/EcomRetrieval)).

Pre-trained models (BGE, BGE-reranker) are governed by their respective licenses on Hugging Face.

---

## 🤝 Contributing

This is an academic research artifact. Issues and pull requests welcome for:
- Bug fixes in evaluation scripts
- Reproducibility issues (please include your Python / OS / hardware details)
- Extensions to other domains or languages

For research collaborations, please open a GitHub issue for initial discussion.

---

## 📧 Contact

- **Author**: Wen-Chung Chen
- **Email**: b0963118770@gmail.com
- **Issue tracker**: GitHub Issues

---

## 🙏 Acknowledgments

This work uses public benchmarks and pre-trained models from:
- [C-MTEB](https://huggingface.co/C-MTEB) (BAAI Chinese MTEB benchmark)
- [Multi-CPR](https://github.com/Alibaba-NLP/Multi-CPR) (Alibaba multi-domain Chinese retrieval)
- [BGE](https://huggingface.co/BAAI/bge-small-zh-v1.5) (BAAI General Embedding)
- [sentence-transformers](https://www.sbert.net/) (Reimers & Gurevych)
- [Hugging Face Datasets](https://huggingface.co/datasets)

The architectural inspiration draws on prior work in long-term memory RAG:
[Mem0], [HippoRAG 2], [AgeMem], [All-Mem], [MemMachine], [Episodic Memory], [Agentic RAG] (full citations in paper).

---

**Last updated**: 2026-05-04
