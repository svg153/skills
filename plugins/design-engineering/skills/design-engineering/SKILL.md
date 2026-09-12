---
name: design-engineering
description: "Improve, redesign, or audit an existing application interface when visual, interaction, or UX judgment is required. Preserve product context, inspect and reuse the existing design/component system first, choose the smallest fitting workflow, and verify rendered behavior. Not for backend-only work or purely mechanical frontend refactors with no visual decision."
license: MIT
metadata:
  author: svg153
  version: "0.2"
---

# Design Engineering

Coordinate interface work rather than acting as another encyclopedia of CSS rules. Keep the user's request simple; discover the product and delegate narrow specialist work only when it adds value.

## Routing boundary

Use this skill for broad or ambiguous UI work such as:

- improve, polish, redesign, modernize, or critique a screen or flow;
- improve hierarchy, usability, responsive behavior, interaction, empty/loading/error states, or visual consistency;
- turn an existing functional interface into a stronger product experience;
- decide whether a requested UI change needs direct polish, divergent prototyping, or audit-first analysis.

Do **not** activate it merely because a frontend file is touched. Backend-only changes, analytics wiring with no visible effect, dependency bumps, mechanical renames, formatting, and explicit narrow specialist requests should stay with their normal workflow/specialist.

## Required first pass: recon before invention

Before proposing or editing visual behavior:

1. Read the product/request context and identify the exact user outcome and affected journey.
2. Inspect the stack, package/dependency manifests, app structure, relevant routes and existing tests.
3. Inspect existing components, primitives, tokens/theme variables, typography, spacing, icons/assets, responsive conventions and any `DESIGN.md`/design docs.
4. Inspect the current rendered UI when the app can run; do not infer the whole experience from source alone.
5. Check whether the requested need is already solved by an existing project component/dependency before searching for or creating another one.

Do not impose a house style or replace a coherent existing system merely because another aesthetic is fashionable.

## Reuse-first decision chain

Prefer, in order:

1. an existing component/pattern in the application;
2. an already-installed library or primitive;
3. a credible maintained component/library compatible with the stack, using the available reuse/discovery specialist when present;
4. a small local implementation only when reuse is unsuitable.

If introducing a dependency, explain why the existing system was insufficient and keep the dependency surface proportional to the need.

## Choose one mode

After recon, choose the smallest workflow that matches scope and uncertainty:

- **Polish** — direction is already sound and the change is localized. Implement directly; do not generate ceremonial variants.
- **Prototype** — the surface is high-impact and the right visual/interaction direction is genuinely uncertain. Explore distinct concepts outside production code, obtain a human/product choice when that choice materially changes the product, then integrate only the selected direction.
- **Audit** — the user asked for review/critique, the problem is unclear, or changing code before diagnosis would be premature. Default to read-only findings prioritized by evidence; mutate only when the request already authorizes fixes or the user subsequently chooses them.

Read `references/workflow.md` after routing for the full state machine, mode entry/exit criteria, degradation rules, browser/quality handoff and completion contract.

## Specialist delegation

Focused capabilities may be available for prototyping, UI-library selection, animation, animation review, web-quality auditing, browser automation, design-system context, or component discovery. Use them as **subordinate specialists**, not competing default routers.

- Delegate only the narrow task they own.
- Preserve their evidence/results when returning to this workflow.
- If a specialist or MCP is unavailable, continue with repository context and the base workflow when safe; state the missing evidence instead of blocking unnecessarily.
- Never fabricate Figma, browser, performance, accessibility, or provider evidence.

## Implementation and verification

For mutation work:

1. Keep edits scoped to the chosen mode and affected journey.
2. Preserve existing behavior unless the UI requirement explicitly changes it.
3. Run the project's relevant tests/lint/type checks.
4. When the page can run, inspect rendered representative states and responsive behavior. Browser evidence is stronger than source-only claims.
5. Check keyboard/focus, overflow, console/runtime errors, loading/empty/error states and accessibility signals relevant to the change.
6. Iterate only on observed issues. Default maximum automatic visual-polish budget: **3 render/inspect/fix cycles**; surface unresolved taste trade-offs instead of tuning indefinitely.

Later capability phases may provide dedicated browser and quality specialists. Their absence does not waive obvious manual/static verification; it only limits what evidence can be claimed.

## Human boundary

Do not auto-merge subjective visual changes. For high-impact design choices, show the chosen direction, material alternatives/trade-offs, and remaining uncertainty so a human can own the product judgment.

## Completion output

Report concisely:

- mode selected and why;
- existing components/dependencies/design constraints reused;
- material UI/interaction changes;
- rendered/test/quality evidence actually obtained;
- degraded or unavailable checks;
- remaining subjective decisions or risks.
