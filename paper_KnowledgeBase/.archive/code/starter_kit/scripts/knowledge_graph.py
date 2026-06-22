#!/usr/bin/env python3
"""
知識圖譜生成器
從 paper_KnowledgeBase 所有 .md 檔案的 [[雙向連結]] 萃取節點與邊，輸出三種格式：
  1. Graphviz DOT  → 圖表/知識圖譜.dot（可用 dot -Tpng 渲染）
  2. JSON          → 圖表/知識圖譜.json（可用 D3.js / vis.js 渲染）
  3. Obsidian Canvas → 圖表/知識圖譜.canvas（Obsidian 直接開啟互動）

執行方式：
  cd ~/paper_KnowledgeBase
  python3 scripts/knowledge_graph.py

可選參數：
  --output-dir   輸出目錄（預設：圖表/）
  --min-links    節點最少連結數才納入圖（預設：0）
  --no-canvas    不輸出 Canvas 格式
"""

import os
import re
import json
import math
import argparse
from pathlib import Path
from collections import defaultdict

VAULT = Path.home() / "paper_KnowledgeBase"

# 排除目錄
EXCLUDE_DIRS = {".venv", "scripts", ".git", "audio_files"}

# 排除檔案前綴（系統輸出報告）
EXCLUDE_PREFIXES = ("00_",)

# 節點分類顏色
NODE_COLORS = {
    "ref":     {"dot": "#4A90D9", "canvas": "#1565c0", "label": "參考文獻"},
    "chapter": {"dot": "#27AE60", "canvas": "#2e7d32", "label": "章節筆記"},
    "script":  {"dot": "#E74C3C", "canvas": "#c62828", "label": "腳本說明"},
    "meta":    {"dot": "#F39C12", "canvas": "#e65100", "label": "系統文件"},
    "diagram": {"dot": "#9B59B6", "canvas": "#6a1b9a", "label": "圖表"},
    "other":   {"dot": "#95A5A6", "canvas": "#424242", "label": "其他"},
}


def classify_node(filename: str) -> str:
    name = filename.lower()
    if name.startswith("ref_"):
        return "ref"
    if re.match(r"第[一二三四五六七八九十]+章", filename) or re.match(r"\d+\.", filename):
        return "chapter"
    if name in ("claude.md", "sessionhandoff.md", "index.md", "principles_manual.md"):
        return "meta"
    if "圖表" in filename or "mermaid" in name or "圖譜" in name:
        return "diagram"
    return "other"


def collect_nodes_and_edges(vault: Path):
    nodes = {}   # rel_path → {name, type, path}
    edges = []   # (src_rel, dst_name)

    wikilink_re = re.compile(r"\[\[([^\]|#]+?)(?:\|[^\]]+)?\]\]")

    for md_file in sorted(vault.rglob("*.md")):
        # 排除目錄
        parts = md_file.relative_to(vault).parts
        if any(p in EXCLUDE_DIRS for p in parts):
            continue
        # 排除系統報告
        if any(md_file.name.startswith(p) for p in EXCLUDE_PREFIXES):
            continue

        rel = str(md_file.relative_to(vault))
        name = md_file.stem
        ntype = classify_node(md_file.name)

        nodes[rel] = {"name": name, "type": ntype, "path": rel}

        try:
            text = md_file.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        for m in wikilink_re.finditer(text):
            target = m.group(1).strip()
            if target and target != name:
                edges.append((rel, target))

    return nodes, edges


def resolve_edges(nodes, edges):
    """將邊的目標名稱解析為節點 rel_path"""
    name_to_rel = {}
    for rel, info in nodes.items():
        name_to_rel[info["name"]] = rel
        # 也用不含副檔名的 rel 作為備用 key
        name_to_rel[Path(rel).stem] = rel

    resolved = []
    for src, dst_name in edges:
        dst_rel = name_to_rel.get(dst_name) or name_to_rel.get(Path(dst_name).stem)
        if dst_rel and dst_rel != src:
            resolved.append((src, dst_rel))

    # 去重
    return list(set(resolved))


def build_adjacency(nodes, edges):
    degree = defaultdict(int)
    for src, dst in edges:
        degree[src] += 1
        degree[dst] += 1
    return degree


# ── 輸出格式 ───────────────────────────────────────────────────────────────────

def write_dot(nodes, edges, degree, out_path: Path, min_links: int):
    active = {r for r, d in degree.items() if d >= min_links} | \
             {r for r in nodes if degree[r] >= min_links}

    lines = [
        'digraph KnowledgeGraph {',
        '  graph [rankdir=LR fontname="Helvetica" bgcolor="#1a1a2e"]',
        '  node  [style=filled fontname="Helvetica" fontsize=10 fontcolor=white]',
        '  edge  [color="#555555" arrowsize=0.6]',
    ]

    for rel, info in nodes.items():
        if rel not in active:
            continue
        color = NODE_COLORS[info["type"]]["dot"]
        label = info["name"].replace('"', '\\"')[:40]
        lines.append(f'  "{rel}" [label="{label}" fillcolor="{color}"]')

    for src, dst in edges:
        if src in active and dst in active:
            lines.append(f'  "{src}" -> "{dst}"')

    lines.append("}")
    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"✅ DOT  → {out_path}  ({len([r for r in nodes if r in active])} 節點, {len(edges)} 邊)")


