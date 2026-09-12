---
phase: 03-external-components
plan: "01"
status: complete
completed: 2026-09-12
requirements: ["EXT-01"]
---

# Phase 03 Summary — External Skill Components

## Result

Implemented a generic, fail-closed `externalSkillComponents` contract for capability Agent Plugins without enrolling Emil/Addy or any new design dependency yet.

A capability may now declare an APM dependency locator, runtime target, license and attribution while **not** carrying an independent version/ref/digest. Resolution remains exclusively owned by `dependencies/external-skills/apm.lock.yaml` and `apm-policy.yml`.

## Implementation

- Added `scripts/apm_external_components.py` to normalize declarations, resolve exact allowlisted APM lock entries, fetch the immutable locked commit and materialize the selected Agent Skill subtree.
- Added generated `external-components.json` provenance evidence with dependency locator, upstream path, resolved ref/commit, APM content hash, license and attribution. It is explicitly derived evidence, not another lock.
- Extended `generate-capability-plugin.py` so write mode converges materialized external payloads and `--check` detects payload/manifest drift.
- Extended `skill-publish` capability planning so external components are validated before mutation and exact lock evidence participates in the approval plan/fingerprint.
- Added runtime-identity collision checks across root catalog skills, other capability skills and local skills in the same package.
- Added fail-closed handling for unallowlisted/unlocked dependencies, malformed commits/hashes, unsafe targets, symlink payloads and dependency replacement under an existing managed target.
- Removing a declaration only removes a target previously recorded as externally managed.
- Added documentation to the capability publishing contract and external dependency model.
- `plugins/design-engineering/distribution.config.json` now exposes `externalSkillComponents: []` explicitly; no external design dependency has been enrolled.

## Verification

Validated in GitHub Actions run **34700780054** before the implementation commit was pushed:

- `test_capability_plugins.py` ✅
  - exact allowlist + lock resolution;
  - invalid target/duplicate target rejection;
  - convergent materialization;
  - local payload drift detection;
  - changed APM content hash -> manifest drift;
  - symlink payload rejection;
  - runtime identity collision rejection.
- `test_skill_publish_capability.py` ✅
  - capability plan preserves declaration;
  - plan captures immutable resolved commit;
  - generated external provenance manifest is part of package outputs.
- `generate-capability-plugin.py --all --check` ✅
- `generate-distribution.py --check` ✅
- `git diff --check` ✅

Validated implementation commit: `ea0b74e389481474b4847ada7696644bd9742666`.

## Decisions

- APM lock/policy remain the single resolution/integrity authority.
- Materialized capability skill copies are derived package artifacts, not editable local forks.
- No extra lock or version field is introduced by the capability layer.
- Generic infrastructure lands before dependency enrollment.
- Phase 1/#46 remains the release/Renovate proof gate before Phase 5 actually adds Emil specialist dependencies.

## Requirement

`EXT-01` complete.
