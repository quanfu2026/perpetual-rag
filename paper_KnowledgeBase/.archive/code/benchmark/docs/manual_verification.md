---
title: 實驗程式人工驗證流程（Manual Verification Guide）
type: research
status: draft
tags: [verification, reproducibility, qa]
source: Claude-Code
project: paper_KnowledgeBase
created: 2026-05-04
last_updated: 2026-05-04
version: 1.0.0
---

# 🔬 實驗 Pipeline 人工驗證流程

照這個 SOP 走一遍，你就能親眼確認**每個 stage 的數字、邏輯、輸出**都正確。
全程約 15–20 分鐘。每步都有「**預期看到**」+「**問題排除**」兩段。

---

## 📋 前置檢查（5 分鐘）

### Step 0.1：檢查目錄與依賴

```bash
cd ~/paper_KnowledgeBase/benchmark
ls -la
```

**預期看到**：
```
README.md
docs/        scripts/      data/        .env
```

**檢查 venv 與依賴**：
```bash
~/paper_KnowledgeBase/.venv/bin/python3 -c "
import jieba, rank_bm25, sklearn, datasets, matplotlib
print('OK: 所有依賴可用')
"
```

**問題排除**：缺哪個套件就 `~/paper_KnowledgeBase/.venv/bin/pip install <套件>`

---

### Step 0.2：檢查 corpus 與 queries 結構

```bash
~/paper_KnowledgeBase/.venv/bin/python3 -c "
import json
c = json.load(open('data/corpus.json'))
q = json.load(open('data/queries.json'))
print(f'corpus: {len(c)} docs')
print(f'queries: {len(q)} queries')
print(f'  dev:  {sum(1 for x in q if x[\"subset\"]==\"dev\")}')
print(f'  test: {sum(1 for x in q if x[\"subset\"]==\"test\")}')
print(f'  has GT: {sum(1 for x in q if x[\"expert_verification\"][\"final_gt\"])}')
"
```

**預期看到**：
```
corpus: 2000 docs
queries: 1000 queries
  dev:  500
  test: 500
  has GT: 1000
```

---

## 🧪 Step 1：手動驗證 corpus 對應

挑一筆查詢，親眼確認 ground truth 文件確實是合理的答案。

```bash
~/paper_KnowledgeBase/.venv/bin/python3 -c "
import json, random
random.seed(7)
qs = json.load(open('data/queries.json'))
corpus = {d['doc_id']: d for d in json.load(open('data/corpus.json'))}
# 隨機抽 5 筆
for q in random.sample(qs, 5):
    gt_doc = corpus[q['expert_verification']['final_gt']]
    print(f'\\n[{q[\"id\"]}]')
    print(f'  Query:    {q[\"query\"]}')
    print(f'  GT doc:   {gt_doc[\"description\"][:80]}')
"
```

**人工檢查清單**（應該都打勾）：

- [ ] Query 看起來像真人會打的搜尋關鍵字
- [ ] GT doc 的描述跟 query 相關（同類商品、同關鍵字）
- [ ] 沒有亂碼、沒有空欄位

**問題排除**：
- 如果 GT 看起來不對 → 表示 C-MTEB qrel 有問題（不太可能，但可以加註記）
- 如果 query 是空字串 → 重跑 `scripts/6_import_cmteb_ecom.py`

---

## 🧪 Step 2：手動驗證檢索器運作

直接呼叫檢索器，看它對一筆查詢回傳什麼 Top-5。

```bash
~/paper_KnowledgeBase/.venv/bin/python3 << 'EOF'
import json, sys
sys.path.insert(0, 'scripts')
from importlib import import_module
ev = import_module('4_evaluate' if False else '_eval_local')  # workaround
EOF

# 或直接用內嵌方式：
~/paper_KnowledgeBase/.venv/bin/python3 << 'EOF'
import json
import sys
sys.path.insert(0, 'scripts')

# 動態載入 4_evaluate.py 中的類別
import importlib.util
spec = importlib.util.spec_from_file_location("ev", "scripts/4_evaluate.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

corpus, queries = ev.load()
test = [q for q in queries if q['subset'] == 'test']
retriever = ev.HybridRetriever(corpus)

# 跑一筆
q = test[0]
gt = q['expert_verification']['final_gt']
top5 = retriever.topk(q['query'], alpha=0.1, k=5)

print(f"Query: {q['query']}")
print(f"GT:    {gt}")
print(f"Top-5 (α=0.1):")
for i, did in enumerate(top5, 1):
    mark = "✅" if did == gt else "  "
    doc = next(d for d in corpus if d['doc_id'] == did)
    print(f"  {mark} {i}. [{did}] {doc['description'][:60]}")
EOF
```

**預期看到**：5 筆 Top-5 結果，其中（很可能）有一筆是 GT，並標 ✅

