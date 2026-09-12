# Requirements: Design Engineering Agent Plugin

**Defined:** 2026-09-11
**Core Value:** A simple request produces a repeatable, rendered, evidence-backed UI improvement workflow while reusing existing design assets and keeping final visual judgment reviewable.

## Milestone Requirements

### Foundation — v1.0

- [ ] **SUPPLY-01**: A genuine upstream release can flow through Renovate -> reviewed APM manifest update -> immutable lock/integrity -> materialization -> repository validation without direct-to-main synchronization.
- [x] **PKG-01**: `plugins/design-engineering/` exists as a governed capability package created/checked by the generic #55 publishing contract.
- [x] **EXT-01**: Capability publishing can consume explicitly declared external skill components through APM-locked provenance without creating a second behavior or lock authority.
- [x] **ORCH-01**: The local `design-engineering` skill routes a simple UI-improvement request through recon, reuse, design context, mode selection, implementation, rendered verification, quality checks and bounded iteration.
- [ ] **EMIL-01**: Selected Emil Kowalski specialist skills are governed external components and can be invoked beneath the orchestrator without competing as the default top-level router.
- [ ] **QUAL-01**: Web-quality auditing covers accessibility, performance/Core Web Vitals, SEO/best practices where relevant and distinguishes runtime evidence from source hypotheses.
- [x] **DSYS-01**: Projects can create or consume a concise project-level `DESIGN.md` that records visual/product constraints without duplicating the PRD.
- [ ] **BROW-01**: UI-changing work renders representative desktop/tablet/mobile states, checks interactions/console/overflow/focus, and iterates within a bounded browser loop before completion.
- [ ] **EVAL-01**: Waza/static fixtures cover orchestrator routing, must-not-trigger boundaries, reuse-first behavior, degraded optional integrations, browser evidence and no-visual-auto-merge policy.
- [ ] **PILOT-01**: One real application pilot demonstrates the full baseline workflow and captures before/after evidence, defects found, trade-offs and lessons before broader rollout.

### Optional integrations — v1.1

- [ ] **FIGMA-01**: Figma MCP can be composed as an optional official integration with client-managed auth, provenance, degraded operation and sanitized runtime evidence.
- [ ] **IMP-01**: Impeccable is benchmarked against the baseline on the same fixture/pilot and is adopted only if measurable quality gains justify its hook/engine/runtime complexity.
- [ ] **ADV-01**: Chrome DevTools MCP and 21st/component discovery are evaluated independently and only added where they materially improve evidence or reuse beyond the baseline.

### Expansion — v1.2

- [ ] **MEDIA-01**: A separate `creative-media` capability provides governed image/video/audio provider integration without coupling credentials/costs to the core design plugin.
- [ ] **AUTO-01**: An explicit GitHub issue/label/request can drive branch -> before screenshots -> implementation -> after screenshots -> QA -> PR while keeping merge human-controlled.

## Cross-cutting Constraints

These are invariants, not separately completable requirements:

- No credential-bearing generated manifests or committed runtime evidence.
- External instruction changes never auto-merge solely on SemVer.
- Generated plugin/marketplace surfaces are not independent sources of truth.
- Existing components/libraries/credible OSS are checked before hand-rolling UI primitives.
- Optional integrations degrade; unavailable providers do not block the core workflow.
- Source-only claims never substitute for rendered UI evidence when the page can run.

## Out of Scope

| Feature | Reason |
|---------|--------|
| Automatic merge of visual PRs | Product/taste trade-offs remain human-owned until substantial evidence says otherwise |
| Custom provider MCP implementations | Reuse official/maintained MCPs first |
| Paid creative media inside core design-engineering | Different security/cost/lifecycle; handled by `creative-media` |
| Scheduled unsolicited redesign bot | Too much autonomous product judgment before the explicit-request workflow is proven |
| One global design style | The system must preserve each product's context instead of imposing a house aesthetic |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| SUPPLY-01 | Phase 1 | Blocked — waiting for genuine upstream release newer than v1.2.3 and Renovate evidence |
| PKG-01 | Phase 2 | Complete |
| EXT-01 | Phase 3 | Complete |
| ORCH-01 | Phase 4 | Complete |
| EMIL-01 | Phase 5 | Pending |
| QUAL-01 | Phase 6 | Pending |
| DSYS-01 | Phase 7 | Complete |
| BROW-01 | Phase 8 | Pending |
| EVAL-01 | Phase 9 | Pending |
| PILOT-01 | Phase 10 | Pending |
| FIGMA-01 | Phase 11 | Pending |
| IMP-01 | Phase 12 | Pending |
| ADV-01 | Phase 13 | Pending |
| MEDIA-01 | Phase 14 | Pending |
| AUTO-01 | Phase 15 | Pending |

**Coverage:**
- Milestone requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-09-11*
*Last updated: 2026-09-12 after Phases 2, 3, 4 and 7; Phase 1 remains externally blocked by #46*
