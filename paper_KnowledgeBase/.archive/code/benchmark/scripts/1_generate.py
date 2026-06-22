#!/usr/bin/env python3
"""
Stage 1: Generate corpus + queries skeleton.

產生：
  - data/corpus.json：200 篇商品文檔（70 空拍機 + 70 農機 + 60 家電）
  - data/queries.json：1000 筆查詢（500 dev + 500 test，50/50 EXS/INT）

查詢內容為模板生成，需後續以 LLM 或人工擴寫為自然語句（見 data/queries.json
之 `query_template` 與 `expansion_hint` 欄位）。
"""
import json
import random
from pathlib import Path

random.seed(42)

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
DATA.mkdir(exist_ok=True)


# ── 商品語料庫 ──────────────────────────────────────────────────

CATEGORIES = {
    "drone": {
        "count": 70,
        "models": ["XYZ-9000", "AeroPro-S2", "SkyHunter-V3", "PhantomLite-X",
                   "DroneMax-7", "FlyMaster-Pro", "SkyView-Z1", "WindRider-Air"],
        "specs_pool": [
            ("最大續航", ["18 分鐘", "25 分鐘", "32 分鐘", "45 分鐘"]),
            ("最大風阻等級", ["4 級", "5 級", "6 級", "7 級"]),
            ("相機解析度", ["4K", "5.1K", "6K HDR", "8K"]),
            ("最大飛行高度", ["120 公尺", "300 公尺", "500 公尺"]),
            ("適用情境", ["山區地形", "海邊強風", "都市低空", "農田巡檢"]),
        ],
    },
    "agri": {
        "count": 70,
        "models": ["AgriSense-A1", "FarmBot-X", "CropGuard-7", "SoilMon-Pro",
                   "GreenIoT-S", "HarvestEye", "PlantWatch-V2"],
        "specs_pool": [
            ("感測類型", ["土壤濕度", "葉面溫度", "病蟲害影像", "光照強度"]),
            ("覆蓋面積", ["0.5 公頃", "1 公頃", "5 公頃", "10 公頃"]),
            ("通訊協定", ["LoRa", "NB-IoT", "WiFi", "Zigbee"]),
            ("電池續航", ["30 天", "90 天", "180 天", "1 年"]),
            ("適用作物", ["稻米", "蔬菜", "果樹", "茶葉"]),
        ],
    },
    "iot": {
        "count": 60,
        "models": ["SmartHub-H1", "EcoSense-G", "AirQ-Pro", "VoiceMate-V",
                   "HomeGuard-S2", "LightCtrl-X"],
        "specs_pool": [
            ("功能", ["環境監控", "能耗統計", "聲控", "防盜偵測", "燈光調節"]),
            ("Hub 整合", ["HomeKit", "Google Home", "Matter", "Alexa"]),
            ("連線方式", ["WiFi 6", "藍牙 5.2", "Thread"]),
            ("電源", ["USB-C", "AC 110V", "電池"]),
        ],
    },
}


def gen_product(category: str, idx: int) -> dict:
    cfg = CATEGORIES[category]
    model = random.choice(cfg["models"]) + f"-{idx:03d}"
    specs = {}
    for spec_name, spec_values in cfg["specs_pool"]:
        specs[spec_name] = random.choice(spec_values)
    description = (
        f"{model} 是一款專為「{specs.get('適用情境', specs.get('適用作物', '一般用途'))}」"
        f"設計的{category} 產品。核心規格如下：" +
        "；".join(f"{k}：{v}" for k, v in specs.items()) +
        f"。價格區間：{random.choice(['NT$5,000', 'NT$12,000', 'NT$28,000', 'NT$48,000'])}。"
    )
    return {
        "doc_id": f"doc_{category}_{idx:03d}",
        "category": category,
        "model": model,
        "specs": specs,
        "description": description,
    }


