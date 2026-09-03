# Behavioral evaluations

This directory contains **catalog-owned** Waza suites. Runtime skill files remain under `skills/`; behavioral evidence lives here so it can evolve independently from distribution packaging and upstream synchronization.

Each covered skill uses:

```text
evals/<catalog-name>/
├── eval.yaml
└── tasks/
    └── *.yaml
```

A suite must contain at least one positive trigger and one negative/boundary case. Positive cases also need a behavioral grader so trigger accuracy is never mistaken for task quality.

## Mirrored upstream skills

For `sync.strategy: download` + `authoritative: upstream` entries, catalog evals must remain here rather than inside the mirrored `skills/<name>/` payload. The upstream project owns its intrinsic behavior tests; this catalog should add only integration concerns that exist because the skill coexists with other catalog entries.

For example, `ghspain/github-build-or-reuse` owns the canonical Waza suite for research-before-build, decision vocabulary, bypass behavior, trivial-work boundaries and evidence-gap disclosure. The local `evals/github-build-or-reuse/` suite instead protects routing boundaries against generic research and repository-delivery skills.

This prevents duplicate behavioral ownership, avoids implying that the upstream author maintains catalog policy, and keeps upstream synchronization replaceable.

See `docs/evals.md` for CI, trusted execution, results, and contributor guidance.
