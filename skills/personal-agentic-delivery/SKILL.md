---
name: personal-agentic-delivery
description: "Continue GitHub roadmaps autonomously for personal projects or small teams: recover unfinished work, prioritize dependencies, and group related issues into concept-level PRs with reviewable commits. Use for sustained backlog delivery with less per-ticket ceremony while retaining decisions, tests, CI evidence and roadmap traceability. Application size does not select Enterprise; do not run competing delivery loops."
metadata:
  short-description: Efficient autonomous roadmap delivery
---

# Personal agentic delivery

Use this workflow when one agent or a small team owns a large application but does not need the full enterprise ceremony for every small change. The objective is to keep the roadmap moving autonomously while making each PR coherent, reviewable later, and safe to merge.

This is not a small-code or low-quality mode. It changes the shape of delivery: related technical steps are grouped into one concept-level PR, while security boundaries, risky migrations, provider integrations, and architectural changes remain separate when they need independent review or rollback.

## Activation and precedence

Use one delivery policy at a time: Personal owns concept-level batching when selected; do not also run Enterprise or Autopilot's delivery loop. Switch modes only on the user's explicit request. Helpers may support the selected mode, not replace it.

Applicable host/repository instructions and actual repository gates take precedence over these defaults. Preserve the configured ODD/SDD route, TDD mode and user-owned RDD switch; invoking this skill does not select SDD, enable reviews or authorize external actions. Never bypass required consent or branch protections.

## Operating objective

Continue the authorized scope of the canonical roadmap until there are no actionable items left, respecting dependencies and priorities. Work autonomously one coherent unit at a time. Create missing issues when the code or roadmap reveals real work, but do not manufacture speculative backlog.

The loop may continue without asking the user after every issue. Ask only when progress requires authorization, a product decision with no safe default, destructive/data-loss action, production credentials or external access, or a conflict that cannot be resolved from the repository and roadmap.

## Phase 0 — Recover before acting

Before editing:

1. Read the current goal, recent memory, repository instructions, branch, worktree, open PRs, and uncommitted changes.
2. Inspect the canonical roadmap and the relevant parent/child issues with GitHub CLI.
3. Check whether a previous branch, PR, or dirty worktree already contains the next implementation. Continue it instead of duplicating it.
4. Select the next issue by dependency, value, risk, and readiness—not by numeric order alone.

Never discard user changes or a half-finished branch. If work is on `main`, preserve it first by moving it to a feature branch or clearly stop before further edits.

## Concept-level batching

Group changes into one PR when they implement one capability and are normally reviewed together. Typical grouping:

- domain contract + its persistence + runtime wiring + focused tests;
- a family of related normalizations;
- an API route plus the server-side composition it directly consumes;
- a refactor required by the feature in the same bounded area.

Keep separate issues/PRs for:

- independent security boundaries;
- unrelated product concepts;
- migrations or data transformations with independent rollback;
- external provider integrations with their own operational risk;
- architecture work that changes the direction or terminology of the roadmap;
- work blocked on an external decision or environment.

This skill adds no hard line-count gate. Follow the effective host/project delivery budget and any enforced PR size gate first. A helper's default 400-line threshold must not silently replace a selected concept-batching policy; conversely, Personal never overrides a real repository limit. Roughly 5,000–7,000 changed lines is an upper review warning, not a target or standing size exception. Prefer much smaller coherent PRs; distinguish authored work from generated/vendor churn without excluding it from review.

## Issue and roadmap handling

Use an existing issue when it already owns the concept. Create a child issue only when the work is genuinely missing from the roadmap or needs a separate dependency/decision record.

New or substantially updated issues must include:

- context and objective;
- scope and non-goals;
- dependencies and affected parent roadmap;
- acceptance criteria;
- expected validation;
- the exact heading `## Decision record — CODEX` for choices, uncertainty, or decisions made autonomously.

Update the direct parent with the new issue or completed PR. Update other parents only when the decision materially changes their scope or dependency graph. Keep the issue body authoritative and comments concise.

If a Boy Scout improvement appears while implementing a feature:

- include it when it is local, necessary, and within the same concept;
- create a follow-up issue when it is independent cleanup;
- create an architecture issue when it changes boundaries, public contracts, storage, or roadmap direction.

## Branches, commits, and PRs

- Create or recover a feature branch before editing; never continue new work on `main`.
- Use several clean, linear commits inside one concept-level PR.
- Make commit messages describe the reviewable step, for example `feat(auth): persist verified identity` or `test(api): cover denied entitlement access`.
- Use the commit history as the primary review path when the PR is larger.
- Avoid a giant mixed bag: one PR may be broad, but every commit must belong to the same capability.

The PR body should contain scope, non-goals, commit map, tests, risks/rollback, linked issues, and `## Decision record — CODEX` where applicable. Do not claim a provider, deployment, E2E test, or review passed without evidence.

## Validation and CI loop

Run checks in increasing cost:

1. Focused tests for changed behavior.
2. Affected package typecheck/build.
3. Targeted lint, formatting, and diff checks.
4. Full repository checks when they are meaningful and not polluted by generated artifacts.

For failures:

- fix failures caused by the change;
- classify failures as code, repository baseline, provider/environment, quota/rate-limit, runner-minute exhaustion, unavailable optional review, or pending infrastructure;
- retry an external check once when useful;
- after the second identical external failure, document the exact evidence under `## Decision record — CODEX` in the PR or issue and continue within authorization only when repository safeguards permit it and local/security validation is sufficient; unavailable required checks remain unmet;
- do not wait indefinitely for optional Copilot review or unavailable agents/runners;
- never weaken security or correctness checks to force green CI.

Examples of acceptable documented external exceptions include Vercel preview rate limits, exhausted GitHub runner minutes, or an unavailable optional review integration. The exception must not conceal a failing test, typecheck, build, or security check caused by the change.

## Merge and autonomous continuation

Before any remote mutation, confirm that the user authorized that operation and destination: issue updates, push, PR creation, merge and release are distinct scopes. Local implementation or skill invocation alone grants none of them. An explicit backlog-wide authorization can cover repeated operations in that same scope; do not ask again per PR unless scope or risk changes. If publication or merge is not authorized, hand off the verified local change or open PR at that boundary.

After an authorized PR is opened:

1. Verify the diff, changed files, base branch, linked issue, commits, and checks.
2. Merge only with user authorization, satisfied repository gates and the permitted strategy; use `gh` rather than browser automation when possible.
3. Verify the merge commit and close the issue only when acceptance criteria are met.
4. Add a concise completion decision record with PR, commit, scope, and CI exceptions.
5. Synchronize the direct parent roadmap.
6. Re-audit the board and immediately choose the next actionable issue.

Do not stop after one PR merely because it is complete. Stop only when the actionable roadmap is exhausted, the user asks to pause, the next operation is outside authorization, or a real external/product/security blocker remains. Leave the blocker with evidence and a resume condition.

## Decision records and memory

Use the exact heading `## Decision record — CODEX` in issues or PRs whenever a decision is made. Include the question, options, selected decision, reason, affected scope, and follow-up. When the repository also uses `[AI-DECISION]`, include that marker inside the same record rather than duplicating it. A decision record never substitutes for authorization.

Persist important decisions, discoveries, bug fixes, user constraints, and workflow changes in the available memory system. Keep the user-facing response short; the issue/PR and commit history are the durable project record.
