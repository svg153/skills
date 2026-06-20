#!/bin/bash
# Migrate skills from .agents/skills to skills-library with metadata
set -euo pipefail

SKILLS_DIR="/tmp/reclaimit/.agents/skills"
LIBRARY_DIR="/tmp/reclaimit/skills-library/skills"

# Origin mapping: skill name -> origin URL
declare -A ORIGIN_MAP=(
  ["gentle-ai-ecosystem"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["branch-pr"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["chained-pr"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["cognitive-doc-design"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["comment-writer"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["go-testing"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["issue-creation"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["judgment-day"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-apply"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-archive"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-design"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-explore"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-init"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-onboard"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-propose"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-spec"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-tasks"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["sdd-verify"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["skill-creator"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["skill-improver"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["skill-registry"]="https://github.com/Gentleman-Programming/gentle-ai"
  ["work-unit-commits"]="https://github.com/Gentleman-Programming/gentle-ai"
)

# Category mapping
declare -A CATEGORY_MAP=(
  ["gentle-ai-ecosystem"]="software-development"
  ["branch-pr"]="github"
  ["chained-pr"]="github"
  ["cognitive-doc-design"]="software-development"
  ["comment-writer"]="software-development"
  ["go-testing"]="software-development"
  ["issue-creation"]="github"
  ["judgment-day"]="software-development"
  ["sdd-apply"]="software-development"
  ["sdd-archive"]="software-development"
  ["sdd-design"]="software-development"
  ["sdd-explore"]="software-development"
  ["sdd-init"]="software-development"
  ["sdd-onboard"]="software-development"
  ["sdd-propose"]="software-development"
  ["sdd-spec"]="software-development"
  ["sdd-tasks"]="software-development"
  ["sdd-verify"]="software-development"
  ["skill-creator"]="software-development"
  ["skill-improver"]="software-development"
  ["skill-registry"]="software-development"
  ["work-unit-commits"]="software-development"
)

for skill_dir in "$SKILLS_DIR"/*/; do
  skill_name=$(basename "$skill_dir")
  
  # Skip _shared
  if [ "$skill_name" = "_shared" ]; then
    continue
  fi
  
  # Skip symlinks
  if [ -L "$skill_dir" ]; then
    continue
  fi
  
  target_dir="$LIBRARY_DIR/$skill_name"
  mkdir -p "$target_dir"
  
  # Copy SKILL.md
  if [ -f "$skill_dir/SKILL.md" ]; then
    cp "$skill_dir/SKILL.md" "$target_dir/SKILL.md"
  fi
  
  # Copy references
  if [ -d "$skill_dir/references" ]; then
    mkdir -p "$target_dir/references"
    cp -r "$skill_dir/references/"* "$target_dir/references/" 2>/dev/null || true
  fi
  
  # Copy templates
  if [ -d "$skill_dir/templates" ]; then
    mkdir -p "$target_dir/templates"
    cp -r "$skill_dir/templates/"* "$target_dir/templates/" 2>/dev/null || true
  fi
  
  # Copy scripts
  if [ -d "$skill_dir/scripts" ]; then
    mkdir -p "$target_dir/scripts"
    cp -r "$skill_dir/scripts/"* "$target_dir/scripts/" 2>/dev/null || true
  fi
  
  # Copy assets
  if [ -d "$skill_dir/assets" ]; then
    mkdir -p "$target_dir/assets"
    cp -r "$skill_dir/assets/"* "$target_dir/assets/" 2>/dev/null || true
  fi
  
  # Generate metadata.yaml
  origin="${ORIGIN_MAP[$skill_name]:-https://github.com/Gentleman-Programming/gentle-ai}"
  category="${CATEGORY_MAP[$skill_name]:-software-development}"
  
  cat > "$target_dir/metadata.yaml" << EOF
name: $skill_name
origin: $origin
origin_path: /gentle-ai
category: $category
status: active
sync:
  enabled: true
  interval: weekly
  strategy: manual
tags:
  - gentle-ai
  - sdd
EOF
  
  echo "Migrated: $skill_name"
done

echo ""
echo "Migration complete. Total skills: $(ls -1 $LIBRARY_DIR | wc -l)"
