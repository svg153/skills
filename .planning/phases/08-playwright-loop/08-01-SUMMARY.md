---
phase: 08-playwright-loop
plan: "01"
status: complete
completed: 2026-09-12
requirements: ["BROW-01"]
---

# Phase 08 Summary — Playwright Visual Loop

## Result

Made rendered browser evidence a normal completion requirement for UI-mutating design-engineering work while keeping browser transport portable, reuse-first and bounded.

## Implementation

- Added `references/browser-loop.md` with:
  - browser capability discovery and cheapest-capability-that-works routing;
  - project-native Playwright/Cypress/e2e tooling precedence;
  - Playwright CLI-style portable fallback for coding agents;
  - optional MCP escalation only when persistent state/richer introspection adds value;
  - launch/auth/fixture safety rules;
  - representative default viewport classes `390×844`, `768×1024`, `1440×900`, overridden by stronger project evidence;
  - relevant-state selection for loading/empty/error/success/confirmation/auth/overlay/interaction states;
  - render/layout, interaction, keyboard/focus, console/runtime and available accessibility-signal checks;
  - before/after screenshot guidance and sensitive-data boundaries;
  - deterministic evidence-report statuses: `Verified`, `Blocked`, `Not checked`, `Not applicable`;
  - bounded repair loop: initial implementation/render plus up to 3 automatic fix→render cycles by default;
  - mode-specific polish/prototype/audit completion behavior;
  - explicit source-only degraded result when the application cannot render.
- Updated the orchestrator workflow so UI-mutating polish/prototype completion now delegates to the browser evidence contract when runnable.
- Updated README with the rendered verification UX and the no-mandatory-browser-MCP boundary.

## Current upstream/tooling decision

Execution re-checked the current Microsoft Playwright CLI. The upstream project explicitly positions CLI + skills as the best fit for coding agents because it avoids always loading large MCP schemas/page trees, while MCP remains useful for long-lived exploratory loops that benefit from persistent state/richer introspection.

Phase 8 therefore does not hardwire a browser MCP or add Playwright as a permanent project dependency.

## Runtime verification

Dedicated Actions run **34701474262** ✅ used official `@playwright/cli@0.1.19` against a real local HTTP fixture.

The run successfully:

- installed the official CLI;
- launched a local rendered application;
- opened it in a named Playwright CLI session;
- captured an accessibility/page snapshot;
- resized to `390×844`, `768×1024`, and `1440×900`;
- navigated by keyboard (`Tab`) and activated the target (`Enter`);
- verified the resulting state in a post-interaction snapshot;
- captured a screenshot;
- queried console output;
- closed the browser session;
- passed all documentation invariants.

Repository Capability Plugin Validation also passed during Phase 8 implementation changes.

The temporary runtime-validation workflow was removed before the final PR.

## Boundaries

- Existing project browser/e2e tooling wins over introducing another stack.
- Browser MCP is optional, not a base capability requirement.
- Screenshots never substitute for interaction/accessibility/performance evidence.
- Browser evidence is scoped to the changed flow/states, not a ceremonial screenshot crawl.
- Subjective micro-tuning does not justify unbounded cycles.
- A page that could not actually render is never reported as browser-verified.

## Requirement

`BROW-01` complete.
