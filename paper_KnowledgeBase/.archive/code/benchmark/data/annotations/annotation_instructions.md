# 標註指南

## 任務
對每筆查詢（query 欄位），從 200 篇商品語料庫（`data/corpus.json`）中
選出最符合該查詢之 ground truth 商品，將其 doc_id 填入 `annotated_doc_id` 欄位。

## 候選查詢範例
```
  - doc_drone_001: AeroPro-S2-001
  - doc_drone_002: AeroPro-S2-002
  - doc_drone_003: XYZ-9000-003
  - doc_drone_004: SkyHunter-V3-004
  - doc_drone_005: AeroPro-S2-005
  - ...（共 200 筆，請參考 data/corpus.json）
```

## 規則
1. 每筆查詢必須有一個確定的 doc_id 答案
2. 若無任何商品符合，填寫 `NONE`
3. 若有多個合理候選，選**最匹配**者（依字面或語意）並在 notes 欄位簡述理由
4. 標註過程中**禁止與另一位標註者討論**

## 一致性目標
- Cohen's Kappa ≥ 0.75（substantial agreement）
- 若 κ < 0.75，需重新檢視標註指南並重標衝突部分

## 完成後
將填好的 CSV 放回 `data/annotations/annotator_{A,B}.csv`，
然後執行：`python scripts/2_annotate.py import`
