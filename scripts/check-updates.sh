#!/usr/bin/env bash
# Check download-managed upstream skills without modifying the working tree.
# Usage: ./scripts/check-updates.sh [skill-name ...]
set -euo pipefail

LIBRARY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$LIBRARY_DIR/skills"

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

git clone --quiet --local "$LIBRARY_DIR" "$tmp/library"

read_sync_field() {
  local meta="$1"
  local field="$2"
  awk -v field="$field" '
    /^sync:/ { in_sync=1; next }
    in_sync && /^[^ ]/ { in_sync=0 }
    in_sync && $1 == field ":" { print $2; exit }
  ' "$meta"
}

if [ "$#" -gt 0 ]; then
  skill_names=("$@")
else
  skill_names=()
  for meta in "$SKILLS_DIR"/*/metadata.yaml; do
    [ -f "$meta" ] || continue
    enabled=$(read_sync_field "$meta" enabled)
    strategy=$(read_sync_field "$meta" strategy)
    authoritative=$(read_sync_field "$meta" authoritative)
    if [ "${enabled:-false}" = "true" ] && [ "${strategy:-manual}" = "download" ] && [ "${authoritative:-}" = "upstream" ]; then
      skill_names+=("$(basename "$(dirname "$meta")")")
    fi
  done
fi

if [ "${#skill_names[@]}" -eq 0 ]; then
  echo "No download-managed upstream skills configured."
  exit 0
fi

updates=0
errors=0

for skill in "${skill_names[@]}"; do
  echo "=== $skill ==="
  if ! "$tmp/library/scripts/sync-upstream-skill.sh" "$skill"; then
    echo "ERROR: could not resolve upstream for $skill" >&2
    errors=$((errors + 1))
    continue
  fi

  if git -C "$tmp/library" diff --quiet -- "skills/$skill"; then
    echo "UP TO DATE: $skill"
  else
    echo "UPDATE AVAILABLE: $skill"
    git -C "$tmp/library" diff --stat -- "skills/$skill"
    updates=$((updates + 1))
  fi

  git -C "$tmp/library" reset --hard --quiet HEAD
  git -C "$tmp/library" clean -fd --quiet
  echo
done

echo "Summary: $updates update(s), $errors error(s), ${#skill_names[@]} checked"
[ "$errors" -eq 0 ]
