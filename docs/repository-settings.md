# Repository settings

The repository keeps portable workflow logic in Git, but a few GitHub repository properties require `Administration: write` and cannot be changed by the normal `GITHUB_TOKEN` used by Actions.

Apply the desired settings from an authenticated GitHub CLI session:

```bash
./scripts/configure-repository-settings.sh
```

The script is idempotent and configures:

- a discovery-oriented repository description;
- automatic deletion of pull-request head branches after merge;
- repository topics for Agent Skills, skills.sh, Codex, Copilot, Claude Code, and agent tooling.

The existing `cleanup-merged-branches.yml` remains a defense-in-depth cleanup for merged branches. The native GitHub setting is preferred because it performs branch deletion without spending runner time.

To inspect the effective state:

```bash
gh repo view svg153/skills \
  --json description,deleteBranchOnMerge,repositoryTopics \
  --jq '{description, deleteBranchOnMerge, topics: [.repositoryTopics[].name]}'
```
