# Delivery workflow compatibility

## Objective
Reconcile the existing Personal, Enterprise, Autopilot, and commit/PR helpers without changing installed global skills or weakening repository gates.

## Scope and authorization
- User authorized the proposed compatibility PR with "Continua"; local edits, checks, branch push and PR creation in svg153/skills are in scope. Merge is not authorized.
- Preserve original skills, licenses, invocation policies and upstream provenance. No new skill, symlink, installation, deletion, unrelated refactor or mortgage application change.
- Skill defaults must defer to applicable host/repository instructions, explicit mode selection, user-owned TDD/RDD settings and operation-specific authorization.
- Keep one searchable decision entry; preserve CODEX heading and legacy indexing without duplicate records.

## Route and controls
- Route: direct inline implementation; one Luna read-only mapper because cross-skill references/eval conventions require more than one inline evidence batch. No parallel writers.
- Independent behavioral forward check: authorization/shared policy boundary; not native receipt-driven review.
- RDD: disabled/unmanaged; `gentle-ai review mode status --cwd <worktree> --json` returned effective off, source global. Do not enable or start reviews.
- TDD: N/A to this instruction/YAML-only change; no application code or TDD configuration changes. Use existing Python validators and Waza behavioral fixtures, report static versus model-backed evidence separately.
- Risk: item 1 (shared authorization and routing contract); preserve branch protection and failing correctness/security checks.
- Baseline: origin/main e633213. Worktree: svg153-skills-delivery-compat; branch fix/delivery-workflow-compat.
- Delivery strategy: single-pr, one compatibility concept; forecast 250-350 authored changed lines. No hard repository size gate has been found. Revisit if the honest scope exceeds the current delivery strategy.

## Tasks
- [x] T1: Reconcile activation, precedence, sizing, decision indexing and remote authorization across skills and supporting references; add relevant behavioral fixtures alongside the change.
  - Acceptance: explicit Personal does not load Enterprise/Autopilot policy in parallel; helpers use the effective host/project budget without bypassing real gates; local continuation does not silently authorize remote actions; CI quota exceptions never turn real failures green.
  - Checks: structural source reread, existing catalog/frontmatter/lifecycle/eval/distribution validators; independent forward scenarios for selected mode, restricted remote authorization, actual size gate and unavailable CI.
  - Runtime harness: N/A (instruction/YAML change); behavioral fixtures and forward-check results are the applicable runtime evidence.
  - Rollback: restore only the changed workflow skill text, references, behavioral fixtures and this document.
  - Commit/evidence: implementation commit 21e58c8fa85873ed084a42681c759c3df6c7a3c7; outcomes below observed.
- [x] T2: Record observed checks and limitations, publish the compatibility PR for user review, and preserve the worktree/global copies.
  - Acceptance: PR has scope, non-goals, checks, decision record, and no merge; task document and Engram mirror agree.
  - Checks: `git diff --check`, clean committed branch, remote PR/check snapshot.
  - Commit/evidence: implementation 21e58c8 published in https://github.com/svg153/skills/pull/97; this documentation-only closeout is recorded in the task file's Git history.

## Progress and next action
T1/T2 complete: PR #97 is open for user review, not merged. No global skill changes. Next action requires maintainer review; installation and cleanup remain separate.
- `python -m unittest discover -s tests -v`: 71 passed (bundled Python with existing PyYAML cache on PYTHONPATH).
- Frontmatter (48 skills), lifecycle (45 entries), metadata-repair check, distribution (8 manifests), catalog renderer and eval validator (12 suites): passed.
- Git Bash `bash scripts/sync-upstreams.sh --list`: passed, 5 legacy-sync upstream skills listed, no sync performed.
- `git diff --check`: passed.
- Independent forward check (Luna, read-only): four observed responses preserved Personal/Enterprise/generic selection, real budgets, remote authorization and genuine-test-failure blockers. Not a Waza model-backed run or RDD receipt.
- Windows workflow-security validator: 3 executable-bit findings on untouched scripts/workflows; Git records sync-upstreams.sh as 100755. No protection or script changed; Linux CI Skills Validation passed at implementation commit 21e58c8, including workflow security, npx discovery and APM consumption (run 39681394980).
- Offline `npx skills add . --list`: unavailable (ENOTCACHED); no network package installation attempted. Local Waza executable unavailable; CI static Waza verification passed at implementation commit 21e58c8 (run 39681394866); trusted model-backed Waza not run.
- RDD remains disabled/unmanaged (global off). Runtime harness N/A (only instruction text/fixtures); no application TDD mode changed.
- Implementation commit authored diff: 272 additions + deletions including the task document; single conceptual PR remains within forecast.

## Publication snapshot
- PR #97 at implementation commit 21e58c8: six check runs passed, merge state CLEAN, PR OPEN. This records observed implementation evidence, not a promise about later CI runs; see the PR for latest status.
- A later documentation-only closeout records this snapshot. Keep the worktree and installed copies until explicit maintainer instructions; no merge or cleanup performed.
