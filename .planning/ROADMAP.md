# Roadmap: Design Engineering Agent Plugin

## Overview

The roadmap deliberately proves governance before adding dependencies, then builds the smallest useful design capability, verifies it on a real app, and only then evaluates optional/high-complexity integrations and automation. The 15 phases map one-to-one to the agreed roadmap so no idea is lost, while milestones make the core baseline (1-10) independently shippable from optional integrations (11-13) and expansion (14-15).

## Milestones

- 🚧 **v1.0 Design Engineering Baseline** — Phases 1-10
- 📋 **v1.1 Evidence-driven Integrations** — Phases 11-13
- 📋 **v1.2 Creative + GitHub Automation** — Phases 14-15

## Phases

- [ ] **Phase 1: Prove APM/Renovate Update Gate** — BLOCKED externally until a genuine stable release newer than `github-build-or-reuse v1.2.3` is processed by hosted Renovate.
- [x] **Phase 2: Establish Design Engineering Capability** — registered and cross-agent validated the package using the generic capability contract landed in #55.
- [x] **Phase 3: External Skill Components** — capability publishing now materializes reviewed APM-lock-backed specialist skills without introducing a second lock or dependency authority.
- [x] **Phase 4: Design Engineering Orchestrator** — broad UI requests now route through recon/reuse, polish/prototype/audit selection, bounded verification and human review boundaries.
- [ ] **Phase 5: Emil Specialist Skills** — govern and package only the narrow high-value design/motion/reuse skills.
- [ ] **Phase 6: Web Quality Skills** — integrate evidence-led accessibility/performance/SEO/best-practice auditing.
- [x] **Phase 7: DESIGN.md Contract** — adopted the open DESIGN.md format with evidence precedence, monorepo scope and reviewable create/update behavior.
- [x] **Phase 8: Playwright Visual Loop** — rendered UI evidence now has a portable browser protocol, responsive/state matrix, interaction/console/focus checks and bounded repair cycles.
- [ ] **Phase 9: Behavioral Evals and Fixtures** — prove routing, reuse, degradation and safety behavior.
- [ ] **Phase 10: Real Application Pilot** — validate the baseline on one production-shaped app before expanding scope.
- [ ] **Phase 11: Optional Figma MCP** — compose official Figma access and capture authenticated/degraded evidence.
- [ ] **Phase 12: Impeccable Benchmark** — compare against the proven baseline before adoption.
- [ ] **Phase 13: Advanced Browser and Component Integrations** — evaluate DevTools MCP and 21st/component discovery independently.
- [ ] **Phase 14: Creative Media Capability** — isolate image/video/audio integrations into a separate governed plugin.
- [ ] **Phase 15: GitHub UI Improvement Automation** — explicit issue/label to evidence-rich PR, without auto-merge.

## Phase Details

### Phase 1: Prove APM/Renovate Update Gate
**Goal**: Complete the first genuine Renovate-driven external skill update from #46 and make it the accepted dependency path for this initiative.
**Depends on**: External genuine upstream release and hosted Renovate processing.
**Requirements**: SUPPLY-01
**Success Criteria**:
1. A real stable upstream release is detected by Renovate and proposed as a normal reviewed PR.
2. Trusted completion produces immutable APM lock/integrity, materializes the mirror, runs policy/SBOM/evals, and rollback remains deterministic.
3. Legacy direct-to-main synchronization stops owning the migrated mirror only after parity is proven.
**Plans**: 1 plan — `01-01-PLAN.md`

### Phase 2: Establish Design Engineering Capability
**Goal**: Create a minimal governed `plugins/design-engineering` package with a local orchestrator placeholder and deterministic generated manifests.
**Depends on**: Phase 1 supply-chain gate for external dependency enrollment; package shell itself is safe to establish independently because it consumes no external design skill.
**Requirements**: PKG-01
**Success Criteria**:
1. `skill-publish` can plan/apply/check the capability without a parallel generator.
2. Generic capability validation and cross-agent discovery pass.
3. Package metadata clearly states purpose, ownership and optional integration boundaries.
**Plans**: 1 plan — `02-01-PLAN.md` — COMPLETE 2026-09-12

### Phase 3: External Skill Components
**Goal**: Add a reusable declaration/materialization model for APM-locked skills embedded in a capability package.
**Depends on**: Phase 2
**Requirements**: EXT-01
**Success Criteria**:
1. Capability config can explicitly reference allowed APM-locked skill components and materialize exact payloads deterministically.
2. Drift, missing locks, path escapes, provenance ambiguity and unauthorized dependencies fail closed.
3. Generated package copies are derived artifacts; APM lock/policy and upstream provenance remain authoritative.
**Plans**: 1 plan — `03-01-PLAN.md` — COMPLETE 2026-09-12

