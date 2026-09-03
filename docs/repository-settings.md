# Repository settings

Portable project policy lives in Git, but GitHub repository metadata requires an administrator identity and cannot be changed by an ordinary workflow `GITHUB_TOKEN`.

Apply the desired state from an authenticated GitHub CLI session:

```bash
./scripts/configure-repository-settings.sh
```

The script is idempotent and converges the repository on:

- description: cross-agent Agent Skills catalog with provenance, stable sync, behavioral evals, and reproducible packaging;
- homepage: `https://svg153.github.io/skills/`;
- automatic deletion of pull-request head branches after merge;
- wiki disabled, so README/docs/Pages remain the documentation sources of truth;
- a focused set of Agent Skills, agent host, open-source, Waza, and Pages topics;
- GitHub private vulnerability reporting enabled.

The script **replaces** the topic set rather than only appending topics, so repeated runs do not accumulate stale discovery metadata.

## Branch cleanup

Native `delete_branch_on_merge` is the preferred mechanism because it needs no runner or repository write token. `.github/workflows/cleanup-merged-branches.yml` remains a narrow fallback for merged same-repository pull requests and no longer runs a second time on every push to `main`.

## Inspect the effective state

```bash
gh api repos/svg153/skills \
  --jq '{description, homepage, delete_branch_on_merge, has_wiki, topics}'

gh api repos/svg153/skills/private-vulnerability-reporting \
  --jq '{enabled}'
```

Administrative settings are intentionally not hidden inside CI. If the script cannot authenticate with repository administration permission, it fails instead of pretending the settings were applied.
