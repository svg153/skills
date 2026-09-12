# Design Engineering Agent Plugin

Portable capability package for improving existing application interfaces with minimal ceremony.

## Scope

The package starts with one canonical local skill, `design-engineering`, which owns broad orchestration. Later GSD phases add focused external specialist skills for prototyping, library selection, motion and web-quality auditing without duplicating their behavior in the local orchestrator.

The base capability intentionally has **no mandatory MCP**. Optional integrations such as Figma or browser tooling are introduced only when they provide measurable value and must degrade safely when unavailable.

## Intended workflow

```text
inspect existing app
  -> reuse existing components/dependencies
  -> choose polish / prototype / audit
  -> implement scoped changes
  -> render and verify responsive behavior
  -> accessibility/performance/quality checks
  -> report evidence and trade-offs for human review
```

## Canonical sources

- `distribution.config.json` — capability package metadata.
- `skills/design-engineering/SKILL.md` — canonical portable orchestration behavior.
- `plugin.json` — generated Agent Plugins 1.0 manifest; do not edit independently.

External skills and MCP composition are governed by the repository's APM/Renovate and capability publishing contracts rather than copied ad hoc.

## Roadmap

Tracked by `svg153/skills#56` and the GSD workspace under `.planning/`.
