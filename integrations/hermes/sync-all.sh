#!/usr/bin/env bash
# Sync this catalog into a local Hermes runtime through symlinks.
# Usage: ./integrations/hermes/sync-all.sh [pull|symlink|verify|list|full]
set -euo pipefail

LIBRARY_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
SKILLS_DIR="$LIBRARY_DIR/skills"
HERMES_SKILLS="${HERMES_SKILLS:-/hermes-home/skills}"
REMOTE_REPO="https://github.com/svg153/skills.git"

log_ok() { printf 'OK: %s\n' "$1"; }
log_warn() { printf 'WARN: %s\n' "$1" >&2; }
log_err() { printf 'ERROR: %s\n' "$1" >&2; }

do_pull() {
  echo "=== Pulling latest from $REMOTE_REPO ==="
  cd "$LIBRARY_DIR"
  if ! git remote get-url origin 2>/dev/null | grep -q 'svg153/skills'; then
    log_warn "not a svg153/skills checkout; skipping pull"
    return 0
  fi
  git pull --ff-only origin main
  log_ok "repository is up to date"
}

do_symlink() {
  echo "=== Creating Hermes symlinks ==="
  mkdir -p "$HERMES_SKILLS"
  local created=0 skipped=0
  for skill_path in "$SKILLS_DIR"/*; do
    [ -d "$skill_path" ] || continue
    local skill target current
    skill=$(basename "$skill_path")
    target="$HERMES_SKILLS/$skill"
    if [ -L "$target" ]; then
      current=$(readlink "$target")
      if [ "$current" != "$skill_path" ]; then
        ln -sfn "$skill_path" "$target"
        log_ok "$skill -> re-linked"
      fi
      skipped=$((skipped + 1))
    elif [ -e "$target" ]; then
      log_warn "$skill exists as a real path; not overwriting"
      skipped=$((skipped + 1))
    else
      ln -s "$skill_path" "$target"
      log_ok "$skill -> linked"
      created=$((created + 1))
    fi
  done
  echo "Summary: $created created, $skipped already present/skipped"
}

do_verify() {
  echo "=== Verifying Hermes symlinks ==="
  local total=0 ok=0 missing=0
  for skill_path in "$SKILLS_DIR"/*; do
    [ -d "$skill_path" ] || continue
    local skill target
    skill=$(basename "$skill_path")
    target="$HERMES_SKILLS/$skill"
    total=$((total + 1))
    if [ -L "$target" ] && [ -f "$target/SKILL.md" ]; then
      ok=$((ok + 1))
    else
      log_err "$skill is not available through a valid Hermes symlink"
      missing=$((missing + 1))
    fi
  done
  echo "Verification: $ok/$total skills OK"
  [ "$missing" -eq 0 ]
}

do_list() {
  echo "=== Catalog skills / Hermes status ==="
  for skill_path in "$SKILLS_DIR"/*; do
    [ -d "$skill_path" ] || continue
    local skill target state
    skill=$(basename "$skill_path")
    target="$HERMES_SKILLS/$skill"
    if [ -L "$target" ]; then state="linked"; elif [ -e "$target" ]; then state="local-path"; else state="missing"; fi
    printf '%-12s %s\n' "$state" "$skill"
  done
}

case "${1:-full}" in
  pull) do_pull ;;
  symlink) do_symlink ;;
  verify) do_verify ;;
  list) do_list ;;
  full) do_pull; do_symlink; do_verify; do_list ;;
  *)
    echo "Usage: $0 [pull|symlink|verify|list|full]" >&2
    exit 2
    ;;
esac
