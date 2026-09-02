---
name: skill-publish
description: "Create or register skills in svg153/skills through a zero-write plan, explicit ownership, approval hash, rollback, catalog registration, and validation. Use for adding a catalog skill, not editing or releasing one."
license: MIT
metadata:
  author: svg153
  version: "2.0"
---

# Skill Publish

Add one skill to `svg153/skills` without inventing lifecycle policy, duplicating an existing capability, or mutating repository state before the exact plan is approved.

## Activation Contract

Use this skill when the job is to create or register a catalog skill, including:

- a new locally authored skill;
- an external skill that should remain upstream-authoritative and synchronize automatically;
- an upstream-derived skill that will intentionally diverge and be maintained locally;
- registration work involving `metadata.yaml`, `skills.sh`, APM packaging, behavioral evals, or generated cross-agent manifests.

Do **not** use it merely to edit the prose or behavior of an already registered skill; use `skill-creator`/the owning skill workflow instead. Do not use it for release/tag/indexing work after registration; hand that phase to `agent-skill-release-lifecycle`.

## Hard Rules

1. Search existing catalog names, runtime names, descriptions, triggers, and use cases before planning a new skill. Prefer extending an existing skill when the overlap is substantial.
2. Choose exactly one ownership mode before mutation: `LOCAL`, `MIRRORED_UPSTREAM`, or `CURATED_UPSTREAM`.
3. Never silently invent provenance, authority, synchronization cadence, channel, license, or APM/eval policy.
4. `plan` is the mandatory first mutation boundary. It must be zero-write and produce the complete file plan plus an approval hash.
5. Apply only the unchanged plan whose hash was approved. Any relevant repository or input change requires a fresh plan and approval.
6. Reject case-insensitive catalog/runtime collisions, unsafe paths, symlinked canonical surfaces, source symlinks, and existing destinations.
7. Generated plugin/distribution manifests come from canonical catalog state. Never patch them independently.
8. Keep behavioral evals catalog-owned under `evals/<catalog-name>/`; do not place catalog-specific eval policy inside an upstream-authoritative mirrored payload.
9. Application is transactional where practical: stage first, write canonical roots atomically, regenerate derived surfaces, run deterministic repository validation, and roll back registration if validation fails.
10. This skill does not commit, push, merge, tag, or publish releases. Those are separate Git/GitHub authorization boundaries.

## Ownership Decision

| Mode | Authority | Sync strategy | Use when |
| --- | --- | --- | --- |
| `LOCAL` | local | `local`, disabled | The skill is authored and maintained in this catalog. |
| `MIRRORED_UPSTREAM` | upstream | `download`, enabled | The upstream artifact must remain authoritative and generic sync may replace the local payload. |
| `CURATED_UPSTREAM` | local | `manual`, disabled | The skill starts from upstream but local adaptation must never be overwritten automatically. |

For `MIRRORED_UPSTREAM`, require `origin`, `origin_path`, `origin_ref`, sync interval, and channel. For `CURATED_UPSTREAM`, retain provenance but keep local authority and manual synchronization.

## Execution Steps

### 1. Discover and de-duplicate

Inspect the repository's actual conventions and existing skill catalog. Compare the proposed name and `use_for` phrases with existing runtime names and descriptions. If another skill owns the same job, stop and propose extending it unless the overlap is deliberate and explicitly recorded with `allow_overlap_with`.

Use `skill-creator` to shape a LOCAL skill's runtime contract when needed. Use `github-build-or-reuse` before introducing substantial new implementation that may already exist upstream.

### 2. Build the spec

Create a temporary JSON spec using the repository-native schema described in `references/creation-contract.md`. Collect only missing values. The spec must state ownership, category, status, tags, optional `skills_sh_group`, whether APM packaging is wanted, and whether Waza eval scaffolding is wanted.

For upstream modes, obtain a regular local `source_dir` containing the exact payload intended for registration. Verify its provenance/ref before planning; the tool deliberately does not pretend a local directory proves remote provenance.

### 3. Produce a zero-write plan

From the repository root:

```bash
python skills/skill-publish/scripts/catalog_skill.py plan \
  --spec /path/to/skill-spec.json
```

Review the complete JSON plan: ownership, runtime name, repository fingerprint, accepted overlap exceptions, every file create/update, generated manifests, validations, post-apply client checks, and `approval_hash`.

Do not mutate the repository during planning. Show the material plan to the user and obtain approval of that exact plan/hash before applying.

### 4. Apply the unchanged approved plan

```bash
python skills/skill-publish/scripts/catalog_skill.py apply \
  --spec /path/to/skill-spec.json \
  --approve <approval_hash>
```

The command recomputes the plan immediately before application. A stale repository fingerprint, changed spec, new collision, or different target produces a different hash and must fail closed.

Application may create:

- `skills/<name>/SKILL.md` for LOCAL skills, or copy the regular upstream payload for upstream modes;
- `skills/<name>/metadata.yaml` with the selected lifecycle semantics;
- optional `skills/<name>/apm.yml`;
- optional catalog-owned `evals/<name>/...` Waza scaffold;
- one append-only registration in an existing `skills.sh.json` grouping;
- regenerated cross-agent distribution manifests.

### 5. Verify before declaring success

Application runs deterministic repository checks and rolls back the new registration if they fail. Then run every reported `post_apply_client_checks`, including telemetry-disabled `npx skills` discovery and APM consumption when applicable.

For an already registered skill, the read-only check path is:

```bash
python skills/skill-publish/scripts/catalog_skill.py check --name <name>
```

Before a PR is considered complete, repository CI must also pass the skill-publish unit tests, catalog validation, workflow-security baseline, Waza static validation when evals are present, `npx skills` discovery, and existing APM smoke tests.

## Coordination Boundaries

- `skill-creator`: author or improve the runtime `SKILL.md` contract.
- `skill-publish`: choose lifecycle, plan, register, regenerate, validate, and roll back registration failures.
- `skill-registry`: index skills for a workspace; it is not repository authority.
- `agent-skill-release-lifecycle`: tag/release, downstream synchronization, skills.sh indexing, and post-merge discoverability.

Do not introduce `.skills-repo/state.json` or another competing repository authority. Canonical `skills/`, `metadata.yaml`, `skills.sh.json`, distribution config, and catalog-owned evals remain the source state.

## Output Contract

Report:

- selected ownership mode and why;
- overlap/collision result;
- exact approval hash and whether it was applied unchanged;
- files created/updated and generated surfaces regenerated;
- deterministic validation results;
- client checks actually executed and their outcomes;
- remaining Git/PR/release work as separate authorized steps.

Never report a skill as registered from a dry-run alone or as published merely because registration succeeded.

## References

- `references/creation-contract.md` — schema, lifecycle examples, and verification contract.
