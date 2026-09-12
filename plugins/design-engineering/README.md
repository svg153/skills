# Design Engineering Agent Plugin

Portable capability package for improving existing application interfaces with a simple user request while preserving product context, reuse and human visual judgment.

## What the user does

Install the capability through a supported Agent Plugin/skills path, then ask naturally:

- `Improve this interface.`
- `Polish the mobile checkout without changing its behavior.`
- `Prototype a few genuinely different directions for this onboarding.`
- `Audit this dashboard UX; do not change code yet.`

The user does **not** need to manually select every underlying design, motion, browser or quality specialist.

## Orchestration model

The canonical local `design-engineering` skill owns broad routing. It first inspects the product, stack, existing components/dependencies, design conventions and rendered baseline when available. It then chooses the smallest fitting mode:

- **Polish** — localized work with low design uncertainty; implement directly.
- **Prototype** — high-impact/uncertain direction; explore meaningful isolated alternatives before integrating one.
- **Audit** — evidence-first findings; read-only by default unless fixes were already authorized.

```text
request
  -> recon existing product/system
  -> reuse gate
  -> polish | prototype | audit
  -> focused specialist delegation when useful
  -> scoped implementation
  -> render / inspect / bounded fix loop
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

## Optional specialists and integrations

The base capability has **no mandatory MCP** and must keep working when optional integrations are absent. Planned/future focused helpers include prototyping, UI-library selection, motion implementation/review, web-quality auditing, browser evidence, Figma context and component discovery.

They are subordinate specialists, not competing broad routers. Missing optional tools reduce available evidence; they do not justify fabricated results or unsafe workarounds.

## Verification and human boundary

For implementation work, the orchestrator uses project-native tests and rendered evidence when the page can run, with a bounded default visual iteration budget of three inspect/fix cycles. It surfaces missing browser/provider evidence explicitly.

Subjective visual changes are **not auto-merged**. High-impact product/taste choices remain reviewable by a human.

## Canonical sources

- `distribution.config.json` — capability package metadata.
- `skills/design-engineering/SKILL.md` — canonical portable orchestration behavior and routing boundary.
- `skills/design-engineering/references/workflow.md` — detailed orchestration state machine loaded after routing.
- `plugin.json` — generated Agent Plugins 1.0 manifest; do not edit independently.

External skills and MCP composition are governed by the repository's APM/Renovate and capability publishing contracts rather than copied ad hoc.

## Scope boundaries

This package is for interface work that needs visual/interaction/UX judgment. It should not activate merely because a frontend file changes: backend-only changes, mechanical refactors, formatting and other no-visual-decision tasks stay with their normal workflows.

No claim of universal runtime/tool availability is made. Each optional integration must carry its own compatibility/auth evidence and degradation path.

## Roadmap

Tracked by `svg153/skills#56` and the GSD workspace under `.planning/`.
