# Behavioral skill evaluations

The repository uses **Waza** for catalog behavioral evaluation. The framework decision is recorded in `docs/adr/0001-behavioral-skill-evaluations.md`.

## What the evals prove

Catalog suites test trigger boundaries and integration behavior. They are regression evidence, not a universal quality or popularity score. A green suite means the declared cases passed under the recorded executor/model conditions; it does not prove a skill is correct for every prompt or every agent host.

The representative set includes:

- `github-build-or-reuse` — **catalog routing only**: specialized build/reuse decisions activate it while generic evidence research and existing-repository delivery do not. Intrinsic behavior is owned upstream by `ghspain/github-build-or-reuse`.
- `social-publishing` — attribution, privacy, and typo-only boundaries.
- `github-repo-autopilot` - autonomous repository delivery, auditable reversible decisions, deferred non-blocking research, and no-merge / CI safety boundaries.
- `evidence-based-decision-research` — primary-evidence discipline and false-precision refusal.
- `wayback-evidence-capture` — fixed-snapshot-only evidence export with hashes and provenance; refuses live-site screenshots and certified-evidence claims.
- `personal-agentic-delivery` — selected-mode isolation, concept batching within effective budgets, local-only authorization and real size/correctness gates.
- `issue-creation` — a compact issue-first/approval-gate workflow.
- `planning` — new-work structuring, provider ownership, degraded GitHub/Jira operation, and the explicit mutation boundary of the planning capability plugin.
- `smart-shopping-advisor` — Costco Same-Day basket routing via store profiles, live dated prices and offer validity, membership amortization, and corporate-analysis / recipe boundaries.
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

`.github/workflows/eval-behavioral.yml` runs only from `workflow_dispatch` or the repository schedule. It is deliberately absent from `pull_request`, so untrusted fork code cannot receive model-backed execution credentials.

The `copilot-sdk` executor uses the GitHub Copilot SDK's **documented authentication variables** rather than a repository-specific variable name:

1. `COPILOT_GITHUB_TOKEN` — preferred explicit user/service token;
2. `GH_TOKEN` — GitHub CLI-compatible fallback supported by the SDK;
3. `GITHUB_TOKEN` — GitHub Actions built-in token.

The repository workflow supports two trusted modes:

- **organization-owned repository:** use the built-in `GITHUB_TOKEN` with `copilot-requests: write`; no stored Copilot secret is required, but the organization must enable the GitHub policy that allows Copilot CLI/requests billed to the organization;
- **user-owned repository:** configure the repository secret `COPILOT_GITHUB_TOKEN` with a Copilot-compatible user token. The SDK supports OAuth/GitHub App user tokens and fine-grained PATs; do not use a deprecated classic `ghp_` PAT.

`svg153/skills` is currently user-owned. If `COPILOT_GITHUB_TOKEN` is absent, behavior now depends on the trigger:

- a **scheduled** run records an explicit `skipped — no supported Copilot credential` job summary and exits without model evidence, avoiding a noisy weekly failure;
- a **manual `workflow_dispatch`** fails deliberately before model execution. A manually requested evidence run must never appear green when no model actually ran.

The previous `COPILOT_SDK_TOKEN` name was removed because it is not an authentication variable consumed by Waza/Copilot SDK.

