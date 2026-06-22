#!/usr/bin/env python3
"""
Stage 0b (替代方案): 程式化模式擴寫。

不靠 LLM，以模板辨識 + 隨機自然語氣變體完成擴寫。
品質夠用、零成本、瞬間完成、entity 字面 100% 保留（不會幻覺）。

每個原始模板有 8-12 個自然變體，模擬真實使用者的多樣語氣。
"""
import json
import random
import re
from pathlib import Path

random.seed(42)
DATA = Path(__file__).resolve().parent.parent / "data"


# ── EXACT 規格類模板對應自然變體 ──────────────────────────────────

EXACT_SPECS = [
    # template 1: "型號 {model} 的 {spec} 是多少？"
    (
        re.compile(r"^型號 (\S+) 的 (.+?) 是多少？$"),
        [
            "請問 {model} 這款的 {spec} 是多少呢？",
            "想請教一下，{model} 的 {spec} 規格是？",
            "你好，{model} 這台的 {spec} 是多少？",
            "請問可以幫我查 {model} 的 {spec} 嗎？",
            "想問一下 {model} 的 {spec}，可以告知嗎？",
            "麻煩問一下 {model} 的 {spec} 數值，謝謝！",
            "{model} 的 {spec} 是多少？想了解一下。",
            "我想確認 {model} 這個型號的 {spec}。",
        ],
    ),
    # template 2: "{model} 的 {spec} 規格為何？"
    (
        re.compile(r"^(\S+) 的 (.+?) 規格為何？$"),
        [
            "想了解 {model} 的 {spec} 規格，可以說明一下嗎？",
            "請問 {model} 的 {spec} 是怎麼樣的呢？",
            "{model} 的 {spec} 是什麼樣的規格？",
            "你好，想請問 {model} 的 {spec} 詳細規格。",
            "可以幫我介紹一下 {model} 的 {spec} 嗎？",
            "想請教 {model} 在 {spec} 方面的規格。",
            "麻煩說明一下 {model} 的 {spec},謝謝。",
            "請問 {model} 在 {spec} 上有什麼規格？",
        ],
    ),
    # template 3: "請問 {model} 支援的 {spec} 是什麼？"
    (
        re.compile(r"^請問 (\S+) 支援的 (.+?) 是什麼？$"),
        [
            "請問一下，{model} 支援哪些 {spec}？",
            "想問 {model} 這款支援的 {spec} 有哪些?",
            "你好，{model} 在 {spec} 上支援什麼？",
            "麻煩問一下 {model} 支援的 {spec},謝謝。",
            "請教一下，{model} 的 {spec} 是哪一種？",
            "想了解 {model} 支援哪種 {spec}。",
            "{model} 這個型號支援的 {spec} 是什麼類型？",
        ],
    ),
    # template 4: "我想查 {model} 這款的 {spec}。"
    (
        re.compile(r"^我想查 (\S+) 這款的 (.+?)。$"),
        [
            "幫我查一下 {model} 的 {spec},謝謝！",
            "想問 {model} 這款的 {spec}, 麻煩了。",
            "請問可以告訴我 {model} 的 {spec} 嗎？",
            "我這邊想了解 {model} 的 {spec}，請幫忙查一下。",
            "{model} 的 {spec} 是多少？想查一下。",
            "你好，想請問 {model} 這台的 {spec}。",
            "麻煩查一下 {model} 的 {spec},謝謝。",
        ],
    ),
]


# ── INTENT 意圖類模板對應自然變體 ─────────────────────────────────

