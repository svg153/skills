# GitHub Actions security baseline

GitHub Actions workflows are executable supply-chain configuration. This repository validates its workflow policy in CI with `scripts/validate-workflow-security.py` instead of relying only on review convention.

## Required invariants

Every workflow under `.github/workflows/` must satisfy these rules:

1. Declare explicit top-level `permissions`.
2. Give every job a positive `timeout-minutes`.
3. Pin every external `uses:` action to an immutable 40-character commit SHA.
4. Set `persist-credentials: false` on every `actions/checkout` step.
5. Keep the validation workflow read-only.
6. Do not use `pull_request_target` for repository workflows.
7. Use `npm ci --ignore-scripts` when npm dependencies are installed by workflows.
8. Keep GitHub Actions dependencies covered by Dependabot.

Version comments should remain beside pinned SHAs for readability, for example:

```yaml
uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
```

Dependabot may propose a new immutable SHA; review the upstream release before merging it.

## Write-capable workflows

Write permission is an explicit exception, not the default.

### Upstream synchronization

`sync-upstream-skills.yml` requires `contents: write` because it commits vetted upstream changes back to `main`. Checkout credentials are still not persisted. The workflow authenticates only the final `git push` with the short-lived `GITHUB_TOKEN`, after synchronization, distribution regeneration and repository validation succeed.

### Merged-branch cleanup

`cleanup-merged-branches.yml` requires `contents: write` to delete same-repository branches from already-merged pull requests and `pull-requests: read` to inspect merged PRs. It does not execute checked-out repository code.

Future write-capable workflows must document why write access is required and should keep that permission scoped to the smallest practical workflow/job surface.

## Trusted execution

Model-backed evaluations or publication workflows added later should separate untrusted pull-request validation from privileged deployment or secret-bearing execution. Do not expose write tokens, deployment credentials or model-provider secrets to untrusted fork code.

## Reference

The baseline intentionally reuses security patterns from `jongio/skills/create-skills-repo` and its generated workflows: immutable action SHAs, non-persisted checkout credentials, least privilege, trusted triggers and bounded jobs.
