---
name: github-repo-autopilot
description: "Assess and maintain GitHub repositories through prioritized issues, implementation, tests, pull requests, documentation, review, merge, and releases. Use when the user asks to continue a repository, clear a backlog, work through issues, improve a project autonomously, plan phases, coordinate authorized agents, or create an ongoing repository-maintenance workflow."
---

# GitHub Repository Autopilot

## Safety and authority

- Operate only on repositories and actions authorized by the user. Never invent credentials, bypass branch protection, disable checks, rewrite published history, expose secrets, or merge without authorization.
- Derive conventions from the actual repository: contributor instructions, agent instructions, issue and PR templates, labels, branch rules, CI, release automation, project boards, and existing code. Never import approval labels, branch naming schemes, coverage thresholds, or required templates from an unrelated project.
- Inspect repository access and available integrations before deciding how to read or modify it. Prefer supported GitHub integrations; use existing authenticated local tooling when available.
- Treat a failed CI run differently from unavailable runner minutes, flaky infrastructure, and genuine test failures. Never claim a substitute proves a required check passed; report actual local verification and remaining risk.
- Ask before destructive changes, public disclosure of sensitive information, ambiguous product decisions, architectural rewrites, dependency removals, forced updates, or merges not already authorized.

## Discovery and planning

1. Inspect repository metadata, default branch, open issues, open pull requests, recent activity, project documentation, contribution rules, automation, dependency manifests, and test commands.
2. Search for existing open-source projects, upstream features, packages, prior issues, and existing repository implementations before designing new functionality. Evaluate license, maintenance, security, and fit.
3. Remove duplicate work from the plan. Build a dependency-aware backlog grouped into coherent phases; identify blockers, product decisions, review boundaries, and reusable repository skills.
4. For new issues, explain the problem, intended outcome, implementation boundaries, dependencies, acceptance criteria, test expectations, documentation impact, and release considerations. Follow the repository's actual templates and labels.
5. When delegation is explicitly authorized and supported, reserve the strongest reasoning for architecture and ambiguous decisions; delegate independent, bounded implementation or verification tasks to appropriate smaller agents. Never assume delegation is available.

## Delivery loop

For each authorized, unblocked work item:

1. Refresh the latest default branch and issue state; check whether another issue or PR already implements the change.
2. Create or reuse the appropriate branch according to actual project conventions. Keep scope focused and avoid unrelated changes.
3. Implement the smallest complete change, including regression or behavior tests and necessary documentation. Preserve compatibility unless a breaking change was approved.
4. Run the repository's relevant formatter, linter, type checks, tests, and build where feasible. Report exact checks performed and environmental limitations.
5. Open or update a focused PR linked to its issue, explaining what changed, why, verification, risks, and follow-up work. Split oversized changes only when reviewability or repository practice warrants it.
6. Inspect CI, review comments, mergeability, and acceptance criteria. Correct recoverable failures and re-run meaningful checks.
7. Merge only when the user has authorized merging and repository safeguards allow it. Confirm the issue state, resulting default-branch commit, and any configured release or deployment outcome.
8. Reassess dependent issues and repeat until the authorized stopping condition is reached or a genuine blocker requires the user.

## Output

Report repository, completed issues and PR links, checks actually executed, merge and release outcomes, remaining prioritized work, blockers requiring a decision, and material risks. Do not report completion from a proposed plan, agent status, submitted command, or unverified merge.
