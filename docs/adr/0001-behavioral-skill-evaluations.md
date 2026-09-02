# ADR 0001: Behavioral evaluation framework for the skills catalog

- Status: Accepted
- Date: 2026-09-02
- Issue: #19
- Decision owner: `svg153/skills`

## Context

The catalog already validates Agent Skill structure, provenance metadata, distribution manifests, `npx skills` discovery, selected APM packaging, upstream synchronization and GitHub Actions policy. Those checks do not answer a different question: **does a skill activate at the right time and behave according to its contract when an agent actually uses it?**

The evaluation layer must respect the repository's provenance model. In particular, evals for `download` / upstream-authoritative skills must be catalog-owned outside the mirrored `skills/<name>/` payload so an upstream sync cannot overwrite local evaluation policy or falsely imply upstream authorship.

This ADR evaluates Vally, Waza and a current real-harness alternative before standardizing. The same `github-build-or-reuse` scenario contract is expressed in both Waza and Vally under `research/evals/` so the decision is based on concrete fit rather than README feature lists.

## Requirements

The selected approach should support:

1. positive and negative trigger behavior;
2. expected workflow/decision behavior, not only final text matching;
3. tool/skill invocation assertions where the execution harness exposes them;
4. deterministic/static validation without model credentials;
5. model-backed evaluation on trusted triggers only;
6. isolated fixtures and reproducible task setup;
7. machine-readable output suitable for CI artifacts and later catalog summaries;
8. multi-trial execution for stochastic behavior;
9. reasonable local developer ergonomics;
10. an open license and active maintenance;
11. catalog-owned evals that can target mirrored upstream skills without modifying them.

## Candidates evaluated

### Waza — `microsoft/waza`

Decision: **USE as the primary behavioral skill-evaluation framework.**

Evidence snapshot: 2026-09-02.

- Public repository: <https://github.com/microsoft/waza>
- License: MIT.
- Current repository version checked: `0.38.6`.
- `v0.38.6` was published 2026-08-14 and ships checksum-addressed binaries.
- Project mode explicitly supports `skills/` plus top-level `evals/`, matching this catalog.
- Skill-specific capabilities include trigger grading, `skill_invocation` with required/forbidden skills, `spec verify` coverage against `SKILL.md`, skill discovery and skill-body injection controls.
- Behavioral capabilities include text/code/file/diff/JSON-schema/prompt/behavior/action-sequence/tool-constraint/tool-call graders.
- Supports multiple trials, cross-model comparison, snapshots/replay, regression gates, adversarial packs, MCP mocks and machine-readable results.
- A mock executor is available for hermetic framework/testing paths; real behavioral quality still requires a real executor/model.
- OpenTelemetry support can export execution traces when useful later.

Important costs/risks:

- Release binaries are large (the v0.38.6 Linux amd64 asset is roughly 145 MB because Waza bundles execution dependencies). Eval-specific CI should therefore pin/cache deliberately rather than install Waza in every repository validation job.
- Some high-signal graders still depend on a real agent or judge model and are inherently stochastic.
- The default Copilot-SDK path is not a guarantee of equivalent behavior in every host. Cross-host claims must be measured separately.

Why it wins here: the repository is specifically a catalog of Agent Skills. Waza's explicit trigger, anti-trigger, skill invocation, spec-coverage and project-mode primitives reduce custom glue for exactly the behaviors #20 needs to measure.

### Vally — `@microsoft/vally` / `@microsoft/vally-cli`

Decision: **KEEP AS A STRONG ALTERNATIVE; do not standardize in this repository now.**

Evidence snapshot: 2026-09-02.

- Documentation: <https://microsoft.github.io/vally/>
- Packages: `@microsoft/vally` and `@microsoft/vally-cli`.
- License reported for the current packages: MIT.
- `jongio/skills/create-skills-repo` currently pins `@microsoft/vally-cli` `0.14.0`.
- Strong fast/static `vally lint` path with no agent required.
- Explicit pipeline of stimulus -> executor -> trajectory -> graders -> score.
- Extensible executors, graders, reporters and backends.
- Built-in trajectory-aware `tool-calls` grading, model/judge support, multi-model execution, multi-trial runs, re-grading without re-running the agent, and OpenTelemetry export.
- Mature usage in multiple Microsoft/GitHub-adjacent skill repositories.

Important costs/risks:

- It is a broader AI evaluation platform rather than an Agent-Skills-first contract. Waza currently exposes more direct skill-specific concepts for routing/anti-routing and skill invocation.
- During this audit the published packages/docs were easy to verify, but a public standalone GitHub source repository for the Vally packages was not resolvable through GitHub repository lookup. Package metadata and docs remain public, but source-level traceability is less direct than `microsoft/waza` today.
- Adding Vally would introduce a Node evaluation toolchain alongside the catalog's intentionally dependency-light Python validation. That is acceptable if its generic executor/plugin model becomes necessary later, but not required for the first behavioral layer.

Vally remains the preferred fallback if the project outgrows Waza's Agent-Skills-centric execution model or needs a custom non-Copilot executor/backend/reporting ecosystem.

### `tardigrde/agent-skill-eval`

Decision: **MONITOR / CONTRIBUTE, not the primary framework today.**

- Public MIT repository.
- Runs real Claude Code, Codex and OpenCode harnesses rather than only raw model APIs.
- Measures with-skill vs without-skill deltas, repeated-run pass@k, deterministic state diffs, LLM rubrics, token cost and wall-clock time.
- This is compelling for future cross-host acceptance testing because it measures the actual host discovery/execution path.

