# Browser verification and visual evidence contract

Use this reference for UI-changing `design-engineering` work when the application can be launched or a representative preview is available. The browser loop converts “looks good” into a bounded, reviewable evidence contract.

It does **not** mandate one browser transport. Reuse the lightest reliable project-supported path first; Playwright CLI-style execution is the preferred portable fallback for coding agents when the project does not already provide an equivalent browser workflow. A browser MCP is optional and should be used only when persistent state or richer interactive inspection materially helps.

## 1. Browser capability discovery

Choose the cheapest capability that can collect the required evidence.

### Preferred order

1. **Existing project browser/e2e tooling**
   - established Playwright tests/config;
   - Cypress or another maintained existing e2e harness;
   - Storybook interaction/browser tests where they represent the changed state;
   - project preview/dev-server scripts plus already-supported browser automation.
2. **Already-available lightweight agent/browser CLI**
   - prefer an approved Playwright CLI path when it can open, inspect and interact with the target without modifying project dependencies.
3. **Temporary approved Playwright CLI execution**
   - use when browser evidence is required, no suitable project path exists, and the environment allows running the official tool without making it a project dependency merely for one verification.
4. **Persistent browser/MCP tooling**
   - use when the task benefits from a durable session, repeated stateful interaction, richer page inspection, or a client already exposes it reliably.
5. **Manual/project-native preview evidence**
   - acceptable when automation is unavailable but an actual rendered view can still be inspected.

Do not silently add a heavy browser stack, new MCP server, project dependency, credential, or CI service when an existing supported path can do the job.

### Playwright CLI guidance

When Playwright CLI is the selected path:

- prefer the current approved `@playwright/cli`/`playwright-cli` interface rather than inventing a wrapper;
- use accessibility/page snapshots for deterministic target selection where practical;
- use explicit browser interactions (`click`, `fill`, keyboard actions, navigation) rather than judging screenshots alone;
- collect console evidence when runtime regressions are plausible;
- use screenshots for visual review, not as the only assertion surface;
- do not claim compatibility with a particular CLI version unless that version was actually executed or pinned by the project/workflow.

`playwright-cli install --skills` can expose the upstream agent skills in environments that intentionally adopt them; this capability does not require that installation and must degrade without it.

## 2. Launch and environment readiness

Before opening the page, discover how the target application is meant to run.

Inspect relevant project sources rather than guessing:

- package/workspace scripts;
- framework dev/preview commands;
- existing Playwright/Cypress config and `webServer` setup;
- documented ports/base URLs;
- fixture/test-account conventions;
- required environment variables that are already available to the authorized environment.

Rules:

- never invent production credentials, API keys or user accounts;
- do not copy secrets into screenshots, logs, fixtures or committed configuration;
- prefer local/dev/test fixtures and existing authenticated test state;
- distinguish “server started” from “target state rendered successfully”;
- if a required backend/provider is unavailable, record the blocked state instead of manufacturing representative data unless the project already uses a fixture/mock path for that purpose.

A source review is **not** browser verification. If the page cannot be launched, report `runtime evidence unavailable` with the concrete blocker.

## 3. Evidence matrix

Build a small matrix before verification. Verify the states that can reveal regressions from the requested change; do not exhaustively screenshot the whole product.

### Representative viewport defaults

Use project-defined breakpoints/device targets when they are stronger evidence. Otherwise start with:

| Class | Default viewport | Purpose |
|---|---:|---|
| Narrow/mobile | `390 x 844` | small-phone composition, wrapping, touch-sized controls |
| Medium/tablet | `768 x 1024` | breakpoint transitions, intermediate layout behavior |
| Wide/desktop | `1440 x 900` | full hierarchy, dense desktop composition, overlays |

These are **representative widths, not magic product breakpoints**. If `DESIGN.md`, CSS/container queries, test config, analytics requirements, or explicit acceptance criteria specify other widths, use those and record why.

For a genuinely local defect that cannot differ across breakpoints, one or two targeted viewports may be sufficient. For layout/responsive work, all relevant breakpoint classes are required.

### State defaults

Select only applicable states, prioritizing the changed user journey:

