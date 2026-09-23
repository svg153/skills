# Enterprise pull request template

```md
## Summary

What this PR delivers and which issue it closes.

## Scope

- Included behavior.
- Explicitly excluded behavior.

## Implementation

- Commit-by-commit review map.
- Important trust, data, or compatibility boundaries.

## Verification

- `command` — result
- `command` — result

## Risk and rollback

Operational risk, migration concerns, feature flag, or revert plan.

## Decision record — CODEX

**Question:** ...
**Options:** ...
**Decision:** ...

## External CI notes

Only include this section when a check is unavailable or fails for a proven external reason. Include exact check name, repeated evidence, and why local validation is sufficient.
```

Keep commits ordered as a readable history: contract, implementation, tests, integration, and documentation only when those are genuinely separate review steps.
