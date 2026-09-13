---
phase: 09-evals-fixtures
plan: "01"
status: complete
completed: 2026-09-13
requirements: ["EVAL-01"]
---

# Phase 09 Summary — Behavioral Evals and Fixtures

## Result

Added catalog-owned behavioral regression coverage for the implemented Design Engineering core without weakening the external dependency gate that still blocks Emil/Addy enrollment.

## Dependency refinement

The original roadmap made Phase 9 depend on Phases 5/6/7/8. Execution showed that `EVAL-01` is specifically about the local orchestrator and already-shipped core behavior: routing, reuse-first decisions, DESIGN.md precedence, optional-integration degradation, rendered evidence and the human visual-merge boundary.

Phase 9 therefore depends directly on Phases 4, 7 and 8 and is complete now. Phases 5 and 6 remain blocked by Phase 1/#46 and must extend this suite with specialist-specific cases when their external components are enrolled. Phase 10 now explicitly depends on Phases 5, 6 and 9, so the real-app pilot still cannot bypass the supply-chain proof.

## Implementation

Added `evals/design-engineering/eval.yaml` using the repository-native Waza contract:

- schemaVersion `1.2`;
- `copilot-sdk` executor;
- one trial per task;
- existing trigger/behavior/completion metric weights;
- `tasks/*.yaml` discovery.

Added 10 deterministic tasks:

1. broad interface improvement activates recon/reuse-first behavior;
2. high-impact uncertain redesign selects isolated prototype exploration;
3. explicit audit remains evidence-first and read-only;
4. mechanical frontend rename/refactor does not trigger;
5. backend-only database work does not trigger;
6. existing project components/libraries win before a new dependency;
7. missing Figma/browser tooling degrades honestly without fabricated evidence;
8. runnable UI mutation requires rendered responsive/interaction evidence and bounded repair cycles;
9. subjective visual changes remain human-reviewed rather than auto-merged;
10. app-local DESIGN.md/tokens outrank root or inferred defaults.

The original stale `suite.yaml` + separate fixture-directory assumption in `09-01-PLAN.md` was replaced by the repository's existing `eval.yaml` + `tasks/*.yaml` convention. Scenario context lives directly in deterministic Waza prompts instead of introducing a parallel fixture harness that the current evaluator does not consume.

## Static validation evidence

Behavioral Eval Static Validation passed on both trigger paths for implementation commit `92fd5a436bcf0ca7a73cbb706597ff55ee53e4cd`:

- push run **34728563872** ✅;
- pull_request run **34728571891** ✅.

The PR run verified successfully:

- checkout and YAML dependency setup;
- `python scripts/validate-evals.py` catalog/eval contract;
- pinned Waza installation;
- `waza spec verify` for all catalog-owned suites, including the new capability-embedded `design-engineering` skill.

## Trust boundary

No CI workflow changes were required.

- `.github/workflows/eval-static.yml` already covers `evals/**`, capability skill/config changes and performs secret-free PR validation.
- `.github/workflows/eval-behavioral.yml` remains `workflow_dispatch`/scheduled only and credential-gated for model-backed execution.
- `scripts/validate-evals.py` already resolves capability-embedded skills uniquely and enforces positive/negative coverage plus behavioral graders.

This preserves cheap deterministic PR checks while keeping model credentials off untrusted PR execution.

## External gate

Phase 1/#46 remains blocked. Rechecked on 2026-09-13: the latest genuine stable `ghspain/github-build-or-reuse` release is still `v1.2.3`, so there is no real newer Renovate update PR to complete the remaining end-to-end proof.

No Emil/Addy dependency was introduced or simulated by this phase.

## Requirement

`EVAL-01` complete.
