# Behavioral evaluation research prototypes

These files support ADR 0001 / issue #19. They are **not** the permanent evaluation contract.

`scenarios.yaml` is framework-neutral and defines the common `github-build-or-reuse` scenario IDs, prompts, trigger expectations and behavioral intent. The same scenarios are represented in Waza and Vally to make the framework comparison concrete.

```text
research/evals/
├── scenarios.yaml
├── waza/github-build-or-reuse/
│   ├── eval.yaml
│   └── tasks/*.yaml
└── vally/github-build-or-reuse/eval.yaml
```

Validate parity without installing either evaluation framework:

```bash
python -m pip install 'PyYAML>=6,<7'
python scripts/validate-eval-research.py
```

The accepted implementation in #20 should move catalog-owned evaluation suites to top-level `evals/<catalog-name>/` and pin Waza rather than treating these research prototypes as production inputs.
