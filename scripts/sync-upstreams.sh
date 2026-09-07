#!/usr/bin/env bash
# Sync every skill whose metadata opts into automatic upstream downloads and is
# still owned by the repository's legacy synchronizer.
#
# Usage:
#   ./scripts/sync-upstreams.sh --due   # only skills due for today's cadence
#   ./scripts/sync-upstreams.sh --all   # every legacy-sync managed skill
#   ./scripts/sync-upstreams.sh --list  # report legacy vs externally governed mirrors
set -euo pipefail

LIBRARY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="${SKILLS_DIR:-$LIBRARY_DIR/skills}"
MODE="${1:---due}"

case "$MODE" in
  --due|--all|--list) ;;
  *)
    echo "Usage: $0 [--due|--all|--list]" >&2
    exit 2
    ;;
esac

read_sync_field() {
  local meta="$1"
  local field="$2"
  awk -v field="$field" '
    /^sync:/ { in_sync=1; next }
    in_sync && /^[^ ]/ { in_sync=0 }
    in_sync && $1 == field ":" { print $2; exit }
  ' "$meta"
}

is_due_today() {
  local interval="$1"
  local dow dom
  dow=$(date -u +%u) # 1=Monday
  dom=$(date -u +%d)

  case "$interval" in
    daily) return 0 ;;
    weekly|"") [ "$dow" = "1" ] ;;
    monthly) [ "$dom" = "01" ] ;;
    manual|never) return 1 ;;
    *)
      echo "WARN: unknown sync.interval '$interval'; treating as manual" >&2
      return 1
      ;;
  esac
}

managed=0
processed=0
external=0

for meta in "$SKILLS_DIR"/*/metadata.yaml; do
  [ -f "$meta" ] || continue

  skill=$(basename "$(dirname "$meta")")
  enabled=$(read_sync_field "$meta" enabled)
  strategy=$(read_sync_field "$meta" strategy)
  authoritative=$(read_sync_field "$meta" authoritative)
  interval=$(read_sync_field "$meta" interval)
  managed_by=$(read_sync_field "$meta" managed_by)
  managed_by="${managed_by:-legacy-sync}"

  # Only explicit download-based, upstream-authoritative entries participate in
  # automated mirror management. Existing manual/local strategies stay untouched.
  if [ "${enabled:-false}" != "true" ] || [ "${strategy:-manual}" != "download" ] || [ "${authoritative:-}" != "upstream" ]; then
    continue
  fi

  # Once a mirror has proven the Renovate/APM lifecycle, metadata switches it to
  # `managed_by: apm`. The legacy scheduler must then stop touching that payload
  # so there is one update authority rather than two racing writers.
  if [ "$managed_by" = "apm" ]; then
    external=$((external + 1))
    if [ "$MODE" = "--list" ]; then
      origin=$(grep '^origin:' "$meta" | sed 's/^origin: *//')
      printf '%-36s manager=%-11s origin=%s\n' "$skill" "apm" "$origin"
    fi
    continue
  fi

  if [ "$managed_by" != "legacy-sync" ]; then
    echo "ERROR: unsupported sync.managed_by '$managed_by' for $skill" >&2
    exit 2
  fi

  managed=$((managed + 1))

  if [ "$MODE" = "--list" ]; then
    origin=$(grep '^origin:' "$meta" | sed 's/^origin: *//')
    origin_ref=$(grep '^origin_ref:' "$meta" | sed 's/^origin_ref: *//' || true)
    printf '%-36s manager=%-11s interval=%-8s ref=%-16s origin=%s\n' \
      "$skill" "legacy-sync" "${interval:-weekly}" "${origin_ref:-main}" "$origin"
    continue
  fi

  if [ "$MODE" = "--due" ] && ! is_due_today "${interval:-weekly}"; then
    echo "Skip $skill: interval=${interval:-weekly} is not due today"
    continue
  fi

  echo "=== Syncing $skill ==="
  "$LIBRARY_DIR/scripts/sync-upstream-skill.sh" "$skill"
  processed=$((processed + 1))
done

if [ "$MODE" = "--list" ]; then
  echo "Legacy-sync upstream skills: $managed"
  echo "Externally governed upstream skills: $external"
else
  echo "Processed upstream skills: $processed / $managed legacy-sync managed ($external externally governed)"
fi
