# Foundation mode

Use Foundation when the product works but does not yet have a coherent visual language, when the current UI is mostly framework defaults or one-off styling, or when the user explicitly asks for a new visual direction.

The goal is not to decorate every screen. The goal is to establish a small, durable design system, prove it on one representative surface, and then scale it without visual drift.

## Entry gate

Choose Foundation when one or more of these are true:

- there is no credible `DESIGN.md`, token system, or stable visual direction;
- adjacent screens use conflicting typography, spacing, color, radius, iconography, or component treatments;
- most of the UI is unstyled or library-default output and the user wants a product-quality result;
- the user explicitly asks to establish branding, visual direction, or a coherent interface system;
- preserving the current UI would preserve accidental or visibly poor decisions.

Do not use Foundation for a small local defect when the product already has a coherent system. Use Polish instead.

Do not treat inconsistency alone as permission to redesign a mature product. If there is evidence of a real design system that has merely drifted, repair toward that system rather than inventing a new one.

## 1. Establish product constraints

Before choosing aesthetics, capture the few constraints that shape the design:

- primary user and primary task;
- product archetype: dashboard, workflow tool, consumer app, content product, landing page, internal admin, etc.;
- information density and usage frequency;
- existing brand assets or colors that must survive;
- accessibility or platform constraints;
- target viewports and input methods;
- technical stack and incumbent component primitives;
- examples the user explicitly likes or dislikes, if provided.

Do not block on a long design interview. Ask only when an unanswered choice would materially change the product direction. Otherwise make a provisional recommendation and explain it.

## 2. Diagnose what can be reused

Separate **behavioral primitives** from **visual identity**.

Reuse accessible buttons, dialogs, menus, form controls, tables and layout primitives when they already work. Their interaction behavior is valuable even if their current styling is weak.

Do not let a component library's default theme silently define the product. A project may keep shadcn, Base UI, Radix, React Aria or another primitive system while establishing its own visual treatment through tokens and variants.

Classify current design evidence:

| Area | Keep | Adapt | Replace |
| --- | --- | --- | --- |
| component behavior | accessible, tested interaction | usable but inconsistent variants | bespoke broken behavior when a maintained primitive is safer |
| typography | coherent roles and readable scale | decent family but weak hierarchy | arbitrary sizes/weights with no hierarchy |
| color | intentional semantic roles | useful brand color but incomplete system | arbitrary per-component colors |
| spacing/layout | recurring rhythm and containers | mostly coherent with local drift | one-off values with no rhythm |
| shape/depth | intentional radius/elevation language | inconsistent values around a useful direction | random card/border/shadow treatment |
| iconography | one coherent library/style | mixed sizing but same family | mixed unrelated styles or decorative emoji-as-icons |

## 3. Choose a visual direction before coding broadly

Define one recommended direction in plain language. The direction must be specific enough to constrain implementation.

Cover:

- **personality**: restrained, editorial, technical, warm, premium, playful, utilitarian, etc.;
- **density**: compact, balanced, or spacious, tied to the product's usage;
- **hierarchy**: what receives the strongest visual weight and what stays quiet;
- **color strategy**: neutral surface system, accent role, semantic states and dark-mode intent if relevant;
- **typography**: family, display/body roles, weight contrast and readable scale;
- **spacing**: base rhythm, container width and grouping strategy;
- **shape/depth**: radius family, border vs shadow strategy and overlay treatment;
- **iconography**: one family, consistent stroke/fill treatment and sizing;
- **motion**: whether motion is mostly absent, functional, or deliberately expressive;
- **responsive behavior**: what compresses, stacks, hides, scrolls or changes interaction model.

A visual direction is not a mood-board adjective list. Each statement must change an implementation choice.

### When to prototype alternatives

If the user has no preference and the product could plausibly support materially different identities, hand off to Prototype for 2-3 divergent directions. Divergence should affect composition, hierarchy, density, typography or interaction model, not merely swap colors.

If uncertainty is low, recommend one direction and continue. Do not manufacture alternatives as ceremony.

## 4. Establish the minimum design foundation

