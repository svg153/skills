# Design Engineering workflow reference

Load this reference only after the `design-engineering` skill has been selected. It defines orchestration; it does not replace project-specific design systems or specialist skills.

## 1. Establish the target

Capture the smallest useful target before editing:

- requested outcome and affected user journey;
- route/screen/component scope;
- whether the user asked for implementation, alternatives, or analysis only;
- important states: first-use, loading, empty, error, populated, success, destructive/confirmation, permission/auth, narrow/wide viewport;
- constraints already present in product docs, code, design docs, issue/PR context, or the user's request.

Do not invent business requirements to fill gaps. Preserve current behavior unless the requested outcome requires a behavior change.

## 2. Recon evidence

Inspect only what is relevant, but establish enough evidence to avoid a blank-slate redesign.

### Product/context

Prefer existing sources in this order when present:

1. explicit user request / issue acceptance criteria;
2. project product/architecture/design docs;
3. existing UI behavior and tests;
4. implementation patterns in adjacent screens;
5. inferred intent, clearly marked as inference.

### Implementation system

Identify:

- framework/runtime and styling approach;
- dependency manifest and installed UI/design libraries;
- component/primitives directories and reusable layouts;
- tokens/themes/CSS variables and typography/icon assets;
- data/state/loading/error patterns;
- routing and responsive conventions;
- tests/storybook/examples that demonstrate intended components.

### Rendered baseline

When the app can run, collect representative current-state evidence before a material redesign. Use the browser evidence protocol in `references/browser-loop.md` to decide the minimum useful baseline rather than collecting screenshots ceremonially.

If the app cannot run, distinguish that limitation from a successful runtime check.

## 3. Resolve durable design context

Before making visual-system decisions, discover the applicable `DESIGN.md` and its stronger underlying sources. Read `references/design-md.md` for the complete contract.

Use these rules:

1. Determine repository/app/workspace scope before choosing a design file.
2. Prefer the nearest applicable app-local `DESIGN.md` over generic root guidance.
3. Treat authoritative tokens/themes/components/approved structured design sources as stronger evidence than generated prose when they conflict.
4. Treat machine-readable `DESIGN.md` tokens as normative only when they reflect the project's real authoritative values.
5. Mark observed/inferred rules as such; unknowns stay unknown rather than becoming invented brand truth.
6. If `DESIGN.md` is missing, do not block normal work. Use project evidence and create/propose one only when durable design memory would materially help.
7. Do not update `DESIGN.md` for one-off CSS fixes, unselected prototypes, temporary campaign styling, or unrelated refactors.

When creating or refreshing it, start from `references/DESIGN.md.template`, keep the official canonical section order, and prefer deleting unsupported sections over filling them with fiction.

A more-specific app design source cannot be silently overridden by a root file. If two authoritative-looking sources disagree, surface the conflict and proceed only with unaffected evidence or the explicitly chosen authority.

## 4. Reuse gate

Before creating a component or adding a library, ask:

1. Does the repository already contain the needed primitive/pattern?
2. Does an installed dependency already solve it idiomatically?
3. Is there a credible maintained external primitive/library that fits the stack and project constraints?
4. Is a small local implementation actually simpler and safer?

Prefer extension/composition over near-duplicate components. Do not replace an established library simply to satisfy personal taste.

A new dependency needs a concrete reason: capability gap, accessibility/interaction complexity, maintenance advantage, or meaningful reduction in custom code. Novelty alone is not a reason.

## 5. Select the mode

Choose exactly one primary mode for a work item. A mode may hand off to specialists, but it stays responsible for completion.

### Polish

Use when:

- product direction and information architecture are already sound;
- the request is localized;
- uncertainty is low enough that multiple concepts would add ceremony rather than insight.

Typical work:

- hierarchy/spacing/typography cleanup;
- responsive fixes;
- state consistency;
- clearer affordances and feedback;
- small interaction/motion improvements;
- replacing an ad-hoc primitive with an existing project/library primitive.

Mutation: allowed when the user asked for implementation/improvement.

Exit: when runnable, the changed target passes the applicable rendered evidence matrix in `references/browser-loop.md`; source-only completion is allowed only when runtime evidence is genuinely unavailable and that limitation is explicit.

### Prototype

Use when all/most are true:

- the surface is important to onboarding/conversion/core workflow;
- visual/interaction direction is genuinely uncertain;
- alternatives imply different hierarchy/layout/density/personality/interaction models, not just colors;
- choosing a direction before integrating would reduce rework.

Create isolated concepts rather than branching production implementation repeatedly. Aim for 2-3 **meaningfully divergent** directions such as quiet vs editorial vs dense/productive; never manufacture variants just to satisfy a count.

Each direction should state its axis of difference and trade-off. Reuse the real design system/components where that does not prevent exploration.

Human boundary: if the alternatives materially change product character or workflow, stop at a reviewable comparison and obtain/record the selected direction before production integration. If the user explicitly delegated that choice and evidence strongly favors one, select it but report the discarded alternatives and rationale.

