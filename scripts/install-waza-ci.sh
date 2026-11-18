#!/usr/bin/env bash
set -euo pipefail

# CI-only installer: pin both the Waza release and the release asset digest.
# Local developers may use the upstream supported installation methods.
WAZA_VERSION="0.41.0"
WAZA_SHA256="9c7397d8d28127d7c99ec6ad1fab730cbd438174a3960afbc82c3a60dacccb74"
WAZA_URL="https://github.com/microsoft/waza/releases/download/v${WAZA_VERSION}/waza-linux-amd64"
DESTINATION="${1:-${RUNNER_TEMP:-/tmp}/waza}"

if [[ "$(uname -s)" != "Linux" || "$(uname -m)" != "x86_64" ]]; then
  echo "ERROR: scripts/install-waza-ci.sh supports the GitHub-hosted Linux x86_64 runner only." >&2
  exit 2
fi

tmp="$(mktemp)"
trap 'rm -f "$tmp"' EXIT

curl --fail --location --silent --show-error --retry 3 --output "$tmp" "$WAZA_URL"
printf '%s  %s\n' "$WAZA_SHA256" "$tmp" | sha256sum --check --status || {
  echo "ERROR: Waza v${WAZA_VERSION} checksum verification failed." >&2
  exit 1
}

mkdir -p "$(dirname "$DESTINATION")"
install -m 0755 "$tmp" "$DESTINATION"
"$DESTINATION" --version
