---
gsd_state_version: '1.0'
status: executing
progress:
  total_phases: 15
  completed_phases: 7
  total_plans: 15
  completed_plans: 7
  percent: 47
---
# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-09-11)

**Core value:** A simple request produces a repeatable, rendered, evidence-backed UI improvement workflow while preserving reuse and human visual judgment.
**Current focus:** Phase 1/#46 external dependency gate is COMPLETE (2026-11-17). Hosted Renovate detected the genuine `github-build-or-reuse` v1.2.4 release, real update PR #105 merged with no automerge, trusted completion pinned the APM lock (commit 5cae7fc, deployments: []), and cutover PR #107 set the mirror to `sync.managed_by: apm` with the legacy sync verified to skip it. Phases 5/6 are now unblocked for enrollment; Phase 10 still waits for those specialists before the real-app baseline pilot.

## Current Position

Phase: 5 of 15 (Emil Specialist Skills)
Plan: 1 of 1
Status: Unblocked 2026-11-17 - Phase 1/#46 proven via #105 (real Renovate update) and #107 (cutover to `managed_by: apm`). Enrollment readiness for Phases 5/6 is being planned in #56; Phase 6 follows, then Phase 10.
Last activity: 2026-11-17 - Phase 1 completed: hosted Renovate opened real update PR #105 for genuine `github-build-or-reuse` v1.2.4 (merged, no automerge), trusted completion pinned the APM lock, and #107 cut the mirror over to APM management with the legacy sync verified to skip it (#46 evidence complete). Previous: 2026-09-28 - reviewed `emilkowalski/skills`, `coreyhaines31/marketingskills` and `oxbshw/watch-skill`. Phase 5 re-evaluates `mobile-native` as an optional fifth specialist without weakening the four-skill EMIL-01 baseline. Evaluations #90 and #91 remain separate so they do not expand the design-engineering critical path or add dependencies before governance permits them.

Progress: [█████░░░░░] 47%

## Accumulated Context

### Decisions

- Reuse #55 capability publishing; do not create another plugin generator.
- Phase 3 `externalSkillComponents` keeps APM policy + lock as the only dependency resolution/integrity authority.
- Phase 1/#46 proved the hosted Renovate update path on 2026-11-17 (#105 real update + #107 cutover); Emil/Addy enrollment may now proceed under the same APM governance, with versions/paths/licenses re-verified and pinned at enrollment time.
- Local `design-engineering` owns broad routing; upstream skills remain subordinate specialists.
- Phase 5 keeps `prototype`, `pick-ui-library`, `animate` and `review-animations` as the required Emil baseline. The newer `mobile-native` skill is an optional candidate that must prove incremental mobile/PWA platform value before adoption. `emil-design-eng` remains excluded by default because it overlaps the broad orchestrator.
- Marketing Skills is tracked in #90 as a selective upstream source, not a monolithic dependency. Existing startup/social capabilities and product-context authority must be mapped before any adoption.
- Watch Skill is tracked in #91 as a possible `media-understanding` capability, not as a simple `SKILL.md` dependency. Runtime, binaries/models and persistent index lifecycle need separate governance.
- `creative-media` remains responsible for generated media. Understanding existing media is a separate concern and must not be folded into Phase 14 merely because both involve video/audio/image formats.
- Phase 7 reuses the open `DESIGN.md` format: scoped evidence precedence, normative tokens only when genuinely authoritative, labelled inference, and no task-local documentation churn.
- Phase 8 chooses the lightest reliable browser path: existing project e2e/browser tooling first, then Playwright CLI-style execution, optional persistent MCP only when it adds material value.
- Browser MCP is not mandatory for the core capability.
- Representative fallback viewports are 390×844, 768×1024 and 1440×900; project-defined breakpoints/device requirements override them.
- Browser evidence covers the changed critical flow plus applicable states, overflow/wrapping, keyboard/focus and relevant console/runtime evidence.
- Screenshots are comparison evidence, not accessibility/interaction proof.
- Final browser evidence uses explicit `Verified` / `Blocked` / `Not checked` / `Not applicable` statuses.
- Automatic fix/render work is bounded to 3 repair cycles by default after the initial implementation/render; subjective tuning is surfaced for human judgment.
- If the app cannot render, the result is explicitly source-validated only rather than falsely reported as browser-verified.
- Phase 9 uses the repository-native `eval.yaml` + `tasks/*.yaml` Waza convention; no second fixture/eval format was introduced.
- Phase 9 tests the already-implemented core independently of Phases 5/6. Those phases must extend the suite with specialist-specific cases when enrolled; Phase 10 still waits for 5/6 so this does not bypass the supply-chain gate.
- Model-backed behavioral evals remain trusted `workflow_dispatch`/scheduled only; PRs receive deterministic static Waza verification without model credentials.
- Manual trusted Waza runs now fail closed when no supported Copilot credential exists; scheduled runs may skip without noise but must record that no model evidence was produced.
- Creative media remains a separate capability and subjective visual PRs do not auto-merge initially.

