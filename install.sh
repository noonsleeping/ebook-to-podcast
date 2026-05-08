#!/usr/bin/env bash
# install.sh — ebook-to-podcast skill installer
# Copies skill files to ~/.claude/skills/ebook-to-podcast/ and writes config.json

set -e

SKILL_DIR="$HOME/.claude/skills/ebook-to-podcast"
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo ""
echo "╔══════════════════════════════════════════════╗"
echo "║         ebook-to-podcast  installer          ║"
echo "╚══════════════════════════════════════════════╝"
echo ""

# ── Check uv ────────────────────────────────────────────────────────────────
if ! command -v uv &>/dev/null; then
  echo "❌  'uv' not found. Install it first:"
  echo "    curl -LsSf https://astral.sh/uv/install.sh | sh"
  echo "    Then re-run this script."
  exit 1
fi

# ── Ask for inbox directory ──────────────────────────────────────────────────
echo "Where should Claude look for ebooks to process?"
echo "  (Drop .pdf / .epub files here before running the skill)"
echo ""
read -r -p "  Inbox directory [~/Downloads/eBooks/inbox]: " INBOX_DIR
INBOX_DIR="${INBOX_DIR:-$HOME/Downloads/eBooks/inbox}"
# Expand tilde manually for paths that start with ~/
INBOX_DIR="${INBOX_DIR/#\~/$HOME}"

# ── Ask for output root ──────────────────────────────────────────────────────
echo ""
echo "Where should Claude create per-book project folders?"
echo "  (A subfolder named after the book will be created here)"
echo ""
read -r -p "  Output root directory [~/Downloads/eBooks]: " OUTPUT_ROOT
OUTPUT_ROOT="${OUTPUT_ROOT:-$HOME/Downloads/eBooks}"
OUTPUT_ROOT="${OUTPUT_ROOT/#\~/$HOME}"

# ── Create directories ───────────────────────────────────────────────────────
mkdir -p "$INBOX_DIR"
mkdir -p "$OUTPUT_ROOT"
mkdir -p "$SKILL_DIR/scripts"
mkdir -p "$SKILL_DIR/references"

# ── Copy files ───────────────────────────────────────────────────────────────
echo ""
echo "📦  Installing skill files to $SKILL_DIR ..."

cp "$REPO_DIR/SKILL.md"                           "$SKILL_DIR/SKILL.md"
cp "$REPO_DIR/scripts/split_book.py"              "$SKILL_DIR/scripts/split_book.py"
cp "$REPO_DIR/references/translation_principles.md" "$SKILL_DIR/references/translation_principles.md"

# ── Write config.json ────────────────────────────────────────────────────────
cat > "$SKILL_DIR/config.json" <<EOF
{
  "inbox_dir": "$INBOX_DIR",
  "output_root": "$OUTPUT_ROOT"
}
EOF

echo "✅  Config written: $SKILL_DIR/config.json"
echo ""
echo "┌─────────────────────────────────────────────────┐"
echo "│  Installation complete!                         │"
echo "│                                                 │"
echo "│  Inbox:       $INBOX_DIR"
echo "│  Output root: $OUTPUT_ROOT"
echo "│                                                 │"
echo "│  Drop a .pdf or .epub into your inbox, then    │"
echo "│  open Claude Code and say:                     │"
echo "│    把inbox里的书处理一下                        │"
echo "│    (or: Process the book in my inbox)          │"
echo "└─────────────────────────────────────────────────┘"
echo ""
