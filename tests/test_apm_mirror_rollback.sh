#!/usr/bin/env bash
# Rehearse a real rollback using two published immutable upstream releases.
# This mutates only the ephemeral CI checkout and must converge exactly back to HEAD.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APM_DIR="$ROOT/dependencies/external-skills"
SKILL="github-build-or-reuse"
SKILL_DIR="$ROOT/skills/$SKILL"
PREVIOUS_COMMIT="74f8cfeca5c0ed5799a0ab71be88d06fc9e2afb1"
PREVIOUS_TAG="v1.2.2"
TMP="$(mktemp -d)"

# The current (restore) target is whatever the reviewed checkout pins, so
# Renovate pin updates need no edit here; only the v1.2.2 rollback target is fixed.
CURRENT_PIN="$(grep -Eo '#[0-9a-f]{40} # v[0-9]+\.[0-9]+\.[0-9]+' "$APM_DIR/apm.yml" | head -n1)"
CURRENT_COMMIT="$(printf '%s' "$CURRENT_PIN" | cut -c2-41)"
if [ -z "$CURRENT_COMMIT" ] || [ "$CURRENT_COMMIT" = "$PREVIOUS_COMMIT" ]; then
  echo 'ERROR: apm.yml must pin a current commit different from the rollback release' >&2
  exit 1
fi
CURRENT_VERSION="$(sed -n 's/^[[:space:]]*version: "\([^"]*\)".*/\1/p' "$SKILL_DIR/SKILL.md" | head -n1)"
if [ -z "$CURRENT_VERSION" ] || [ "$CURRENT_VERSION" = "1.2.2" ]; then
  echo 'ERROR: checked-out mirror must be at a version different from the rollback release' >&2
  exit 1
fi

cp "$APM_DIR/apm.yml" "$TMP/apm.yml.current"
cp "$APM_DIR/apm.lock.yaml" "$TMP/apm.lock.yaml.current"

restore_checkout() {
  cp "$TMP/apm.yml.current" "$APM_DIR/apm.yml" 2>/dev/null || true
  cp "$TMP/apm.lock.yaml.current" "$APM_DIR/apm.lock.yaml" 2>/dev/null || true
  git -C "$ROOT" restore --worktree -- \
    "skills/$SKILL" \
    plugin.json marketplace.json gemini-extension.json \
    .agents .codex-plugin .claude-plugin .cursor-plugin 2>/dev/null || true
  rm -rf "$TMP"
}
trap restore_checkout EXIT

cat > "$APM_DIR/apm.yml" <<YAML
name: svg153-external-skills
version: 1.0.0
description: Locked external Agent Skill dependencies consumed or mirrored by the svg153 skills catalog.
author: svg153
dependencies:
  apm:
    - ghspain/github-build-or-reuse/skills/github-build-or-reuse#${PREVIOUS_COMMIT} # ${PREVIOUS_TAG}
  mcp: []
scripts: {}
YAML

(
  cd "$APM_DIR"
  apm lock
)

python "$ROOT/scripts/materialize-apm-mirror.py" "$SKILL" --apply
python "$ROOT/scripts/generate-distribution.py"
python "$ROOT/scripts/materialize-apm-mirror.py" "$SKILL" --check

grep -q 'version: "1.2.2"' "$SKILL_DIR/SKILL.md"
if git -C "$ROOT" diff --quiet -- "$SKILL_DIR"; then
  echo 'ERROR: rollback rehearsal did not change the mirrored payload' >&2
  exit 1
fi

echo "OK: rolled canonical mirror back to published ${PREVIOUS_TAG}@${PREVIOUS_COMMIT:0:12}"

# Restore the exact dependency declaration + lock that were present at HEAD,
# then rematerialize from that immutable state. This is the operational rollback
# primitive in reverse: revert manifest+lock, materialize, regenerate.
cp "$TMP/apm.yml.current" "$APM_DIR/apm.yml"
cp "$TMP/apm.lock.yaml.current" "$APM_DIR/apm.lock.yaml"
python "$ROOT/scripts/materialize-apm-mirror.py" "$SKILL" --apply
python "$ROOT/scripts/generate-distribution.py"
python "$ROOT/scripts/materialize-apm-mirror.py" "$SKILL" --check

grep -q "version: \"${CURRENT_VERSION}\"" "$SKILL_DIR/SKILL.md"

git -C "$ROOT" diff --exit-code -- \
  dependencies/external-skills/apm.yml \
  dependencies/external-skills/apm.lock.yaml \
  "skills/$SKILL" \
  plugin.json marketplace.json gemini-extension.json \
  .agents .codex-plugin .claude-plugin .cursor-plugin

echo 'OK: rollback + restore round trip converged byte-for-byte to the checked-out state'
