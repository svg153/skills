# DESIGN.md discovery and maintenance contract

Use this reference when `design-engineering` needs durable visual context for an application. `DESIGN.md` is **visual-system memory**, not a PRD, backlog, UX research repository, or substitute for source code.

This capability follows the current open `DESIGN.md` format from `google-labs-code/design.md`: optional YAML frontmatter contains machine-readable design tokens, while the Markdown body carries rationale and usage guidance. Tokens are normative when present; prose explains how to apply them.

## 1. Canonical format

Keep compatible `DESIGN.md` files within the canonical section order:

1. `## Overview`
2. `## Colors`
3. `## Typography`
4. `## Layout`
5. `## Elevation & Depth`
6. `## Shapes`
7. `## Components`
8. `## Do's and Don'ts`

Sections that have no evidence may be intentionally omitted instead of filled with invented rules. Do not add a custom top-level section merely because a concept needs documenting; place responsive rules under Layout, motion/interaction behavior under Components, accessibility constraints under Components or Do's and Don'ts, and evidence/provenance as subsections or inline annotations.

The frontmatter may describe real project tokens for:

- colors;
- typography;
- rounded/radius scales;
- spacing scales;
- component-level tokens supported by the format.

Use `{path.to.token}` references where appropriate. Preserve the project's incumbent token names and canonical CSS value format instead of translating everything to a preferred naming system.

## 2. Evidence precedence

Never treat a generated `DESIGN.md` as stronger evidence than the system it documents. Resolve conflicts in this order:

1. **Explicit current user/design decision** for the affected scope.
2. **Authoritative structured design source** explicitly adopted by the project, such as design tokens, theme files, component-library definitions, or an approved Figma/design-system source.
3. **App-local existing `DESIGN.md`** when it is current and consistent with implementation.
4. **Existing reusable components and rendered behavior** in the affected application.
5. **Repository/root `DESIGN.md`** when the app inherits it and no more-specific source overrides it.
6. **Adjacent established patterns** in the same product.
7. **Restrained inference**, labelled as inference and never represented as brand truth.

A lower-precedence source may reveal drift in a higher-precedence document. Report the conflict; do not silently choose whichever value is easier to implement.

### Normative vs descriptive evidence

- Machine-readable tokens copied from an authoritative project source are **normative** only to the extent that source is normative.
- Observed repeated component behavior is **descriptive evidence** until the project treats it as a rule.
- A value inferred from visual similarity is **inferred**, even if it looks obvious.
- A missing rule is **unknown**, not permission to invent a new design-system law.

When creating or refreshing the file, label inferred prose with wording such as `Inferred from current UI:` or `Provisional:`. Do not encode an inferred exact token in frontmatter unless the task explicitly establishes it as the new reviewed token.

## 3. Scope discovery

Resolve scope before reading or writing a design file.

### Single-application repository

Search from the application/project root upward to the repository root. Prefer the nearest relevant `DESIGN.md`. If only a root file exists, confirm that its guidance matches the target application before treating it as inherited context.

### Monorepo

Use nearest-app precedence:

```text
repo/
├── DESIGN.md                 # optional organization/product defaults
├── apps/
│   ├── customer-web/
│   │   └── DESIGN.md         # wins for customer-web
│   └── admin/
│       └── DESIGN.md         # wins for admin
└── packages/
    └── ui/                   # shared implementation evidence
```

An app-local design source wins over a generic root file for that app. Root guidance may supply defaults only where the app does not override them.

If several apps intentionally share one design system, keep one shared `DESIGN.md` only when that ownership is explicit. Do not duplicate it into every workspace just for discoverability.

### Component/package scope

A shared UI package may be stronger evidence for component primitives than an app-local prose file, while the app-local file may still own density, layout, product personality, and composition. Record that split rather than forcing a single global authority.

## 4. Discovery when DESIGN.md exists

Before using an existing file:

1. identify its scope;
2. inspect relevant token/theme/component sources;
3. compare its rules with the affected rendered UI when runnable;
4. note obvious conflicts or staleness;
5. use it as context only to the confidence supported by that evidence.

Do not rewrite `DESIGN.md` merely because a UI task touched CSS. Update it when the task establishes or changes a **durable reusable visual rule**, fixes documented drift, or explicitly asks to document the design system.

Examples that usually justify an update:

- primary token/theme values intentionally changed;
- a project-wide radius/spacing/type rule changes;
- a shared component family gains a reviewed durable interaction rule;
- responsive composition rules change across a class of screens;
- an existing design file is proven stale and the task includes documentation repair.

Examples that normally do **not** justify an update:

- one-off bug fix;
- route-specific content/layout exception;
- experimental prototype not yet selected;
- temporary campaign styling;
- a taste suggestion that has not been adopted;
- backend or mechanical refactor with no visual-system effect.

## 5. Creation when DESIGN.md is missing

Do not block ordinary UI improvement solely because no `DESIGN.md` exists. Use current project evidence and create/propose the file when doing so will preserve useful durable context.

### Scan mode — existing application

Use scan mode when code/design assets already exist.

Inspect, in order of usefulness:

- CSS custom properties and global styles;
- Tailwind/theme/token configuration;
- CSS-in-JS/theme modules;
- design-token JSON/DTCG sources;
- shared component primitives and their variants;
- typography/icon/font assets;
- Storybook/examples/tests that encode intended states;
- rendered/computed behavior when the application can run.

Synthesize intent rather than dumping every CSS value. Record only stable recurring choices. A frequently repeated magic number may reveal a pattern, but it remains inferred until the evidence supports treating it as a rule.

### Seed mode — pre-implementation

Use only when the project intentionally needs a new visual direction and there is little/no incumbent UI. Derive the seed from explicit product/brand context and reviewed choices. Keep provisional decisions labelled until implementation validates them.

Do not silently switch a brownfield application to seed mode simply because its current design is inconsistent.

## 6. What belongs in each canonical section

### Overview

Capture visual personality, density, design philosophy, target experience, scope, and a short list of evidence sources. Avoid business requirements, roadmap items, personas, architecture, or feature acceptance criteria unless they directly constrain visual behavior.

Recommended evidence note:

```markdown
### Evidence
- Normative: `src/theme/tokens.css`, shared `Button`/`Input` primitives.
- Observed: dashboard/list surfaces reviewed 2026-09-12.
- Inferred: compact density appears intentional for operator workflows.
```

### Colors

Record functional roles and exact values only when supported by tokens/theme/source. Preserve color format if the project treats `oklch()`, `hsl()`, CSS variables, etc. as canonical. Include interaction/state/contrast rules when durable.

### Typography

Record real font stacks, role hierarchy, scale, weights, line-height/letter-spacing and usage constraints. Do not create a new type scale just to make the document complete.

### Layout

Place spacing rhythm, containers, grids, density, responsive breakpoints/behavior and content-width rules here. Distinguish exact token/breakpoint evidence from qualitative observations.

### Elevation & Depth

Describe shadows, tonal layering, borders/backdrops, overlays and z/elevation philosophy. Flat design is a valid explicit rule; do not invent shadows.

### Shapes

Record radii, border/form language, clipping and recurring geometry. Frontmatter `rounded` values should reflect actual project tokens.

### Components

Describe durable visual/interaction behavior of shared primitives: buttons, inputs, cards, dialogs, nav, tables, tooltips, etc. Include motion/feedback rules where they belong to a component or interaction family. Accessibility-critical behavior belongs here when component-specific.

### Do's and Don'ts

Keep a short set of high-signal rules. Include cross-cutting accessibility constraints, visual anti-patterns actually rejected by the project, and hard boundaries that prevent design drift. Avoid generic web-design advice that is not project-specific.

## 7. Reviewable update protocol

Treat `DESIGN.md` changes as normal source changes:

1. identify the evidence that changed;
2. make the smallest durable documentation/token update;
3. keep exact values synchronized with their authoritative source rather than creating a forked token system;
4. show conflicts instead of silently overwriting stronger sources;
5. include the file in review alongside the implementation that establishes the new rule;
6. when practical, lint the resulting file with the current official `@google/design.md` CLI.

If a task discovers stale documentation but is not authorized to change it, report the drift and proposed correction rather than silently relying on the stale value.

## 8. Optional Figma / external design sources

Figma is optional and later capability work may provide structured access. When available, it can be strong evidence, but it does not automatically outrank a code-owned token system. Determine which source the project explicitly treats as authoritative.

If Figma and code disagree:

- identify the conflicting token/component/rule;
- identify declared ownership if available;
- avoid synchronizing either direction automatically unless the task authorizes it;
- continue with unaffected evidence where safe.

No Figma connection is required to use, create, or maintain `DESIGN.md`.

## 9. Portability rules

- Prefer the official canonical headings/order over a repo-specific schema.
- Keep frontmatter valid YAML and token values representable by the current format.
- Keep the document concise enough to load as working context; link to deeper sources instead of copying them.
- Never put secrets, provider credentials, private design URLs containing tokens, or generated authentication evidence in the file.
- Do not copy a product PRD into `DESIGN.md`.
- Do not represent inferred values as confirmed tokens.
- Do not make the document the only place a code-required token exists.

Use `references/DESIGN.md.template` as the starting structure, deleting irrelevant sections instead of filling them with fiction.