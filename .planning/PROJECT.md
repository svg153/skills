# Design Engineering Agent Plugin

## What This Is

A governed Design Engineering capability for `svg153/skills` that lets an agent improve real application interfaces from a simple user request while reusing specialized design skills, existing UI libraries, browser verification, web-quality checks, and optional design integrations. It is packaged as an Agent Plugin and uses the repository's existing APM/Renovate supply chain instead of copying unmanaged prompts or building provider-specific wrappers.

Tracking initiative: #56.

## Core Value

A user can say “improve this interface” and get a repeatable, evidence-backed UI improvement workflow that respects the existing product, reuses before building, renders the result, verifies it, and keeps the final visual decision reviewable by a human.

## Requirements

### Validated

- ✓ Agent Plugin capability packaging, generic validation, and `skill-publish` capability registration exist in the repository — #55.
- ✓ External Agent Skill resolution/integrity has an APM + policy + Renovate architecture — #44.
- ✓ Capability MCP composition supports official reusable MCP endpoints without embedding credentials — #33/#35.
- ✓ Waza behavioral evaluation can target capability-embedded skills — #33/#36.

### Active

- [ ] Prove the first genuine Renovate-driven APM dependency update and use that path for design dependencies.
- [ ] Ship an installable `design-engineering` capability with a local orchestrator plus governed external components.
- [ ] Make browser rendering, responsive inspection, accessibility/performance evidence, and bounded iteration part of the normal workflow.
- [ ] Prove the workflow on a real application before adding expensive/optional integrations or broad automation.
- [ ] Keep Figma, Impeccable, DevTools/component discovery, creative media, and GitHub automation evidence-driven and independently degradable.

### Out of Scope

- Automatically merging visual changes — aesthetic/product judgment remains human-reviewed in the initial milestones.
- Building custom GitHub, Figma, browser, media, or component MCP servers when maintained official/community capabilities already exist.
- Treating every upstream design opinion as a universal rule; upstream skills remain specialized advisers beneath local orchestration.
- Putting Higgsfield/ElevenLabs/MiniMax credentials or paid-generation behavior in the core design plugin.
- A scheduled bot that redesigns applications without an explicit issue/label/request; automation arrives only after the manual path is proven.

## Context

- `plugins/planning/` is the proven capability-package reference and already demonstrates skill + multi-MCP composition.
- #55 made capability creation and validation generic; new design work should extend that contract rather than introduce another generator.
- `dependencies/external-skills/` already contains resolver-only APM state, immutable lock/integrity policy, SBOM/audit plumbing, and Renovate configuration.
- Emil Kowalski's skills are strongest as narrow specialists (`prototype`, `pick-ui-library`, `animate`, `review-animations`) rather than as a competing top-level router.
- Addy Osmani's web-quality skills provide evidence-led accessibility, performance, Core Web Vitals, SEO and best-practice audits with browser/CLI degradation paths.
- Impeccable is promising but has a larger runtime/hook/engine surface; it must be benchmarked against the simpler baseline before core adoption.
- The preferred browser path for coding work is a lightweight Playwright CLI/skill loop; MCP/browser state is optional when it adds value.

## Constraints

- **Supply chain**: External skill payloads must be immutable, provenance-governed, reviewed, and covered by behavioral/routing evidence before merge.
- **Source of truth**: `SKILL.md` owns portable behavior; package config owns package/MCP provenance; generated manifests are derived only.
- **Security**: No external credentials in plugin manifests, planning artifacts, fixtures, or runtime evidence.
- **Compatibility**: Optional MCPs/services must degrade safely; core design work cannot require Figma or a paid media provider.
- **Reuse-first**: Inspect the project, installed dependencies, existing components and credible OSS/components before building new primitives.
- **Visual verification**: UI changes are not complete from source inspection alone; rendered evidence is required for representative viewports/states.
- **Human control**: Important redesigns may propose variants, but promotion/merge remains a human decision initially.

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Make `design-engineering` an Agent Plugin capability, not a mega root skill | One install can carry orchestration + specialist skills + optional MCP composition without duplicating behavior | — Pending |
| Extend #55 capability publishing for governed external skill components | Avoid a second plugin generator and keep APM/Renovate as the dependency authority | — Pending |
| Keep local orchestration narrow and delegate specialist craft | Reduces trigger conflict and lets upstream expertise update independently | — Pending |
| Use Playwright-style rendered verification as core; browser MCPs optional | Keeps the default coding loop lower-context and deterministic | — Pending |
| Gate Impeccable adoption behind a real benchmark | Its runtime hooks/engine add complexity that must earn its place | — Pending |
| Split creative media into a separate capability | Different credentials, costs, latency and security lifecycle from normal UI engineering | — Pending |
| No visual auto-merge in initial milestones | Automated checks cannot fully replace product/taste judgment | — Pending |

---
*Last updated: 2026-09-11 after GSD initiative planning for #56*
