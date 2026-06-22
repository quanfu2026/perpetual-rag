#!/usr/bin/env python3
"""
Stage 7: 產生論文圖表（matplotlib）。

兩張圖：
  - Fig IV-1: α 掃描曲線（Hit@5 / MRR vs α）
  - Fig IV-2: 四組對照長條圖（B0/B1/B2/T，含 95% CI 誤差棒）

輸出：data/figures/fig_alpha_sweep.png + data/figures/fig_conditions.png
       同時輸出 PDF 以便論文嵌入。
"""
import json
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
FIGS = DATA / "figures"
FIGS.mkdir(exist_ok=True)


def wilson_ci(k, n, z=1.96):
    if n == 0:
        return 0, 0
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return max(0, center - half), min(1, center + half)


def setup_chinese_font():
    """嘗試找 macOS 上能渲染中文的字型。"""
    candidates = ["Heiti TC", "PingFang TC", "STSong", "Arial Unicode MS"]
    available = {f.name for f in fm.fontManager.ttflist}
    for c in candidates:
        if c in available:
            plt.rcParams["font.sans-serif"] = [c]
            plt.rcParams["axes.unicode_minus"] = False
            return c
    return None


# ── Figure 1: α sweep ──────────────────────────────────────────

def plot_alpha_sweep(R):
    tfidf_sweep = R["alpha_sweep_dev"]
    bge_sweep = R.get("bge_hybrid_alpha_sweep_dev", {})
    alphas = sorted(float(a) for a in tfidf_sweep.keys())
    tfidf_hit5 = [tfidf_sweep[str(a)]["Hit@5"] for a in alphas]
    bge_hit5 = [bge_sweep[str(a)]["Hit@5"] for a in alphas] if bge_sweep else None

    tfidf_best = max(alphas, key=lambda a: tfidf_sweep[str(a)]["Hit@5"])
    bge_best = max(alphas, key=lambda a: bge_sweep[str(a)]["Hit@5"]) if bge_sweep else None

    fig, ax = plt.subplots(figsize=(7.5, 4.8))

    color_tfidf = "#457B9D"
    color_bge = "#E63946"

    ax.plot(alphas, tfidf_hit5, "o-", color=color_tfidf,
            linewidth=2, markersize=8, label="TF-IDF + BM25 (T config)")
    if bge_hit5:
        ax.plot(alphas, bge_hit5, "s-", color=color_bge,
                linewidth=2, markersize=8, label="BGE + BM25 (T+ config)")

    ax.set_xlabel(r"$\alpha$ (BM25 weight; $\alpha$=0: Dense only, $\alpha$=1: BM25 only)", fontsize=11)
    ax.set_ylabel("Hit@5 (development set)", fontsize=11)
    all_y = tfidf_hit5 + (bge_hit5 or [])
    ax.set_ylim(min(all_y) * 0.95, 1.0)
    ax.grid(True, alpha=0.3)

    # 標記兩條曲線之最佳 α*
    ax.axvline(tfidf_best, color=color_tfidf, linestyle=":", alpha=0.5)
    ax.annotate(rf"TF-IDF $\alpha^*={tfidf_best}$",
                xy=(tfidf_best, tfidf_sweep[str(tfidf_best)]["Hit@5"]),
                xytext=(tfidf_best + 0.15, tfidf_sweep[str(tfidf_best)]["Hit@5"] - 0.02),
                fontsize=10, color=color_tfidf, fontweight="bold",
                arrowprops=dict(arrowstyle="->", color=color_tfidf, alpha=0.7))
    if bge_best is not None:
        ax.axvline(bge_best, color=color_bge, linestyle=":", alpha=0.5)
        ax.annotate(rf"BGE $\alpha^*={bge_best}$ (pure BGE)",
                    xy=(bge_best, bge_sweep[str(bge_best)]["Hit@5"]),
                    xytext=(bge_best + 0.15, bge_sweep[str(bge_best)]["Hit@5"] + 0.015),
                    fontsize=10, color=color_bge, fontweight="bold",
                    arrowprops=dict(arrowstyle="->", color=color_bge, alpha=0.7))

    ax.legend(loc="lower left", fontsize=10)
    plt.title("Fig. 1. α Sweep on Development Set (n=500): T vs T+ Configurations", fontsize=12)
    plt.tight_layout()
    out_png = FIGS / "fig_alpha_sweep.png"
    out_pdf = FIGS / "fig_alpha_sweep.pdf"
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.close()
    print(f"   ✅ {out_png.relative_to(ROOT)}")
    print(f"   ✅ {out_pdf.relative_to(ROOT)}")


