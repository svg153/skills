---
name: enterprise-agentic-delivery
description: Run traceable, autonomous enterprise development through roadmap audit, GSD issues, linear commits, pull requests, CI, merge, and parent-roadmap synchronization. Use for GitHub-backed work where auditability and decision history matter; do not use this workflow for personal or MVP batching unless explicitly requested.
metadata:
  short-description: Traceable enterprise issue-to-PR delivery
---

# Enterprise agentic delivery

Use this skill when the work must remain auditable from roadmap to merged code. The goal is not to maximize the number of issues or PRs; it is to make every change explainable, reviewable, reversible, and linked to its architectural context.

## Core operating rule

One issue and one PR represent one independently reviewable unit. A small change is still a valid standalone unit when it has its own security boundary, migration, operational risk, compliance/audit value, rollback need, or explicit normalization purpose. Do not merge unrelated work merely to reduce PR count.

Conversely, combine changes when they are only contract, storage, runtime wiring, or tests for the same capability and have no useful independent rollback or review boundary.

## Phase 0 — Audit before mutation

Before editing files or GitHub:

1. Inspect the current branch, worktree, uncommitted changes, repository instructions, and remote state.
2. Read the roadmap parent and candidate child issues, including comments and existing PRs.
3. Trace the relevant code path and search for existing helpers, stores, tests, and callers.
4. Build a small dependency map: prerequisite issues, affected parents, deployment/CI constraints, and external blockers.
5. Choose the smallest **independently reviewable** unit, not automatically the smallest diff.

If implementation already exists on a dirty branch or worktree, preserve and verify it; do not create duplicate work or silently overwrite it.

## Planning and GSD issue discipline

Create a child issue only when no existing issue accurately owns the work. Prefer updating an existing issue over creating a parallel one.

Use the issue structure in [references/issue-template.md](references/issue-template.md). It must state:

- objective and context;
- exact scope and explicit non-goals;
- dependencies and affected parents;
- acceptance criteria that can be verified;
- risks, rollback, and external prerequisites;
- a decision record using the exact heading `## Decision record — CODEX` whenever a choice, uncertainty, or user-help decision exists.

For roadmap synchronization, update the direct parent first. Update additional parents only when the decision or dependency materially affects them. Keep links in the issue body so the graph remains navigable without duplicating the same prose everywhere.

## Branch and implementation

- Never start new implementation on `main`.
- Create a named branch from the verified base before editing.
- Keep commits linear and concept-focused. A PR may contain several commits when each commit is a useful review checkpoint.
- Use imperative commit messages with a stable scope, for example `feat(auth): persist verified identity`.
- Do not create abstractions, adapters, or configuration for speculative future consumers.
- Preserve trust boundaries: never use client-supplied email, account IDs, or demo flags as server authorization.
- Add the smallest meaningful automated check for non-trivial logic.

For repetitive normalizations or a family of closely related changes, prefer one issue/PR for the concept with several clean commits, unless individual changes need separate ownership, rollback, release, or audit evidence.

## Validation

Validate in this order:

1. Focused tests for changed behavior.
2. Typecheck/build for the affected package or service.
3. Targeted lint/format/diff checks for changed files.
4. Repository-wide checks when they are meaningful and configured to exclude generated artifacts.

Record pre-existing failures separately from regressions. Do not “fix” generated output or unrelated baseline lint merely to make a PR green.

Before opening the PR, verify the diff, changed files, branch base, issue link, test commands, and working tree. Never claim an external deployment or integration test passed without evidence.

## Pull request and CI

Use the structure in [references/pr-template.md](references/pr-template.md). The PR must include scope, non-goals, implementation summary, tests, risk/rollback, linked issues, and the exact decision-record heading when relevant.

CI policy:

- Fix failures caused by the change.
- Investigate external failures and rerun once when useful.
- If the same external failure occurs twice, document the exact evidence and risk in the PR and issue; merge only when the remaining local and security validation is sufficient.
- Never bypass required security or correctness checks by relabeling them as external.

Inspect repository merge rules before choosing squash, merge, or rebase. If the repository rejects squash, use the permitted strategy and document it.

## Merge and closeout

After merge:

1. Verify the merge commit and target branch.
2. Close the implementation issue only when acceptance criteria are actually met.
3. Add a concise completion `## Decision record — CODEX` comment with commit, PR, scope boundaries, and CI exceptions.
4. Synchronize the direct parent roadmap and only materially affected related parents.
5. Delete the feature branch when safe.
6. Re-audit the next candidate instead of assuming the next numeric issue is correct.

If blocked by real external state, leave the issue open with evidence, owner/action, and a precise resume condition. Do not fabricate production, provider, email, storage, or E2E evidence.

## Safety stops

Stop and document a decision before proceeding when:

- the issue conflicts with the canonical roadmap;
- the only way to demo it would weaken authorization or persistence guarantees;
- the worktree contains unrelated user changes;
- the requested scope would mix multiple independent product capabilities;
- acceptance depends on an unavailable external environment.

When a safe default exists, choose it, record the alternatives and rationale under `## Decision record — CODEX`, and continue without unnecessary clarification loops.

## Tooling

Prefer repository-native CLI/API tooling (`gh`, Git, package scripts) over browser automation. Use the available memory system to persist architectural decisions, discoveries, bugs, and user constraints. Use the code-review skill before merging when a multi-axis review is requested or required by the repository.
