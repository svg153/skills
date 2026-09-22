# Design Engineering Agent Plugin

Portable capability package for creating, improving and auditing application interfaces with a simple user request while preserving product context, reuse, rendered evidence and human visual judgment.

The goal is not to make the user orchestrate a bag of UI skills. The plugin owns the workflow and calls narrow specialists only when they add value.

## What the user does

Install the capability through a supported Agent Plugin/skills path, then ask naturally:

- `Make this app look like a real product.`
- `Give this working frontend a coherent visual system.`
- `Improve this interface.`
- `Polish the mobile checkout without changing its behavior.`
- `Prototype a few genuinely different directions for this onboarding.`
- `Audit this dashboard UX; do not change code yet.`
- `Improve this screen and explain the main design decisions so I can learn.`

The user does **not** need to manually select every underlying design, motion, browser or quality specialist.

Longer prompt recipes are available in `skills/design-engineering/references/prompt-recipes.md`, but short outcome-oriented requests are intentionally supported.

## The problem this capability is designed to solve

A functional frontend can still feel amateur when it has no coherent hierarchy, palette, typography, spacing rhythm, component treatment or interaction language. Repeated local fixes often make this worse because each component becomes individually plausible while the product remains visually inconsistent.

`design-engineering` therefore distinguishes between preserving a good system and creating one when the current design is missing or unsuitable. Existing code is evidence, not automatically a design decision worth keeping.

## Orchestration model

The canonical local `design-engineering` skill owns broad routing. It first inspects the product, stack, existing components/dependencies, scoped `DESIGN.md`/tokens and rendered baseline when available. It also classifies the visual foundation as coherent, partial/inconsistent, or missing/unsuitable. It then chooses the smallest fitting mode:

- **Foundation**: establish a coherent visual direction and prove it on one representative production surface when the current design system is missing, weak or unsuitable.
- **Polish**: localized work when the existing direction is sound.
- **Prototype**: explore meaningfully different directions when a high-impact choice is genuinely uncertain.
- **Audit**: evidence-first findings, read-only by default unless fixes were already authorized.

```text
request
  -> recon product/system/rendered baseline
  -> classify visual foundation
  -> resolve scoped design context
  -> reuse gate
  -> foundation | polish | prototype | audit
  -> focused specialist delegation when useful
  -> scoped implementation
  -> rendered browser evidence matrix
  -> bounded objective fix/render loop
  -> quality checks
  -> evidence + trade-offs for human review
```

The full state machine is documented in `skills/design-engineering/references/workflow.md`.

Foundation mode has its own playbook in `skills/design-engineering/references/foundation-mode.md`.

## Foundation mode: from functional to intentional

Foundation mode is aimed at projects where keeping the current styling would preserve accidental or poor decisions. It does not immediately restyle the whole app.

The workflow is:

1. understand the primary user, task, density and platform constraints;
2. separate reusable interaction behavior from weak visual styling;
3. choose a visual direction that constrains real implementation decisions;
4. establish a small system for color, typography, spacing, shape/depth, iconography, responsive behavior and motion;
5. implement one representative **golden surface** first;
6. render and calibrate that surface across relevant states/viewports;
7. move durable decisions into real theme/token/component owners and `DESIGN.md` when appropriate;
8. propagate through shared owners rather than editing every screen independently.

The golden surface is important. It prevents an agent from applying a half-tested aesthetic across the entire product before seeing whether the hierarchy, density and component treatment actually work together.

Foundation mode also includes an anti-slop pass for common AI UI failure modes such as gratuitous cards, arbitrary gradients/glow, weak typography hierarchy, mixed icon styles, library defaults as final identity, random radii/shadows and marketing-page spacing inside dense product workflows. These are diagnostic signals rather than universal bans.

## Reuse before build

The capability prefers, in order:

1. an existing project component/pattern when it fits the selected visual direction;
2. an already-installed library or primitive;
3. a credible maintained external component/library compatible with the stack;
4. a small bespoke implementation only when reuse is unsuitable.

Accessible component behavior and product visual identity are treated separately. A project can reuse shadcn, Base UI, Radix, React Aria or another primitive system without letting the library's default theme define the final product.

