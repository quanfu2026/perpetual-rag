#!/usr/bin/env bash
# =============================================================================
# Perpetual RAG 永續性知識管理系統 — 一鍵安裝腳本
# =============================================================================
# 執行方式（未來上傳 GitHub 後）：
#   curl -fsSL https://raw.githubusercontent.com/quanfu2026/perpetual-rag/main/install.sh | bash
#
# 本地執行：
#   bash starter_kit/install.sh
#   bash starter_kit/install.sh --vault ~/my_vault --project "我的研究"
# =============================================================================

set -e  # 任何錯誤立刻停止

# ── 顏色輸出 ──────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
BLUE='\033[0;34m'; BOLD='\033[1m'; RESET='\033[0m'

ok()   { echo -e "${GREEN}✅ $1${RESET}"; }
warn() { echo -e "${YELLOW}⚠️  $1${RESET}"; }
err()  { echo -e "${RED}❌ $1${RESET}"; exit 1; }
info() { echo -e "${BLUE}   $1${RESET}"; }
sep()  { echo -e "${BOLD}$(printf '─%.0s' {1..60})${RESET}"; }

# ── 參數解析 ──────────────────────────────────────────────────────────────────
VAULT="$HOME/my_KnowledgeBase"
PROJECT="我的研究專案"

while [[ $# -gt 0 ]]; do
  case $1 in
    --vault)   VAULT="$2";   shift 2 ;;
    --project) PROJECT="$2"; shift 2 ;;
    --help|-h)
      echo "用法：bash install.sh [--vault 路徑] [--project 名稱]"
      echo "  --vault    知識庫路徑（預設：~/my_KnowledgeBase）"
      echo "  --project  專案名稱（預設：我的研究專案）"
      exit 0 ;;
    *) warn "未知參數：$1"; shift ;;
  esac
done

# ── 開始安裝 ──────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}║    Perpetual RAG 永續性知識管理系統 — 一鍵安裝              ║${RESET}"
echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
info "知識庫路徑：$VAULT"
info "專案名稱：$PROJECT"
echo ""

# ── Step 1：偵測作業系統 ──────────────────────────────────────────────────────
sep
echo -e "${BOLD}Step 1／5  偵測作業系統${RESET}"
sep

OS=""
case "$(uname -s)" in
  Darwin) OS="mac";   ok "macOS $(sw_vers -productVersion)" ;;
  Linux)  OS="linux"; ok "Linux ($(uname -r | cut -d'-' -f1))" ;;
  MINGW*|CYGWIN*|MSYS*) OS="windows"; ok "Windows (Git Bash / WSL)" ;;
  *) err "不支援的作業系統：$(uname -s)" ;;
esac

# ── Step 2：檢查並安裝 Python 3 ───────────────────────────────────────────────
sep
echo -e "${BOLD}Step 2／5  Python 3 環境${RESET}"
sep

if command -v python3 &>/dev/null; then
  PY_VER=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  PY_MAJOR=$(python3 -c "import sys; print(sys.version_info.major)")
  PY_MINOR=$(python3 -c "import sys; print(sys.version_info.minor)")
  if [[ $PY_MAJOR -ge 3 && $PY_MINOR -ge 8 ]]; then
    ok "Python $PY_VER"
  else
    warn "Python $PY_VER 版本過低（需要 3.8+），嘗試升級..."
    [[ $OS == "mac" ]] && brew install python3 || true
  fi
else
  warn "未找到 Python 3，正在安裝..."
  if [[ $OS == "mac" ]]; then
    command -v brew &>/dev/null || err "請先安裝 Homebrew：https://brew.sh"
    brew install python3
  elif [[ $OS == "linux" ]]; then
    sudo apt-get update -qq && sudo apt-get install -y python3 python3-pip
  else
    err "請先手動安裝 Python 3：https://python.org/downloads/"
  fi
fi

# 安裝 Python 套件
info "安裝 Python 依賴套件..."
python3 -m pip install --quiet --upgrade pip
python3 -m pip install --quiet rank-bm25 jieba scikit-learn pyyaml
ok "Python 套件就緒（rank-bm25, jieba, scikit-learn, pyyaml）"

