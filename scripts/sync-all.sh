#!/bin/bash
# Auto-sync ALL skills from svg153/skills GitHub repo to Hermes
# Usage: ./scripts/sync-all [pull|symlink|verify|full]
set -euo pipefail

LIBRARY_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILLS_DIR="$LIBRARY_DIR/skills"
HERMES_SKILLS="/hermes-home/skills"
REMOTE_REPO="https://github.com/svg153/skills.git"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_ok() { echo -e "${GREEN}✅ $1${NC}"; }
log_warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }
log_err() { echo -e "${RED}❌ $1${NC}"; }

# Step 1: Pull latest from remote
do_pull() {
    echo "=== Pulling latest from $REMOTE_REPO ==="
    cd "$LIBRARY_DIR"
    if git remote get-url origin | grep -q "svg153/skills"; then
        git pull origin main 2>&1 || {
            log_warn "Git pull failed, trying to fetch first..."
            git fetch origin
            git reset --hard origin/main 2>&1 || true
        }
        log_ok "Repository up to date"
    else
        log_warn "Not a svg153/skills repo, skipping pull"
    fi
}

# Step 2: Create/update symlinks for ALL skills
do_symlink() {
    echo ""
    echo "=== Creating symlinks for all skills ==="
    
    created=0
    skipped=0
    errors=0
    
    for skill in $(ls -1 "$SKILLS_DIR"); do
        skill_path="$SKILLS_DIR/$skill"
        
        # Skip if not a directory
        if [ ! -d "$skill_path" ]; then
            log_warn "$skill: not a directory, skipping"
            skipped=$((skipped + 1))
            continue
        fi
        
        target="$HERMES_SKILLS/$skill"
        
        if [ -L "$target" ]; then
            # Already a symlink
            current=$(readlink "$target")
            if [ "$current" = "$skill_path" ]; then
                log_ok "$skill → already linked correctly"
            else
                ln -sf "$skill_path" "$target"
                log_ok "$skill → re-linked to $skill_path"
            fi
            skipped=$((skipped + 1))
        elif [ -e "$target" ]; then
            # Exists as real directory/file
            log_warn "$skill → exists as real directory, NOT overwriting"
            skipped=$((skipped + 1))
        else
            # Create new symlink
            ln -sf "$skill_path" "$target"
            log_ok "$skill → symlink created"
            created=$((created + 1))
        fi
    done
    
    echo ""
    echo "Summary: $created created, $skipped skipped"
}

# Step 3: Verify all skills are accessible
do_verify() {
    echo ""
    echo "=== Verifying all skills ==="
    
    total=0
    ok=0
    missing=0
    
    for skill in $(ls -1 "$SKILLS_DIR"); do
        total=$((total + 1))
        
        # Check symlink exists
        if [ ! -L "$HERMES_SKILLS/$skill" ]; then
            log_err "$skill → no symlink"
            missing=$((missing + 1))
            continue
        fi
        
        # Check SKILL.md exists
        if [ -f "$HERMES_SKILLS/$skill/SKILL.md" ]; then
            ok=$((ok + 1))
        else
            log_err "$skill → SKILL.md missing"
            missing=$((missing + 1))
        fi
    done
    
    echo ""
    echo "Verification: $ok/$total skills OK, $missing missing"
    
    if [ $missing -gt 0 ]; then
        return 1
    fi
}

# Step 4: List all skills with status
do_list() {
    echo ""
    echo "=== Skills in svg153/skills repo ==="
    echo ""
    
    for skill in $(ls -1 "$SKILLS_DIR"); do
        skill_path="$SKILLS_DIR/$skill"
        target="$HERMES_SKILLS/$skill"
        
        # Get metadata
        meta_file="$skill_path/metadata.yaml"
        if [ -f "$meta_file" ]; then
            origin=$(grep "^origin:" "$meta_file" 2>/dev/null | sed 's/^origin: *//' || echo "N/A")
            category=$(grep "^category:" "$meta_file" 2>/dev/null | sed 's/^category: *//' || echo "N/A")
            status=$(grep "^status:" "$meta_file" 2>/dev/null | sed 's/^status: *//' || echo "N/A")
        else
            origin="N/A"
            category="N/A"
            status="N/A"
        fi
        
        # Check symlink status
        if [ -L "$target" ]; then
            link_status="✅ linked"
        elif [ -d "$target" ]; then
            link_status="📁 local dir"
        else
            link_status="❌ not synced"
        fi
        
        echo "  $link_status  $skill  |  category: $category  |  status: $status  |  origin: $origin"
    done
    
    echo ""
    echo "Total: $(ls -1 "$SKILLS_DIR" | wc -l) skills"
}

# Main
case "${1:-full}" in
    pull)
        do_pull
        ;;
    symlink)
        do_symlink
        ;;
    verify)
        do_verify
        ;;
    list)
        do_list
        ;;
    full)
        do_pull
        do_symlink
        do_verify
        do_list
        ;;
    *)
        echo "Usage: $0 [pull|symlink|verify|list|full]"
        echo "  pull     - Pull latest from remote"
        echo "  symlink  - Create/update symlinks for all skills"
        echo "  verify   - Verify all skills are accessible"
        echo "  list     - List all skills with status"
        echo "  full     - Pull + symlink + verify + list (default)"
        ;;
esac
