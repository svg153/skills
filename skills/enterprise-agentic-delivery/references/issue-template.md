# Enterprise GSD issue template

```md
## Objective

What capability or corrective change is being delivered?

## Context

Why now? What current code, roadmap item, incident, or dependency motivates it?

## Scope

- Exact files, boundaries, behavior, and data affected.

## Non-goals

- Explicitly deferred behavior and adjacent issues.

## Dependencies

- Parent roadmap and prerequisite issues.
- External systems or evidence required.

## Acceptance criteria

- [ ] Observable behavior or artifact exists.
- [ ] Security and failure behavior are covered.
- [ ] Tests/build/checks pass.

## Risk and rollback

What can fail, and how is the change reverted or disabled?

## Decision record — CODEX

**Question:** What choice required judgment?

**Options:**

1. ...
2. ...

**Decision:** ...
**Reason:** ...

## Verification

Commands and evidence expected before close.
```

For a completed issue, append a second decision record with the merged PR, commit, final scope, and any CI exception.
