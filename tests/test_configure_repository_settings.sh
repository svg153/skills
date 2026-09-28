#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
script="$root/scripts/configure-repository-settings.sh"
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

mock_bin="$tmp/bin"
mkdir -p "$mock_bin"
log="$tmp/gh.log"

cat > "$mock_bin/gh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

printf '%s\n' "$*" >> "$GH_LOG"

if [[ "$1" == auth ]]; then
  exit 0
fi
if [[ "$1" == repo ]]; then
  exit 0
fi
if [[ "$1" != api ]]; then
  exit 0
fi

shift
method=GET
endpoint=""
while (($#)); do
  case "$1" in
    --method) method="$2"; shift 2 ;;
    --input)
      body="$(cat)"
      printf 'BODY %s\n' "$body" >> "$GH_LOG"
      shift 2
      ;;
    --jq) shift 2 ;;
    --paginate|--silent) shift ;;
    -f) shift 2 ;;
    *)
      if [[ -z "$endpoint" && "$1" != -* ]]; then endpoint="$1"; fi
      shift
      ;;
  esac
done

printf '%s %s\n' "$method" "$endpoint" >> "$GH_LOG"
if [[ "$method" != GET ]]; then
  exit 0
fi

case "$endpoint" in
  repos/*/private-vulnerability-reporting)
    printf '%s\n' '{"enabled":true}'
    ;;
  repos/*/automated-security-fixes)
    if [[ "$GH_SCENARIO" == fresh ]]; then
      printf '%s\n' '{"enabled":false}'
    else
      printf '%s\n' '{"enabled":true}'
    fi
    ;;
  repos/*/code-scanning/default-setup)
    if [[ "$GH_SCENARIO" == codeql-disabled ]]; then
      printf '%s\n' '{"state":"not-configured"}'
    else
      printf '%s\n' '{"state":"configured"}'
    fi
    ;;
  repos/*/rulesets\?per_page=100)
    case "$GH_SCENARIO" in
      managed) printf '%s\n' '[{"id":1,"name":"main-pull-request"}]' ;;
      custom) printf '%s\n' '[{"id":2,"name":"custom-protection"}]' ;;
      *) printf '%s\n' '[]' ;;
    esac
    ;;
  users/maintainer)
    printf '%s\n' '{"id":42,"login":"maintainer"}'
    ;;
  repos/*)
    if [[ "$GH_SCENARIO" == no-admin ]]; then
      printf '%s\n' '{"default_branch":"main","permissions":{"admin":false},"security_and_analysis":{}}'
    elif [[ "$GH_SCENARIO" == fresh ]]; then
      printf '%s\n' '{"default_branch":"main","permissions":{"admin":true},"security_and_analysis":{"secret_scanning":{"status":"disabled"},"secret_scanning_push_protection":{"status":"disabled"}}}'
    elif [[ "$GH_SCENARIO" == non-main ]]; then
      printf '%s\n' '{"default_branch":"develop","permissions":{"admin":true},"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}'
    else
      printf '%s\n' '{"default_branch":"main","permissions":{"admin":true},"security_and_analysis":{"secret_scanning":{"status":"enabled"},"secret_scanning_push_protection":{"status":"enabled"}}}'
    fi
    ;;
  *)
    printf '%s\n' '{}'
    ;;
esac
EOF
chmod +x "$mock_bin/gh"

run_case() {
  local scenario="$1"
  shift
  : > "$log"
  GH_SCENARIO="$scenario" GH_LOG="$log" PATH="$mock_bin:$PATH" bash "$script" --repo owner/repo "$@"
}

assert_log_absent() {
  ! grep -Fq -- "$1" "$log"
}

echo "metadata behavior"
run_case default
grep -Fq 'repo edit owner/repo' "$log"
grep -Fq 'PUT repos/owner/repo/topics' "$log"
grep -Fq 'PUT repos/owner/repo/private-vulnerability-reporting' "$log"
assert_log_absent 'automated-security-fixes'

echo "fresh security configuration"
output="$(run_case fresh --configure-security --bypass-login maintainer --required-check test --required-check title --required-check commits)"
grep -Fq 'PATCH repos/owner/repo' "$log"
grep -Fq 'PUT repos/owner/repo/automated-security-fixes' "$log"
grep -Fq 'POST repos/owner/repo/rulesets' "$log"
grep -Fq 'explicit bypass user maintainer' <<<"$output"
grep -Fq 'refs/heads/main' "$log"
grep -Fq '"context":"test"' "$log"

echo "non-main default branch is targeted"
output="$(run_case non-main --configure-security --bypass-login maintainer --required-check ci/test)"
grep -Fq 'POST repos/owner/repo/rulesets' "$log"
grep -Fq 'refs/heads/develop' "$log"
grep -Fq 'created main-pull-request' <<<"$output"

echo "idempotent existing state"
run_case managed --configure-security --bypass-login maintainer >/dev/null
assert_log_absent 'PATCH repos/owner/repo'
assert_log_absent 'PUT repos/owner/repo/automated-security-fixes'
assert_log_absent 'POST repos/owner/repo/rulesets'

echo "unrelated ruleset is preserved"
output="$(run_case custom --configure-security --bypass-login maintainer)"
assert_log_absent 'POST repos/owner/repo/rulesets'
grep -Fq 'existing branch/tag rulesets detected' <<<"$output"

echo "missing bypass identity is reported"
output="$(run_case fresh --configure-security --required-check ci/test)"
assert_log_absent 'POST repos/owner/repo/rulesets'
grep -Fq 'no bypass identity supplied' <<<"$output"

echo "missing required checks are reported"
output="$(run_case fresh --configure-security --bypass-login maintainer)"
assert_log_absent 'POST repos/owner/repo/rulesets'
grep -Fq 'required status checks were not supplied' <<<"$output"

echo "insufficient permissions are reported"
output="$(run_case no-admin --configure-security)"
grep -Fq 'repository administration permission' <<<"$output"
assert_log_absent 'automated-security-fixes'

echo "CodeQL pending state is reported without a write"
output="$(run_case codeql-disabled --configure-security --bypass-login maintainer)"
grep -Fq 'CodeQL default setup is not-configured' <<<"$output"
assert_log_absent 'PATCH repos/owner/repo/code-scanning/default-setup'

echo "dry-run is a safe no-op"
output="$(run_case fresh --configure-security --bypass-login maintainer --dry-run)"
grep -Fq 'DRY-RUN' <<<"$output"
! grep -Fq 'created main-pull-request' <<<"$output"
! grep -Fq 'enabled missing secret scanning protections' <<<"$output"
assert_log_absent 'repo edit'
assert_log_absent '--method'

echo "All repository settings tests passed."