Exit: alternatives have enough equivalent rendered context to support selection. After one direction is selected and integrated, run the production browser evidence matrix on that result. Do not fully QA discarded prototypes as if each were shipping product.

### Audit

Use when:

- the user asked to review/critique/audit;
- symptoms are broad/unclear;
- a redesign would be premature without evidence;
- the requested output is findings rather than code.

Default mutation policy: read-only. If the same request explicitly authorizes fixes, findings can transition into scoped polish/prototype work without asking redundant permission.

Findings should separate:

- **observed runtime evidence** — seen in rendered behavior/trace/test;
- **source evidence** — concrete implementation issue visible in code;
- **hypothesis** — plausible issue needing runtime/user validation;
- **taste suggestion** — subjective option, not defect.

Prioritize by user impact and confidence, not by how easy a CSS edit is. When the app can run, use browser evidence for claims about rendered behavior instead of upgrading source hypotheses into observed defects.

Exit: findings are actionable, evidence-labelled, prioritized, and either fixed under existing authorization or handed back for selection.

## 6. Specialist routing

Use specialists opportunistically; never require the user to manually orchestrate them.

| Need | Preferred specialist when installed | Base fallback |
|---|---|---|
| Divergent UI directions | `prototype` | Produce a small isolated comparison using project conventions |
| Existing/new UI library decision | `pick-ui-library` / reuse discovery | Inspect package manifest and established primitives manually |
| Motion implementation | `animate` | Prefer simple CSS/platform behavior; avoid unnecessary motion |
| Motion critique | `review-animations` | Check purpose, interruption, reduced motion, duration and layout/perf risk |
| Web quality | `web-quality-audit` | Relevant project tests/static checks + explicit evidence limits |
| Browser interaction/rendering | existing project e2e/browser path; otherwise Playwright CLI-style tooling | Manual rendered preview if possible; otherwise explicit source-only limitation |
| Persistent browser session / rich exploratory introspection | optional browser MCP when already available/justified | Project tooling or Playwright CLI-style execution |
| Structured design source | optional Figma MCP | Scoped `DESIGN.md`, tokens, components and rendered baseline |
| Component discovery | optional component/OSS discovery | Existing repo/dependencies first, then normal maintained OSS research |

A missing specialist is not permission to fabricate its evidence or silently skip a critical check. MCP is not required for core browser verification.

## 7. Implement with minimum necessary change

During mutation:

- preserve component APIs/behavior unless change is intentional;
- prefer token/theme/component-level fixes when several affected surfaces share the same cause;
- avoid global restyling for a local request;
- avoid introducing design-system abstractions before repeated need exists;
- keep accessibility semantics/native controls intact or improve them;
- keep content density appropriate to the product rather than defaulting every interface to spacious marketing UI;
- use motion only when it communicates state/spatial relationship/feedback or adds deliberate delight at a frequency that tolerates it.

When implementation establishes a new durable cross-surface visual rule, update the applicable `DESIGN.md` in the same reviewable change. Do not make the document the only place a runtime-required token exists.

## 8. Rendered evidence and bounded fix loop

For UI-mutating work, read `references/browser-loop.md`. When the application can run, rendered browser evidence is part of completion, not an optional polish step.

Default evidence rules:

- use project-defined breakpoints when present; otherwise representative defaults are `390×844`, `768×1024`, and `1440×900` for the viewport classes materially affected;
- exercise the changed critical flow plus applicable loading/empty/error/confirmation/overlay states rather than screenshotting the whole application;
- inspect overflow/clipping, wrapping, changed interactions, keyboard/focus and relevant console/runtime evidence;
- screenshots are comparison evidence, not proof of semantics/accessibility/interaction;
- use before+after evidence for material visual changes and only the minimum useful visual artifacts for small defects;
- report each selected state/viewport as `Verified`, `Blocked`, `Not checked`, or `Not applicable` rather than using a generic “looks good”.

Normal loop:

```text
baseline -> implement -> render evidence matrix -> identify objective defect
         -> fix -> rerender affected evidence -> stop when criteria pass
```

The initial implementation/render is not a repair cycle. Default budget is **up to 3 automatic fix -> render cycles**. Stop earlier when the applicable evidence matrix passes. An additional cycle is justified only for a concrete functional/accessibility/runtime defect, not subjective micro-tuning.

Do not expand feature scope to improve screenshots. When remaining choices are taste/product trade-offs, stop and surface them for human/product judgment.

If the application cannot run, perform relevant source/test validation, state the concrete blocker, and report the result as **source-validated only**. Never claim browser verification for a page/state/viewport that was not actually rendered.

## 9. Quality handoff

Run project-native lint/type/test/e2e checks relevant to changed files. When installed, route through the dedicated web-quality specialist for evidence-led accessibility/performance/SEO/best-practice review.

A visually attractive result is not complete if the change creates a material accessibility, interaction, runtime, or performance regression.

