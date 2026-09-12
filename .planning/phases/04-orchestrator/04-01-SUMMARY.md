---
phase: 04-orchestrator
plan: "01"
status: complete
requirements: ["ORCH-01"]
completed: 2026-09-12
---

# Phase 4 Plan 01 Summary — Design Engineering Orchestrator

## Outcome

Implemented the local `design-engineering` skill as the single broad UI/UX orchestration entry point. It coordinates product/repository recon, reuse-first decisions, mode selection, specialist delegation, rendered verification and bounded iteration without absorbing the specialist design rules that later phases will package.

## Delivered

- Tight routing boundary: use when visual/interaction/UX judgment is required; do not trigger for backend-only or purely mechanical frontend work.
- Mandatory recon before invention: product/request context, stack, dependencies, components/primitives, tokens/theme, design docs and rendered baseline when runnable.
- Reuse chain: project component -> installed dependency -> credible maintained external primitive -> bespoke local implementation.
- Three explicit workflows:
  - **polish** for localized, low-uncertainty changes;
  - **prototype** for high-impact genuinely uncertain directions;
  - **audit** for evidence-first/read-only diagnosis.
- `references/workflow.md` with mode entry/exit criteria, specialist routing, mutation rules, degraded operation, browser/quality handoff and completion checklist.
- Default maximum of 3 automatic render/inspect/fix visual-polish cycles.
- Human review boundary for subjective/high-impact visual decisions; no visual auto-merge.
- README now exposes simple user prompts rather than requiring manual specialist orchestration.

## Verification

Implementation-head validation completed successfully:

- Capability Plugin Validation run `34697105168` — success, including generated package checks, unit tests, Agent Skills reference validation, cross-agent skill discovery, GitHub Copilot CLI install/discovery and Codex CLI install/discovery.
- Behavioral Eval Static Validation run `34697105160` — success.

Dedicated model-backed design routing evals are intentionally Phase 9 work; this phase establishes the behavior contract they will test.

## Degradation contract

The orchestrator requires no Figma/media/browser MCP. Missing specialists reduce available evidence but do not cause fabricated results or credential workarounds. If runtime evidence cannot be collected, the final result must say so rather than claim visual verification.

## Next

Phase 3 remains the next safe implementation block: build generic APM-lock-backed external skill component materialization without enrolling Emil/Addy yet. Phase 1 remains externally blocked by #46.
