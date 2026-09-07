#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
FIXTURE="$(mktemp -d)"
trap 'rm -rf "$FIXTURE"' EXIT

mkdir -p "$FIXTURE/apm-mirror" "$FIXTURE/legacy-mirror" "$FIXTURE/local-skill"

cat >"$FIXTURE/apm-mirror/metadata.yaml" <<'YAML'
name: apm-mirror
origin: https://github.com/example/apm-mirror
origin_path: skills/apm-mirror
origin_ref: latest-release
category: test
status: active
sync:
  enabled: true
  interval: weekly
  strategy: download
  authoritative: upstream
  channel: stable
  managed_by: apm
YAML

cat >"$FIXTURE/legacy-mirror/metadata.yaml" <<'YAML'
name: legacy-mirror
origin: https://github.com/example/legacy-mirror
origin_path: skills/legacy-mirror
origin_ref: latest-release
category: test
status: active
sync:
  enabled: true
  interval: weekly
  strategy: download
  authoritative: upstream
  channel: stable
YAML

cat >"$FIXTURE/local-skill/metadata.yaml" <<'YAML'
name: local-skill
origin: https://github.com/svg153/skills
origin_path: skills/local-skill
category: test
status: active
sync:
  enabled: false
  interval: manual
  strategy: local
  authoritative: local
YAML

list_output=$(SKILLS_DIR="$FIXTURE" "$ROOT/scripts/sync-upstreams.sh" --list)
printf '%s\n' "$list_output"

grep -q '^apm-mirror .*manager=apm' <<<"$list_output"
grep -q '^legacy-mirror .*manager=legacy-sync' <<<"$list_output"
! grep -q '^local-skill ' <<<"$list_output"
grep -q 'Legacy-sync upstream skills: 1' <<<"$list_output"
grep -q 'Externally governed upstream skills: 1' <<<"$list_output"

# With only an APM-owned mirror, --all must not invoke the legacy downloader.
rm -rf "$FIXTURE/legacy-mirror"
all_output=$(SKILLS_DIR="$FIXTURE" "$ROOT/scripts/sync-upstreams.sh" --all)
printf '%s\n' "$all_output"
grep -q 'Processed upstream skills: 0 / 0 legacy-sync managed (1 externally governed)' <<<"$all_output"

echo 'OK: APM-owned mirrors are excluded from legacy scheduled synchronization'
