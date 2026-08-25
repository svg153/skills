#!/usr/bin/env bash
# Sync one externally maintained skill into this library while preserving local metadata.yaml.
# This is the common primitive used by scripts/sync-upstreams.sh and CI.
# Usage: ./scripts/sync-upstream-skill.sh <skill-name>
set -euo pipefail

LIBRARY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$LIBRARY_DIR/skills"

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <skill-name>" >&2
  exit 2
fi

skill="$1"
target="$SKILLS_DIR/$skill"
meta="$target/metadata.yaml"

if [ ! -f "$meta" ]; then
  echo "ERROR: $skill has no metadata.yaml" >&2
  exit 1
fi

read_sync_field() {
  local field="$1"
  awk -v field="$field" '
    /^sync:/ { in_sync=1; next }
    in_sync && /^[^ ]/ { in_sync=0 }
    in_sync && $1 == field ":" { print $2; exit }
  ' "$meta"
}

origin=$(grep '^origin:' "$meta" | sed 's/^origin: *//')
origin_path=$(grep '^origin_path:' "$meta" | sed 's/^origin_path: *//' || true)
origin_ref=$(grep '^origin_ref:' "$meta" | sed 's/^origin_ref: *//' || true)
enabled=$(read_sync_field enabled)
strategy=$(read_sync_field strategy)
authoritative=$(read_sync_field authoritative)

if [ "${enabled:-false}" != "true" ]; then
  echo "ERROR: sync is not enabled for $skill" >&2
  exit 1
fi
if [ "${strategy:-manual}" != "download" ]; then
  echo "ERROR: $skill uses sync.strategy=${strategy:-manual}; this script only handles download" >&2
  exit 1
fi
if [ "${authoritative:-}" != "upstream" ]; then
  echo "ERROR: $skill is not marked authoritative: upstream" >&2
  exit 1
fi
if [ -z "$origin" ]; then
  echo "ERROR: origin is empty for $skill" >&2
  exit 1
fi

origin_ref=${origin_ref:-main}
origin_path=${origin_path:-/}
resolved_ref="$origin_ref"

# `latest-release` tracks only stable semantic-version tags (vX.Y.Z).
# It deliberately ignores main, prereleases and arbitrary tags so the catalog
# cannot ingest unpublished upstream behavior by accident.
if [ "$origin_ref" = "latest-release" ]; then
  resolved_ref=$(
    {
      git ls-remote --tags --refs "$origin" 'refs/tags/v*' \
        | awk '{sub("refs/tags/", "", $2); print $2}' \
        | grep -E '^v[0-9]+\.[0-9]+\.[0-9]+$' \
        | sort -V \
        | tail -n 1
    } || true
  )
  if [ -z "$resolved_ref" ]; then
    echo "ERROR: no stable vX.Y.Z tag found for $origin" >&2
    exit 1
  fi
fi

tmp=$(mktemp -d)
trap 'rm -rf "$tmp"' EXIT

git clone --depth 1 --branch "$resolved_ref" "$origin" "$tmp/upstream"

if [ "$origin_path" = "/" ] || [ "$origin_path" = "." ]; then
  source_dir="$tmp/upstream"
else
  source_dir="$tmp/upstream/${origin_path#/}"
fi

if [ ! -f "$source_dir/SKILL.md" ]; then
  echo "ERROR: upstream source does not contain SKILL.md: $source_dir" >&2
  exit 1
fi

# Preserve catalog-only metadata. Everything else in the skill directory is
# authoritative upstream content for download-managed skills.
cp "$meta" "$tmp/metadata.yaml"
find "$target" -mindepth 1 -maxdepth 1 ! -name metadata.yaml -exec rm -rf {} +

shopt -s dotglob nullglob
for entry in "$source_dir"/*; do
  name=$(basename "$entry")
  [ "$name" = ".git" ] && continue
  [ "$name" = "metadata.yaml" ] && continue
  cp -a "$entry" "$target/"
done
shopt -u dotglob nullglob

cp "$tmp/metadata.yaml" "$meta"

echo "Synced $skill from $origin@$resolved_ref ($origin_path; configured ref: $origin_ref)"
