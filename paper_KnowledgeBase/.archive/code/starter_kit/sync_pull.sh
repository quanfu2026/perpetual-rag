#!/bin/bash
# sync_pull.sh — 抵達後執行：從 GitHub / 隨身碟 拉取最新知識庫
# 使用方式：bash sync_pull.sh

set -e
GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn()  { echo -e "${YELLOW}[!]${NC} $1"; }
error() { echo -e "${RED}[✗]${NC} $1"; exit 1; }
step()  { echo -e "\n${CYAN}── $1 ──────────────────────────────────${NC}"; }

KB="$HOME/paper_KnowledgeBase"
cd "$KB"

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║   Perpetual RAG  ·  抵達同步（Pull）     ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 0. 本地未提交變更警告 ────────────────────────────
CHANGED=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$CHANGED" -gt 0 ]; then
  warn "本地有 $CHANGED 個未提交變更："
  git status --short
  echo ""
  read -p "是否先提交本地變更再拉取？（y/n，建議 y）：" DO_COMMIT
  if [ "$DO_COMMIT" = "y" ]; then
    read -p "提交說明（直接 Enter 使用預設）：" MSG
    MSG="${MSG:-sync: $(date '+%Y-%m-%d %H:%M') 拉取前備份}"
    git add -A
    git commit -m "$MSG"
    info "本地變更已提交"
  fi
fi

# ── 1. 選擇同步來源 ──────────────────────────────────
step "步驟 1／2：選擇同步來源"
echo ""
echo "  [1] GitHub（有網路，推薦）"
echo "  [2] 隨身碟（無網路備援）"
echo "  [3] 兩者都同步（隨身碟優先，再推至 GitHub）"
echo ""
read -p "請選擇（1/2/3）：" SRC

# ── 2. 從 GitHub 拉取 ────────────────────────────────
if [ "$SRC" = "1" ] || [ "$SRC" = "3" ]; then
  step "從 GitHub 拉取"
  if git remote get-url origin &>/dev/null; then
    # 偵測衝突
    git fetch origin master 2>&1
    LOCAL=$(git rev-parse HEAD)
    REMOTE=$(git rev-parse origin/master)
    BASE=$(git merge-base HEAD origin/master)

    if [ "$LOCAL" = "$REMOTE" ]; then
      info "本地已是最新，無需拉取"
    elif [ "$LOCAL" = "$BASE" ]; then
      git pull origin master
      info "已從 GitHub 拉取最新知識庫"
    elif [ "$REMOTE" = "$BASE" ]; then
      warn "本地版本比 GitHub 新，建議先執行 sync_push.sh"
    else
      warn "偵測到分叉！本地與 GitHub 都有新變更"
      echo ""
      echo "  [a] 保留本地版本（放棄 GitHub 更新）"
      echo "  [b] 採用 GitHub 版本（放棄本地更新）"
      echo "  [c] 嘗試自動合併（可能需要手動解決衝突）"
      echo ""
      read -p "請選擇處理方式（a/b/c）：" CONFLICT
      case "$CONFLICT" in
        a) info "保留本地版本，略過 GitHub 拉取" ;;
        b) git reset --hard origin/master && info "已採用 GitHub 版本" ;;
        c) git merge origin/master && info "合併完成" || warn "有衝突需手動處理：git status 查看" ;;
        *) warn "無效選項，略過" ;;
      esac
    fi
  else
    warn "未設定 Git remote，略過 GitHub 拉取"
  fi
fi

# ── 3. 從隨身碟同步 ──────────────────────────────────
if [ "$SRC" = "2" ] || [ "$SRC" = "3" ]; then
  step "從隨身碟同步"
  echo "可用磁碟區："
  ls /Volumes/ 2>/dev/null || echo "  （無）"
  echo ""
  read -p "隨身碟路徑（例如 /Volumes/MyUSB）：" USB

  USB_KB="$USB/perpetual-rag/paper_KnowledgeBase"
  if [ -d "$USB_KB" ]; then
    # 顯示隨身碟版本的同步記錄
    SYNCLOG="$USB/perpetual-rag/sync_log.txt"
    if [ -f "$SYNCLOG" ]; then
      echo "隨身碟最後同步記錄："
      tail -3 "$SYNCLOG"
      echo ""
    fi

    read -p "確認從隨身碟覆蓋本地知識庫？（y/n）：" CONFIRM_USB
    if [ "$CONFIRM_USB" = "y" ]; then
      rsync -av \
        --exclude=".git" \
        --exclude="__pycache__" \
        --exclude="*.pyc" \
        --exclude=".DS_Store" \
        "$USB_KB/" "$KB/"
      info "已從隨身碟同步"

      # 若選擇「兩者」，把隨身碟的更新再推到 GitHub
      if [ "$SRC" = "3" ] && git remote get-url origin &>/dev/null; then
        git add -A
        CHANGED2=$(git status --porcelain | wc -l | tr -d ' ')
        if [ "$CHANGED2" -gt 0 ]; then
          git commit -m "sync: $(date '+%Y-%m-%d %H:%M') 從隨身碟同步後推送"
          git push origin master && info "已將隨身碟更新推送至 GitHub"
        fi
      fi
    else
      info "略過隨身碟同步"
    fi
  else
    warn "找不到隨身碟知識庫：$USB_KB"
  fi
fi

# ── 完成 ──────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
info "抵達同步完成！$(date '+%Y-%m-%d %H:%M')"
echo "  知識庫已是最新狀態，可開始研究。"
echo "══════════════════════════════════════════"
echo ""
