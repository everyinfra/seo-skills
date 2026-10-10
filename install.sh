#!/usr/bin/env bash
# EveryInfra SEO Skills — one-command install
# Installs the seo-suite skill for Claude Code / Codex / any agentskills.io-compatible agent.
# Usage:  curl -fsSL https://raw.githubusercontent.com/everyinfra/seo-skills/main/install.sh | bash
#         install.sh [--help] [--dry-run] [--version] [--force] [--no-backup]
set -euo pipefail

REPO="https://github.com/everyinfra/seo-skills.git"
SKILL_NAME="seo-suite"
VERSION="0.30.1"

DRY_RUN=0
FORCE=0
BACKUP=1

usage() {
  cat <<'EOF'
EveryInfra SEO Skills installer

usage: install.sh [--dry-run] [--force] [--no-backup] [--help] [--version]

options:
  --dry-run     Print what would happen, change nothing on disk
  --force       Overwrite an existing install (backup kept unless --no-backup)
  --no-backup   Skip the .bak backup of an existing install (with --force)
  --help, -h    Show this help and exit 0
  --version, -V Show installer version and exit 0

environment:
  CLAUDE_SKILLS_DIR  Target skills directory (default: ~/.claude/skills)

notes:
  If the target directory already exists, the installer defaults to a dry-run
  and only tells you what it would do; pass --force to actually replace it.
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    --help|-h) usage; exit 0 ;;
    --version|-V) echo "everyinfra-seo-skills installer $VERSION"; exit 0 ;;
    --dry-run) DRY_RUN=1 ;;
    --force) FORCE=1 ;;
    --no-backup) BACKUP=0 ;;
    *) echo "unknown option: $1" >&2; usage >&2; exit 2 ;;
  esac
  shift
done

# Prefer a skill dir the user already has; default to Claude Code's.
DEST_BASE="${CLAUDE_SKILLS_DIR:-$HOME/.claude/skills}"
DEST="$DEST_BASE/$SKILL_NAME"

run() { # run "description" cmd... — echo in dry-run, execute otherwise
  if [ "$DRY_RUN" -eq 1 ]; then
    echo "  [dry-run] would run: $*"
  else
    "$@"
  fi
}

EXISTS=0
[ -d "$DEST" ] && EXISTS=1

if [ "$EXISTS" -eq 1 ] && [ "$FORCE" -ne 1 ]; then
  echo "!! Found existing $DEST"
  echo "   Default is dry-run: nothing will be overwritten."
  echo "   Re-run with --force to replace it (existing copy backed up to $DEST.bak unless --no-backup)."
  DRY_RUN=1
fi

echo "→ Plan: install $SKILL_NAME to $DEST"
if [ "$DRY_RUN" -eq 1 ]; then
  echo "  [dry-run] mode: no changes will be made"
fi

if [ "$EXISTS" -eq 1 ] && [ "$FORCE" -eq 1 ]; then
  if [ "$BACKUP" -eq 1 ]; then
    echo "→ Backing up existing install to $DEST.bak"
    run rm -rf "$DEST.bak"
    run mv "$DEST" "$DEST.bak"
  else
    echo "→ --no-backup: removing existing install (no .bak)"
    run rm -rf "$DEST"
  fi
fi

TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

echo "→ Cloning EveryInfra SEO Skills..."
run git clone -q --depth 1 "$REPO" "$TMP/seo-skills"

run mkdir -p "$DEST_BASE"
run cp -R "$TMP/seo-skills/skills/$SKILL_NAME/." "$DEST/"

if [ "$DRY_RUN" -eq 1 ]; then
  echo "✓ Dry run complete — nothing was installed. Re-run without --dry-run to install."
  exit 0
fi

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