### Phase 4: Design Engineering Orchestrator
**Goal**: Implement the small local skill that selects the right workflow instead of embedding every design rule itself.
**Depends on**: Phase 2
**Requirements**: ORCH-01
**Success Criteria**:
1. A generic “improve this interface” request triggers recon -> reuse -> design context -> mode -> implement -> render -> quality -> iterate.
2. `polish`, `prototype`, and `audit` behavior differ appropriately and avoid needless prototype work for small changes.
3. The orchestrator fails/degrades clearly when optional specialist/browser capabilities are absent.
**Plans**: 1 plan — `04-01-PLAN.md` — COMPLETE 2026-09-12

### Phase 5: Emil Specialist Skills
**Goal**: Integrate selected narrow specialist skills without installing another competing broad router.
**Depends on**: Phases 3 and 4; enrollment additionally waits for the Phase 1 hosted Renovate/APM proof.
**Requirements**: EMIL-01
**Success Criteria**:
1. `prototype`, `pick-ui-library`, `animate`, and `review-animations` are pinned, provenance-governed and packaged.
2. Their routing is subordinate/specialized; the normal broad design request still lands on the local orchestrator.
3. Upstream updates produce reviewable dependency diffs and behavioral evidence before merge.
**Plans**: 1 plan — `05-01-PLAN.md`

### Phase 6: Web Quality Skills
**Goal**: Add evidence-led quality auditing as a normal post-implementation capability.
**Depends on**: Phases 3 and 4; enrollment additionally waits for the Phase 1 hosted Renovate/APM proof.
**Requirements**: QUAL-01
**Success Criteria**:
1. The required Addy Osmani skill set is packaged with relative references intact.
2. Runtime evidence is separated from source-only hypotheses and unavailable browser tools have documented fallbacks.
3. Accessibility/performance regressions relevant to a UI change can block completion even when visual appearance is acceptable.
**Plans**: 1 plan — `06-01-PLAN.md`

### Phase 7: DESIGN.md Contract
**Goal**: Give each application a concise, durable design context that can be inferred, created and updated without becoming a second PRD.
**Depends on**: Phase 4
**Requirements**: DSYS-01
**Success Criteria**:
1. The contract covers personality, typography, color, spacing, radii/elevation, components, motion, responsive rules, accessibility and do/don't guidance.
2. Existing design systems/tokens/Figma context win over invented defaults.
3. Monorepo/project-local scope is explicit and changes are reviewable.
**Plans**: 1 plan — `07-01-PLAN.md` — COMPLETE 2026-09-12

### Phase 8: Playwright Visual Loop
**Goal**: Make rendered UI evidence mandatory for normal UI-changing work while keeping the loop bounded.
**Depends on**: Phase 4
**Requirements**: BROW-01
**Success Criteria**:
1. Representative 390/768/1440 viewport classes plus relevant loading/empty/error/interaction states are exercised when applicable, with project-defined breakpoints taking precedence.
2. Console errors, overflow, focus/keyboard behavior and key flows are checked, with before/after screenshots where useful but never as the sole accessibility/interaction evidence.
3. Automatic polish repair iteration is capped at three cycles after the initial implementation/render and unresolved subjective trade-offs are surfaced rather than endlessly tuned.
**Plans**: 1 plan — `08-01-PLAN.md` — COMPLETE 2026-09-12

### Phase 9: Behavioral Evals and Fixtures
**Goal**: Make the capability's routing and safety properties regression-testable before the first real pilot.
**Depends on**: Phases 5, 6, 7 and 8
**Requirements**: EVAL-01
**Success Criteria**:
1. Positive and negative Waza cases cover broad design requests, small mechanical frontend edits, prototype-worthy changes, audit-only requests and no-visual backend work.
2. Fixtures prove reuse-first, optional-integration degradation, browser-evidence requirements and human merge boundaries.
3. Static PR validation is cheap; model-backed evals remain trusted/scheduled/manual as in the existing repository contract.
**Plans**: 1 plan — `09-01-PLAN.md`

### Phase 10: Real Application Pilot
**Goal**: Prove the baseline against a real application rather than a synthetic landing page.
**Depends on**: Phase 9
**Requirements**: PILOT-01
**Success Criteria**:
1. One real app (prefer Future Family Flow or the price comparator) is onboarded without special-case code in `svg153/skills`.
2. Evidence includes baseline screenshots/quality findings, implemented changes, after screenshots, tests/audits and human judgment on usefulness.
3. Pilot lessons feed back into the orchestrator/evals before optional integrations are accepted.
**Plans**: 1 plan — `10-01-PLAN.md`