# ── Figure 2: condition comparison ────────────────────────────

def plot_conditions(R):
    pq = R["per_query_correct_test"]
    n_test = len(R["test_query_ids"])

    # 按性能由低到高排列；T+ (BGE) 是主方法（紅色）
    order = []
    if "B0 (Random)" in pq: order.append("B0 (Random)")
    if "B2 (BM25 only, α=1)" in pq: order.append("B2 (BM25 only, α=1)")
    if "B1 (Naive RAG, α=0)" in pq: order.append("B1 (Naive RAG, α=0)")
    t_tfidf = next((c for c in pq if c.startswith("T ") or c == "T"), None)
    if t_tfidf: order.append(t_tfidf)
    rerank_key = "T++ (T+ → CrossEncoder rerank)"
    if rerank_key in pq: order.append(rerank_key)
    if "T+ (BGE-only)" in pq: order.append("T+ (BGE-only)")

    short_labels = {
        "B0 (Random)": "B0\nRandom",
        "B1 (Naive RAG, α=0)": "B1\nTF-IDF\n(Naive)",
        "B2 (BM25 only, α=1)": "B2\nBM25\nonly",
        t_tfidf if t_tfidf else "": "T\nTF-IDF\nHybrid",
        rerank_key: "T++ (ablation)\nT+ → Cross-\nencoder rerank",
        "T+ (BGE-only)": "T+ (proposed)\nBGE\nNeural",
    }

    hits = [sum(pq[c]) for c in order]
    means = [h / n_test for h in hits]
    cis = [wilson_ci(h, n_test) for h in hits]
    err_low = [m - lo for m, (lo, _) in zip(means, cis)]
    err_high = [hi - m for m, (_, hi) in zip(means, cis)]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    # 6 colors: gray, light blue, mid blue, dark blue, orange (rerank ablation), red (proposed)
    palette = ["#999999", "#A8DADC", "#7FB3D5", "#457B9D", "#F4A261", "#E63946"]
    colors = palette[:len(order)]
    x = list(range(len(order)))
    bars = ax.bar(
        x, means, yerr=[err_low, err_high],
        color=colors, edgecolor="black", linewidth=1,
        capsize=8, error_kw={"linewidth": 1.5}
    )

    for bar, m in zip(bars, means):
        ax.text(bar.get_x() + bar.get_width() / 2, m + 0.02,
                f"{m*100:.1f}%", ha="center", fontsize=10, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([short_labels[c] for c in order], fontsize=10)
    ax.set_ylabel("Hit@5 (95% Wilson CI)", fontsize=11)
    ax.set_ylim(0, 1.05)
    ax.set_title(f"Fig. 2. Hit@5 across {len(order)} Conditions (Test Set, n={n_test})", fontsize=12)
    ax.grid(True, axis="y", alpha=0.3)

    # 顯著性註記（如果你想在圖中加 *** 標記）
    plt.tight_layout()
    out_png = FIGS / "fig_conditions.png"
    out_pdf = FIGS / "fig_conditions.pdf"
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.savefig(out_pdf, bbox_inches="tight")
    plt.close()
    print(f"   ✅ {out_png.relative_to(ROOT)}")
    print(f"   ✅ {out_pdf.relative_to(ROOT)}")


# ── 主流程 ────────────────────────────────────────────────────

def main():
    R = json.loads((DATA / "evaluation_results.json").read_text(encoding="utf-8"))
    font = setup_chinese_font()
    if font:
        print(f"📝 中文字型：{font}")

    print("\n📊 產生圖表：")
    plot_alpha_sweep(R)
    plot_conditions(R)
    print(f"\n✅ 圖表已輸出至 {FIGS.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