Once a supported credential path is available, the workflow runs suites under `evals/` using the `copilot-sdk` executor, including capability-plugin skill suites. Which suites run, with which model and at what cost is described in [Cost controls](#cost-controls).

### Workspace isolation

Waza gives each task an empty temp workspace, but the agent is an ordinary process with the runner user's privileges and can discover and modify the real checkout (for example through `~/work`). A first model-backed run (44134233088) showed this: one autopilot task ran `git init` in the checkout's parent directory followed by `git clean -ffd`, deleting `evals/` so every later suite failed with `failed to load spec`.

`scripts/run-behavioral-suites.sh` therefore:

- resolves the suite list to absolute paths once, before any suite runs;
- runs each suite from a fresh, disposable copy of the repository under `$RUNNER_TEMP`, so any mutation stays in the copy;
- makes the real checkout and its parent directory read-only while a suite runs (defense in depth; it stops accidental `git clean`, `git checkout`, `rm` and `git init`, not a deliberate `chmod`);
- compares `HEAD`, the current ref and `git status --porcelain` (ignoring the results directory) before and after each suite, and aborts with an error naming the suite if the checkout changed.

The script refuses to start when the checkout is not clean.

### Token exposure and single-suite runs

- When `COPILOT_GITHUB_TOKEN` is present (`user-token` mode) the agent environment contains no `GITHUB_TOKEN` or `GH_TOKEN`: the workflow does not export it and `scripts/run-behavioral-suites.sh` unsets any ambient one. The Copilot SDK only needs `COPILOT_GITHUB_TOKEN`, and a model-driven agent then cannot call `gh` against the live repository. `GITHUB_TOKEN` (`github.token`) is passed only in `actions-token` mode.
- Tasks that need repository state must provide it as inline `inputs.files` fixtures and set a task-level `timeout_seconds`, instead of relying on the live repository (see `autopilot-maintain-repo-no-merge`).
- `workflow_dispatch` accepts an optional `suite` input to run a single suite. It is passed through an environment variable, must match `[a-z0-9-]+` and must exist as `evals/<suite>/eval.yaml`; empty runs every suite. Scheduled runs only run changed suites (see below).

Each model-backed run retains for 14 days Waza JSON, JUnit XML and per-task transcripts where available. Treat those artifacts as diagnostic evidence, not as a one-dimensional public quality score.

## Cost controls

Model-backed runs spend Copilot premium requests. Three controls keep that bounded.

### Schedule policy: only changed suites

The schedule (`17 4 * * 1`, Mondays 04:17 UTC) no longer runs all suites. `scripts/eval_cost.py select` runs a suite only if one of its inputs changed since the last successful model-backed run:

- `evals/<suite>/**`;
- the skill directory the suite targets, resolved from the `skill:` field to `skills/<skill>/` or `plugins/*/skills/<skill>/`;
- the shared machinery: `scripts/run-behavioral-suites.sh`, `scripts/install-waza-ci.sh` (the Waza pin) and `.github/workflows/eval-behavioral.yml`. A change to any of these runs **every** suite. `scripts/eval_cost.py` itself is deliberately not shared machinery: it is unit-tested and only decides what to run.

**Baseline.** A run that executed suites and finished successfully on the default branch uploads a tiny artifact, `waza-eval-baseline` (`baseline.json` with the run's SHA, retention 90 days), as its last step. The next scheduled run lists those artifacts with `gh api` (needs `actions: read`; the step is the only one that receives a token) and diffs that SHA against `HEAD` (the checkout uses `fetch-depth: 0` for this). Properties:

- it is written only after every step succeeded, so a failing suite leaves the old baseline in place and that suite is retried on the next schedule;
- it is written only by runs that covered every suite with each suite's own model: scheduled runs, or manual runs without `suite` and with `model: default`. Single-suite or model-override manual runs never advance it;
- scheduled runs that selected nothing write no marker and keep the old one.

**No baseline = run nothing.** If no unexpired marker exists (first run after this policy lands, or no model-backed run for 90 days) or the baseline commit is unreachable, the scheduled run evaluates nothing, spends zero premium requests and says so in the step summary. Create the baseline with one manual dispatch (empty `suite`, `model: default`); that run costs a full pass (see below).

**Manual dispatch** keeps its previous behaviour: every suite, or the single `suite`. `force_all: true` ignores `suite` and runs everything; it never consults the baseline.

### Model and budget per suite class

Waza 0.38.6 (the pin) supports `config.model`, `config.timeout_seconds` (and per-task `timeout_seconds`), `config.first_event_timeout_seconds` and a `--model` CLI override (checked against the source at tag `v0.38.6`). It has **no max-turns / turn-cap setting**: `max_iterations` and `max_tool_calls` exist only as `behavior` grader rules that fail a task after the fact and do not stop spending. The per-task timeout is therefore the only hard cap.

| Class | Suites | Model | Timeout per task |
| --- | --- | --- | --- |
| Routing | `github-build-or-reuse` (2 of 3 tasks are trigger-only; the third adds one verdict check) | `claude-haiku-4.5` (`config.model`) | 150 s |
| Behavior | every other suite (all mix trigger graders with response-quality prompt graders) | Copilot default (`model` unset) | 300 s |

Source for the choice (GitHub Docs, [model multipliers](https://docs.github.com/en/copilot/reference/copilot-billing/request-based-billing-legacy/model-multipliers-for-annual-plans), read 2026-11-17): Claude Haiku 4.5 is 0.33x, the cheapest widely available model listed; MAI-Code-1.1-Flash is 0.25x but is left off the allowlist because its Copilot CLI model id could not be verified without a run. The page lists no 0x model and says multipliers apply only to Pro/Pro+ annual plans still on request-based billing; GitHub moved other plans to usage-based billing on 2026-06-01 ([models and pricing](https://docs.github.com/en/copilot/reference/copilot-billing/models-and-pricing)), so re-check the table before relying on a multiplier. Behavior suites keep the default model: no evidence yet that a cheaper model grades response quality equivalently.

`workflow_dispatch` input `model` (`default`, `claude-haiku-4.5`, `claude-sonnet-4.6`) overrides every selected suite's model. It is a `choice` input, re-validated against the same allowlist in `scripts/run-behavioral-suites.sh`, and reaches the script only through the `WAZA_MODEL` environment variable, never through `${{ }}` inside `run:`. Validation (`scripts/validate-evals.py`) rejects any `config.model` outside the allowlist and any `timeout_seconds` outside 1..600.

### Cost reporting

After each run the step summary has a `Premium requests per suite` table (suite, model, premium requests, tasks) built from `summary.usage.premium_requests` in each `results.json` (falling back to the sum of per-run usage). A suite whose usage is missing or unparsable shows `not reported` and the total is flagged as partial.

### Cost expectations

Measured on the default model before this change (premium requests per suite per run): backlog-management 4, deck-design-system 1, design-engineering 14, evidence-based-decision-research 3, github-build-or-reuse 34 (3 routing tasks, 2-3 minutes each with live research), github-repo-autopilot 36-38. Those six are about 92-94 of the total; the other eleven suites were not measured.

| Scenario | Premium requests |
| --- | --- |
| Old weekly schedule, those six suites only | about 92-94 per week |
| Scheduled run, nothing changed (or no baseline) | 0 |
| Scheduled run, one suite changed | that suite's cost, e.g. 1-14, up to 38 for autopilot |
| `github-build-or-reuse` with Haiku (expected) | roughly 34 x 0.33, about 11; unmeasured, check the first summary |
| Full manual pass | previous total, minus the routing saving |

Weekly cost is now proportional to churn instead of constant. Shared-machinery changes (workflow, runner script, Waza bump) still trigger a full pass, so batch them.

### Forcing a full run

Actions > Trusted Behavioral Skill Evaluations > Run workflow, then either leave `suite` empty or tick `force_all`, keep `model: default`, run from the default branch. Or `gh workflow run eval-behavioral.yml -f force_all=true`.
## Interpreting workflow status

Do not infer behavioral evidence from the workflow name alone:

- static Waza verification proves only schema/path/grader contract validity;
- a scheduled trusted run may be deliberately skipped when no supported credential exists;
- a successful manual trusted run implies the workflow found a supported credential and reached model-backed execution, but the retained Waza results remain the actual task-level evidence;
- a failed manual run with no credential is an evidence-integrity guard, not a skill regression.

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
