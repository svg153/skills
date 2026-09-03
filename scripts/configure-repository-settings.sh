#!/usr/bin/env bash
# Apply GitHub repository properties that require an administrator identity.
set -euo pipefail

repo="${1:-svg153/skills}"
homepage="https://svg153.github.io/skills/"
description="Cross-agent Agent Skills catalog with provenance, stable upstream sync, behavioral evals, and reproducible packaging."

if ! command -v gh >/dev/null 2>&1; then
  echo "ERROR: GitHub CLI (gh) is required." >&2
  exit 1
fi

gh auth status >/dev/null

echo "Configuring $repo"
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

echo "Repository state:"
gh api "repos/$repo" \
  --jq '{description, homepage, delete_branch_on_merge, has_wiki, topics}'

echo "Private vulnerability reporting:"
gh api "repos/$repo/private-vulnerability-reporting" --jq '{enabled}'
