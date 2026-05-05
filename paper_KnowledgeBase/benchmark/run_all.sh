#!/usr/bin/env bash
# Full pipeline reproducibility wrapper.
# Usage: bash run_all.sh

set -euo pipefail

# Auto-detect Python: local .venv → parent dir .venv → system python3
if [ -x ".venv/bin/python3" ]; then
  PYTHON="${PYTHON:-.venv/bin/python3}"
elif [ -x "../.venv/bin/python3" ]; then
  PYTHON="${PYTHON:-../.venv/bin/python3}"
else
  PYTHON="${PYTHON:-python3}"
fi

echo "═══════════════════════════════════════════════════════════════"
echo "  Perpetual RAG Benchmark — Full Pipeline"
echo "  Using Python: $PYTHON"
echo "═══════════════════════════════════════════════════════════════"
echo ""

if ! command -v "$PYTHON" >/dev/null 2>&1 && [ ! -x "$PYTHON" ]; then
  echo "❌ Python not found at $PYTHON"
  echo "   Setup: python3.12 -m venv .venv && .venv/bin/pip install -r requirements.txt"
  exit 1
fi

echo "▶ Stage 1/6: Importing C-MTEB EcomRetrieval..."
$PYTHON scripts/6_import_cmteb_ecom.py
echo ""

echo "▶ Stage 2/6: Evaluating TF-IDF Hybrid + baselines..."
$PYTHON scripts/4_evaluate.py
echo ""

echo "▶ Stage 3/6: Evaluating BGE-only..."
$PYTHON scripts/8_bge_eval.py
echo ""

echo "▶ Stage 4/6: Evaluating BGE Hybrid (proposed T+)..."
$PYTHON scripts/9_bge_hybrid_eval.py
echo ""

echo "▶ Stage 5/6: Computing statistics..."
$PYTHON scripts/5_statistics.py
echo ""

echo "▶ Stage 6/6: Generating figures..."
$PYTHON scripts/7_plot.py
echo ""

echo "═══════════════════════════════════════════════════════════════"
echo "  ✅ Pipeline complete!"
echo "  Results: data/final_report.md"
echo "  Figures: data/figures/*.{png,pdf}"
echo "═══════════════════════════════════════════════════════════════"
