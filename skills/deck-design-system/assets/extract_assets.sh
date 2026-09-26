#!/usr/bin/env bash
# Phase 2: extract PPTX internals (media, theme, masters, layouts, slides) for design analysis.
# Usage: extract_assets.sh <src-dir> <out-dir>
# Output: <out-dir>/<deck-name>/ppt/...  (analyze_design.py consumes this layout)
set -euo pipefail

SRC="$(cd "$1" && pwd)"
OUT="$(mkdir -p "$2" && cd "$2" && pwd)"

for f in "$SRC"/*.pptx; do
  name="$(basename "$f" .pptx)"
  dest="$OUT/$name"
  mkdir -p "$dest"
  unzip -o -q "$f" 'ppt/media/*' 'ppt/theme/*' 'ppt/slideMasters/*' 'ppt/slideLayouts/*' 'ppt/slides/*' -d "$dest"
  echo "$name: $(find "$dest/ppt/media" -type f | wc -l) media files"
done

echo "Dedup byte-identical media (language variants ship identical assets):"
echo "  find \"$OUT\" -type f -path '*/ppt/media/*' -exec md5sum {} + | sort | uniq -w32 -d"