**人工檢查**：
- [ ] Top-5 各筆看起來都跟 query 相關（不是完全亂噴）
- [ ] 如果 GT 在 Top-5，✅ 標在合理位置（通常 Top-1~3）
- [ ] 如果 GT 不在 Top-5，看其他 5 筆是否語意相近（合理錯誤）vs 完全無關（系統有 bug）

**問題排除**：
- 全部 Top-5 都跟 query 無關 → 檢查 jieba 分詞是否正常運作
- 永遠 Top-1 是 GT（百發百中）→ 可能有 data leakage，需檢查

---

## 🧪 Step 3：手動驗證 α 掃描

挑一個固定的 α 值（例如 α=0.5），手動跑 10 筆查詢，記錄 Hit@5。

```bash
~/paper_KnowledgeBase/.venv/bin/python3 << 'EOF'
import importlib.util, json
spec = importlib.util.spec_from_file_location("ev", "scripts/4_evaluate.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

corpus, queries = ev.load()
dev = [q for q in queries if q['subset'] == 'dev'][:10]
retriever = ev.HybridRetriever(corpus)

for alpha in [0.0, 0.5, 1.0]:
    hits = 0
    for q in dev:
        top5 = retriever.topk(q['query'], alpha, 5)
        if q['expert_verification']['final_gt'] in top5:
            hits += 1
    print(f"α={alpha}: Hit@5 = {hits}/10 = {hits*10}%")
EOF
```

**預期看到**（順序大致如此）：
```
α=0.0: Hit@5 ≈ 8/10 (80%)   ← Dense only
α=0.5: Hit@5 ≈ 8-9/10        ← Hybrid
α=1.0: Hit@5 ≈ 6-8/10        ← BM25 only（通常稍差）
```

**人工檢查**：
- [ ] α=0（Dense only）的 Hit@5 顯著高於 α=1（BM25 only） — 因為這是中文短查詢
- [ ] α=0.1~0.5 中間值通常最佳
- [ ] 如果 α=1 反而最好，表示語料有大量字面匹配場景，需檢查

---

## 🧪 Step 4：手動驗證統計檢定

McNemar 檢定的核心是 contingency table。手算 10 筆驗證腳本算對了：

```bash
~/paper_KnowledgeBase/.venv/bin/python3 << 'EOF'
import json
R = json.load(open('data/evaluation_results.json'))
pq = R['per_query_correct_test']
T_name = next(c for c in pq if c.startswith('T '))
B2 = "B2 (BM25 only, α=1)"

# 前 20 筆的對應關係
print(f"{'idx':>4}  {'T':>3}  {'B2':>3}  說明")
both = T_only = B_only = neither = 0
for i, (t, b) in enumerate(zip(pq[T_name][:20], pq[B2][:20])):
    note = ""
    if t==1 and b==0: note = "T✓ B✗"; T_only+=1
    elif t==0 and b==1: note = "T✗ B✓"; B_only+=1
    elif t==1 and b==1: note = "都對"; both+=1
    else: note = "都錯"; neither+=1
    print(f"{i:>4}  {t:>3}  {b:>3}  {note}")

print(f"\n前 20 筆統計：")
print(f"  T✓ B✗ (b): {T_only}")
print(f"  T✗ B✓ (c): {B_only}")
print(f"  都對:      {both}")
print(f"  都錯:      {neither}")
EOF
```

**人工檢查**：
- [ ] b（T 對 B 錯）應該明顯多於 c（T 錯 B 對） — 表示 T 比 B 強
- [ ] 大部分樣本是「都對」 — 因為兩者都很強
- [ ] 「都錯」的樣本可以拿來做 error analysis

---

## 🧪 Step 5：手動驗證 Hit@K 計算

直接驗證 Hit@K 算法寫對了：

```bash
~/paper_KnowledgeBase/.venv/bin/python3 << 'EOF'
# 模擬 5 筆查詢的 Top-5 結果
top5_list = [
    ['A', 'B', 'C', 'D', 'E'],  # query 1
    ['B', 'A', 'C', 'D', 'E'],  # query 2
    ['X', 'Y', 'A', 'D', 'E'],  # query 3
    ['X', 'Y', 'Z', 'W', 'A'],  # query 4
    ['X', 'Y', 'Z', 'W', 'V'],  # query 5
]
gts = ['A', 'A', 'A', 'A', 'A']

# 手算
print("手算驗證：")
print("  Hit@1: 1, 0, 0, 0, 0 → 1/5 = 20%")
print("  Hit@3: 1, 1, 1, 0, 0 → 3/5 = 60%")
print("  Hit@5: 1, 1, 1, 1, 0 → 4/5 = 80%")
print("  MRR:   1/1, 1/2, 1/3, 1/5, 0 = (1+0.5+0.333+0.2+0)/5 = 0.4067")

# 程式碼計算
def hit_at_k(pred, gt, k):
    return 1 if gt in pred[:k] else 0
def rr(pred, gt):
    for i, p in enumerate(pred, 1):
        if p == gt: return 1/i
    return 0

print("\n程式計算：")
for k in [1, 3, 5]:
    h = sum(hit_at_k(t, g, k) for t, g in zip(top5_list, gts)) / len(gts)
    print(f"  Hit@{k}: {h:.2%}")
mrr = sum(rr(t, g) for t, g in zip(top5_list, gts)) / len(gts)
print(f"  MRR:   {mrr:.4f}")

print("\n✅ 兩邊一致則邏輯正確")
EOF
```

