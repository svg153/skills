# Behavioral skill evaluations

The repository uses **Waza** for catalog behavioral evaluation. The decision and framework comparison are recorded in `docs/adr/0001-behavioral-skill-evaluations.md`.

## What the evals prove

Behavioral suites test trigger boundaries and selected runtime promises. They are regression evidence, not a universal quality or popularity score. A green suite means the declared cases passed under the recorded executor/model conditions; it does not prove a skill is correct for every prompt or every agent host.

The initial representative set covers:

- `github-build-or-reuse` — research-before-build, decision vocabulary, explicit bypasses, and degraded-search disclosure;
- `social-publishing` — attribution, privacy, and typo-only boundaries;
- `github-repo-autopilot` — repository delivery and no-merge / failed-CI safety boundaries;
- `evidence-based-decision-research` — primary-evidence discipline and false-precision refusal;
- `issue-creation` — a compact issue-first/approval-gate workflow.

## Repository convention

Production suites live in `evals/<catalog-name>/`, never in generated cross-agent manifests. The `skill:` field in `eval.yaml` must equal the catalog directory name, and tasks live under `tasks/*.yaml`.

This location is mandatory for mirrored upstream-authoritative skills. Their runtime payload under `skills/<name>/` may be replaced by generic upstream synchronization; the local catalog can evaluate that payload without modifying it or claiming the upstream project authored the tests.

## Pull-request validation: no model credentials

PR validation is intentionally unprivileged:

```bash
python -m pip install 'PyYAML>=6,<7'
python scripts/validate-evals.py
waza spec verify --skill skills/<name> --eval evals/<name>/eval.yaml
```

`.github/workflows/eval-static.yml` runs the repository validator and a pinned, checksum-verified Waza `spec verify`. It does not call an LLM and receives no model secret. Invalid paths, duplicate task IDs, missing positive/negative coverage, mismatched trigger graders, and malformed catalog ownership fail before behavioral execution.

## Trusted model-backed runs

`.github/workflows/eval-behavioral.yml` runs only from `workflow_dispatch` or the repository schedule. It is deliberately absent from `pull_request`, so untrusted fork code cannot receive model credentials.

Waza's documented GitHub Actions credential is the repository secret `COPILOT_SDK_TOKEN`.

If that secret is absent, the trusted workflow emits a notice and exits successfully without calling a model. Once configured, it runs every catalog suite using the `copilot-sdk` executor.

Each run retains for 14 days:

- Waza machine-readable JSON per skill;
- JUnit XML per skill;
- per-task transcripts where Waza produces them.

Artifacts are diagnostic evidence. Do not aggregate them into a public one-dimensional "quality score".

## Local behavioral execution

Install a compatible Waza release using its supported installation method, authenticate the Copilot SDK, then run a single suite:

```bash
waza run evals/github-build-or-reuse/eval.yaml \
  --output eval-results/github-build-or-reuse/results.json \
  --reporter junit:eval-results/github-build-or-reuse/junit.xml
```

Run deterministic coverage without model calls:

```bash
waza spec verify \
  --skill skills/github-build-or-reuse \
  --eval evals/github-build-or-reuse/eval.yaml
```

`./scripts/install-waza-ci.sh` is intentionally CI-specific: it pins Waza v0.38.6 and verifies the Linux x86_64 release SHA-256. It is not a general developer installer.

## Adding or changing an eval

1. Start from the actual `SKILL.md` activation and hard rules, not from generic benchmark prompts.
2. Add at least one prompt that should activate the skill and one realistic boundary that should not.
3. For positive cases, add a behavioral grader for the promise being protected.
4. Prefer stable behavioral contracts over stylistic wording checks.
5. Keep catalog evals outside upstream-authoritative mirrored payloads.
6. Run `python scripts/validate-evals.py` and Waza `spec verify`.
7. Use a trusted behavioral run before treating a major behavior change as validated.

If a behavioral case is stochastic, improve the rubric or use multiple trials before turning a single model outcome into a brittle release gate.
