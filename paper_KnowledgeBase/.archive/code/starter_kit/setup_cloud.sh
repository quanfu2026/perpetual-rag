#!/bin/bash
# setup_cloud.sh — 一次性設定：將知識庫連結到雲端硬碟自動同步
# 支援：iCloud Drive / Google Drive / Dropbox / 自訂路徑
# 使用方式：bash setup_cloud.sh

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }

KB="$HOME/paper_KnowledgeBase"
CLOUD_LINK="$KB/.cloud_sync_target"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Perpetual RAG  ·  雲端同步設定         ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 偵測已安裝的雲端服務 ─────────────────────────────
ICLOUDDRIVE="$HOME/Library/Mobile Documents/com~apple~CloudDocs"
GOOGLEDRIVE_V1="$HOME/Google Drive/My Drive"
GOOGLEDRIVE_V2=$(ls "$HOME/Library/CloudStorage/" 2>/dev/null | grep -i "GoogleDrive" | head -1)
GOOGLEDRIVE_V2="${HOME}/Library/CloudStorage/${GOOGLEDRIVE_V2}/My Drive"
DROPBOX="$HOME/Dropbox"
ONEDRIVE=$(ls "$HOME/Library/CloudStorage/" 2>/dev/null | grep -i "OneDrive" | head -1)
ONEDRIVE="${HOME}/Library/CloudStorage/${ONEDRIVE}"

echo "偵測可用雲端服務："
echo ""

OPT=0
declare -a OPTIONS
declare -a PATHS

if [ -d "$ICLOUDDRIVE" ]; then
  OPT=$((OPT+1)); OPTIONS[$OPT]="iCloud Drive"; PATHS[$OPT]="$ICLOUDDRIVE/perpetual-rag"
  echo "  [$OPT] iCloud Drive ✅  （${ICLOUDDRIVE}）"
fi

if [ -d "$GOOGLEDRIVE_V1" ]; then
  OPT=$((OPT+1)); OPTIONS[$OPT]="Google Drive"; PATHS[$OPT]="$GOOGLEDRIVE_V1/perpetual-rag"
  echo "  [$OPT] Google Drive ✅  （${GOOGLEDRIVE_V1}）"
elif [ -d "$GOOGLEDRIVE_V2" ]; then
  OPT=$((OPT+1)); OPTIONS[$OPT]="Google Drive"; PATHS[$OPT]="$GOOGLEDRIVE_V2/perpetual-rag"
  echo "  [$OPT] Google Drive ✅  （${GOOGLEDRIVE_V2}）"
fi

if [ -d "$DROPBOX" ]; then
  OPT=$((OPT+1)); OPTIONS[$OPT]="Dropbox"; PATHS[$OPT]="$DROPBOX/perpetual-rag"
  echo "  [$OPT] Dropbox ✅  （${DROPBOX}）"
fi

if [ -d "$ONEDRIVE" ]; then
  OPT=$((OPT+1)); OPTIONS[$OPT]="OneDrive"; PATHS[$OPT]="$ONEDRIVE/perpetual-rag"
  echo "  [$OPT] OneDrive ✅  （${ONEDRIVE}）"
fi

OPT=$((OPT+1)); OPTIONS[$OPT]="自訂路徑"; PATHS[$OPT]="custom"
echo "  [$OPT] 自訂路徑（手動輸入）"
OPT=$((OPT+1)); OPTIONS[$OPT]="取消"; PATHS[$OPT]="cancel"
echo "  [$OPT] 取消"

echo ""

if [ "${#OPTIONS[@]}" -eq 2 ]; then
  warn "未偵測到任何雲端服務，請先安裝 iCloud/Google Drive/Dropbox 桌面版"
  echo "  或選擇自訂路徑"
fi

read -p "請選擇雲端服務（數字）：" CHOICE

CLOUD_NAME="${OPTIONS[$CHOICE]}"
CLOUD_PATH="${PATHS[$CHOICE]}"

[ "$CLOUD_PATH" = "cancel" ] && echo "已取消" && exit 0

if [ "$CLOUD_PATH" = "custom" ]; then
  read -p "請輸入雲端資料夾完整路徑：" CLOUD_PATH
  CLOUD_NAME="自訂路徑"
fi

[ -z "$CLOUD_PATH" ] && error "無效選項"

# ── 建立雲端資料夾 ────────────────────────────────────
mkdir -p "$CLOUD_PATH"
info "雲端目標資料夾：$CLOUD_PATH"

# ── 初次同步 ──────────────────────────────────────────
echo ""
echo "正在初次同步知識庫到 $CLOUD_NAME..."
rsync -av \
  --exclude=".git" \
  --exclude="__pycache__" \
  --exclude="*.pyc" \
  --exclude=".DS_Store" \
  --exclude="dist/" \
  --exclude="venv/" \
  "$KB/" "$CLOUD_PATH/"
info "初次同步完成"

# ── 記錄雲端目標路徑 ─────────────────────────────────
echo "$CLOUD_PATH" > "$CLOUD_LINK"
info "已記錄雲端路徑：$CLOUD_LINK"

# ── 提示後續使用方式 ─────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
info "雲端同步設定完成！"
echo ""
echo "  服務：$CLOUD_NAME"
echo "  路徑：$CLOUD_PATH"
echo ""
echo "後續使用："
echo "  • 出門前執行 sync_push.sh → 自動同步到 $CLOUD_NAME"
echo "  • $CLOUD_NAME 會在背景持續同步到所有裝置"
echo "  • 另一台電腦執行 sync_pull.sh 即可取得最新知識庫"
echo ""

# ── 詢問是否在其他電腦設定反向同步 ─────────────────────
echo "在其他電腦設定接收同步："
echo "  1. 安裝相同的 $CLOUD_NAME 桌面版"
echo "  2. 執行：bash setup_cloud.sh"
echo "  3. 選擇相同的 $CLOUD_NAME"
echo "══════════════════════════════════════════"
echo ""
