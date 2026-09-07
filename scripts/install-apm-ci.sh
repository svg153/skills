#!/usr/bin/env bash
# Install the exact APM CLI release approved for repository automation.
# Keep the version and release checksum here so every workflow uses one pin.
set -euo pipefail

readonly APM_VERSION="0.30.0"
readonly APM_ARCHIVE_SHA256="8b84bebf19c350faf36d21aebb350dc656d04c0b7a1c2bf8ea35c0caa0e44bb9"
readonly APM_ASSET="apm-linux-x86_64.tar.gz"

: "${RUNNER_TEMP:?RUNNER_TEMP must be set (this installer is CI-specific)}"
: "${GITHUB_PATH:?GITHUB_PATH must be set (this installer is CI-specific)}"

archive="$RUNNER_TEMP/$APM_ASSET"
extracted="$RUNNER_TEMP/apm-extracted"
rm -rf "$extracted"
mkdir -p "$extracted"

curl --fail --silent --show-error --location \
  "https://github.com/microsoft/apm/releases/download/v${APM_VERSION}/${APM_ASSET}" \
  --output "$archive"
echo "${APM_ARCHIVE_SHA256}  ${archive}" | sha256sum --check --strict

tar -xzf "$archive" -C "$extracted"
apm_binary=$(find "$extracted" -type f -name apm -print -quit)
test -n "$apm_binary"
apm_dir=$(dirname "$apm_binary")
test -d "$apm_dir/_internal"

"$apm_binary" --version | tee /tmp/apm-version.txt
grep -q "$APM_VERSION" /tmp/apm-version.txt
echo "$apm_dir" >> "$GITHUB_PATH"

echo "OK: installed checksum-verified APM CLI v${APM_VERSION}"