def build_corpus():
    corpus = []
    counter = {"drone": 0, "agri": 0, "iot": 0}
    for cat, cfg in CATEGORIES.items():
        for i in range(1, cfg["count"] + 1):
            counter[cat] += 1
            corpus.append(gen_product(cat, i))
    print(f"[corpus] 已生成 {len(corpus)} 篇商品（{counter}）")
    (DATA / "corpus.json").write_text(
        json.dumps(corpus, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return corpus


# ── 查詢骨架 ────────────────────────────────────────────────────

EXACT_TEMPLATES = [
    "型號 {model} 的 {spec_name} 是多少？",
    "{model} 的 {spec_name} 規格為何？",
    "請問 {model} 支援的 {spec_name} 是什麼？",
    "我想查 {model} 這款的 {spec_name}。",
]

INTENT_TEMPLATES = [
    "我想要找一台適合在 {scenario} 使用、{requirement}的 {category_zh}。",
    "推薦一款 {scenario} 場景下、{requirement}的 {category_zh}。",
    "什麼 {category_zh} 適合 {scenario} 又能 {requirement}？",
    "想買 {category_zh}，主要用在 {scenario}，希望 {requirement}。",
]

CAT_ZH = {"drone": "空拍機", "agri": "農業感測器", "iot": "智慧家電"}

SCENARIOS = {
    "drone": ["山區地形", "海邊強風", "都市低空", "農田巡檢", "夜間拍攝", "婚禮跟拍"],
    "agri": ["稻田監測", "果園管理", "溫室環境", "茶園採收期", "山坡地作物"],
    "iot": ["公寓套房", "獨棟別墅", "辦公室", "出租套房", "長輩居住空間"],
}

REQUIREMENTS = {
    "drone": ["操作簡單", "續航長", "抗風強", "影像穩定", "預算內最划算"],
    "agri": ["低耗電", "雲端可看", "雨季耐用", "資料即時"],
    "iot": ["安裝簡單", "支援語音", "省電", "跨品牌整合"],
}


def gen_queries(corpus):
    queries = []
    qid = 0
    for subset_idx, subset in enumerate(["dev", "test"]):
        for i in range(500):
            qid += 1
            is_exact = (i % 2 == 0)
            category = random.choice(list(CATEGORIES.keys()))
            gt_doc = random.choice([d for d in corpus if d["category"] == category])

            if is_exact:
                spec_name = random.choice(list(gt_doc["specs"].keys()))
                template = random.choice(EXACT_TEMPLATES)
                query_template = template.format(
                    model=gt_doc["model"], spec_name=spec_name
                )
                expansion_hint = (
                    f"以自然口語改寫此查詢，保留型號『{gt_doc['model']}』與規格名"
                    f"『{spec_name}』之精確字面，可加入語氣詞、客服寒暄。"
                )
                category_label = "exact_specification"
            else:
                template = random.choice(INTENT_TEMPLATES)
                scenario = random.choice(SCENARIOS[category])
                requirement = random.choice(REQUIREMENTS[category])
                query_template = template.format(
                    scenario=scenario,
                    requirement=requirement,
                    category_zh=CAT_ZH[category],
                )
                expansion_hint = (
                    f"以自然口語改寫此查詢，保留情境『{scenario}』與需求"
                    f"『{requirement}』之語意，但避免直接出現產品型號。"
                )
                category_label = "intent_oriented"

            queries.append({
                "id": f"{subset}_{qid:04d}",
                "subset": subset,
                "category": category_label,
                "product_category": category,
                "query_template": query_template,
                "query": query_template,  # 預設等於 template，待 LLM 擴寫
                "expansion_hint": expansion_hint,
                "ground_truth_doc_id": gt_doc["doc_id"],
                "expert_verification": {
                    "annotator_A": None,
                    "annotator_B": None,
                    "status": "pending",
                    "final_gt": None,
                },
            })

    print(f"[queries] 已生成 {len(queries)} 筆查詢骨架")
    print(f"  - dev:  {sum(1 for q in queries if q['subset']=='dev')} 筆")
    print(f"  - test: {sum(1 for q in queries if q['subset']=='test')} 筆")
    print(f"  - exact_specification:  {sum(1 for q in queries if q['category']=='exact_specification')} 筆")
    print(f"  - intent_oriented:      {sum(1 for q in queries if q['category']=='intent_oriented')} 筆")

    (DATA / "queries.json").write_text(
        json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return queries


def main():
    corpus = build_corpus()
    queries = gen_queries(corpus)
    print(f"\n✅ Stage 1 完成。下一步：")
    print(f"   1. 以 LLM 將 query_template 擴寫為自然語句（更新 'query' 欄位）")
    print(f"   2. 執行 python scripts/2_annotate.py export")


if __name__ == "__main__":
    main()
