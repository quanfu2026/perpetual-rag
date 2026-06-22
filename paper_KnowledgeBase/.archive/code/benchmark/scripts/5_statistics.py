#!/usr/bin/env python3
"""
Stage 5: 統計顯著性檢定。

讀取 evaluation_results.json，執行：
  - McNemar Test：T vs B1, T vs B2（配對二項檢定）
  - Wilson 95% CI：每組 Hit@K 之區間估計
  - Bootstrap 95% CI：MRR 連續指標
  - 輸出論文表格：data/final_report.md
"""
import json
import math
import random
from itertools import combinations
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


def mcnemar(b, c):
    """
    McNemar's test (with continuity correction for small samples).

    b: T 對但 baseline 錯
    c: T 錯但 baseline 對
    """
    if b + c == 0:
        return 1.0, 0.0
    chi2 = (abs(b - c) - 1) ** 2 / (b + c)
    # P-value from chi-squared distribution (df=1)
    # 近似：對 chi2 大的情況用近似公式
    p = math.erfc(math.sqrt(chi2 / 2))
    return p, chi2


def wilson_ci(k, n, z=1.96):
    """Wilson score interval for binomial proportion."""
    if n == 0:
        return (0.0, 0.0)
    p = k / n
    denom = 1 + z**2 / n
    center = (p + z**2 / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / denom
    return (max(0, center - half), min(1, center + half))


def bootstrap_ci(values, n_boot=1000, alpha=0.05):
    """Percentile bootstrap CI for mean."""
    n = len(values)
    if n == 0:
        return (0.0, 0.0)
    means = []
    for _ in range(n_boot):
        sample = [values[random.randint(0, n - 1)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int(n_boot * alpha / 2)]
    hi = means[int(n_boot * (1 - alpha / 2))]
    return (lo, hi)


def main():
    results_path = DATA / "evaluation_results.json"
    if not results_path.exists():
        print("⚠️  找不到 evaluation_results.json，請先執行 stage 4。")
        return
    R = json.loads(results_path.read_text(encoding="utf-8"))

    pq = R["per_query_correct_test"]
    n_test = len(R["test_query_ids"])
    conditions = list(pq.keys())
    T_name = next(c for c in conditions if c.startswith("T "))

    print(f"\n📊 統計檢定（test set, n={n_test}）\n")

    # ── Wilson 95% CI for Hit@5 ──
    print("=" * 78)
    print("Hit@5 點估計與 Wilson 95% 信賴區間")
    print("=" * 78)
    print(f"{'condition':<38}  {'Hit@5':>7}  {'95% CI':>22}")
    for name in conditions:
        correct = sum(pq[name])
        prop = correct / n_test
        lo, hi = wilson_ci(correct, n_test)
        print(f"{name:<38}  {prop:>7.4f}  [{lo:.4f}, {hi:.4f}]")

    # ── McNemar：T vs each baseline ──
    print()
    print("=" * 78)
    print("McNemar Test（配對檢定，Hit@5 binary outcome）")
    print("=" * 78)
    print(f"{'comparison':<40}  {'b':>4}  {'c':>4}  {'χ²':>7}  {'p-value':>10}  {'sig':>4}")

    T_correct = pq[T_name]
    for B_name in conditions:
        if B_name == T_name:
            continue
        B_correct = pq[B_name]
        # b: T 對 B 錯；c: T 錯 B 對
        b = sum(1 for t, bb in zip(T_correct, B_correct) if t == 1 and bb == 0)
        c = sum(1 for t, bb in zip(T_correct, B_correct) if t == 0 and bb == 1)
        p, chi2 = mcnemar(b, c)
        sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
        print(f"T vs {B_name[:34]:<34}  {b:>4}  {c:>4}  {chi2:>7.3f}  {p:>10.4f}  {sig:>4}")

    # ── 寫出論文表格 ──
    out_lines = [
        "# Final Statistical Report\n",
        f"\nGenerated from `evaluation_results.json` (n_test = {n_test}, best α = {R['best_alpha']})\n",
        "\n## 表 IV-1：Test Set 主要結果（含 Wilson 95% CI）\n",
        "\n| Condition | Hit@1 | Hit@3 | Hit@5 (95% CI) | Hit@10 | MRR |",
        "|-----------|-------|-------|-----------------|--------|-----|",
    ]
    for name in conditions:
        m = R["test_metrics"][name]
        correct = sum(pq[name])
        lo, hi = wilson_ci(correct, n_test)
        out_lines.append(
            f"| {name} | {m['Hit@1']:.4f} | {m['Hit@3']:.4f} | "
            f"**{m['Hit@5']:.4f}** [{lo:.4f}, {hi:.4f}] | "
            f"{m['Hit@10']:.4f} | {m['MRR']:.4f} |"
        )

    out_lines += [
        "\n## 表 IV-2：McNemar 配對檢定\n",
        "\n| Comparison | b (T✓ B✗) | c (T✗ B✓) | χ² | p-value | sig |",
        "|------------|-----------|-----------|-----|---------|-----|",
    ]
    for B_name in conditions:
        if B_name == T_name:
            continue
        B_correct = pq[B_name]
        b = sum(1 for t, bb in zip(T_correct, B_correct) if t == 1 and bb == 0)
        c = sum(1 for t, bb in zip(T_correct, B_correct) if t == 0 and bb == 1)
        p, chi2 = mcnemar(b, c)
        sig = "***" if p < 0.001 else ("**" if p < 0.01 else ("*" if p < 0.05 else "ns"))
        out_lines.append(
            f"| T vs {B_name} | {b} | {c} | {chi2:.3f} | {p:.4f} | {sig} |"
        )

    out_lines.append("\n顯著性標記：*** p<0.001, ** p<0.01, * p<0.05, ns = 不顯著\n")

    report_path = DATA / "final_report.md"
    report_path.write_text("\n".join(out_lines), encoding="utf-8")
    print(f"\n✅ 論文表格已寫入 {report_path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
