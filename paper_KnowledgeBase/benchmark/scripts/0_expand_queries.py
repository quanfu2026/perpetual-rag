#!/usr/bin/env python3
"""
Stage 0 (optional): LLM-driven query expansion via Claude Haiku 4.5.

Reads queries.json, expands `query_template` (機械模板) → 自然語句 `query`
based on `expansion_hint`. Writes back with `expanded: true` flag.

Features:
  - Async concurrency (10 parallel requests)
  - Prompt caching on system prompt (saves ~90% on repeated input tokens)
  - Resumable: skips already-expanded queries
  - Periodic save every 50 queries (crash-safe)
  - Cost estimation

Usage:
  export ANTHROPIC_API_KEY="sk-ant-..."
  python scripts/0_expand_queries.py              # full run (1000 queries)
  python scripts/0_expand_queries.py --limit=10   # test run (10 queries)
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path

import anthropic

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"

# ── load API key from .env if not already in env ──
def _load_dotenv():
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        v = v.strip().strip('"').strip("'")
        os.environ.setdefault(k.strip(), v)

_load_dotenv()
MODEL = "claude-haiku-4-5"
MAX_TOKENS = 250
CONCURRENCY = 10

SYSTEM_PROMPT = """你是一位電商客服語料工程師，任務是把機械化的查詢模板改寫為真實使用者會打的中文自然語句。

規則：
1. 完全保留模板中的關鍵實體（型號、規格名、情境、需求關鍵字）— 這些是 ground truth 的字面錨點
2. 加入自然口語的修辭（例如「請問」、「想請教」），但不要改變查詢意圖
3. 長度控制在 15–60 個中文字
4. 不要加入任何模板中沒有的新實體（不可虛構新的型號或規格）
5. 直接輸出改寫後的查詢一行，不要加任何解釋、編號、引號或前綴

範例：
模板：「型號 XYZ-9000 的最大續航 是多少？」
擴寫提示：保留型號『XYZ-9000』與規格名『最大續航』之精確字面
請問 XYZ-9000 這款的最大續航時間是多久？想了解一下。

模板：「我想要找一台適合在 山區地形 使用、操作簡單的 空拍機。」
擴寫提示：保留情境『山區地形』與需求『操作簡單』之語意
朋友最近想入門空拍，主要在山區地形拍，希望操作簡單一點，有什麼推薦嗎？"""

USER_TEMPLATE = """模板：「{query_template}」
擴寫提示：{expansion_hint}

請直接輸出改寫後的查詢："""

PREFIXES_TO_STRIP = ["→", "改寫後：", "查詢：", "改寫：", "擴寫：", "「", "」"]


def clean_output(text: str) -> str:
    text = text.strip().split("\n")[0].strip()
    for p in PREFIXES_TO_STRIP:
        if text.startswith(p):
            text = text[len(p):].strip()
        if text.endswith(p):
            text = text[: -len(p)].strip()
    return text


async def expand_one(client, query, semaphore, retries=4):
    async with semaphore:
        prompt = USER_TEMPLATE.format(
            query_template=query["query_template"],
            expansion_hint=query["expansion_hint"],
        )
        for attempt in range(retries):
            try:
                resp = await client.messages.create(
                    model=MODEL,
                    max_tokens=MAX_TOKENS,
                    system=[{
                        "type": "text",
                        "text": SYSTEM_PROMPT,
                        "cache_control": {"type": "ephemeral"},
                    }],
                    messages=[{"role": "user", "content": prompt}],
                )
                expanded = clean_output(resp.content[0].text)
                if not expanded:
                    raise ValueError("empty response")
                return query["id"], expanded, resp.usage
            except (anthropic.RateLimitError, anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                wait = 2 ** attempt
                if attempt == retries - 1:
                    print(f"   ❌ {query['id']}: gave up after {retries} retries ({type(e).__name__})")
                    return query["id"], None, None
                await asyncio.sleep(wait)
            except Exception as e:
                print(f"   ❌ {query['id']}: {type(e).__name__}: {e}")
                return query["id"], None, None
        return query["id"], None, None


async def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("⚠️  ANTHROPIC_API_KEY 未設定")
        print("   export ANTHROPIC_API_KEY='sk-ant-...'")
        sys.exit(1)

    queries_path = DATA / "queries.json"
    queries = json.loads(queries_path.read_text(encoding="utf-8"))

    pending = [q for q in queries if not q.get("expanded")]
    if not pending:
        print("✅ 所有查詢已擴寫完成。")
        return

    limit = None
    for arg in sys.argv[1:]:
        if arg.startswith("--limit="):
            limit = int(arg.split("=")[1])
    if limit:
        pending = pending[:limit]
        print(f"⚙️  限制處理前 {limit} 筆（測試模式）")

    print(f"📋 待擴寫：{len(pending)} 筆，模型：{MODEL}，並行：{CONCURRENCY}")

    client = anthropic.AsyncAnthropic()
    semaphore = asyncio.Semaphore(CONCURRENCY)
    by_id = {q["id"]: q for q in queries}

    start = time.time()
    total_input = total_output = total_cache_r = total_cache_c = 0
    done = success = 0

    tasks = [expand_one(client, q, semaphore) for q in pending]
    for coro in asyncio.as_completed(tasks):
        qid, expanded, usage = await coro
        done += 1
        if expanded:
            success += 1
            by_id[qid]["query"] = expanded
            by_id[qid]["expanded"] = True
        if usage:
            total_input += usage.input_tokens
            total_output += usage.output_tokens
            total_cache_r += getattr(usage, "cache_read_input_tokens", 0) or 0
            total_cache_c += getattr(usage, "cache_creation_input_tokens", 0) or 0

        if done % 50 == 0 or done == len(pending):
            elapsed = time.time() - start
            rate = done / elapsed if elapsed > 0 else 0
            eta = (len(pending) - done) / rate if rate > 0 else 0
            print(f"   [{done}/{len(pending)}] {success} ok | "
                  f"{elapsed:.0f}s elapsed, ~{eta:.0f}s left | "
                  f"in={total_input:,}, out={total_output:,}, cache_r={total_cache_r:,}")
            queries_path.write_text(
                json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8"
            )

    queries_path.write_text(
        json.dumps(queries, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # Haiku 4.5 pricing: $1/MTok in, $5/MTok out, $0.10/MTok cache_r, $1.25/MTok cache_c
    cost = (
        (total_input - total_cache_c) * 1.00e-6
        + total_output * 5.00e-6
        + total_cache_r * 0.10e-6
        + total_cache_c * 1.25e-6
    )
    print(f"\n✅ 完成 {success}/{len(pending)} 筆，耗時 {time.time()-start:.0f}s")
    print(f"   tokens: input={total_input:,} (cache_r={total_cache_r:,}, cache_c={total_cache_c:,}), output={total_output:,}")
    print(f"   estimated cost: ${cost:.4f} USD")


if __name__ == "__main__":
    asyncio.run(main())
