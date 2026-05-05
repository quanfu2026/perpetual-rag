# Perpetual RAG Benchmark — One-shot reproducibility
#
# Usage:
#   make all      # full pipeline end-to-end
#   make data     # import C-MTEB benchmark only
#   make eval     # all evaluation conditions
#   make stats    # statistics + figures
#   make clean    # remove generated outputs (keeps source data)

PYTHON := .venv/bin/python3
SCRIPTS := scripts

.PHONY: all data eval stats clean install verify

all: data eval stats
	@echo ""
	@echo "✅ Pipeline complete. See data/final_report.md and data/figures/ for results."

install:
	python3.12 -m venv .venv
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install -r requirements.txt

data:
	@echo "📥 Importing C-MTEB EcomRetrieval..."
	$(PYTHON) $(SCRIPTS)/6_import_cmteb_ecom.py

eval: eval_tfidf eval_bge eval_rerank

eval_tfidf:
	@echo "🔬 Evaluating TF-IDF Hybrid (T condition)..."
	$(PYTHON) $(SCRIPTS)/4_evaluate.py

eval_bge:
	@echo "🤖 Evaluating BGE-only and BGE Hybrid (T+ proposed)..."
	$(PYTHON) $(SCRIPTS)/8_bge_eval.py
	$(PYTHON) $(SCRIPTS)/9_bge_hybrid_eval.py

eval_rerank:
	@echo "🎯 Evaluating Cross-encoder rerank (T++ optional)..."
	$(PYTHON) $(SCRIPTS)/10_rerank_eval.py

stats:
	@echo "📊 Computing statistics..."
	$(PYTHON) $(SCRIPTS)/5_statistics.py
	@echo "🎨 Generating figures..."
	$(PYTHON) $(SCRIPTS)/7_plot.py

verify:
	@echo "🔍 Running QA verification..."
	@echo "See docs/manual_verification.md for the 7-step manual checklist."

clean:
	rm -rf data/evaluation_results.json data/final_report.md data/figures/*.png data/figures/*.pdf
	@echo "🧹 Cleaned generated outputs (raw data preserved)."

clean_all: clean
	rm -rf data/embeddings/
	@echo "🧹 Also removed cached BGE embeddings."
