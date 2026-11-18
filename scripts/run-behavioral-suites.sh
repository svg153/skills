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
#   suite is one name or a comma-separated list; each must match [a-z0-9-]+ and
#   exist as evals/<suite>/eval.yaml.
# Env: WAZA_MODEL (optional, allowlisted) overrides every suite's config.model.
#      WAZA_MAX_CREDITS (optional) is a fail-closed cumulative AI-credit cap for this
#      run, checked between suites; unset/empty disables it, 0 disables it explicitly.

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"
parent="$(dirname "$root")"
mkdir -p "${1:-$root/eval-results}"
results_root="$(cd "${1:-$root/eval-results}" && pwd -P)"
results_rel=""
[[ "$results_root" == "$root"/* ]] && results_rel="${results_root#"$root"/}"

suite_filter="${2:-}"
# Comma-separated list of suites (validated one by one); empty means every suite.
suite_list=()
if [[ -n "$suite_filter" ]]; then
  IFS=',' read -r -a suite_list <<< "$suite_filter"
  for name in "${suite_list[@]}"; do
    if [[ ! "$name" =~ ^[a-z0-9-]+$ ]]; then
      echo "::error::invalid suite name (allowed: [a-z0-9-]+)" >&2
      exit 2
    fi
  done
fi

# Optional model override (WAZA_MODEL), allowlisted. Empty or "default" keeps each
# suite's config.model. Keep in sync with ALLOWED_MODELS in scripts/eval_cost.py.
ALLOWED_MODELS=(claude-haiku-4.5 claude-sonnet-4.6)
model_args=()
model_override="${WAZA_MODEL:-}"
if [[ -n "$model_override" && "$model_override" != "default" ]]; then
  allowed=0
  for m in "${ALLOWED_MODELS[@]}"; do [[ "$m" == "$model_override" ]] && allowed=1; done
  if [[ $allowed -ne 1 ]]; then
    echo "::error::model '$model_override' is not in the allowlist (${ALLOWED_MODELS[*]})" >&2
    exit 2
  fi
  model_args=(--model "$model_override")
fi

max_credits="${WAZA_MAX_CREDITS:-}"
if [[ -n "$max_credits" && ! "$max_credits" =~ ^[0-9]+([.][0-9]+)?$ ]]; then
  echo "::error::WAZA_MAX_CREDITS must be a non-negative number" >&2
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
if [[ ${#suite_list[@]} -gt 0 ]]; then
  suites=()
  for name in "${suite_list[@]}"; do
    want="$root/evals/$name/eval.yaml"
    if [[ ! -f "$want" ]]; then
      echo "::error::unknown suite '$name': evals/$name/eval.yaml does not exist" >&2
      exit 2
    fi
    suites+=("$want")
  done
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
  if ! (cd "$snap" && waza run "evals/$skill/eval.yaml" "${model_args[@]}" \
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
  # Cumulative AI-credit guard between suites. Waza has no atomic spend cap (its
  # execution budgets cover wall time, model turns and tool calls only), so a run can
  # overshoot the cap by at most one suite. It fails closed: unreported or unparsable
  # credits abort the run instead of letting untracked spend continue.
  if [[ -n "$max_credits" ]]; then
    if ! python3 "$root/scripts/eval_cost.py" guard "$results_root" --cap "$max_credits"; then
      echo "::error::AI-credit budget guard aborted the run (fail-closed)." >&2
      exit 1
    fi
  fi
  rm -rf "$snap"
done

exit "$status"
