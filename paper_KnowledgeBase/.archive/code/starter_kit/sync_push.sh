#!/bin/bash
# sync_push.sh — 出門前執行：將知識庫推送到 GitHub / 隨身碟 / 雲端
# 使用方式：bash sync_push.sh

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
echo "║   Perpetual RAG  ·  出門同步（Push）     ║"
echo "╚══════════════════════════════════════════╝"
echo ""

# ── 1. Git 同步 ──────────────────────────────────────
step "步驟 1／3：Git 推送到 GitHub"

CHANGED=$(git status --porcelain | wc -l | tr -d ' ')
if [ "$CHANGED" -eq 0 ]; then
  info "沒有新變更，知識庫已是最新狀態"
else
  echo "偵測到 $CHANGED 個變更："
  git status --short
  echo ""
  read -p "提交說明（直接 Enter 使用預設）：" MSG
  MSG="${MSG:-sync: $(date '+%Y-%m-%d %H:%M') 出門備份}"
  git add -A
  git commit -m "$MSG"
  info "已提交：$MSG"
fi

if git remote get-url origin &>/dev/null; then
  git push origin master 2>&1 && info "已推送至 GitHub" || warn "GitHub 推送失敗（可能無網路，繼續其他同步）"
else
  warn "未設定 Git remote，略過 GitHub 推送"
fi

# ── 2. 隨身碟同步（選用）────────────────────────────
step "步驟 2／3：隨身碟同步"
echo "可用磁碟區："
ls /Volumes/ 2>/dev/null || echo "  （無）"
echo ""
read -p "是否同步到隨身碟？（y/n）：" DO_USB

if [ "$DO_USB" = "y" ]; then
  read -p "隨身碟路徑（例如 /Volumes/MyUSB）：" USB
  if [ -d "$USB" ]; then
    DEST="$USB/perpetual-rag/paper_KnowledgeBase"
    mkdir -p "$DEST"
    rsync -av --delete \
      --exclude=".git" \
      --exclude="__pycache__" \
      --exclude="*.pyc" \
      --exclude=".DS_Store" \
      --exclude="dist/" \
      "$KB/" "$DEST/"
    echo "$(date '+%Y-%m-%d %H:%M') push from $(hostname)" >> "$USB/perpetual-rag/sync_log.txt"
    info "已同步至隨身碟：$DEST"
  else
    warn "找不到隨身碟：$USB，略過"
  fi
else
  info "略過隨身碟同步"
fi

# ── 3. 雲端硬碟同步（若已設定 symlink 則自動生效）────
step "步驟 3／3：雲端硬碟"

CLOUD_LINK="$KB/.cloud_sync_target"
if [ -f "$CLOUD_LINK" ]; then
  CLOUD_PATH=$(cat "$CLOUD_LINK")
  if [ -d "$CLOUD_PATH" ]; then
    rsync -a --delete \
      --exclude=".git" \
      --exclude="__pycache__" \
      --exclude="*.pyc" \
      --exclude=".DS_Store" \
      --exclude="dist/" \
      "$KB/KnowledgeBase/" "$CLOUD_PATH/KnowledgeBase/"
    info "已同步至雲端硬碟：$CLOUD_PATH"
  else
    warn "雲端路徑已失效：$CLOUD_PATH（請重新執行 setup_cloud.sh）"
  fi
else
  warn "尚未設定雲端硬碟，執行 bash starter_kit/setup_cloud.sh 可一鍵設定"
fi

# ── 完成 ──────────────────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
info "出門同步完成！$(date '+%Y-%m-%d %H:%M')"
echo "  知識庫版本已備份，可安心出門。"
echo "══════════════════════════════════════════"
echo ""
