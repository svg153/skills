# Behavioral skill evaluations

The repository uses **Waza** for catalog behavioral evaluation. The framework decision is recorded in `docs/adr/0001-behavioral-skill-evaluations.md`.

## What the evals prove

Catalog suites test trigger boundaries and integration behavior. They are regression evidence, not a universal quality or popularity score. A green suite means the declared cases passed under the recorded executor/model conditions; it does not prove a skill is correct for every prompt or every agent host.

The representative set includes:

- `github-build-or-reuse` — **catalog routing only**: specialized build/reuse decisions activate it while generic evidence research and existing-repository delivery do not. Intrinsic behavior is owned upstream by `ghspain/github-build-or-reuse`.
- `social-publishing` — attribution, privacy, and typo-only boundaries.
- `github-repo-autopilot` — repository delivery and no-merge / failed-CI safety boundaries.
- `evidence-based-decision-research` — primary-evidence discipline and false-precision refusal.
- `issue-creation` — a compact issue-first/approval-gate workflow.
- `planning` — new-work structuring, provider ownership, degraded GitHub/Jira operation, and the explicit mutation boundary of the planning capability plugin.
- `backlog-management` — existing-backlog cleanup, cross-provider source-of-truth rules, degraded provider reads, and the boundary with greenfield planning.

## Canonical skill source

Behavioral evidence must point at the real portable skill, never an eval-only copy. A suite name resolves uniquely to one of:

```text
skills/<name>/SKILL.md
plugins/<plugin>/skills/<name>/SKILL.md
```

The validator fails if the name is missing or becomes ambiguous across those namespaces. Capability-plugin skills therefore get the same Waza evidence without being copied into the root catalog merely for testing.

For embedded capability skills, the owning package must contain both `plugin.json` and `distribution.config.json`. This keeps behavioral evidence attached to a real generated/distributable capability boundary.

## Upstream ownership boundary

For a `download` + `authoritative: upstream` root catalog skill, do not copy the upstream behavioral suite into this catalog. The upstream repository should test the product's intrinsic promises; the catalog adds only behavior that is specific to coexistence, routing, packaging, synchronization or catalog policy.

`github-build-or-reuse` is the first explicit example:

```text
ghspain/github-build-or-reuse/evals/...   intrinsic product behavior
svg153/skills/evals/github-build-or-reuse integration/routing behavior
```

Its mirrored runtime payload remains replaceable by the generic sync mechanism, while local integration evals stay outside that payload.

## Repository convention

Production suites live in `evals/<skill-name>/`, never in generated cross-agent manifests or inside an upstream-authoritative mirrored payload. The `skill:` field in `eval.yaml` must equal the suite directory name, and tasks live under `tasks/*.yaml`.

Each suite must resolve to exactly one canonical skill source. Trigger graders must point to that exact `SKILL.md` path, whether it lives under `skills/` or under a capability plugin.

## Pull-request validation: no model credentials

PR validation is intentionally unprivileged:

```bash
python -m pip install 'PyYAML>=6,<7'
python scripts/validate-evals.py
skill_dir="$(python scripts/validate-evals.py --resolve-skill-dir <name>)"
waza spec verify --skill "$skill_dir" --eval evals/<name>/eval.yaml
```

`.github/workflows/eval-static.yml` runs the repository validator and a pinned, checksum-verified Waza `spec verify`. It does not call an LLM and receives no model secret. Invalid paths, ambiguous skill sources, duplicate task IDs, missing positive/negative coverage, mismatched trigger graders, malformed catalog ownership, and invalid capability-package ownership fail before behavioral execution.

The static workflow watches both root catalog skills and `plugins/**/skills/**/SKILL.md`, so changing an embedded planning skill cannot bypass its behavioral contract.

## Trusted model-backed runs

`.github/workflows/eval-behavioral.yml` runs only from `workflow_dispatch` or the repository schedule. It is deliberately absent from `pull_request`, so untrusted fork code cannot receive model credentials.

Waza's GitHub Actions credential is the repository secret `COPILOT_SDK_TOKEN`. If that secret is absent, the trusted workflow emits a notice and exits successfully without calling a model. Once configured, it runs every suite under `evals/` using the `copilot-sdk` executor, including capability-plugin skill suites.

Each run retains for 14 days Waza JSON, JUnit XML and per-task transcripts where available. Treat those artifacts as diagnostic evidence, not as a one-dimensional public quality score.

## Local execution

Root catalog skill:

```bash
waza run evals/github-build-or-reuse/eval.yaml \
  --output eval-results/github-build-or-reuse/results.json \
  --reporter junit:eval-results/github-build-or-reuse/junit.xml

waza spec verify \
  --skill skills/github-build-or-reuse \
  --eval evals/github-build-or-reuse/eval.yaml
```

Capability-plugin skill:

```bash
waza spec verify \
  --skill plugins/planning/skills/planning \
  --eval evals/planning/eval.yaml
```

`./scripts/install-waza-ci.sh` is intentionally CI-specific: it pins Waza v0.38.6 and verifies the Linux x86_64 release SHA-256.

## Adding or changing an eval

1. Decide who owns the behavior: upstream intrinsic contract or catalog/plugin integration concern.
2. Target the canonical `SKILL.md`; do not create a testing copy.
3. Start from actual activation/hard rules rather than generic benchmark prompts.
4. Add at least one positive prompt and one realistic non-trigger boundary.
5. Positive cases need a behavioral grader in addition to trigger accuracy.
6. Prefer stable behavioral contracts over stylistic wording checks.
7. Keep catalog evals outside upstream-authoritative mirrored payloads.
8. Run `python scripts/validate-evals.py` and Waza `spec verify`.
9. Use a trusted behavioral run before treating a major behavior change as validated.
