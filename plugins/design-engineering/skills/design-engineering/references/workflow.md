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

When the app can run, collect representative current-state evidence before a material redesign. At minimum inspect the target state at a normal desktop or mobile viewport; later browser specialists may expand the required matrix.

If the app cannot run, distinguish that limitation from a successful runtime check.

## 3. Reuse gate

Before creating a component or adding a library, ask:

1. Does the repository already contain the needed primitive/pattern?
2. Does an installed dependency already solve it idiomatically?
3. Is there a credible maintained external primitive/library that fits the stack and project constraints?
4. Is a small local implementation actually simpler and safer?

Prefer extension/composition over near-duplicate components. Do not replace an established library simply to satisfy personal taste.

A new dependency needs a concrete reason: capability gap, accessibility/interaction complexity, maintenance advantage, or meaningful reduction in custom code. Novelty alone is not a reason.

## 4. Select the mode

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

Exit: target state is rendered/checked when possible, regressions are addressed, and remaining choices are minor or stated.

### Prototype

Use when all/most are true:

- the surface is important to onboarding/conversion/core workflow;
- visual/interaction direction is genuinely uncertain;
- alternatives imply different hierarchy/layout/density/personality/interaction models, not just colors;
- choosing a direction before integrating would reduce rework.

Create isolated concepts rather than branching production implementation repeatedly. Aim for 2-3 **meaningfully divergent** directions such as quiet vs editorial vs dense/productive; never manufacture variants just to satisfy a count.

Each direction should state its axis of difference and trade-off. Reuse the real design system/components where that does not prevent exploration.

Human boundary: if the alternatives materially change product character or workflow, stop at a reviewable comparison and obtain/record the selected direction before production integration. If the user explicitly delegated that choice and evidence strongly favors one, select it but report the discarded alternatives and rationale.

Exit: one direction is selected; unselected prototype artifacts are removed/kept outside production unless the project explicitly wants a design lab.

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

Prioritize by user impact and confidence, not by how easy a CSS edit is.

Exit: findings are actionable, evidence-labelled, prioritized, and either fixed under existing authorization or handed back for selection.

## 5. Specialist routing

Use specialists opportunistically; never require the user to manually orchestrate them.

| Need | Preferred specialist when installed | Base fallback |
|---|---|---|
| Divergent UI directions | `prototype` | Produce a small isolated comparison using project conventions |
| Existing/new UI library decision | `pick-ui-library` / reuse discovery | Inspect package manifest and established primitives manually |
| Motion implementation | `animate` | Prefer simple CSS/platform behavior; avoid unnecessary motion |
| Motion critique | `review-animations` | Check purpose, interruption, reduced motion, duration and layout/perf risk |
| Web quality | `web-quality-audit` | Relevant project tests/static checks + explicit evidence limits |
| Browser interaction/rendering | browser/Playwright capability | Existing e2e tools/manual run if available; otherwise state runtime evidence unavailable |
| Structured design source | optional Figma MCP | Repository `DESIGN.md`, tokens, components and rendered baseline |
| Component discovery | optional component/OSS discovery | Existing repo/dependencies first, then normal maintained OSS research |

A missing specialist is not permission to fabricate its evidence or silently skip a critical check.

## 6. Implement with minimum necessary change

During mutation:

- preserve component APIs/behavior unless change is intentional;
- prefer token/theme/component-level fixes when several affected surfaces share the same cause;
- avoid global restyling for a local request;
- avoid introducing design-system abstractions before repeated need exists;
- keep accessibility semantics/native controls intact or improve them;
- keep content density appropriate to the product rather than defaulting every interface to spacious marketing UI;
- use motion only when it communicates state/spatial relationship/feedback or adds deliberate delight at a frequency that tolerates it.

## 7. Render/inspect/fix loop

When runnable, the loop is:

```text
baseline -> implement -> render -> inspect -> fix observed issue -> render again
```

Default automatic iteration budget: **3 cycles** after the first implementation. Stop earlier when acceptance criteria are met. Exceed the budget only for a concrete functional/accessibility defect, not subjective micro-tuning.

Until the dedicated browser phase supplies the full matrix, use the best representative states/viewports available in the project. Never claim a viewport/state was checked unless it actually was.

Inspect relevant:

- layout overflow/clipping and responsive hierarchy;
- navigation and primary interaction path;
- keyboard/focus for changed controls;
- loading/empty/error/populated state coherence;
- console/runtime failures;
- text wrapping/content extremes where likely;
- accessible names/semantics/contrast signals available to the current tooling;
- unintended behavior changes.

## 8. Quality handoff

Run project-native lint/type/test/e2e checks relevant to changed files. When installed, route through the dedicated web-quality specialist for evidence-led accessibility/performance/SEO/best-practice review.

A visually attractive result is not complete if the change creates a material accessibility, interaction, runtime, or performance regression.

Do not make SEO/performance claims from source inspection alone when runtime evidence is required to substantiate them.

## 9. Degraded operation

Optional services are enhancements, not prerequisites.

- No Figma: use repository design docs/tokens/components/rendered UI.
- No specialist skill: execute the narrow fallback and disclose the limitation.
- No browser runtime: do source/test validation, explain why rendered verification was unavailable, and do not label it visually verified.
- No external network/component discovery: reuse local components/dependencies and avoid speculative package recommendations.
- Authentication/provider failure: do not move credentials into manifests or code to work around it.

If missing evidence makes the requested change unsafe to judge (for example a major visual redesign cannot be rendered at all), leave a reviewable partial result rather than asserting completion.

## 10. Completion contract

Before declaring implementation complete, confirm as applicable:

- [ ] requested user outcome is satisfied;
- [ ] recon/design constraints were read and preserved or intentionally changed;
- [ ] existing components/dependencies were checked before new primitives;
- [ ] chosen mode matched scope/uncertainty;
- [ ] relevant project checks passed;
- [ ] rendered evidence was obtained when the app could run, or its absence is explicit;
- [ ] changed interactions/states/responsive behavior were inspected at an evidence level supported by current tooling;
- [ ] critical accessibility/runtime/quality regressions are not knowingly left behind;
- [ ] automatic iteration stayed bounded;
- [ ] subjective product/taste choices remain human-reviewable;
- [ ] final report distinguishes verified facts from remaining hypotheses/trade-offs.

## Examples

### Broad request

> Improve the onboarding screen; it feels generic and confusing.

Route: `design-engineering` -> recon. If hierarchy/content direction is clear, polish. If onboarding structure/personality is uncertain and high-impact, prototype distinct directions before integration.

### Small visual defect

> The mobile actions overflow the card and focus is clipped.

Route: `design-engineering` polish (or normal frontend fix if no design judgment is needed). No three-variant prototype.

### Audit-only

> Audit the dashboard UX and tell me what you would change.

Route: audit. Gather evidence and findings; no mutation by default.

### Mechanical frontend change

> Rename `UserCard` to `MemberCard` everywhere without changing UI.

Do not route here. This is a mechanical refactor.

### Backend-only

> Add a database index for the search query.

Do not route here.
