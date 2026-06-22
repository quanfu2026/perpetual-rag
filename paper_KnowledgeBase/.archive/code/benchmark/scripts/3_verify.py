#!/usr/bin/env python3
"""
Stage 3: Cross-verification — Cohen's Kappa + 衝突解決工作表。

讀取 queries.json 中已完成標註之樣本，計算：
  - 整體 Cohen's Kappa
  - 分類別 Kappa（exact_specification / intent_oriented）
  - 列出所有衝突樣本，輸出 conflict_resolution.csv 供第三人仲裁
"""
import csv
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
ANNO = DATA / "annotations"


def cohens_kappa(labels_a, labels_b):
    """雙標註者多類別 Cohen's Kappa（無序類別）。"""
    assert len(labels_a) == len(labels_b)
    n = len(labels_a)
    if n == 0:
        return float("nan")

    classes = sorted(set(labels_a) | set(labels_b))
    obs_agree = sum(1 for a, b in zip(labels_a, labels_b) if a == b) / n

    cnt_a = Counter(labels_a)
    cnt_b = Counter(labels_b)
    exp_agree = sum((cnt_a[c] / n) * (cnt_b[c] / n) for c in classes)

    if exp_agree == 1.0:
        return 1.0
    return (obs_agree - exp_agree) / (1 - exp_agree)


def kappa_interpretation(k):
    if k < 0:
        return "poor"
    if k < 0.20:
        return "slight"
    if k < 0.40:
        return "fair"
    if k < 0.60:
        return "moderate"
    if k < 0.80:
        return "substantial"
    return "almost perfect"


def main():
    import sys
    apply_arb = "--apply-arbitration" in sys.argv
    queries = json.loads((DATA / "queries.json").read_text(encoding="utf-8"))

    # 收集已雙標註之樣本
    rated = [q for q in queries
             if q["expert_verification"]["annotator_A"] is not None
             and q["expert_verification"]["annotator_B"] is not None]

    if not rated:
        print("⚠️  尚無雙標註樣本。請先完成 stage 2。")
        return

    a_labels = [q["expert_verification"]["annotator_A"] for q in rated]
    b_labels = [q["expert_verification"]["annotator_B"] for q in rated]

    # 整體 Kappa
    overall_k = cohens_kappa(a_labels, b_labels)
    print(f"\n📊 雙標註者一致性分析（n={len(rated)}）")
    print(f"   整體 Cohen's Kappa = {overall_k:.4f}  [{kappa_interpretation(overall_k)}]")

    # 分類 Kappa
    for cat in ("exact_specification", "intent_oriented"):
        sub = [q for q in rated if q["category"] == cat]
        if not sub:
            continue
        ka = [q["expert_verification"]["annotator_A"] for q in sub]
        kb = [q["expert_verification"]["annotator_B"] for q in sub]
        k = cohens_kappa(ka, kb)
        print(f"   {cat:25s}  κ = {k:.4f}  [{kappa_interpretation(k)}]  (n={len(sub)})")

    # 一致性檢驗門檻
    print()
    if overall_k >= 0.75:
        print(f"✅ 整體 κ = {overall_k:.4f} ≥ 0.75 — 達 substantial agreement，符合標準")
    else:
        print(f"⚠️  整體 κ = {overall_k:.4f} < 0.75 — 未達標，建議：")
        print("    1. 檢視衝突樣本，找出常見分歧模式")
        print("    2. 補強標註指南，讓兩位標註者重標衝突部分")

    # 輸出衝突解決工作表（除非 --apply-arbitration，避免覆蓋已填好的仲裁）
    conflicts = [q for q in rated if q["expert_verification"]["status"] == "conflict"]
    if conflicts and not apply_arb:
        path = ANNO / "conflict_resolution.csv"
        with path.open("w", encoding="utf-8", newline="") as f:
            w = csv.writer(f)
            w.writerow(["id", "category", "query",
                        "annotator_A_choice", "annotator_B_choice",
                        "arbitrator_decision", "reason"])
            for q in conflicts:
                ev = q["expert_verification"]
                w.writerow([q["id"], q["category"], q["query"],
                            ev["annotator_A"], ev["annotator_B"], "", ""])
        print(f"\n📝 已輸出 {len(conflicts)} 筆衝突樣本至 {path.relative_to(ROOT)}")
        print("   請第三人仲裁後填回 arbitrator_decision 與 reason 欄位")
        print("   完成後執行：python scripts/3_verify.py --apply-arbitration")

    # 套用仲裁結果
    if apply_arb:
        path = ANNO / "conflict_resolution.csv"
        if not path.exists():
            print("⚠️  找不到衝突解決檔，先跑無 flag 版本")
            return
        by_id = {q["id"]: q for q in queries}
        applied = 0
        with path.open(encoding="utf-8") as f:
            for row in csv.DictReader(f):
                qid = row["id"]
                decision = row["arbitrator_decision"].strip()
                if not decision or qid not in by_id:
                    continue
                by_id[qid]["expert_verification"]["final_gt"] = decision
                by_id[qid]["expert_verification"]["status"] = "arbitrated"
                applied += 1
        (DATA / "queries.json").write_text(
            json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        print(f"\n✅ 已套用 {applied} 筆仲裁結果")


if __name__ == "__main__":
    main()