def write_json(nodes, edges, degree, out_path: Path, min_links: int):
    active = {r for r in nodes if degree[r] >= min_links}

    node_list = []
    for rel, info in nodes.items():
        if rel not in active:
            continue
        node_list.append({
            "id": rel,
            "label": info["name"],
            "type": info["type"],
            "color": NODE_COLORS[info["type"]]["dot"],
            "degree": degree[rel],
        })

    edge_list = [
        {"from": src, "to": dst}
        for src, dst in edges
        if src in active and dst in active
    ]

    out_path.write_text(
        json.dumps({"nodes": node_list, "edges": edge_list}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )
    print(f"✅ JSON → {out_path}  ({len(node_list)} 節點, {len(edge_list)} 邊)")


def write_canvas(nodes, edges, degree, out_path: Path, min_links: int):
    active = {r for r in nodes if degree[r] >= min_links}

    # 按類型分組，圓形排列
    type_groups = defaultdict(list)
    for rel in active:
        type_groups[nodes[rel]["type"]].append(rel)

    canvas_nodes = []
    canvas_edges = []
    pos = {}

    type_list = list(type_groups.keys())
    R_outer = 1800  # 外圈半徑（類型）
    R_inner = 600   # 內圈半徑（節點）

    for ti, ntype in enumerate(type_list):
        angle_outer = (2 * math.pi * ti) / len(type_list)
        cx = R_outer * math.cos(angle_outer)
        cy = R_outer * math.sin(angle_outer)

        members = type_groups[ntype]
        for ni, rel in enumerate(members):
            angle_inner = (2 * math.pi * ni) / max(len(members), 1)
            x = cx + R_inner * math.cos(angle_inner)
            y = cy + R_inner * math.sin(angle_inner)
            pos[rel] = (x, y)

            label = nodes[rel]["name"][:50]
            color = NODE_COLORS[ntype]["canvas"]
            canvas_nodes.append({
                "id": rel,
                "type": "text",
                "text": f"**{label}**",
                "x": round(x),
                "y": round(y),
                "width": 200,
                "height": 60,
                "color": color,
            })

    edge_id = 0
    seen_edges = set()
    for src, dst in edges:
        if src not in active or dst not in active:
            continue
        key = tuple(sorted([src, dst]))
        if key in seen_edges:
            continue
        seen_edges.add(key)
        canvas_edges.append({
            "id": f"e{edge_id}",
            "fromNode": src,
            "fromSide": "right",
            "toNode": dst,
            "toSide": "left",
        })
        edge_id += 1

    canvas_data = {"nodes": canvas_nodes, "edges": canvas_edges}
    out_path.write_text(json.dumps(canvas_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ Canvas → {out_path}  ({len(canvas_nodes)} 節點, {len(canvas_edges)} 邊)")


# ── 統計摘要 ───────────────────────────────────────────────────────────────────

def print_summary(nodes, edges, degree):
    print("\n📊 知識圖譜統計摘要")
    print(f"   總節點數：{len(nodes)}")
    print(f"   總連結數：{len(edges)}")

    type_count = defaultdict(int)
    for info in nodes.values():
        type_count[info["type"]] += 1
    for ntype, count in sorted(type_count.items(), key=lambda x: -x[1]):
        label = NODE_COLORS[ntype]["label"]
        print(f"   {label}：{count} 個")

    top10 = sorted(degree.items(), key=lambda x: -x[1])[:10]
    print("\n🔗 連結最密集的前 10 個節點：")
    for rel, deg in top10:
        name = nodes[rel]["name"] if rel in nodes else rel
        print(f"   {deg:3d} 連結  {name}")


# ── 主程式 ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="知識圖譜生成器")
    parser.add_argument("--output-dir", default="圖表", help="輸出目錄（相對於 vault）")
    parser.add_argument("--min-links", type=int, default=0, help="節點最少連結數")
    parser.add_argument("--no-canvas", action="store_true", help="不輸出 Canvas 格式")
    args = parser.parse_args()

    out_dir = VAULT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("🔍 掃描知識庫...")
    nodes, raw_edges = collect_nodes_and_edges(VAULT)
    edges = resolve_edges(nodes, raw_edges)
    degree = build_adjacency(nodes, edges)

    print_summary(nodes, edges, degree)
    print()

    write_dot(nodes, edges, degree, out_dir / "知識圖譜.dot", args.min_links)
    write_json(nodes, edges, degree, out_dir / "知識圖譜.json", args.min_links)
    if not args.no_canvas:
        write_canvas(nodes, edges, degree, out_dir / "知識圖譜.canvas", args.min_links)

    print("\n📌 後續使用方式：")
    print("   Obsidian Canvas：直接在 Obsidian 開啟 圖表/知識圖譜.canvas")
    print("   靜態圖片：dot -Tpng 圖表/知識圖譜.dot -o 圖表/知識圖譜.png")
    print("   網頁互動：將 知識圖譜.json 搭配 D3.js / vis.js 渲染")


if __name__ == "__main__":
    main()