**預期看到**：手算和程式算數字一致

---

## 🧪 Step 6：端到端 sanity check

跑完整流水線，從頭到尾每個 stage 看一眼：

```bash
# Stage 4：評估
~/paper_KnowledgeBase/.venv/bin/python3 scripts/4_evaluate.py

# Stage 5：統計
~/paper_KnowledgeBase/.venv/bin/python3 scripts/5_statistics.py

# Stage 7：產圖
~/paper_KnowledgeBase/.venv/bin/python3 scripts/7_plot.py
```

**人工檢查 4 個關鍵數字**：

| 預期值 | 實際看到 | OK? |
|-------|---------|-----|
| best α* = 0.0 ~ 0.3 | ___ | □ |
| T (Hybrid) Hit@5 ≈ 84% | ___ | □ |
| T vs Random p < 0.001 *** | ___ | □ |
| T vs B2 (BM25) p < 0.001 *** | ___ | □ |

---

## 🧪 Step 7：人工抽查 error analysis（重要！）

找 5 筆 T 答錯的查詢，看它錯成什麼樣 — 這是寫論文 §VI-D「Error Analysis」的素材。

```bash
~/paper_KnowledgeBase/.venv/bin/python3 << 'EOF'
import importlib.util, json
spec = importlib.util.spec_from_file_location("ev", "scripts/4_evaluate.py")
ev = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ev)

corpus, queries = ev.load()
corpus_dict = {d['doc_id']: d for d in corpus}
test = [q for q in queries if q['subset'] == 'test']

R = json.load(open('data/evaluation_results.json'))
T_name = next(c for c in R['per_query_correct_test'] if c.startswith('T '))
T_correct = R['per_query_correct_test'][T_name]
test_ids = R['test_query_ids']

retriever = ev.HybridRetriever(corpus)

# 找 T 答錯的前 5 筆
errors = []
for q, correct in zip(test, T_correct):
    if correct == 0:
        errors.append(q)
    if len(errors) >= 5:
        break

print(f"=== T 答錯的 5 筆樣本（用於 error analysis）===\n")
for q in errors:
    gt = q['expert_verification']['final_gt']
    top5 = retriever.topk(q['query'], 0.1, 5)
    print(f"[{q['id']}]")
    print(f"  Query:  {q['query']}")
    print(f"  GT doc: {corpus_dict[gt]['description'][:60]}")
    print(f"  T 預測 Top-1: {corpus_dict[top5[0]]['description'][:60]}")
    print(f"  GT 在 Top-K 的位置: ", end="")
    full_top = retriever.topk(q['query'], 0.1, 50)
    if gt in full_top:
        print(f"#{full_top.index(gt)+1}")
    else:
        print("不在 Top-50（嚴重失敗）")
    print()
EOF
```

**人工檢查 / 分析**：

對每筆答錯的查詢，分類錯誤類型：

| 錯誤類型 | 描述 | 範例情境 |
|---------|------|---------|
| **A. Query 太模糊** | 多個 doc 都合理 | "中國風"、"高品質" |
| **B. 字面被相似商品誘導** | 前綴相似 | "iPhone 15" 對到 "iPhone 15 Pro" |
| **C. GT 描述太短** | 缺乏字詞 | doc 只有 5 字 |
| **D. 同義詞無法對應** | Dense 模型沒抓到 | "風扇" vs "電風扇" |
| **E. 標註可能本身有問題** | 看起來別的 doc 更合理 | qrel 主觀差異 |

把分類結果寫進論文 §VI-D 即可。每類抽 1–2 個範例就夠。

---

## ✅ 全部跑完代表

1. ✅ 你**親眼**看過實驗每個環節
2. ✅ 數字與邏輯**手動驗證過**
3. ✅ 你能**回答 reviewer**任何「你怎麼確定 X」的提問
4. ✅ Error analysis 素材**已備齊**
5. ✅ 寫論文時可以**從容**引用 protocol.md + final_report.md

如果某 step 失敗，**先別急著找 reviewer 解釋**，回報給我，我幫你 debug。

---

## 🆘 常見問題排除速查

| 症狀 | 解法 |
|------|------|
| ImportError | `~/paper_KnowledgeBase/.venv/bin/pip install <套件>` |
| Hit@5 為 0 | 檢查 final_gt 是否填好（`scripts/3_verify.py --apply-arbitration`） |
| α 掃描全部一樣 | 檢查 BM25 / TF-IDF 是否正常運作（看 Step 2）|
| 中文字型不顯示 | matplotlib 改用 PingFang TC 或 Heiti TC |
| 數字不穩定 | 檢查 random.seed=42 是否固定 |
