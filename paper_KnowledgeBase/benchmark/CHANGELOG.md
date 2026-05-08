# Changelog

All notable changes to this benchmark are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/);
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] — 2026-05-08

### Fixed
- **Reproducibility bug in corpus generation** (`scripts/6_import_cmteb_ecom.py`).
  The line `distractor_pool = list(all_pids - gt_pids)` produced a list whose
  order depends on Python's `PYTHONHASHSEED`. Even with `random.seed(42)`,
  `random.shuffle` was applied to a non-deterministic input, producing a
  different distractor sample on every run. Fixed by inserting `sorted(...)`
  before the shuffle. After this fix, `corpus.json` and `queries.json` produce
  bit-identical output (verified by MD5) across repeated runs.
- **Stale BGE embedding cache** (`scripts/8_bge_eval.py`).
  `encode_with_cache()` previously loaded `corpus_bge.npy` blindly without
  validating that it corresponded to the current `corpus.json`. When the
  corpus changed (e.g., after rerunning `make data`), the cached embeddings
  silently misaligned with the new `doc_id` ordering, causing BGE-only
  results to collapse to near-random (≈0.6%–2.6% Hit@5). Fixed by writing
  a SHA-256 sidecar (`corpus_bge.sha256`) alongside the cache and refusing
  to load when the hash does not match the live texts.

### Changed
- **Headline result**: with the two reproducibility bugs fixed, the
  re-evaluated test-set Hit@5 numbers are:
  - T+ (BGE-only, α=0): **93.2%** [90.7%, 95.1%] — proposed primary method
  - T++ (T+ → CrossEncoder rerank, ablation): 90.8%
  - T (TF-IDF Hybrid, α*=0.1, fallback): 85.6%
  - B1 (Naive TF-IDF, α=0): 83.8%
  - B2 (BM25 only, α=1): 73.2%
  - B0 (Random): 0.6%
- **α* for BGE configuration moved from 0.1 to 0.0**: the BM25+BGE α-sweep
  on the dev set now shows a monotonic decrease from α=0; pure BGE is the
  optimal configuration on this benchmark. The TF-IDF configuration still
  prefers a small BM25 mix (α*=0.1).
- **`scripts/7_plot.py`** updated: Fig. 1 now plots both TF-IDF and BGE
  α-sweeps in a single figure (annotated α*=0.1 vs α*=0.0); Fig. 2 title
  is now driven dynamically by the number of conditions plotted.
- **Cross-encoder rerank ablation**: the impact of reranking on Hit@5 is
  now reported as `93.2% → 90.8%, b=25, c=13, χ²=3.18, p=0.074` — a
  trend toward degradation that **does not reach statistical significance**
  on this run (previously reported as a significant drop under the buggy
  pipeline). The qualitative conclusion ("rerank does not help on short
  Chinese e-commerce queries") is unchanged.

### Notes
- The cross-encoder rerank step (`10_rerank_eval.py`) on Mac Mini 2014 Intel
  CPU takes approximately 6.7 hours wall-clock for 25,000 (query, document)
  scoring pairs. Earlier README/paper notes citing "~38 minutes" were on a
  different machine; the figure has been corrected.
- All v1.0.0 numbers should be considered superseded; please cite v1.0.1
  or later for any results derived from this benchmark.

## [1.0.0] — 2026-05-05

Initial public release accompanying the Perpetual RAG paper. Includes
data import, evaluation, statistics, plotting, and cross-encoder rerank
pipelines, plus a one-shot `make all` reproducibility entry point.