# ── Step 3：檢查並安裝 Node.js + Claude Code CLI ──────────────────────────────
sep
echo -e "${BOLD}Step 3／5  Node.js + Claude Code CLI${RESET}"
sep

if command -v node &>/dev/null; then
  NODE_VER=$(node --version)
  ok "Node.js $NODE_VER"
else
  warn "未找到 Node.js，正在安裝..."
  if [[ $OS == "mac" ]]; then
    brew install node
  elif [[ $OS == "linux" ]]; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
  else
    err "請先手動安裝 Node.js LTS：https://nodejs.org"
  fi
fi

if command -v claude &>/dev/null; then
  ok "Claude Code CLI 已安裝"
else
  info "安裝 Claude Code CLI..."
  npm install -g @anthropic-ai/claude-code --silent
  ok "Claude Code CLI 安裝完成"
fi

# 提示設定 API Key
if [[ -z "$ANTHROPIC_API_KEY" ]]; then
  echo ""
  warn "尚未設定 ANTHROPIC_API_KEY"
  info "請取得 API Key：https://console.anthropic.com"
  info "設定方式（加入 ~/.zshrc 或 ~/.bashrc）："
  info '  export ANTHROPIC_API_KEY="sk-ant-你的金鑰"'
  echo ""
fi

# ── Step 4：建立知識庫 ────────────────────────────────────────────────────────
sep
echo -e "${BOLD}Step 4／5  初始化知識庫：$VAULT${RESET}"
sep

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -f "$SCRIPT_DIR/scripts/setup.py" ]]; then
  python3 "$SCRIPT_DIR/scripts/setup.py" --vault "$VAULT" --project "$PROJECT"
else
  warn "找不到 setup.py，手動建立資料夾結構..."
  mkdir -p "$VAULT"/{第一章_緒論,第二章_文獻回顧,第三章_研究方法,第四章_系統實作,第五章_實驗結果,第六章_結論,參考文獻,圖表,scripts}
  ok "資料夾結構建立完成"
fi

# ── Step 5：驗證安裝 ──────────────────────────────────────────────────────────
sep
echo -e "${BOLD}Step 5／5  驗證安裝${RESET}"
sep

PASS=0; FAIL=0

check() {
  if eval "$2" &>/dev/null; then
    ok "$1"; ((PASS++))
  else
    warn "$1 — 未通過"; ((FAIL++))
  fi
}

check "Python 3.8+"        "python3 -c 'import sys; assert sys.version_info >= (3,8)'"
check "rank-bm25"          "python3 -c 'import rank_bm25'"
check "jieba"              "python3 -c 'import jieba'"
check "scikit-learn"       "python3 -c 'import sklearn'"
check "Node.js"            "node --version"
check "Claude Code CLI"    "claude --version"
check "知識庫目錄"          "[[ -d '$VAULT' ]]"
check "CLAUDE.md"          "[[ -f '$VAULT/CLAUDE.md' ]]"
check "sessionhandoff.md"  "[[ -f '$VAULT/sessionhandoff.md' ]]"
check "bm25_search.py"     "[[ -f '$VAULT/scripts/bm25_search.py' ]]"

# ── 完成 ──────────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}╔══════════════════════════════════════════════════════════════╗${RESET}"
if [[ $FAIL -eq 0 ]]; then
  echo -e "${BOLD}║  🎉  安裝完成！通過 $PASS/$((PASS+FAIL)) 項驗證                              ║${RESET}"
else
  echo -e "${BOLD}║  ⚠️   安裝完成，通過 $PASS/$((PASS+FAIL)) 項驗證（$FAIL 項需手動處理）          ║${RESET}"
fi
echo -e "${BOLD}╚══════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "  📂 知識庫位置：${BOLD}$VAULT${RESET}"
echo ""
echo -e "  ${BOLD}接下來：${RESET}"
echo "    1. 在 Obsidian 開啟 $VAULT 作為 Vault"
echo "    2. 進入知識庫目錄：cd $VAULT"
echo "    3. 啟動 Claude Code：claude"
echo "    4. 輸入：開工"
echo ""
echo -e "  ${BOLD}常用指令：${RESET}"
echo "    python3 scripts/bm25_search.py \"關鍵字\""
echo "    python3 scripts/hallucination_guard.py"
echo "    python3 scripts/knowledge_graph.py"
echo ""