### Phase 11: Optional Figma MCP
**Goal**: Add Figma as optional structured design context, never as a hard dependency.
**Depends on**: Phase 10
**Requirements**: FIGMA-01
**Success Criteria**:
1. Official Figma MCP provenance/config is generated without credentials and client-managed auth is documented.
2. Authenticated read evidence is captured and sanitized; failure/unavailability falls back to repository/DESIGN.md context.
3. Figma context can enrich design decisions without creating a second design-system source of truth.
**Plans**: 1 plan — `11-01-PLAN.md`

### Phase 12: Impeccable Benchmark
**Goal**: Decide USE/CONTRIBUTE/FORK/SKIP for Impeccable based on evidence from the same baseline fixture/pilot.
**Depends on**: Phase 10
**Requirements**: IMP-01
**Success Criteria**:
1. Baseline and Impeccable-assisted runs are compared on quality findings, routing reliability, runtime friction, portability and maintenance/security surface.
2. Current hook/engine/reference-loading behavior and open operational risks are explicitly considered.
3. Adoption happens only if the benefit is material; otherwise the decision and revisit trigger are recorded.
**Plans**: 1 plan — `12-01-PLAN.md`

### Phase 13: Advanced Browser and Component Integrations
**Goal**: Evaluate Chrome DevTools MCP and 21st/component discovery separately, adding only capabilities not already covered well.
**Depends on**: Phase 10
**Requirements**: ADV-01
**Success Criteria**:
1. DevTools is judged on diagnostics/performance evidence beyond the Playwright baseline, not on novelty.
2. Component discovery is judged on reuse quality and dependency risk beyond `pick-ui-library`/existing project components.
3. Each integration has an independent keep/skip decision and degradation path.
**Plans**: 1 plan — `13-01-PLAN.md`

### Phase 14: Creative Media Capability
**Goal**: Create a separately installable capability for generated image/video/audio needs after the core design path is proven.
**Depends on**: Phases 3 and 10
**Requirements**: MEDIA-01
**Success Criteria**:
1. `plugins/creative-media` has provider-neutral orchestration and no committed credentials.
2. Higgsfield/ElevenLabs/MiniMax-like providers are evaluated/reused according to actual supported APIs/MCPs/skills at implementation time.
3. `design-engineering` can recommend/delegate asset work without requiring or owning paid-media configuration.
**Plans**: 1 plan — `14-01-PLAN.md`

### Phase 15: GitHub UI Improvement Automation
**Goal**: Turn an explicit GitHub request into a reviewable evidence-rich design PR using the proven baseline.
**Depends on**: Phases 10-14 as applicable
**Requirements**: AUTO-01
**Success Criteria**:
1. An explicit issue/label/workflow dispatch creates isolated work, captures before evidence, applies the capability, captures after/QA evidence and opens a non-draft PR.
2. PR output explains reuse decisions, screenshots/viewports, quality checks, trade-offs and any manual verification still required.
3. The workflow never auto-merges visual changes and does not require optional paid/Figma integrations to operate.
**Plans**: 1 plan — `15-01-PLAN.md`

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Prove APM/Renovate Update Gate | v1.0 | 0/1 | Blocked — external release/Renovate condition | - |
| 2. Establish Design Engineering Capability | v1.0 | 1/1 | Complete | 2026-09-12 |
| 3. External Skill Components | v1.0 | 1/1 | Complete | 2026-09-12 |
| 4. Design Engineering Orchestrator | v1.0 | 1/1 | Complete | 2026-09-12 |
| 5. Emil Specialist Skills | v1.0 | 0/1 | Blocked by Phase 1 external release/Renovate proof | - |
| 6. Web Quality Skills | v1.0 | 0/1 | Blocked by Phase 1 external release/Renovate proof | - |
| 7. DESIGN.md Contract | v1.0 | 1/1 | Complete | 2026-09-12 |
| 8. Playwright Visual Loop | v1.0 | 1/1 | Complete | 2026-09-12 |
| 9. Behavioral Evals and Fixtures | v1.0 | 0/1 | Blocked by Phases 5/6 | - |
| 10. Real Application Pilot | v1.0 | 0/1 | Blocked by Phase 9 | - |
| 11. Optional Figma MCP | v1.1 | 0/1 | Blocked by Phase 10 | - |
| 12. Impeccable Benchmark | v1.1 | 0/1 | Blocked by Phase 10 | - |
| 13. Advanced Browser and Component Integrations | v1.1 | 0/1 | Blocked by Phase 10 | - |
| 14. Creative Media Capability | v1.2 | 0/1 | Blocked by Phase 10 | - |
| 15. GitHub UI Improvement Automation | v1.2 | 0/1 | Blocked by Phase 10+ | - |
