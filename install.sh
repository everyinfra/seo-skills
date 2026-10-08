#!/usr/bin/env bash
# EveryInfra SEO Skills — one-command install
# Installs the seo-suite skill for Claude Code / Codex / any agentskills.io-compatible agent.
# Usage:  curl -fsSL https://raw.githubusercontent.com/everyinfra/seo-skills/main/install.sh | bash
set -euo pipefail

REPO="https://github.com/everyinfra/seo-skills.git"
SKILL_NAME="seo-suite"

# Prefer a skill dir the user already has; default to Claude Code's.
DEST_BASE="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
DEST="$DEST_BASE/$SKILL_NAME"

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "→ Cloning EveryInfra SEO Skills..."
git clone -q --depth 1 "$REPO" "$TMP/seo-skills"

if [ -d "$DEST" ]; then
  echo "!! Found existing $DEST — backing it up to $DEST.bak"
  rm -rf "$DEST.bak"
  mv "$DEST" "$DEST.bak"
fi

mkdir -p "$DEST_BASE"
cp -R "$TMP/seo-skills/skills/$SKILL_NAME/." "$DEST/"

echo "✓ Installed $SKILL_NAME to $DEST"
echo ""
echo "  References:   $(find "$DEST/references" -name '*.md' | wc -l | tr -d ' ') files"
echo "  Templates:    $(find "$DEST/templates" -name '*.md' 2>/dev/null | wc -l | tr -d ' ') files"
echo ""
echo "  No API key, no model, no runtime dependency — the skill is instructions"
echo "  and references only; your agent and your data do the work."
echo ""
echo "  Next: restart your agent (or /reload skills) and try:"
echo "    帮我做一次 SEO 整站诊断"
echo "    run a backlink profile analysis on example.com"
