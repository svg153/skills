#!/usr/bin/env bash
# Apply GitHub repository properties that require an administrator identity.
set -euo pipefail

default_repo="svg153/skills"
repo="$default_repo"
configure_security=false
configure_metadata_requested=false
dry_run=false
bypass_login=""
required_checks=()
ruleset_name="main-pull-request"
homepage="https://svg153.github.io/skills/"
description="Cross-agent Agent Skills catalog with provenance, stable upstream sync, behavioral evals, and reproducible packaging."

usage() {
  cat <<'EOF'
Usage: ./scripts/configure-repository-settings.sh [options]

Options:
  --repo OWNER/REPO             Repository to configure (default: svg153/skills)
  --configure-security          Read and configure supported security defaults
  --configure-metadata          Explicitly apply metadata, topics, and vulnerability reporting
  --bypass-login LOGIN          Explicit GitHub user for a new default-branch ruleset
  --required-check CONTEXT      Required status check (repeat for each check)
  --dry-run                     Report planned writes without changing GitHub
  -h, --help                   Show this help
EOF
}

while (($#)); do
  case "$1" in
    --repo)
      [[ $# -ge 2 ]] || { echo "ERROR: --repo requires OWNER/REPO." >&2; exit 2; }
      repo="$2"
      shift 2
      ;;
    --configure-security)
      configure_security=true
      shift
      ;;
    --configure-metadata)
      configure_metadata_requested=true
      shift
      ;;
    --bypass-login)
      [[ $# -ge 2 ]] || { echo "ERROR: --bypass-login requires a GitHub login." >&2; exit 2; }
      bypass_login="$2"
      shift 2
      ;;
    --required-check)
      [[ $# -ge 2 && -n "$2" && "$2" != -* ]] || { echo "ERROR: --required-check requires a check context." >&2; exit 2; }
      required_checks+=("$2")
      shift 2
      ;;
    --dry-run)
      dry_run=true
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      if [[ "$repo" == "svg153/skills" && "$1" != -* ]]; then
        repo="$1"
        shift
      else
        echo "ERROR: unknown option: $1" >&2
        usage >&2
        exit 2
      fi
      ;;
  esac
done

if [[ ! "$repo" =~ ^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$ ]]; then
  echo "ERROR: --repo must be an OWNER/REPO slug." >&2
  exit 2
fi

if [[ "$repo" != "$default_repo" && "$configure_security" != true && "$configure_metadata_requested" != true ]]; then
  echo "ERROR: metadata writes for --repo $repo require explicit --configure-metadata." >&2
  exit 2
fi

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI (gh) is required." >&2
  exit 1
fi

if [[ "$configure_security" == true ]] && ! command -v jq >/dev/null 2>&1; then
  echo "ERROR: jq is required with --configure-security." >&2
  exit 1
fi

gh auth status >/dev/null

api_read() {
  gh api "$1"
}

api_write() {
  local method="$1" endpoint="$2" body=""
  if [[ $# -ge 3 ]]; then body="$3"; fi
  if [[ "$dry_run" == true ]]; then
    echo "DRY-RUN: would $method $endpoint"
    return 0
  fi
  if [[ -n "$body" ]]; then
    printf '%s' "$body" | gh api --method "$method" "$endpoint" --input - >/dev/null
  else
    gh api --method "$method" "$endpoint" --silent
  fi
}

report_api_failure() {
  local action="$1" error="$2"
  echo "REPORT: $action was not changed; verify GitHub permissions or feature entitlement manually."
  [[ -n "$error" ]] && echo "REPORT: $error"
}

configure_metadata() {
  if [[ "$dry_run" == true ]]; then
    echo "DRY-RUN: would configure repository metadata, topics, and private vulnerability reporting."
    return
  fi

  gh repo edit "$repo" \
    --description "$description" \
    --homepage "$homepage" \
    --delete-branch-on-merge \
    --enable-wiki=false

  # Replace topics rather than only appending them so repeated runs converge on one state.
  gh api --method PUT "repos/$repo/topics" \
    -f 'names[]=agent-skills' \
    -f 'names[]=ai-agents' \
    -f 'names[]=agent-plugins' \
    -f 'names[]=skills-sh' \
    -f 'names[]=github-copilot' \
    -f 'names[]=codex' \
    -f 'names[]=claude-code' \
    -f 'names[]=cursor' \
    -f 'names[]=gemini-cli' \
    -f 'names[]=developer-tools' \
    -f 'names[]=open-source' \
    -f 'names[]=software-reuse' \
    -f 'names[]=waza' \
    -f 'names[]=github-pages' \
    -f 'names[]=automation' >/dev/null

  # Prefer private security reports over public disclosure of exploit details.
  gh api --method PUT "repos/$repo/private-vulnerability-reporting" --silent
}

configure_security() {
  local base="repos/$repo" repo_state security_state secret_status push_status default_branch
  if ! repo_state=$(api_read "$base" 2>&1); then
    report_api_failure "security defaults" "$repo_state"
    return
  fi

  if [[ "$(jq -r '.permissions.admin // false' <<<"$repo_state")" != true ]]; then
    report_api_failure "security defaults" "authenticated account does not have verified repository administration permission"
    return
  fi

  default_branch=$(jq -r '.default_branch // empty' <<<"$repo_state")
  if [[ -z "$default_branch" ]]; then
    report_api_failure "branch ruleset" "repository response did not contain default_branch"
    return
  fi

  if ! security_state=$(jq -c '.security_and_analysis // {}' <<<"$repo_state"); then
    report_api_failure "secret scanning and push protection" "repository response did not contain readable security settings"
  else
    secret_status=$(jq -r '.secret_scanning.status // "unavailable"' <<<"$security_state")
    push_status=$(jq -r '.secret_scanning_push_protection.status // "unavailable"' <<<"$security_state")
    local security_body='{}'
    if [[ "$secret_status" != enabled ]]; then
      security_body=$(jq -c '. + {secret_scanning: {status: "enabled"}}' <<<"$security_body")
    fi
    if [[ "$push_status" != enabled ]]; then
      security_body=$(jq -c '. + {secret_scanning_push_protection: {status: "enabled"}}' <<<"$security_body")
    fi
    if [[ "$security_body" == '{}' ]]; then
      echo "Security: secret scanning and push protection already enabled; no write needed."
    else
      local error
      if [[ "$dry_run" == true ]]; then
        api_write PATCH "$base" "{\"security_and_analysis\":$security_body}"
        echo "REPORT: dry-run only; secret scanning protections were not changed."
      elif error=$(api_write PATCH "$base" "{\"security_and_analysis\":$security_body}" 2>&1); then
        echo "Security: enabled missing secret scanning protections."
      else
        report_api_failure "secret scanning and push protection" "$error"
      fi
    fi
  fi

  local dependabot_state dependabot_enabled error
  if ! dependabot_state=$(api_read "$base/automated-security-fixes" 2>&1); then
    report_api_failure "Dependabot security updates" "$dependabot_state"
  else
    dependabot_enabled=$(jq -r '.enabled // false' <<<"$dependabot_state")
    if [[ "$dependabot_enabled" == true ]]; then
      echo "Security: Dependabot security updates already enabled; no write needed."
    elif [[ "$dry_run" == true ]]; then
      api_write PUT "$base/automated-security-fixes"
      echo "REPORT: dry-run only; Dependabot security updates were not changed."
    elif error=$(api_write PUT "$base/automated-security-fixes" 2>&1); then
      echo "Security: enabled Dependabot security updates."
    else
      report_api_failure "Dependabot security updates" "$error"
    fi
  fi

  local codeql_state codeql_status
  if ! codeql_state=$(api_read "$base/code-scanning/default-setup" 2>&1); then
    report_api_failure "CodeQL default setup" "$codeql_state"
  else
    codeql_status=$(jq -r '.state // "unknown"' <<<"$codeql_state")
    if [[ "$codeql_status" == configured ]]; then
      echo "Security: CodeQL default setup is already configured; no write needed."
    else
      echo "REPORT: CodeQL default setup is $codeql_status; review or enable it in repository Settings > Advanced Security."
    fi
  fi

  configure_ruleset "$base" "$default_branch"
}

configure_ruleset() {
  local base="$1" default_branch="$2" rulesets actor_json actor_id ruleset_count error
  if ! rulesets=$(api_read "$base/rulesets?per_page=100" 2>&1); then
    report_api_failure "branch ruleset" "$rulesets"
    return
  fi

  ruleset_count=$(jq 'length' <<<"$rulesets")
  if (( ruleset_count > 0 )); then
    if [[ "$(jq --arg name "$ruleset_name" '[.[] | select(.name == $name)] | length' <<<"$rulesets")" -gt 0 ]]; then
      echo "Ruleset: $ruleset_name already exists; preserving it without replacement."
    else
      echo "REPORT: existing branch/tag rulesets detected; not adding or replacing $ruleset_name. Review them manually."
    fi
    return
  fi

  if [[ -z "$bypass_login" ]]; then
    echo "REPORT: no bypass identity supplied; pass --bypass-login LOGIN before creating $ruleset_name."
    return
  fi

  if ((${#required_checks[@]} == 0)); then
    echo "REPORT: required status checks were not supplied; skipping $ruleset_name creation. Pass --required-check CONTEXT once per check."
    return
  fi

  if ! actor_json=$(api_read "users/$bypass_login" 2>&1); then
    report_api_failure "branch ruleset" "$actor_json"
    return
  fi
  actor_id=$(jq -r '.id // empty' <<<"$actor_json")
  if [[ ! "$actor_id" =~ ^[0-9]+$ ]]; then
    report_api_failure "branch ruleset" "GitHub did not return a numeric ID for --bypass-login $bypass_login"
    return
  fi

  local required_status_checks='[]' check ruleset
  for check in "${required_checks[@]}"; do
    required_status_checks=$(jq -c --arg context "$check" '. + [{context: $context}]' <<<"$required_status_checks")
  done

  ruleset=$(jq -cn --argjson actor_id "$actor_id" --arg name "$ruleset_name" --arg branch "$default_branch" --argjson checks "$required_status_checks" '{
    name: $name,
    target: "branch",
    enforcement: "active",
    conditions: {ref_name: {include: ["refs/heads/" + $branch], exclude: []}},
    rules: [
      {type: "deletion"},
      {type: "non_fast_forward"},
      {type: "required_linear_history"},
      {type: "pull_request", parameters: {
        dismiss_stale_reviews_on_push: true,
        require_code_owner_review: true,
        require_last_push_approval: false,
        required_approving_review_count: 1,
        required_review_thread_resolution: true,
        allowed_merge_methods: ["squash"]
      }},
      {type: "required_status_checks", parameters: {
        strict_required_status_checks_policy: true,
        do_not_enforce_on_create: false,
        required_status_checks: $checks
      }}
    ],
    bypass_actors: [{actor_id: $actor_id, actor_type: "User", bypass_mode: "always"}]
  }')

  if [[ "$dry_run" == true ]]; then
    api_write POST "$base/rulesets" "$ruleset"
    echo "REPORT: dry-run only; $ruleset_name was not created."
  elif error=$(api_write POST "$base/rulesets" "$ruleset" 2>&1); then
    echo "Ruleset: created $ruleset_name with explicit bypass user $bypass_login."
  else
    report_api_failure "branch ruleset" "$error"
  fi
}

echo "Configuring $repo"
if [[ "$configure_metadata_requested" == true ]]; then
  configure_metadata
elif [[ "$configure_security" != true && "$repo" == "$default_repo" ]]; then
  configure_metadata
else
  echo "Metadata: skipped; security mode is non-destructive."
fi

if [[ "$configure_security" == true ]]; then
  configure_security
else
  echo "Security: skipped; pass --configure-security to inspect and configure security defaults."
fi

echo "Repository state:"
gh api "repos/$repo" --jq '{description, homepage, delete_branch_on_merge, has_wiki, topics}'

echo "Private vulnerability reporting:"
gh api "repos/$repo/private-vulnerability-reporting" --jq '{enabled}'
