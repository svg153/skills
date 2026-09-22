# Prompt recipes

The capability should work from a short natural request. These examples are for users who want more control or want to learn the design reasoning without manually orchestrating specialist skills.

## Start from a functional but ugly app

```text
This application works, but the frontend looks generic and inconsistent.
Use design-engineering to give it a coherent product-quality visual direction.
Keep existing behavior and reuse accessible components where they are sound.
Establish the design foundation on one representative screen first, render it at relevant breakpoints, then propagate the selected system.
Explain the main design decisions so I can learn from them.
```

Expected route: Foundation.

## New product with almost no visual system

```text
Design the frontend foundation for this product from the current working implementation.
First understand the primary user and task, then propose the most suitable visual direction.
Do not default to generic AI SaaS styling or library defaults.
Define a small coherent system for color, typography, spacing, radii/depth, icons, responsive behavior and interaction feedback.
Prove it on the main product surface before scaling it.
```

Expected route: Foundation, optionally handing off to Prototype if materially different directions are plausible.

## Improve an already coherent interface

```text
Polish this interface without changing its visual identity.
Reuse the existing design system and components.
Focus on hierarchy, spacing, responsive behavior, component states and small interaction details.
Render the changed states and only fix issues you can actually observe.
```

Expected route: Polish.

## Explore alternative directions before committing

```text
This onboarding flow is important and I am not convinced by the current direction.
Prototype 2 or 3 genuinely different approaches that vary in hierarchy, density, composition or interaction model, not just colors.
Keep them isolated from production code until one direction is selected.
For each option, explain the trade-off and what kind of product experience it creates.
```

Expected route: Prototype.

## Audit before touching code

```text
Audit this dashboard UI before changing anything.
Use the rendered product and its actual design evidence.
Separate observed defects, source evidence, hypotheses and subjective taste suggestions.
Prioritize the few changes with the highest user impact and confidence.
```

Expected route: Audit.

## Learn while improving

```text
Improve this screen, but treat this as a learning exercise for me too.
Do the implementation rather than only giving design theory.
At the end, explain the five most important decisions you made around hierarchy, color, typography, spacing/density, components or motion and why they fit this product.
```

Expected behavior: normal selected mode plus Learning mode output.

## Use a public product as inspiration without copying it

```text
I like the quality and visual discipline of <reference URL/product>, but I do not want a clone.
Analyze the transferable principles that fit this product, such as hierarchy, density, typography, surface treatment and interaction rhythm.
Preserve our product identity and content structure.
Do not copy brand assets, proprietary content or distinctive trade dress.
Use the reference only to inform a coherent direction, then verify the result in our own application.
```

Expected route: Foundation or Prototype depending on design maturity and uncertainty.

## Dashboard or internal tool

```text
Make this dashboard feel like a serious product rather than a collection of cards.
Prioritize information hierarchy, scanability, density, table/form quality and clear action hierarchy.
Do not import spacious marketing-page patterns into a high-frequency workflow.
Reuse the current data behavior and accessible primitives.
```

Expected route: Foundation for weak systems, Polish for coherent ones.

## Landing page

```text
Improve this landing page so it feels intentional and production-ready.
First clarify the single primary conversion goal and content hierarchy.
Create a coherent visual system rather than decorating every section independently.
Use motion only where it supports narrative or interaction, and verify mobile as carefully as desktop.
```

Expected route: Foundation, Polish or Prototype based on current maturity.

## Mobile-first product pass

```text
Improve this product for real phone use first.
Check safe areas, touch targets, keyboard/input behavior, navigation, overflow, density and interaction feedback before desktop polish.
Preserve the product's design language unless the current foundation is weak enough to require Foundation mode.
```

Expected route: Polish or Foundation with mobile-first verification.

## Short prompts that should still work

The orchestrator should not require the long recipes above. These are intentionally valid requests:

```text
Make this app look like a real product.
```

```text
This frontend looks amateur. Fix the design without breaking behavior.
```

```text
Give this app a coherent design system and improve the main screen.
```

```text
Polish this UI and explain what you changed so I can learn.
```

The agent is responsible for recon, mode selection, reuse, rendered verification and specialist routing.

## What not to ask for manually

Normally avoid prompts such as:

```text
Run better-ui, then animate, then accessibility, then Playwright, then update DESIGN.md.
```

That makes the user responsible for orchestration and can apply specialists in the wrong order. Ask for the product outcome instead and let `design-engineering` choose the smallest useful sequence.

## Packaging note

Portable Agent Plugins 1.0 standardizes skills and MCP server configuration. It does not define a cross-client first-class prompt or slash-command component. These recipes therefore live as a reference inside the portable `design-engineering` skill and ship with it.

Client-specific commands or automation templates may be added under a client's extension namespace when they materially improve usability, but the canonical workflow and examples should remain portable here rather than depending on one host.
