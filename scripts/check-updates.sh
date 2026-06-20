#!/bin/bash
# Check for updates in upstream skill repos
# Usage: ./scripts/check-updates [skill-name]
set -euo pipefail

LIBRARY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$LIBRARY_DIR/skills"

if [ $# -gt 0 ]; then
  skill_names=("$@")
else
  skill_names=($(ls -1 "$SKILLS_DIR"))
fi

echo "Checking for updates in ${#skill_names[@]} skills..."
echo ""

for skill in "${skill_names[@]}"; do
  skill_dir="$SKILLS_DIR/$skill"
  meta_file="$skill_dir/metadata.yaml"
  
  if [ ! -f "$meta_file" ]; then
    echo "⚠️  $skill: no metadata.yaml found"
    continue
  fi
  
  # Extract origin URL
  origin=$(grep "^origin:" "$meta_file" | sed 's/^origin: *//')
  
  if [ -z "$origin" ]; then
    echo "⚠️  $skill: no origin URL in metadata"
    continue
  fi
  
  echo "✅ $skill → $origin"
done
