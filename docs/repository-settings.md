# Repository settings

Portable project policy lives in Git, but GitHub repository metadata requires an administrator identity and cannot be changed by an ordinary workflow `GITHUB_TOKEN`.

Apply the desired state from an authenticated GitHub CLI session:

```bash
./scripts/configure-repository-settings.sh --repo svg153/skills
```

The script is idempotent and converges the repository on:

- description: cross-agent Agent Skills catalog with provenance, stable sync, behavioral evals, and reproducible packaging;
- homepage: `https://svg153.github.io/skills/`;
- automatic deletion of pull-request head branches after merge;
- wiki disabled, so README/docs/Pages remain the documentation sources of truth;
- a focused set of Agent Skills, agent host, open-source, Waza, and Pages topics;
- GitHub private vulnerability reporting enabled.

The script **replaces** the topic set rather than only appending topics, so repeated runs do not accumulate stale discovery metadata.

Security settings are opt-in and read before every security write:

```bash
./scripts/configure-repository-settings.sh \
  --repo svg153/skills \
  --configure-security \
  --bypass-login MAINTAINER_LOGIN
```

The security mode enables only missing secret-scanning protections and Dependabot security updates. It reports CodeQL default setup for UI or entitlement review, and it creates the managed `main-pull-request` ruleset only when no rulesets exist and an explicit bypass login is supplied. Existing rulesets are preserved and reported, never replaced. Use `--dry-run` for a read-only report.

## Branch cleanup

Native `delete_branch_on_merge` is the preferred mechanism because it needs no runner or repository write token. `.github/workflows/cleanup-merged-branches.yml` remains a narrow fallback for merged same-repository pull requests and no longer runs a second time on every push to `main`.

## Inspect the effective state

```bash
gh api repos/svg153/skills \
  --jq '{description, homepage, delete_branch_on_merge, has_wiki, topics}'

gh api repos/svg153/skills/private-vulnerability-reporting \
  --jq '{enabled}'
```

Administrative settings are intentionally not hidden inside CI. Metadata failures remain fatal; opt-in security operations report missing administration permission or feature entitlement without pretending the settings were applied.
