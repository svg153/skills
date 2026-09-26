---
name: github-repo-autopilot
description: "Assess and maintain GitHub repositories through prioritized issues, implementation, tests, pull requests, documentation, review, merge, and releases. Use when the user asks to continue a repository, clear a backlog, work through issues, improve a project autonomously, plan phases, coordinate authorized agents, or create an ongoing repository-maintenance workflow."
---

# GitHub Repository Autopilot

## Safety and authority

- Operate only on repositories and actions authorized by the user. Never invent credentials, bypass branch protection, disable required checks, rewrite published history, expose secrets, or merge without authorization.
- A prior explicit instruction to merge an authorized backlog can cover later PRs in that scope. Do not ask for merge approval again unless the scope, risk, or repository safeguards materially change.
- Derive conventions from the actual repository: contributor instructions, agent instructions, issue and PR templates, labels, branch rules, CI, release automation, project boards, and existing code. Never import approval labels, branch naming schemes, coverage thresholds, or required templates from an unrelated project.
- Inspect repository access and available integrations before deciding how to read or modify it. Prefer supported GitHub integrations; use existing authenticated local tooling when available.
- Do not pause for ordinary reversible implementation choices or local architectural trade-offs that are already inside authorized scope. Use the autonomous decision policy below, record the choice, and continue.
- Escalate before destructive or irreversible changes, credential or security-policy changes, sensitive public disclosure, material changes to product intent or authorized scope, forced history updates, or merges that were not already authorized.
- Treat a failed CI run differently from unavailable runner minutes, flaky infrastructure, and genuine test failures. Never claim a substitute proves a required check passed; report actual verification and remaining risk.

## Autonomous decision policy

When the user has authorized autonomous repository work, keep moving unless a decision crosses an escalation boundary.

1. Classify the decision. If it is reversible, bounded in impact, and already inside the authorized problem scope, treat it as non-blocking.
2. Research proportionally using repository precedent, upstream documentation, existing implementations, and relevant evidence. Avoid analysis that is much larger than the decision warrants.
3. Record the decision in the active issue or PR with the common marker `[AI-DECISION]`. Prefer the artifact already carrying the work instead of creating a separate decision-only issue.
4. Use this compact contract:

   ```text
   [AI-DECISION] <short title>
   Question: <what had to be decided>
   Options: <viable alternatives considered>
   Evidence: <repository precedent, research, constraints, or test evidence>
   Decision: <selected option>
   Rationale: <why this option is preferred>
   Reversibility / risk: <how easy it is to change later and material risk>
   Follow-up: <none, or the linked deferred issue>
   ```

5. Implement the recommended option and continue without waiting for retrospective approval. The record exists so the user can audit the choice later and create a follow-up issue if they disagree.
6. If the choice becomes destructive, security-sensitive, irreversible, or materially changes product intent or scope, stop and escalate instead of using `[AI-DECISION]` as a substitute for approval.

## Deferred decisions

Do not let a non-blocking research question stall the current delivery loop.

1. If resolving a decision now would require disproportionate research and the current work can remain correct without it, create a follow-up issue using the repository's real issue conventions.
2. Capture why the decision is deferred, the evidence still needed, dependencies, acceptance criteria, and what current assumption allows work to continue.
3. Link the follow-up from the active issue or PR. Add it to a roadmap, project, or dependency graph only when the repository actually uses that mechanism.
4. Add an `[AI-DECISION]` record that names the deferred issue and continue the current work.
5. When the deferred issue becomes active, perform the deeper research in that context. If the unresolved decision blocks correctness or crosses an escalation boundary, do not defer it silently.

## Discovery and planning

1. Inspect repository metadata, default branch, open issues, open pull requests, recent activity, project documentation, contribution rules, automation, dependency manifests, and test commands.
2. Search for existing open-source projects, upstream features, packages, prior issues, and existing repository implementations before designing new functionality. Evaluate license, maintenance, security, and fit.
3. Remove duplicate work from the plan. Build a dependency-aware backlog grouped into coherent phases; identify blockers, product decisions, review boundaries, and reusable repository skills.
4. For new issues, explain the problem, intended outcome, implementation boundaries, dependencies, acceptance criteria, test expectations, documentation impact, and release considerations. Follow the repository's actual templates and labels.
5. Prefer linear delivery by default: one active implementation issue and one focused PR at a time. Use parallel or stacked work only when explicitly authorized, required by repository practice, or clearly independent and safe.
6. When delegation is explicitly authorized and supported, reserve the strongest reasoning for architecture and ambiguous decisions; delegate independent, bounded implementation or verification tasks to appropriate smaller agents. Never assume delegation is available.

## Delivery loop

For each authorized, unblocked work item:

1. Refresh the latest default branch and issue state; check whether another issue or PR already implements the change.
2. Create or reuse the appropriate branch according to actual project conventions. Keep scope focused and avoid unrelated changes.
3. Resolve ordinary reversible choices with the autonomous decision policy. Defer expensive non-blocking research with a linked follow-up issue instead of stopping the implementation.
4. Implement the smallest complete change, including regression or behavior tests and necessary documentation. Preserve compatibility unless a breaking change was approved.
5. Run the repository's relevant formatter, linter, type checks, tests, and build where feasible. Report exact checks performed and environmental limitations.
6. Open or update a focused PR linked to its issue, explaining what changed, why, verification, risks, `[AI-DECISION]` records, and follow-up work. Split oversized changes only when reviewability or repository practice warrants it.
7. Inspect CI, review comments, mergeability, and acceptance criteria. Classify failures before deciding whether to repair, retry, defer, or merge.
8. Merge only when the user has authorized merging and repository safeguards allow it. Apply the CI recovery policy below rather than waiting indefinitely on unavailable infrastructure.
9. Confirm the resulting default-branch commit, issue state, and any configured release or deployment outcome. Refresh default branch state, reassess dependent issues, and repeat until the authorized stopping condition is reached or a genuine escalation boundary requires the user.

## CI recovery and merge policy

Classify CI state before acting. Do not treat every red or missing check as the same failure.

- **Genuine code or test failure:** fix the regression before merge. Do not merge a known failing behavior merely to keep the backlog moving.
- **Flaky check:** use a small bounded retry and reproduction budget, inspect evidence, and document why the failure is considered flaky before proceeding.
- **Infrastructure, unavailable runner, credits, or time limit:** retry only while useful, then run equivalent local checks where feasible. If merge is already authorized and repository safeguards permit it, the PR may be merged with an explicit record that CI did not pass or could not run, which local checks were executed, and what residual risk remains.
- **Unknown cause:** keep diagnosing until it can be classified. Do not merge solely to preserve momentum while the unknown failure could still be a product regression.

Never disable or bypass required branch protection or required checks. Never report CI as green when it did not run. Keep retry and repair loops bounded so unavailable infrastructure does not turn into indefinite CI churn.

## Output

Report repository, completed issues and PR links, checks actually executed, CI classification and limitations, merge and release outcomes, `[AI-DECISION]` records, deferred follow-up issues, remaining prioritized work, escalation blockers, and material risks. Do not report completion from a proposed plan, agent status, submitted command, or unverified merge.
