---
gsd_state_version: '1.0'
status: executing
progress:
  total_phases: 15
  completed_phases: 6
  total_plans: 15
  completed_plans: 6
  percent: 40
---
# Project State

## Project Reference

See: `.planning/PROJECT.md` (updated 2026-09-11)

**Core value:** A simple request produces a repeatable, rendered, evidence-backed UI improvement workflow while preserving reuse and human visual judgment.
**Current focus:** External dependency gate - Phase 1/#46. Hosted Renovate activation is now verified through #75; the remaining gate is a genuine stable `github-build-or-reuse` release newer than v1.2.3 producing the real Renovate update PR. Phases 5/6 remain blocked by that genuine update proof, and Phase 10 deliberately waits for those specialists before the real-app baseline pilot.

## Current Position

Phase: 9 of 15 (Behavioral Evals and Fixtures)
Plan: 1 of 1
Status: Complete; no further v1.0 implementation can truthfully complete until the Phase 1 external condition unlocks Phases 5/6.
Last activity: 2026-09-28 - reviewed `emilkowalski/skills`, `coreyhaines31/marketingskills` and `oxbshw/watch-skill`. Phase 5 now explicitly re-evaluates `mobile-native` as an optional fifth specialist without weakening the original four-skill EMIL-01 baseline. Separate evaluations #90 and #91 were opened for growth-marketing and media-understanding so those ideas do not silently expand the design-engineering critical path or add dependencies before governance permits them.

Progress: [████░░░░░░] 40%

## Accumulated Context

### Decisions

- Reuse #55 capability publishing; do not create another plugin generator.
- Phase 3 `externalSkillComponents` keeps APM policy + lock as the only dependency resolution/integrity authority.
- No Emil/Addy dependency is enrolled until Phase 1/#46 proves the hosted Renovate update path with a genuine newer upstream release.
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

- Revisit Phase 1 immediately when `ghspain/github-build-or-reuse` publishes a genuine stable release newer than v1.2.3 and hosted Renovate opens the required update PR.
- After Phase 1 proof, re-verify the four selected Emil specialists plus `mobile-native`; adopt `mobile-native` only with an explicit evidence-based gap analysis, then execute Phase 5 and extend the Phase 9 suite for every enrolled specialist.
- Execute Phase 6 web-quality skills next and extend the same suite with quality-specialist behavior/evidence cases.
- Execute Phase 10 real-application pilot only after Phases 5 and 6 are complete.
- Execute #90 research independently of the design-engineering phase count: build the overlap/context/evidence matrix for the shortlisted Marketing Skills, but do not add production APM dependencies before the external dependency gate permits enrollment.
- Execute #91 research independently of Phase 14: benchmark Watch Skill against lighter/direct media-understanding paths and define runtime/toolchain provenance before deciding whether a new capability is justified.

### Blockers/Concerns

- Phase 1 intentionally cannot claim success until #46 observes a genuine newer upstream release and Renovate PR; latest checked 2026-09-16 remains v1.2.3.
- Hosted Renovate activation/processing is already evidenced by #75, so installation/configuration is no longer the blocker; the missing external event is the next genuine stable upstream release.
- The resolver-only upstream proposal remains unanswered; keep the current trusted local completion glue until a maintainer-backed alternative exists.
- Exact Emil/Addy upstream versions/paths/licenses must be re-verified at enrollment time and pinned through APM.
- `mobile-native` was added upstream after the original Phase 5 selection, so novelty alone must not promote it into the required baseline.
- Marketing Skills contains broad context/router behavior and strong quantitative claims that require overlap and evidence review before becoming catalog authority.
- Watch Skill has a wider runtime supply chain than its Agent Skill instructions; an APM lock on the skill alone would not provide complete reproducibility.
- Optional provider integrations require sanitized authenticated evidence before compatibility claims.

## Session Continuity

Last session: 2026-09-28
Stopped at: Phases 2, 3, 4, 7, 8 and 9 remain complete/verified. Hosted Renovate activation remains verified; the remaining v1.0 chain is externally gated at the next genuine upstream release: Phase 1/#46 -> Phase 5/6 -> Phase 10. Phase 5 planning now includes an explicit optional `mobile-native` decision. Adjacent evaluations #90 and #91 are recorded but do not change phase counts or bypass dependency governance.
Resume file: `.planning/phases/01-apm-renovate-proof/01-01-PLAN.md`