Browser screenshots/evidence do not replace dedicated accessibility, Core Web Vitals/performance, SEO or project-native regression testing. Conversely, source inspection does not substitute for rendered evidence when the page can run.

Do not make SEO/performance claims from source inspection alone when runtime evidence is required to substantiate them.

When `DESIGN.md` changed, validate its structure with the current official DESIGN.md tooling when practical and review token/prose diffs as source changes rather than treating generated documentation as automatically correct.

## 10. Degraded operation

Optional services are enhancements, not prerequisites.

- No Figma: use scoped repository `DESIGN.md`, tokens/components and rendered UI.
- No `DESIGN.md`: use stronger project evidence and continue; create/propose one only when durable design memory is useful.
- Stale/conflicting `DESIGN.md`: report the conflict and prefer the applicable stronger source; do not silently overwrite either side.
- No specialist skill: execute the narrow fallback and disclose the limitation.
- No browser MCP: use project-native browser/e2e tooling or Playwright CLI-style execution; MCP absence is not a core blocker.
- No browser automation but rendered preview exists: record what was manually rendered and what interaction/console/accessibility evidence remains missing.
- No runnable browser/runtime: do source/test validation, explain why rendered verification was unavailable, mark affected evidence `Blocked`/`Not checked`, and do not label it visually verified.
- No external network/component discovery: reuse local components/dependencies and avoid speculative package recommendations.
- Authentication/provider failure: use existing authorized test state or mark the authenticated state blocked; do not move credentials into manifests/code to work around it.

If missing evidence makes the requested change unsafe to judge (for example a major visual redesign cannot be rendered at all), leave a reviewable partial result rather than asserting completion.

## 11. Completion contract

Before declaring implementation complete, confirm as applicable:

- [ ] requested user outcome is satisfied;
- [ ] target scope and applicable design-context scope were resolved;
- [ ] recon/design constraints were read and preserved or intentionally changed;
- [ ] existing `DESIGN.md`/tokens/components were reconciled by evidence precedence rather than assumed equal;
- [ ] inferred design rules remain labelled and unknowns were not invented as brand truth;
- [ ] existing components/dependencies were checked before new primitives;
- [ ] chosen mode matched scope/uncertainty;
- [ ] relevant project checks passed;
- [ ] browser tooling followed the lightest reliable project-supported path rather than adding unnecessary infrastructure;
- [ ] changed target actually rendered when the application could run, or the runtime blocker/source-only status is explicit;
- [ ] applicable viewport/state evidence matrix was recorded with explicit statuses;
- [ ] changed critical interaction flow was exercised where reachable;
- [ ] overflow/clipping/wrapping and keyboard/focus were checked at affected widths where applicable;
- [ ] relevant console/runtime evidence was inspected;
- [ ] screenshots were used as visual comparison evidence rather than sole accessibility/interaction proof;
- [ ] critical accessibility/runtime/quality regressions are not knowingly left behind;
- [ ] any `DESIGN.md` update represents a durable reviewed rule rather than task-local noise;
- [ ] automatic fix/render iteration stayed bounded;
- [ ] subjective product/taste choices remain human-reviewable;
- [ ] final report distinguishes verified facts from blocked/not-checked evidence, hypotheses and trade-offs.

## Examples

### Broad request

> Improve the onboarding screen; it feels generic and confusing.

Route: `design-engineering` -> recon -> resolve scoped design context. If hierarchy/content direction is clear, polish. If onboarding structure/personality is uncertain and high-impact, prototype distinct directions before integration. Render the selected/implemented result across the affected evidence matrix before completion.

### Monorepo app-local context

> Improve the admin dashboard tables.

If `apps/admin/DESIGN.md` exists, it wins over a generic repository `DESIGN.md` for admin-specific density/layout rules. Shared package tokens/components may still be stronger evidence for primitives. Browser verification uses the admin app's real launch/e2e path and relevant breakpoints rather than assuming repository-wide defaults.

### Brownfield project without DESIGN.md

> Polish this settings page.

Continue from existing tokens/components/rendered behavior. Do not block on documentation. If the work reveals stable reusable design rules worth preserving, propose/create a scoped `DESIGN.md` from evidence and label inferences. Browser verification still applies when the page can run.

### Responsive defect

> The mobile actions overflow the card and focus is clipped.

Route: polish. Verify the narrow viewport around the actual project breakpoint plus at least one unaffected larger representative width as needed. Check horizontal overflow, wrapping and keyboard focus. No three-variant prototype and normally no `DESIGN.md` update.

### Audit-only

> Audit the dashboard UX and tell me what you would change.

Route: audit. Gather browser evidence where runnable, distinguish observed rendered defects from source hypotheses/taste suggestions, and do not mutate by default.

### Mechanical frontend change

> Rename `UserCard` to `MemberCard` everywhere without changing UI.

Do not route here. This is a mechanical refactor and must not churn `DESIGN.md` or generate ceremonial screenshots.

### Backend-only

> Add a database index for the search query.

Do not route here.