INTENT_PATTERNS = [
    # template 5: "我想要找一台適合在 {scenario} 使用、{requirement}的 {category}。"
    # group order: scenario, requirement, category
    (
        re.compile(r"^我想要找一台適合在 (?P<scenario>\S+) 使用、(?P<requirement>\S+)的 (?P<category>\S+)。$"),
        [
            "請問有沒有適合 {scenario}、又 {requirement} 的 {category} 推薦？",
            "想找一台 {category}，主要用在 {scenario}，希望 {requirement}, 有什麼推薦嗎？",
            "我這邊想買 {category}，要在 {scenario} 用，最重視 {requirement}，可以推薦嗎？",
            "請問 {scenario} 場景的 {category}，{requirement} 的有哪些選項？",
            "想請問 {scenario} 用的 {category}，{requirement} 是首要需求，謝謝。",
            "你好，想找一台在 {scenario} 表現好的 {category}，希望 {requirement}。",
            "麻煩推薦適合 {scenario}、且 {requirement} 的 {category},感謝。",
        ],
    ),
    # template 6: "推薦一款 {scenario} 場景下、{requirement}的 {category}。"
    # group order: scenario, requirement, category
    (
        re.compile(r"^推薦一款 (?P<scenario>\S+) 場景下、(?P<requirement>\S+)的 (?P<category>\S+)。$"),
        [
            "可以推薦 {scenario} 場景、{requirement} 的 {category} 嗎？",
            "想請大家推薦一款適合 {scenario}、{requirement} 的 {category}。",
            "請問 {scenario} 用、希望 {requirement} 的 {category} 怎麼挑？",
            "我在 {scenario} 場景需要 {requirement} 的 {category}，求推薦！",
            "麻煩推薦一下 {scenario} 用、{requirement} 的 {category},謝謝。",
            "想了解 {scenario} 場景下哪款 {category} 最 {requirement}？",
            "{scenario} 用 {category} 的話，{requirement} 的有什麼推薦？",
        ],
    ),
    # template 7: "什麼 {category} 適合 {scenario} 又能 {requirement}？"
    # group order: category, scenario, requirement
    (
        re.compile(r"^什麼 (?P<category>\S+) 適合 (?P<scenario>\S+) 又能 (?P<requirement>\S+)？$"),
        [
            "想問什麼 {category} 適合 {scenario},而且能 {requirement}？",
            "請問哪款 {category} 適合 {scenario} 用,還要能 {requirement}？",
            "{scenario} 場景能 {requirement} 的 {category}, 有推薦嗎？",
            "想找適合 {scenario}、又能 {requirement} 的 {category},請問有哪些？",
            "在 {scenario} 環境下還能 {requirement} 的 {category}, 有什麼選擇？",
            "什麼 {category} 在 {scenario} 表現好,又能 {requirement}?",
            "麻煩問一下,{scenario} 適用、{requirement} 的 {category} 有哪些?",
        ],
    ),
    # template 8: "想買 {category}，主要用在 {scenario}，希望 {requirement}。"
    # group order: category, scenario, requirement
    (
        re.compile(r"^想買 (?P<category>\S+)，主要用在 (?P<scenario>\S+)，希望 (?P<requirement>\S+)。$"),
        [
            "我想買 {category},主要在 {scenario} 使用,最希望 {requirement}, 求推薦！",
            "計畫入手一台 {category},場景是 {scenario},希望 {requirement},有建議嗎？",
            "想入手 {category},用途是 {scenario},最重視 {requirement}, 麻煩推薦。",
            "我打算買 {category},會用在 {scenario},想要 {requirement} 的款,請推薦。",
            "預計買一台 {category} 給 {scenario} 用,需要 {requirement},謝謝。",
            "考慮買 {category},主要在 {scenario},很在意 {requirement},怎麼選好?",
        ],
    ),
]


def expand_query(template: str, hint: str) -> str:
    """嘗試模式匹配；找到就隨機選一個自然變體填空，否則回傳原模板。"""
    # EXACT 類（兩個變數：model + spec）
    for pat, variants in EXACT_SPECS:
        m = pat.match(template)
        if m:
            model, spec = m.group(1), m.group(2)
            return random.choice(variants).format(model=model, spec=spec)

    # INTENT 類（命名群組）
    for pat, variants in INTENT_PATTERNS:
        m = pat.match(template)
        if m:
            return random.choice(variants).format(**m.groupdict())

    return template  # fallback


def main():
    queries = json.loads((DATA / "queries.json").read_text(encoding="utf-8"))
    pending = [q for q in queries if not q.get("expanded")]
    print(f"📋 待擴寫：{len(pending)} 筆")

    matched = unmatched = 0
    for q in queries:
        if q.get("expanded"):
            continue
        new_query = expand_query(q["query_template"], q["expansion_hint"])
        if new_query != q["query_template"]:
            matched += 1
            q["query"] = new_query
            q["expanded"] = True
        else:
            unmatched += 1

    (DATA / "queries.json").write_text(
        json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"✅ 模式匹配成功：{matched} 筆")
    if unmatched:
        print(f"⚠️  未匹配：{unmatched} 筆（保留原模板）")
    print(f"\n=== 隨機抽樣 5 筆查看品質 ===")
    expanded_samples = [q for q in queries if q.get("expanded")]
    for q in random.sample(expanded_samples, min(5, len(expanded_samples))):
        print(f"\n[{q['id']}] {q['category']}")
        print(f"  原模板：{q['query_template']}")
        print(f"  擴寫後：{q['query']}")


if __name__ == "__main__":
    main()