It is currently a much younger, small independent project than the Microsoft-backed alternatives. It also makes real harness credentials/runtime availability part of the normal evaluation surface. Adopt later as a complementary end-to-end layer if cross-host parity becomes a release requirement; do not make it the catalog's foundational contract yet.

### Static-only skill scoring tools

Static analyzers such as `effectorHQ/skill-eval` can provide useful lint/safety signals but do not replace behavioral execution. Our existing structural validation already covers much of that role. They are not selected as the behavioral framework.

## Comparison

| Dimension | Waza | Vally | agent-skill-eval |
| --- | --- | --- | --- |
| License | MIT | MIT packages | MIT |
| Primary focus | Agent Skills / custom agents | General AI eval platform | Real coding-agent skill harnesses |
| Project `skills/` + `evals/` mode | Native | Configurable | Supported via explicit paths/workspaces |
| Positive/negative routing | Native trigger + spec concepts | Expressible through stimuli/graders | Expressible with controls/baselines |
| Skill invocation assertions | Native `skill_invocation` | Generic trajectory/tool assertions | Observed through real harness behavior |
| Tool-call assertions | Native | Native | State/trajectory dependent |
| Static/no-model path | Schema/check/spec tools + mock paths | Strong `lint` | More execution-oriented |
| Fixtures/isolation | Native | Environments/backends | Fresh workspace |
| Multi-trial/statistics | Yes | Yes | Yes, pass@k emphasis |
| Cross-model | Yes | Yes | Per harness/model |
| Real multi-host harness | Primarily configured executor | Pluggable executors | Claude Code + Codex + OpenCode first-class |
| Machine-readable results | Yes | Yes | Yes |
| Snapshot/replay | Yes | Re-grade saved trajectories; backend-dependent execution replay | Workspace/evidence reports |
| MCP mocking | Native | Extensible/custom execution | Not a core differentiator |
| CI fit for this catalog | High | High | Medium today |
| Source transparency | Public Microsoft repo | Public packages/docs; source repo not directly resolved in audit | Public repo |

## Prototype result

`research/evals/scenarios.yaml` defines one framework-neutral scenario set for `github-build-or-reuse`:

- non-trivial build -> research before build;
- explicit GitHub/open-source comparison;
- trivial snippet -> avoid disproportionate discovery;
- explicit discovery bypass -> acknowledge bypass rather than silently pretending to vet;
- unavailable search/tooling -> disclose the evidence gap.

The same IDs/prompts are represented in:

- `research/evals/waza/github-build-or-reuse/`
- `research/evals/vally/github-build-or-reuse/eval.yaml`

`scripts/validate-eval-research.py` verifies parity without installing either framework. This research validator is intentionally not the eventual behavioral runner.

Waza expresses trigger expectations directly and maps naturally to the future distinction between required/forbidden skill invocation. Vally expresses the same high-level behavior cleanly, but uses more generic prompt/output/trajectory graders. That concrete difference supports choosing Waza for the first implementation.

## Decision

Use **Waza** as the repository's behavioral skill-evaluation framework beginning in #20.

The permanent contract should use a top-level catalog-owned `evals/<catalog-name>/` tree rather than putting local evals inside mirrored upstream skill payloads.

### CI execution model

Pull requests touching skills/evals:

- parse/lint eval artifacts;
- verify scenario IDs and duplicate/collision rules;
- run Waza deterministic readiness/spec-coverage checks where they do not require model credentials;
- never expose privileged model/provider secrets to fork PRs;
- keep expensive/stochastic evaluation out of the generic `Skills Validation` workflow.

Trusted manual/scheduled evaluation:

- install a **pinned Waza release** and verify its published checksum;
- execute model-backed evals only from trusted repository state;
- begin with one run for smoke/debug and multiple trials for release/nightly signal;
- persist machine-readable results as workflow artifacts;
- report raw pass/fail/evidence and per-suite metrics, not a fabricated universal skill-quality score.

### Version policy

Pin an exact Waza release in CI rather than `main` or a floating installer. The first implementation target is `v0.38.6`; upgrades should be ordinary reviewed dependency changes with schema compatibility checks.

### Cross-host policy

A Waza/Copilot-SDK pass means the skill works under that measured executor; it does **not** prove identical behavior in Codex, Claude Code, Cursor or Gemini. If cross-host parity becomes a release gate, evaluate `agent-skill-eval` or a Vally executor matrix as a complementary end-to-end layer.

## Consequences

Positive:

- native skill routing/anti-routing and invocation concepts;
- fewer custom graders for the first catalog suites;
- open, active, Microsoft-maintained implementation;
- future support for MCP mocks, snapshots and regression gates without replacing the contract.

Negative:

- Waza binary size makes indiscriminate CI installation wasteful;
- behavioral results can still be stochastic and provider-dependent;
- a second tool is added to the repository's developer workflow.

Mitigations:

- eval-specific workflow paths;
- pinned checksum-verified binaries;
- cheap PR checks vs trusted full runs;
- multiple trials for important regressions;
- preserve raw evidence/artifacts;
- never publish a context-free global quality score.

## References checked

- <https://github.com/microsoft/waza>
- <https://microsoft.github.io/waza/guides/graders/>
- <https://microsoft.github.io/waza/guides/spec-verify/>
- <https://github.com/microsoft/waza/releases/tag/v0.38.6>
- <https://microsoft.github.io/vally/>
- <https://microsoft.github.io/vally/reference/cli/lint/>
- <https://microsoft.github.io/vally/reference/graders/tool-calls/>
- <https://github.com/jongio/skills/tree/main/skills/create-skills-repo>
- <https://github.com/tardigrde/agent-skill-eval>