- default/populated;
- loading/skeleton;
- empty/no-results;
- validation/error/failure;
- success/confirmation;
- destructive confirmation;
- permission/authenticated/unauthorized state;
- open popover/menu/dialog/drawer;
- hover/focus/active/selected state when materially changed;
- long/localized/extreme content where wrapping/density risk exists.

If a state cannot be reached with the authorized environment, mark it `Blocked` or `Not applicable`; do not silently omit a state that acceptance criteria explicitly require.

## 4. Per-state verification checklist

For each selected viewport/state/flow, inspect the dimensions relevant to the change.

### Render/layout

- target actually renders rather than showing a fallback/runtime crash;
- no unexpected horizontal scroll, clipping, overlap or off-screen controls;
- hierarchy/composition changes at breakpoints are intentional;
- text wraps/truncates according to product conventions;
- overlays/dialogs/popovers stay in viewport and maintain usable stacking;
- loading/empty/error content does not collapse the layout unexpectedly.

### Interaction

- primary changed flow can be completed;
- changed buttons/links/forms/dialogs/menus behave as intended;
- state transitions preserve user feedback and do not double-trigger;
- destructive/confirmation behavior remains explicit where relevant;
- pointer-only interaction is not introduced for keyboard-reachable functionality.

### Keyboard/focus

For changed interactive UI:

- keyboard navigation reaches the control in a sensible order;
- focus is visible and not clipped/hidden;
- overlays/dialogs follow the project’s established focus behavior;
- keyboard activation/escape/close behavior remains usable when applicable.

This is focused browser evidence, not a full accessibility conformance audit. Dedicated accessibility checks may still be required.

### Runtime/console

Inspect browser console/runtime evidence when the changed path can plausibly introduce client errors:

- no new uncaught exception;
- no new relevant React/framework hydration/runtime error;
- no repeated error/warning caused by the new interaction;
- expected network/provider failures are distinguished from regressions introduced by the change.

Do not fail work merely because an unrelated pre-existing warning exists; label it separately when discovered.

### Accessibility signals available in the current tooling

Inspect relevant accessible names/roles/semantics and obvious contrast/focus signals when supported by the selected browser path. A screenshot does not prove semantics, keyboard support, accessible naming, contrast compliance, or screen-reader behavior.

## 5. Before/after visual evidence

Screenshots are comparison artifacts, not test truth.

### When to collect both

Prefer **before + after** for:

- material visual redesign;
- hierarchy/density/layout changes;
- responsive restructuring;
- a defect whose visual baseline is useful to demonstrate the fix;
- PRs where reviewers need a quick visual comparison.

An **after-only** screenshot may be enough for a small localized defect when the baseline is already unambiguous from issue evidence and the meaningful validation is interaction/layout rather than visual comparison.

Do not create screenshots for backend/mechanical/no-visual changes merely to satisfy a process ritual.

### Naming convention

When the project has no existing evidence convention, use an ephemeral structure such as:

```text
artifacts/design-evidence/<work-slug>/
├── before/
│   ├── mobile-default.png
│   └── desktop-default.png
└── after/
    ├── mobile-default.png
    └── desktop-default.png
```

Prefer project CI artifacts, PR attachments or temporary/worktree files. Do **not** commit binary screenshots to the product repository unless that repository intentionally tracks visual fixtures/golden images or the task explicitly requires it.

Never capture sensitive personal/account/payment data in shareable screenshots. Use approved fixtures/redaction when necessary.

## 6. Deterministic evidence report

Do not conclude with only “looks good”. Summarize what was actually rendered and exercised.

Example:

| Viewport | State / flow | Rendered | Interaction | Console | Focus / overflow | Evidence |
|---|---|---|---|---|---|---|
| 390×844 | checkout default | Verified | purchase CTA path verified | No new errors | focus visible; no horizontal scroll | `after/mobile-default.png` |
| 768×1024 | checkout validation error | Verified | submit -> error verified | No new errors | error focus checked | no screenshot needed |
| 1440×900 | checkout default | Blocked | Not checked | Not checked | Not checked | auth fixture unavailable |