Create or update durable design context only after the direction is selected. Use `references/design-md.md` and `references/DESIGN.md.template`.

At minimum, Foundation should resolve these areas when they are relevant:

1. semantic color roles;
2. typography roles;
3. spacing/density rules;
4. radii and elevation/border strategy;
5. component-state treatment for common controls;
6. iconography rules;
7. responsive composition rules;
8. motion/feedback rules;
9. explicit anti-patterns that would cause visible drift.

Prefer a small coherent scale over many arbitrary tokens. Do not create a full enterprise design system before the product proves it needs one.

## 5. Build one golden surface first

Do not restyle the whole application in one pass.

Select one representative surface that exercises the foundation:

- navigation/shell;
- primary heading and secondary text;
- a main content container;
- at least one primary and secondary action;
- common data/content presentation;
- one form or interactive control when relevant;
- loading/empty/error state when relevant.

Implement that surface using the selected direction and existing behavioral primitives. Render it at the relevant viewport classes and inspect it before propagating the system.

The golden surface is the calibration point. Fix visual hierarchy, spacing rhythm, density, contrast, component treatment and responsive behavior here before copying patterns elsewhere.

## 6. Anti-slop review

AI-generated interfaces often fail through accumulation of plausible local choices that do not form a coherent whole. Review the golden surface for these failure modes:

- every section placed in a rounded card even when grouping can be expressed with spacing;
- arbitrary gradients, glow, glass or blur used to manufacture visual interest;
- one accent color used everywhere rather than reserved for actions/meaning;
- multiple unrelated radius, shadow or border treatments;
- weak type hierarchy where every label, heading and body line has similar weight;
- excessive centered content in task-oriented product UI;
- huge empty spacing copied from marketing pages into dense workflows;
- generic hero/dashboard compositions that ignore the actual product task;
- inconsistent icon families, sizes or stroke weights;
- buttons that differ only by random color rather than hierarchy/state;
- library defaults visible as the final product identity;
- hover animation without a corresponding keyboard/focus treatment;
- decorative motion repeated on routine high-frequency interactions;
- beautiful populated screens with neglected empty, loading, error or destructive states.

These are diagnostic signals, not universal bans. Keep a treatment when product context and evidence justify it.

## 7. Propagate through owners, not screenshots

After the golden surface passes review:

1. move durable values into the project's real token/theme owners;
2. update shared component variants before editing repeated consumers one by one;
3. apply layout rules through reusable compositions where repeated need exists;
4. migrate additional surfaces in coherent slices;
5. preserve deliberate product-specific exceptions.

Do not turn every visual detail into an abstraction. Abstract only repeated, stable decisions.

## 8. Verify the result

Use `references/browser-loop.md` for rendered evidence. Foundation work should verify at least:

- the golden surface at affected mobile/tablet/desktop classes;
- hierarchy and content readability;
- horizontal overflow and wrapping;
- focus visibility and keyboard reachability for changed controls;
- loading/empty/error states relevant to the surface;
- contrast/accessibility signals available to the current toolchain;
- console/runtime health;
- before/after evidence for a material redesign.

Then run project-native lint/type/test checks and any installed quality specialists.

## 9. Learning output

When the user wants to improve their own design judgment, add a compact decision log:

```markdown
## Why this direction works
- Hierarchy: <decision and product reason>
- Color: <decision and role of accent/neutral/semantic colors>
- Typography: <decision and hierarchy reason>
- Spacing/density: <decision and workflow reason>
- Components: <what was reused and what was visually adapted>
- Motion: <what moves, what intentionally does not, and why>
```

Prefer five useful explanations over narrating every CSS edit.

## Exit criteria

Foundation is complete when:

- one coherent visual direction has been selected;
- the golden surface demonstrates it in real rendered states;
- durable tokens/rules live in the appropriate project owners and design context;
- reused component behavior remains accessible and functional;
- obvious anti-slop patterns have been reviewed rather than blindly applied;
- representative browser evidence and project checks pass or limitations are explicit;
- remaining subjective choices are reviewable by a human.
