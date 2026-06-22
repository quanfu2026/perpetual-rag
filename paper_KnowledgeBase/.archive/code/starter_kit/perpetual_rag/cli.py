#!/usr/bin/env python3
"""
perpetual-rag CLI 入口點

安裝後可用指令：
  perpetual-rag init    建立新知識庫
  perpetual-rag search  搜尋知識庫
  perpetual-rag audit   執行防幻覺掃描
  perpetual-rag graph   生成知識圖譜
  perpetual-rag bump    升版版本號
  perpetual-rag version 顯示版本資訊
"""

import sys
import argparse
from pathlib import Path

from perpetual_rag import __version__


def cmd_init(args):
    """建立新知識庫"""
    from perpetual_rag.scripts import init_vault
    init_vault.run(vault=args.vault, project=args.project)


def cmd_search(args):
    """搜尋知識庫"""
    vault = Path(args.vault).expanduser()
    sys.path.insert(0, str(vault / "scripts"))
    try:
        import bm25_search
        bm25_search.main_with_args(args.query, args.top)
    except ImportError:
        # fallback：直接執行 scripts/bm25_search.py
        import subprocess
        script = vault / "scripts" / "bm25_search.py"
        if script.exists():
            subprocess.run([sys.executable, str(script), args.query, "--top", str(args.top)])
        else:
            print(f"❌ 找不到 {script}，請先執行 perpetual-rag init")
            sys.exit(1)


def cmd_audit(args):
    """防幻覺掃描"""
    vault = Path(args.vault).expanduser()
    script = vault / "scripts" / "hallucination_guard.py"
    if not script.exists():
        print(f"❌ 找不到 {script}，請先執行 perpetual-rag init")
        sys.exit(1)
    import subprocess
    subprocess.run([sys.executable, str(script)])


def cmd_graph(args):
    """生成知識圖譜"""
    vault = Path(args.vault).expanduser()
    script = vault / "scripts" / "knowledge_graph.py"
    if not script.exists():
        print(f"❌ 找不到 {script}，請先執行 perpetual-rag init")
        sys.exit(1)
    import subprocess
    cmd = [sys.executable, str(script)]
    if args.min_links:
        cmd += ["--min-links", str(args.min_links)]
    subprocess.run(cmd)


def cmd_bump(args):
    """互動式升版"""
    import subprocess
    script = Path(__file__).parent.parent / "scripts" / "bump_version.py"
    if not script.exists():
        # 嘗試從知識庫找
        script = Path(args.vault).expanduser() / "scripts" / "bump_version.py"
    if script.exists():
        subprocess.run([sys.executable, str(script)])
    else:
        print("❌ 找不到 bump_version.py")
        sys.exit(1)


def cmd_version(args):
    """顯示版本"""
    print(f"perpetual-rag v{__version__}")
    print("論文：永續性知識管理：基於 Obsidian-NotebookLM-Claude Code 三層架構的防幻覺 RAG 框架")
    print("投稿：ILT2026 國際學習科技研討會")


# ── 主程式 ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="perpetual-rag",
        description="永續性知識管理系統 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
指令範例：
  perpetual-rag init --vault ~/my_vault --project "論文研究"
  perpetual-rag search "幻覺成因" --top 5
  perpetual-rag audit
  perpetual-rag graph
  perpetual-rag bump
        """
    )
    parser.add_argument("--vault", default="~/my_KnowledgeBase",
                        help="知識庫路徑（預設：~/my_KnowledgeBase）")

    subparsers = parser.add_subparsers(dest="command", metavar="指令")
    subparsers.required = True

    # init
    p_init = subparsers.add_parser("init", help="建立新知識庫")
    p_init.add_argument("--vault", default="~/my_KnowledgeBase")
    p_init.add_argument("--project", default="我的研究專案", help="專案名稱")
    p_init.set_defaults(func=cmd_init)

    # search
    p_search = subparsers.add_parser("search", help="BM25 搜尋知識庫")
    p_search.add_argument("query", help="搜尋關鍵字")
    p_search.add_argument("--top", type=int, default=5, help="回傳筆數（預設 5）")
    p_search.add_argument("--vault", default="~/my_KnowledgeBase")
    p_search.set_defaults(func=cmd_search)

    # audit
    p_audit = subparsers.add_parser("audit", help="執行防幻覺掃描")
    p_audit.add_argument("--vault", default="~/my_KnowledgeBase")
    p_audit.set_defaults(func=cmd_audit)

    # graph
    p_graph = subparsers.add_parser("graph", help="生成知識圖譜")
    p_graph.add_argument("--vault", default="~/my_KnowledgeBase")
    p_graph.add_argument("--min-links", type=int, default=0)
    p_graph.set_defaults(func=cmd_graph)

    # bump
    p_bump = subparsers.add_parser("bump", help="互動式版本升級")
    p_bump.add_argument("--vault", default="~/my_KnowledgeBase")
    p_bump.set_defaults(func=cmd_bump)

    # version
    p_ver = subparsers.add_parser("version", help="顯示版本資訊")
    p_ver.set_defaults(func=cmd_version)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
