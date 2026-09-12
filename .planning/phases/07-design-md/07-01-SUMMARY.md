---
phase: 07-design-md
plan: "01"
status: complete
completed: 2026-09-12
requirements: ["DSYS-01"]
---

# Phase 07 Summary — DESIGN.md Contract

## Result

Defined portable project visual memory without inventing another proprietary design schema. The capability now follows the current open `google-labs-code/design.md` format and adds repository-specific orchestration rules for evidence precedence, monorepo scope, inference, safe creation and reviewable updates.

## Implementation

- Added `references/design-md.md` with:
  - canonical DESIGN.md section/order rules;
  - normative-token vs descriptive/inferred evidence semantics;
  - evidence precedence and conflict handling;
  - single-app, monorepo and shared-component scope rules;
  - scan vs seed creation behavior;
  - durable-update vs task-local-change boundaries;
  - optional Figma/design-source conflict handling;
  - portability/security constraints.
- Added `references/DESIGN.md.template` as a linter-valid starting point using the canonical 8-section format.
- Integrated design-context resolution into the main orchestrator before reuse/mode/visual decisions.
- Added completion/degraded-operation checks so missing/stale DESIGN.md never fabricates evidence or blocks ordinary work unnecessarily.

## Upstream research

Execution re-checked the current ecosystem before authoring:

- `google-labs-code/design.md` is now the open format specification and CLI for DESIGN.md.
- Current format uses optional normative YAML token frontmatter plus canonical prose sections.
- Google Stitch's `extract-design-md` confirms source-first extraction across React/Vue/Svelte/Angular/CSS and design-token systems.
- Impeccable's current document flow also consumes the official DESIGN.md format and separates durable visual system context from product truth.

We therefore reuse the open format rather than introducing a competing schema.

## Verification

Dedicated validation run **34701151824** ✅

- Official `@google/design.md@0.4.0` CLI linted `DESIGN.md.template` with **0 errors, 0 warnings, 0 infos**.
- Contract invariants passed for normative tokens, monorepo/app-local precedence, explicit inference, no one-off documentation churn, template handoff and orchestrator scope handling.
- Repository `Skills Validation` also ran during implementation changes.

Temporary validation workflow was removed before the final PR.

## Requirement

`DSYS-01` complete.
