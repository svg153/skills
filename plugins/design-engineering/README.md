# Design Engineering Agent Plugin

Portable capability package for improving existing application interfaces with a simple user request while preserving product context, reuse, rendered evidence and human visual judgment.

## What the user does

Install the capability through a supported Agent Plugin/skills path, then ask naturally:

- `Improve this interface.`
- `Polish the mobile checkout without changing its behavior.`
- `Prototype a few genuinely different directions for this onboarding.`
- `Audit this dashboard UX; do not change code yet.`

The user does **not** need to manually select every underlying design, motion, browser or quality specialist.

## Orchestration model

The canonical local `design-engineering` skill owns broad routing. It first inspects the product, stack, existing components/dependencies, scoped `DESIGN.md`/tokens and rendered baseline when available. It then chooses the smallest fitting mode:

- **Polish** — localized work with low design uncertainty; implement directly.
- **Prototype** — high-impact/uncertain direction; explore meaningful isolated alternatives before integrating one.
- **Audit** — evidence-first findings; read-only by default unless fixes were already authorized.

```text
request
  -> recon existing product/system
  -> resolve scoped design context
  -> reuse gate
  -> polish | prototype | audit
  -> focused specialist delegation when useful
  -> scoped implementation
  -> rendered browser evidence matrix
  -> bounded objective fix/render loop
  -> quality checks
  -> evidence + trade-offs for human review
```

The full state machine is documented in `skills/design-engineering/references/workflow.md`.

## Reuse before build

The capability prefers, in order:

1. an existing project component/pattern;
2. an already-installed library/primitive;
3. a credible maintained external component/library compatible with the stack;
4. a small bespoke implementation only when reuse is unsuitable.

Future packaged specialists can improve component/library discovery without changing this ownership rule.

## DESIGN.md context

The capability follows the open `DESIGN.md` format rather than a repository-specific design-memory schema. It resolves the nearest applicable project/app context, gives stronger authoritative token/component sources precedence when they conflict, and labels inferred visual rules rather than silently converting them into brand truth.

`DESIGN.md` is durable visual-system memory, not a PRD. One-off CSS fixes, unselected prototypes and temporary styling should not churn it.

Detailed behavior is in:

- `skills/design-engineering/references/design-md.md`
- `skills/design-engineering/references/DESIGN.md.template`

## Rendered browser evidence

When an interface can run, UI-mutating work is not complete from source review alone. The capability builds a small evidence matrix around the changed flow and the viewport/state classes that can reveal regressions.

Tooling remains portable and reuse-first:

1. reuse the project's existing Playwright/Cypress/e2e/browser path when it already works;
2. otherwise prefer an available lightweight coding-agent browser CLI such as Playwright CLI;
3. use temporary approved CLI execution rather than adding a project dependency solely for verification when appropriate;
4. escalate to a persistent browser MCP only when durable session state/richer exploratory inspection materially helps;
5. if no automation is available but a real preview can be rendered, report the weaker manual evidence explicitly.

The base capability has **no mandatory browser MCP**.

Representative viewport defaults are `390×844`, `768×1024`, and `1440×900` only when the project has no stronger breakpoint/device requirements. Relevant loading, empty, error, confirmation and interaction states are selected according to the changed journey rather than screenshotting the entire product.

Verification covers, as applicable:

- responsive layout, wrapping, clipping and overflow;
- critical changed interactions;
- keyboard/focus for changed controls;
- relevant console/runtime failures;
- actual rendered loading/empty/error/populated states;
- before/after screenshots when useful for review.

Screenshots are comparison artifacts, not proof of accessibility or interaction correctness. The final evidence report says what was `Verified`, `Blocked`, `Not checked`, or `Not applicable` instead of relying on “looks good”.

The browser/fix loop is bounded: after the initial implementation/render, default maximum is **3 automatic fix → render cycles**, with additional iteration reserved for a concrete functional/accessibility/runtime defect rather than subjective micro-tuning.

Full protocol: `skills/design-engineering/references/browser-loop.md`.

## Optional specialists and integrations

The base capability has **no mandatory MCP** and must keep working when optional integrations are absent. Planned/future focused helpers include prototyping, UI-library selection, motion implementation/review, web-quality auditing, Figma context and component discovery.

They are subordinate specialists, not competing broad routers. Missing optional tools reduce available evidence; they do not justify fabricated results or unsafe workarounds.

## Verification and human boundary

For implementation work, the orchestrator uses project-native tests plus rendered evidence when the page can run. Missing runtime/provider evidence is surfaced explicitly instead of being upgraded to a successful check.

Subjective visual changes are **not auto-merged**. High-impact product/taste choices remain reviewable by a human.

## Canonical sources

- `distribution.config.json` — capability package metadata.
- `skills/design-engineering/SKILL.md` — canonical portable orchestration behavior and routing boundary.
- `skills/design-engineering/references/workflow.md` — detailed orchestration state machine loaded after routing.
- `skills/design-engineering/references/design-md.md` — project design-memory discovery/precedence/update contract.
- `skills/design-engineering/references/browser-loop.md` — rendered browser evidence and bounded iteration contract.
- `plugin.json` — generated Agent Plugins 1.0 manifest; do not edit independently.

External skills and MCP composition are governed by the repository's APM/Renovate and capability publishing contracts rather than copied ad hoc.

## Scope boundaries

This package is for interface work that needs visual/interaction/UX judgment. It should not activate merely because a frontend file changes: backend-only changes, mechanical refactors, formatting and other no-visual-decision tasks stay with their normal workflows.

No claim of universal runtime/tool availability is made. Each optional integration must carry its own compatibility/auth evidence and degradation path.

## Roadmap

Tracked by `svg153/skills#56` and the GSD workspace under `.planning/`.
