#!/usr/bin/env bash
# Apply the repository settings that cannot be managed by GITHUB_TOKEN workflows.
# Requires an authenticated GitHub CLI identity with Administration: write.
set -euo pipefail

repo="${1:-svg153/skills}"

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI (gh) is required." >&2
  exit 1
fi

gh auth status >/dev/null

echo "Configuring $repo"
gh repo edit "$repo" \
  --description "Portable Agent Skills catalog with provenance, stable upstream sync, npx skills discovery, and reproducible agent packaging" \
  --delete-branch-on-merge \
  --add-topic agent-skills \
  --add-topic ai-agents \
  --add-topic skills-sh \
  --add-topic codex \
  --add-topic github-copilot \
  --add-topic claude-code \
  --add-topic developer-tools \
  --add-topic automation

echo "Result:"
gh repo view "$repo" --json description,deleteBranchOnMerge,repositoryTopics \
  --jq '{description, deleteBranchOnMerge, topics: [.repositoryTopics[].name]}'
