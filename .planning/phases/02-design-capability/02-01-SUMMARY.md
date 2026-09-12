---
phase: 02-design-capability
plan: "01"
status: complete
requirements: ["PKG-01"]
completed: 2026-09-12
---

# Phase 2 Plan 01 Summary — Design Engineering Capability

## Outcome

Established `plugins/design-engineering/` as a governed Agent Plugins 1.0 capability using the repository-native `skill-publish` transaction landed in #55. The package begins with one canonical local `design-engineering` orchestration skill and deliberately has no mandatory MCP or external skill dependency yet.

## Delivered

- `plugins/design-engineering/distribution.config.json` — canonical capability metadata, version `0.1.0`.
- `plugins/design-engineering/skills/design-engineering/SKILL.md` — canonical runtime identity and minimal reuse-first/UI-verification contract.
- `plugins/design-engineering/plugin.json` — generated Agent Plugins 1.0 manifest.
- `plugins/design-engineering/README.md` — package boundary, canonical sources, degradation and roadmap notes.
- Root `marketplace.json` and `.agents/plugins/marketplace.json` now expose `design-engineering` beside the existing `planning` capability.

No duplicate root `skills/design-engineering` copy was introduced.

## Governed creation evidence

The capability was not hand-registered. A temporary unregistered staging source was passed through:

1. `catalog_capability.py plan` — zero-write plan succeeded in GitHub Actions run `34696653927`.
2. Exact approved plan hash: `20211512207f8eb5f6981394270ae59489707848317337b88f5d0925449bcede`.
3. `catalog_capability.py apply --approve <exact-hash>` — succeeded in run `34696678251`.
4. Apply-time deterministic generation/checks all returned 0, including `generate-capability-plugin.py --all --check` and `generate-distribution.py --check`.
5. Temporary capability spec, staging skill and validation workflow were removed after evidence was captured; they are not repository authorities.

## Verification

Dedicated verification run `34696761179` completed successfully and proved:

- governed capability `check --name design-engineering`;
- generic capability generator and root distribution are clean/idempotent;
- capability publisher and generator unit tests pass;
- Agent Skills reference validation passes;
- `npx skills` discovers `design-engineering`;
- GitHub Copilot CLI `1.0.83` installs/discovers the plugin from the repository marketplace;
- OpenAI Codex CLI `0.153.4` installs/discovers the same portable capability.

Repository `Skills Validation` run `34696761161` for the same verification commit also completed successfully.

## Design decisions retained

- Broad interface requests route to the local `design-engineering` skill; future upstream skills remain narrow specialists.
- Existing application context/components/dependencies are inspected and reused before adding new UI primitives.
- Browser-rendered evidence and accessibility/responsive checks are part of the intended baseline, but later phases implement the full workflow.
- Optional MCPs must degrade safely; Phase 2 ships with none.
- Subjective visual changes remain human-reviewable and are not auto-merged.

## Phase 1 relationship

Phase 1 remains externally blocked. On 2026-09-12 the latest genuine `ghspain/github-build-or-reuse` release is still `v1.2.3`, so #46 cannot yet prove a newer real Renovate-driven update. Phase 2 is safe to complete out of numeric order because it adds no external design dependency and therefore does not weaken that supply-chain gate.

## Next

Phase 3 can implement the **generic lock-backed external component contract** without yet enrolling Emil/Addy dependencies. Actual external design skill consumption remains gated by the supply-chain policy and review evidence.