### Pending Todos

- Phase 1: COMPLETE 2026-11-17. Real Renovate update PR #105 (v1.2.4) merged with trusted completion; #107 cut the mirror over to `sync.managed_by: apm`. The legacy-sync race is resolved: `scripts/sync-upstreams.sh` now skips this APM-managed mirror, so the former 2026-11-23 06:17 UTC deadline no longer applies.
- #81: compare `create-design-md` URL reconstruction with the local DESIGN.md contract (no dependency needed); enrollment waits for Phase 1. Benchmark `frontend-design` vs local Foundation in Phase 12 after the Phase 10 pilot.
- Phases 5/6 (now unblocked): re-verify the four selected Emil specialists plus `mobile-native` and the Addy Osmani web-quality set (versions/paths/licenses); adopt `mobile-native` only with an explicit evidence-based gap analysis, then execute Phase 5 and Phase 6 and extend the Phase 9 suite for every enrolled specialist. Enrollment readiness plan is being posted to #56.
- Execute Phase 6 web-quality skills next and extend the same suite with quality-specialist behavior/evidence cases.
- Execute Phase 10 real-application pilot only after Phases 5 and 6 are complete.
- Execute #90 research independently of the design-engineering phase count: build the overlap/context/evidence matrix for the shortlisted Marketing Skills, but do not add production APM dependencies before the external dependency gate permits enrollment.
- Execute #91 research independently of Phase 14: benchmark Watch Skill against lighter/direct media-understanding paths and define runtime/toolchain provenance before deciding whether a new capability is justified.

### Blockers/Concerns

- Phase 1 is no longer a blocker: #46's real Renovate update (#105) and cutover (#107) completed on 2026-11-17, satisfying all three Phase 1 success criteria.
- The remaining supply-chain work is enrollment-time re-verification of Emil/Addy upstream versions/paths/licenses and pinning through APM, not the update gate itself.
- The resolver-only upstream proposal remains unanswered; keep the current trusted local completion glue until a maintainer-backed alternative exists.
- Exact Emil/Addy upstream versions/paths/licenses must be re-verified at enrollment time and pinned through APM.
- `mobile-native` was added upstream after the original Phase 5 selection, so novelty alone must not promote it into the required baseline.
- Marketing Skills contains broad context/router behavior and strong quantitative claims that require overlap and evidence review before becoming catalog authority.
- Watch Skill has a wider runtime supply chain than its Agent Skill instructions; an APM lock on the skill alone would not provide complete reproducibility.
- Optional provider integrations require sanitized authenticated evidence before compatibility claims.

## Session Continuity

Last session: 2026-11-17
Stopped at: Phases 1, 2, 3, 4, 7, 8 and 9 complete/verified (7/15). Phase 1/#46 proven via #105 (real Renovate v1.2.4 update) and #107 (cutover to `managed_by: apm`); the legacy-sync race is resolved. The v1.0 chain is now Phase 5/6 enrollment -> Phase 10. Phase 5 includes an explicit optional `mobile-native` decision; enrollment readiness is being planned in #56. Adjacent evaluations #90 and #91 do not change phase counts or bypass dependency governance.
Resume file: `.planning/phases/05-emil-skills/05-01-PLAN.md`