Future packaged specialists can improve component/library discovery without changing this ownership rule.

## DESIGN.md context

The capability follows the open `DESIGN.md` format rather than a repository-specific design-memory schema. It resolves the nearest applicable project/app context, gives stronger authoritative token/component sources precedence when they conflict, and labels inferred visual rules rather than silently converting them into brand truth.

`DESIGN.md` is durable visual-system memory, not a PRD. One-off CSS fixes, unselected prototypes and temporary styling should not churn it.

Detailed behavior is in:

- `skills/design-engineering/references/design-md.md`
- `skills/design-engineering/references/DESIGN.md.template`

Foundation mode may create or substantially update `DESIGN.md` after a visual direction is selected and proven. It should not document speculative alternatives as production truth.

## Prompt recipes and learning mode

Agent Plugins 1.0 has a portable core for skills and MCP server configuration. It does not standardize a cross-client first-class prompt/slash-command component. The plugin therefore keeps canonical prompt examples as a reference shipped inside the skill:

- `skills/design-engineering/references/prompt-recipes.md`

This keeps the usage guidance available across compatible clients without making the workflow depend on one host-specific command format.

Client-specific commands or automation templates can be added later under extension namespaces when they materially improve UX, but they should delegate to the same canonical skill rather than fork its behavior.

When the user asks to learn, the skill adds a compact design rationale covering the few decisions that matter most, such as hierarchy, color, typography, spacing/density, component treatment and motion. It still performs the implementation rather than replacing work with generic design theory.

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

Screenshots are comparison artifacts, not proof of accessibility or interaction correctness. The final evidence report says what was `Verified`, `Blocked`, `Not checked`, or `Not applicable` instead of relying on "looks good".

The browser/fix loop is bounded: after the initial implementation/render, default maximum is **3 automatic fix -> render cycles**, with additional iteration reserved for a concrete functional/accessibility/runtime defect rather than subjective micro-tuning.

Full protocol: `skills/design-engineering/references/browser-loop.md`.

## Optional specialists and integrations

The base capability has **no mandatory MCP** and must keep working when optional integrations are absent. Planned/future focused helpers include UI polish, prototyping, UI-library selection, motion implementation/review, web-quality auditing, Figma context and component discovery.

They are subordinate specialists, not competing broad routers. Missing optional tools reduce available evidence; they do not justify fabricated results or unsafe workarounds.

Public UI-skill registries are useful discovery sources, but dynamically loading unreviewed external instructions would bypass this repository's provenance and update-review model. Candidate specialists should therefore be evaluated and enrolled through the repository's governed dependency path before they become package authority.

## Verification and human boundary

For implementation work, the orchestrator uses project-native tests plus rendered evidence when the page can run. Missing runtime/provider evidence is surfaced explicitly instead of being upgraded to a successful check.

Subjective visual changes are **not auto-merged**. High-impact product/taste choices remain reviewable by a human.

## Canonical sources

- `distribution.config.json`: capability package metadata.
- `skills/design-engineering/SKILL.md`: canonical portable orchestration behavior and routing boundary.
- `skills/design-engineering/references/workflow.md`: detailed orchestration state machine loaded after routing.
- `skills/design-engineering/references/foundation-mode.md`: visual-foundation and golden-surface workflow.
- `skills/design-engineering/references/prompt-recipes.md`: portable usage examples and learning-mode prompts.
- `skills/design-engineering/references/design-md.md`: project design-memory discovery/precedence/update contract.
- `skills/design-engineering/references/browser-loop.md`: rendered browser evidence and bounded iteration contract.
- `plugin.json`: generated Agent Plugins 1.0 manifest; do not edit independently.

External skills and MCP composition are governed by the repository's APM/Renovate and capability publishing contracts rather than copied ad hoc.

## Scope boundaries

This package is for interface work that needs visual/interaction/UX judgment. It should not activate merely because a frontend file changes: backend-only changes, mechanical refactors, formatting and other no-visual-decision tasks stay with their normal workflows.

No claim of universal runtime/tool availability is made. Each optional integration must carry its own compatibility/auth evidence and degradation path.

## Roadmap

Tracked by `svg153/skills#56` and the GSD workspace under `.planning/`.
