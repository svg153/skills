---
name: design-engineering
description: "Improve, redesign, or audit an existing application interface with minimal ceremony while preserving product context, reusing existing components first, and verifying rendered behavior. Use for UI/UX improvement work that spans design judgment and implementation; optional specialist skills and MCPs may extend the workflow when available."
license: MIT
metadata:
  author: svg153
  version: "0.1"
---

# Design Engineering

Orchestrate interface improvement without assuming a blank-slate redesign or requiring optional integrations.

## Initial contract

This v0.1 capability boundary is intentionally minimal. Until the dedicated orchestration phase expands it:

1. Inspect the existing application, product context, stack, components, and design conventions before proposing changes.
2. Reuse existing project components and dependencies before adding new UI libraries or building bespoke primitives.
3. Keep changes scoped to the user's requested interface outcome; do not redesign unrelated surfaces.
4. Treat browser-rendered evidence, responsive behavior, accessibility, and existing tests as required verification inputs when those tools are available.
5. Optional design or browser integrations must degrade safely when unavailable; no MCP is mandatory for this base capability.
6. Do not auto-merge subjective visual changes. Report trade-offs and evidence for human review.

## Phase boundary

This skill establishes the canonical runtime identity for the `design-engineering` Agent Plugin. Later GSD phases add specialist upstream skills, `DESIGN.md` context, prototyping, browser verification, quality audits, optional MCP composition, and GitHub automation without moving this canonical path.