Use explicit statuses such as `Verified`, `Blocked`, `Not checked`, and `Not applicable`. A missing row should not masquerade as successful verification.

## 7. Bounded render/fix loop

Normal loop:

```text
baseline -> implement -> render matrix -> identify objective defect
         -> fix -> rerender affected evidence -> stop when criteria pass
```

Budget:

- initial implementation/render is not counted as a repair cycle;
- default maximum: **3 automatic fix -> render cycles**;
- stop earlier when the applicable matrix passes;
- one additional cycle is justified only for a concrete functional/accessibility/runtime defect introduced or exposed by the change, not for endless subjective micro-tuning;
- never expand product scope merely to improve a screenshot.

Objective defects include overflow, broken interaction, inaccessible focus, unreadable state, console/runtime failure, incorrect responsive composition, or a clear acceptance-criteria miss.

Subjective choices such as “slightly warmer gray”, “more premium”, or two equally credible spacing/density directions should be surfaced as trade-offs for human/product judgment rather than repeatedly tuned until the agent prefers one.

Prototype mode must not silently turn variant selection into an endless polish tournament. Once the evidence is sufficient to compare alternatives, return the decision to the authorized selector.

## 8. Completion rules by orchestration mode

### Polish

When the app can run, completion requires browser evidence for the changed state/flow and every viewport class materially affected. A localized non-responsive change may use a narrower matrix with rationale.

### Prototype

Each reviewable direction should be rendered in enough identical context to compare the intended axis of difference. Do not fully QA every discarded prototype as if it were production. After one direction is selected and integrated, run the production completion matrix on that result.

### Audit

Remain read-only unless fixes are authorized. Browser evidence strengthens findings and should distinguish:

- observed rendered defect;
- source-only finding;
- hypothesis requiring additional runtime/user evidence;
- subjective taste suggestion.

Audit screenshots should illustrate material findings, not create a screenshot inventory of the application.

## 9. Degraded operation

### Existing browser path unavailable

Try the next approved lighter path. Do not change project architecture merely to satisfy this capability.

### Application cannot launch

Run relevant source/lint/type/unit validation, report the launch blocker, and state explicitly:

> Runtime/browser verification unavailable; this result is source-validated only.

Do not mark BROW evidence as verified.

### Authentication unavailable

Use an existing authorized test/session/fixture path. If none exists, verify unaffected public states and mark the authenticated state blocked. Do not introduce credential workarounds.

### Browser automation unavailable but manual rendered preview exists

Record what was manually rendered/checked and what interaction/console/a11y evidence remains missing. Manual screenshot inspection is still weaker than a real interaction/browser automation path.

### Persistent MCP unavailable

Continue with project-native tooling or Playwright CLI-style execution. MCP absence is not a blocker for the core design workflow.

## 10. Handoff to quality specialists

Browser evidence answers “what rendered and behaved in this execution?”. It does not replace:

- project tests;
- accessibility audit tooling;
- performance/Core Web Vitals evidence;
- SEO/best-practice auditing;
- visual-regression baselines already owned by the project.

Forward observed runtime evidence to those checks. Do not convert source hypotheses into measured performance/accessibility claims.

## 11. Completion checklist

Before calling UI-mutating work browser-verified, confirm as applicable:

- [ ] application/preview actually rendered the changed target;
- [ ] selected viewport matrix follows project evidence or the documented defaults;
- [ ] relevant loading/empty/error/interaction states were exercised or explicitly marked blocked/not applicable;
- [ ] critical changed user flow works;
- [ ] overflow/clipping/text wrapping was checked at affected widths;
- [ ] keyboard/focus was checked for changed interactive controls;
- [ ] relevant console/runtime evidence was inspected;
- [ ] screenshots are comparison evidence, not the sole accessibility/interaction assertion;
- [ ] before/after evidence was captured when useful and contains no sensitive data;
- [ ] automatic fix/render iteration stayed within the default bounded budget;
- [ ] unresolved subjective trade-offs are surfaced rather than endlessly tuned;
- [ ] final report states exactly what was Verified, Blocked, Not checked or Not applicable.
