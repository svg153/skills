#!/usr/bin/env bash
set -uo pipefail

# Run every evals/*/eval.yaml Waza suite against an isolated, disposable copy of
# the repository, and fail loudly if a model-driven agent mutated the real checkout.
#
# Why: Waza gives each task an empty temp workspace, but the agent is a normal
# process with the runner user's privileges. In run 44134233088 an agent found the
# real checkout via ~/work, ran `git init` in its parent directory and then
# `git clean -ffd`, which deleted evals/ for every later suite.
#
# Usage: scripts/run-behavioral-suites.sh [results-dir [suite]]
#   results-dir default: <repo>/eval-results; suite default (empty): every suite.
#   suite must match [a-z0-9-]+ and exist as evals/<suite>/eval.yaml.

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
parent="$(dirname "$root")"
mkdir -p "${1:-$root/eval-results}"
results_root="$(cd "${1:-$root/eval-results}" && pwd -P)"
results_rel=""
[[ "$results_root" == "$root"/* ]] && results_rel="${results_root#"$root"/}"

suite_filter="${2:-}"
if [[ -n "$suite_filter" && ! "$suite_filter" =~ ^[a-z0-9-]+$ ]]; then
  echo "::error::invalid suite name (allowed: [a-z0-9-]+)" >&2
  exit 2
fi

# With an explicit Copilot user token the agent needs no GitHub token: drop any
# ambient one so a model-driven agent cannot use gh/git with repository credentials.
if [[ -n "${COPILOT_GITHUB_TOKEN:-}" ]]; then
  unset GITHUB_TOKEN GH_TOKEN
fi

command -v waza >/dev/null || { echo "::error::waza is not on PATH" >&2; exit 2; }
git -C "$root" rev-parse --git-dir >/dev/null 2>&1 || { echo "::error::$root is not a git checkout" >&2; exit 2; }

# Resolve the suite list to absolute paths once, before anything can change the tree.
mapfile -t suites < <(find "$root/evals" -mindepth 2 -maxdepth 2 -name eval.yaml -print | sort)
if [[ -n "$suite_filter" ]]; then
  want="$root/evals/$suite_filter/eval.yaml"
  if [[ ! -f "$want" ]]; then
    echo "::error::unknown suite '$suite_filter': evals/$suite_filter/eval.yaml does not exist" >&2
    exit 2
  fi
  suites=("$want")
fi
if [[ ${#suites[@]} -eq 0 ]]; then
  echo "::error::no evals/*/eval.yaml suites found under $root" >&2
  exit 2
fi
for spec in "${suites[@]}"; do
  mkdir -p "$results_root/$(basename "$(dirname "$spec")")/transcripts"
done

snap_base="$(mktemp -d "${RUNNER_TEMP:-${TMPDIR:-/tmp}}/waza-suites.XXXXXX")"

restore_permissions() {
  chmod -R u+w "$root" "$snap_base" 2>/dev/null || true
  chmod u+w "$parent" 2>/dev/null || true
}
cleanup() { restore_permissions; rm -rf "$snap_base"; }
trap cleanup EXIT

checkout_state() {
  local excludes=()
  [[ -n "$results_rel" ]] && excludes=(":(exclude)$results_rel")
  printf 'HEAD=%s\nREF=%s\n' \
    "$(git -C "$root" rev-parse HEAD 2>&1)" \
    "$(git -C "$root" symbolic-ref -q HEAD 2>&1 || echo detached)"
  git -C "$root" status --porcelain --untracked-files=all -- . "${excludes[@]}" 2>&1
}

# Defense in depth: agents run as the same user, so this cannot stop a deliberate
# chmod, but it turns accidental git clean/checkout/rm/git init into failures.
# Output directories stay writable.
protect_checkout() {
  find "$root" \( -path "$results_root" -o -path "$results_root/*" \) -prune -o -exec chmod a-w {} + 2>/dev/null || true
  chmod a-w "$parent" 2>/dev/null || true
}

baseline="$(checkout_state)"
if [[ "$(printf '%s\n' "$baseline" | sed -n '3,$p')" != "" ]]; then
  echo "::error::checkout is not clean before running suites:" >&2
  printf '%s\n' "$baseline" >&2
  exit 2
fi

status=0
for spec in "${suites[@]}"; do
  skill="$(basename "$(dirname "$spec")")"
  out="$results_root/$skill"
  snap="$snap_base/$skill"
  echo "Evaluating ${skill} (isolated copy: $snap)"

  mkdir -p "$snap"
  if ! git -C "$root" ls-files -z --cached --others --exclude-standard \
      | { grep -zv -e '^eval-results/' -e "^${results_rel:-eval-results}/" || true; } \
      | tar -C "$root" --null -T - -cf - | tar -C "$snap" -xf -; then
    echo "::error::could not create isolated copy for suite ${skill}" >&2
    exit 1
  fi
  if [[ ! -f "$snap/evals/$skill/eval.yaml" ]]; then
    echo "::error::isolated copy for suite ${skill} is missing evals/$skill/eval.yaml" >&2
    exit 1
  fi

  protect_checkout
  # Relative spec path inside the copy keeps skill and task paths resolved exactly
  # as they were; every output path is absolute.
  if ! (cd "$snap" && waza run "evals/$skill/eval.yaml" \
      --output "$out/results.json" \
      --reporter "junit:$out/junit.xml" \
      --transcript-dir "$out/transcripts"); then
    status=1
  fi
  restore_permissions

  after="$(checkout_state)"
  if [[ "$after" != "$baseline" ]]; then
    echo "::error::suite '${skill}' modified the runner checkout. Results after it are not trustworthy; aborting." >&2
    diff <(printf '%s\n' "$baseline") <(printf '%s\n' "$after") | head -50 >&2 || true
    exit 1
  fi
  rm -rf "$snap"
done

exit "$status"
