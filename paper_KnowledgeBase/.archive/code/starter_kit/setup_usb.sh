#!/bin/bash
# setup_usb.sh — 一鍵將 Perpetual RAG 知識庫打包到隨身碟
# 使用方式：bash setup_usb.sh [隨身碟路徑]
# 範例：bash setup_usb.sh /Volumes/MyUSB

set -e

# ── 顏色 ──────────────────────────────────────────────
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
info()    { echo -e "${GREEN}[✓]${NC} $1"; }
warn()    { echo -e "${YELLOW}[!]${NC} $1"; }
error()   { echo -e "${RED}[✗]${NC} $1"; exit 1; }

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Perpetual RAG  ·  隨身碟部署工具       ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. 偵測隨身碟路徑 ─────────────────────────────────
if [ -n "$1" ]; then
  USB="$1"
else
  echo "可用磁碟區："
  ls /Volumes/
  echo ""
  read -p "請輸入隨身碟路徑（例如 /Volumes/MyUSB）：" USB
fi

[ -d "$USB" ] || error "找不到路徑：$USB"
info "隨身碟路徑：$USB"

# ── 2. 建立目標資料夾結構 ──────────────────────────────
DEST="$USB/perpetual-rag"
mkdir -p "$DEST"
info "建立目標資料夾：$DEST"

# ── 3. 複製知識庫 ──────────────────────────────────────
SOURCE="$HOME/paper_KnowledgeBase"
[ -d "$SOURCE" ] || error "找不到知識庫：$SOURCE"

rsync -av --delete \
  --exclude=".git" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude=".DS_Store" \
  --exclude="dist/" \
  --exclude="*.egg-info" \
  "$SOURCE/" "$DEST/paper_KnowledgeBase/"

info "知識庫已同步至隨身碟"

# ── 4. 建立 Python 虛擬環境（含所有依賴）────────────────
VENV="$DEST/venv"
if [ -d "$VENV" ]; then
  warn "venv 已存在，略過建立（若要重建請先刪除 $VENV）"
else
  echo ""
  read -p "是否建立內建 Python 虛擬環境？（y/n，建議 y）：" BUILD_VENV
  if [ "$BUILD_VENV" = "y" ]; then
    python3 -m venv "$VENV"
    source "$VENV/bin/activate"
    pip install --quiet --upgrade pip
    pip install --quiet rank-bm25 jieba scikit-learn pyyaml
    deactivate
    info "Python 虛擬環境已建立：$VENV"
  else
    warn "略過虛擬環境，目標電腦需自行安裝 Python 套件"
  fi
fi

# ── 5. 寫入啟動腳本 ────────────────────────────────────
cat > "$DEST/start.sh" << 'EOF'
#!/bin/bash
# 在任意電腦上啟動 Perpetual RAG

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV="$SCRIPT_DIR/venv"
KB="$SCRIPT_DIR/paper_KnowledgeBase"

echo ""
echo "╔══════════════════════════════════════╗"
echo "║   Perpetual RAG  ·  啟動中...        ║"
echo "╚══════════════════════════════════════╝"
echo ""

# 啟動 venv（若存在）
if [ -d "$VENV" ]; then
  source "$VENV/bin/activate"
  echo "[✓] 已啟動內建 Python 環境"
fi

# 切換到知識庫目錄
cd "$KB"
echo "[✓] 知識庫路徑：$KB"

# 檢查 Claude Code
if command -v claude &>/dev/null; then
  echo "[✓] Claude Code 已安裝"
else
  echo "[!] 未偵測到 Claude Code"
  echo "    請執行：npm install -g @anthropic-ai/claude-code"
fi

echo ""
echo "── 可用指令 ──────────────────────────────────────"
echo "  BM25 搜尋：  python3 starter_kit/scripts/bm25_search.py <關鍵字>"
echo "  幻覺掃描：  python3 starter_kit/scripts/hallucination_guard.py"
echo "  術語稽核：  python3 starter_kit/scripts/consistency_check.py"
echo "  啟動 Claude Code：  claude"
echo "──────────────────────────────────────────────────"
echo ""
EOF
chmod +x "$DEST/start.sh"
info "啟動腳本已建立：$DEST/start.sh"

# ── 6. 寫入 README ────────────────────────────────────
cat > "$DEST/README.txt" << EOF
Perpetual RAG 隨身碟版
======================
建立時間：$(date '+%Y-%m-%d %H:%M')
來源機器：$(hostname)

使用方式：
  Mac/Linux：bash /Volumes/隨身碟/perpetual-rag/start.sh
  Windows  ：需在 WSL 或 Git Bash 中執行

目標電腦需要：
  - Claude Code：npm install -g @anthropic-ai/claude-code
  - Anthropic API Key

知識庫路徑：perpetual-rag/paper_KnowledgeBase/
GitHub    ：https://github.com/quanfu2026/perpetual-rag
說明網站  ：https://quanfu2026.github.io/perpetual-rag/
EOF
info "README 已建立"

# ── 7. 完成統計 ────────────────────────────────────────
echo ""
USED=$(du -sh "$DEST" | cut -f1)
echo "══════════════════════════════════════════"
info "部署完成！"
echo "  隨身碟路徑：$DEST"
echo "  佔用空間  ：$USED"
echo ""
echo "在其他電腦使用："
echo "  bash $DEST/start.sh"
echo "══════════════════════════════════════════"
echo ""
