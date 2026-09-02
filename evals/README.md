# Behavioral evaluations

This directory contains **catalog-owned** Waza suites. Runtime skill files remain under
`skills/`; behavioral evidence lives here so it can evolve independently from distribution
packaging and, critically, from upstream synchronization.

Each covered skill uses:

```text
evals/<catalog-name>/
├── eval.yaml
└── tasks/
    └── *.yaml
```

A suite must contain at least one positive trigger and one negative/boundary case. Positive
cases also need a behavioral grader so trigger accuracy is never mistaken for task quality.

For `sync.strategy: download` + `authoritative: upstream` entries, keep these evals here rather
than adding local Waza files to the mirrored `skills/<name>/` payload. That prevents the next
upstream sync from deleting the tests and avoids implying that the upstream author maintains
catalog-specific evals.

See `docs/evals.md` for CI, trusted execution, results, and contributor guidance.
