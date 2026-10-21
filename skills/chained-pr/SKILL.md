---
name: chained-pr
description: "Split large or review-heavy changes into stacked PRs to main or a feature-branch chain with a tracker. Use when the user requests PR slicing, stacked changes or reviewer-load control, or the effective project delivery strategy requires a split. Define slice boundaries, dependencies, review order and checks without replacing the selected delivery mode or imposing a universal line-count gate."
license: Apache-2.0
metadata:
  author: gentleman-programming
  version: "1.1"
---

## Activation Contract

Load when the effective project PR budget is exceeded, SDD/ODD explicitly requests slicing, or the user asks for stacked/chained PRs or reviewer-load control. This is a slicing helper, not a second delivery policy.

Resolve the applicable host/repository budget and selected delivery strategy first. Without a specified budget, use 400 authored additions plus deletions as a planning default, not a universal acceptance gate. Preserve any actual repository/CI limit: a mode preference cannot waive it. Preserve configured TDD/RDD; do not activate either or enter SDD from a size signal.

## Hard Rules

- Split when the effective strategy requires it. A hard repository size gate needs the repository's actual exception process, not a self-issued `size:exception`. An advisory budget only prompts a coherent slicing assessment; never invent a label or approval gate.
- Keep each PR reviewable in about **≤60 minutes**.
- Use one deliverable work unit per PR; keep tests/docs with the unit they verify.
- State start, end, prior dependencies, follow-up work, and out-of-scope items in every chained PR.
- Every child PR must include a dependency diagram marking the current PR with `📍`.
- In Feature Branch Chain, create a draft/no-merge tracker PR; child PR #1 targets the tracker branch, later children target the immediate parent branch.
- Treat polluted diffs as base bugs: retarget or rebase until only the current work unit appears.
- Do not mix chain strategies after the user chooses one.

## Decision Gates

| Condition | Action |
|---|---|
| Within the effective budget and focused | Keep single PR. |
| Slicing selected, each slice can land independently | Use Stacked PRs to main. |
| Slicing selected, feature must integrate before main | Use Feature Branch Chain with tracker. |
| Advisory budget exceeded but no coherent split exists | Record rationale; do not manufacture micro-PRs. |
| Enforced size gate exceeded | Follow the actual exception process or stop at that gate. |
| SDD provides `delivery_strategy` | Follow it before apply/PR creation. |

## Execution Steps

1. Resolve the effective budget/strategy, distinguish authored from generated work, and identify independent units. Generated files still belong in the complete review.
2. When chaining is required or selected, ask for a chain strategy only if none is already established.
3. Create branches/PRs using the chosen strategy only, with user authorization for remote operations. Never compress code or drop tests/docs merely to fit a count.
4. Add Chain Context to each PR without replacing the repo PR template.
5. Verify each PR independently: CI/tests/docs/manual checks, rollback scope, and clean diff.
6. Keep tracker PR draft/no-merge until all child PRs are reviewed and integrated.

## Output Contract

Return the chosen strategy, PR order, current PR boundary, dependency diagram, review budget (`additions + deletions`), verification plan, and any `size:exception` rationale.

## References

- [references/chaining-details.md](references/chaining-details.md) — strategy diagrams, PR body section, branch commands, and reviewer guidance.
