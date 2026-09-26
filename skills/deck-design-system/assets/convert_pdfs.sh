#!/usr/bin/env bash
# Phase 1: convert every .pptx in SRC to PDF in OUT with headless LibreOffice in Docker.
# Usage: convert_pdfs.sh <src-dir> <out-dir>
# Requires Docker (WSL2 backend on Windows). Windows-native LibreOffice is unreliable for batch conversion.
set -euo pipefail

SRC="$(cd "$1" && pwd)"
OUT="$(mkdir -p "$2" && cd "$2" && pwd)"

docker run --rm -v "$SRC:/in:ro" -v "$OUT:/out" --entrypoint bash instructure/libreoffice:26.2 -c '
  for f in /in/*.pptx; do
    soffice -env:UserInstallation=file:///tmp/lo --headless --norestore --convert-to pdf --outdir /out "$f"
  done
'

ls -la "$OUT"
