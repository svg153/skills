---
name: skill-publish
description: "Create, register, or repair skills in svg153/skills through zero-write plans, explicit ownership, approval hashes, rollback, catalog registration, and validation. Use for catalog lifecycle work, not ordinary skill prose edits or releases."
license: MIT
metadata:
  author: svg153
  version: "2.1"
---

# Skill Publish

Manage catalog registration in `svg153/skills` without inventing lifecycle policy, duplicating an existing capability, or mutating repository state before the exact plan is approved.

## Activation Contract

Use this skill when the job is to create, register, or repair catalog lifecycle state, including:

- a new locally authored skill;
- an external skill that should remain upstream-authoritative and synchronize automatically;
- an upstream-derived skill that will intentionally diverge and be maintained locally;
- registration involving `metadata.yaml`, `skills.sh`, APM packaging, behavioral evals, or generated cross-agent manifests;
- normalization of legacy lifecycle metadata already present in the catalog.

Do **not** use it merely to edit the prose or behavior of an already registered `SKILL.md`; use `skill-creator`/the owning workflow instead. Do not use it for tag/release/indexing work after registration; hand that phase to `agent-skill-release-lifecycle`.

## Hard Rules

1. Search existing catalog names, runtime names, descriptions, triggers, and use cases before planning a new skill. Prefer extending an existing skill when overlap is substantial.
2. Choose exactly one ownership mode: `LOCAL`, `MIRRORED_UPSTREAM`, or `CURATED_UPSTREAM`.
3. Never silently invent provenance, authority, synchronization cadence, channel, license, or APM/eval policy.
4. A zero-write `plan` is the mandatory mutation boundary and must produce an approval hash.
5. Apply only the unchanged plan whose hash was approved; repository or input drift requires a new plan.
6. Reject case-insensitive catalog/runtime collisions, unsafe paths, symlinked canonical surfaces, source symlinks, and silent overwrites.
7. Generated distribution manifests come from canonical catalog state. Never patch them independently.
8. Keep catalog behavioral evals under `evals/<catalog-name>/`; do not place local eval policy in an upstream-authoritative mirrored payload.
9. Apply transactionally where practical and roll back registration/repair if deterministic validation fails.
10. This skill does not commit, push, merge, tag, or publish releases.

## Ownership Decision

| Mode | Authority | Sync strategy | Use when |
| --- | --- | --- | --- |
| `LOCAL` | local | `local`, disabled | The skill is authored and maintained in this catalog. |
| `MIRRORED_UPSTREAM` | upstream | `download`, enabled | Stable upstream payload remains authoritative. |
| `CURATED_UPSTREAM` | local | `manual`, disabled | Upstream provenance is retained but local adaptation must not be overwritten. |

## Create or register a skill

1. Inspect repository conventions and existing skills for overlap/collisions.
2. Use `skill-creator` for the runtime contract when needed and `github-build-or-reuse` before substantial new implementation.
3. Build the JSON spec described in `references/creation-contract.md`.
4. Produce a zero-write plan:

```bash
python skills/skill-publish/scripts/catalog_skill.py plan --spec /path/to/skill-spec.json
```

5. Review the complete plan and approve its exact `approval_hash`.
6. Apply the unchanged plan:

```bash
python skills/skill-publish/scripts/catalog_skill.py apply \
  --spec /path/to/skill-spec.json \
  --approve <approval_hash>
```

7. Run every reported client check and repository CI before declaring registration complete.

For an existing registered skill, use:

```bash
python skills/skill-publish/scripts/catalog_skill.py check --name <name>
```

## Repair legacy lifecycle metadata

Use the repository-wide repair path when old entries do not conform to the current ownership semantics:

```bash
python skills/skill-publish/scripts/metadata_repair.py plan
python skills/skill-publish/scripts/metadata_repair.py apply --approve <approval_hash>
python skills/skill-publish/scripts/metadata_repair.py check
```

The repair path derives `LOCAL` only from the catalog's own origin, treats external manual entries as `CURATED_UPSTREAM`, and leaves valid upstream-authoritative downloads untouched. It never treats `strategy: manual` as an enabled synchronization mode.

## Coordination Boundaries

- `skill-creator`: author or improve runtime `SKILL.md` behavior.
- `skill-publish`: lifecycle choice, plan, register/repair, regenerate and validate.
- `skill-registry`: workspace index only; not repository authority.
- `agent-skill-release-lifecycle`: tag/release, downstream sync, skills.sh indexing and post-merge discoverability.

Canonical `skills/`, `metadata.yaml`, `skills.sh.json`, distribution config and catalog-owned evals remain the source state. Do not introduce `.skills-repo/state.json` or another competing authority.

## Output Contract

Report ownership mode, overlap/collision findings, exact approval hash, whether it was applied unchanged, changed/generated files, validation results, client checks actually run, and remaining Git/release work. Never report a dry-run as applied or registration as a published release.

## References

- `references/creation-contract.md` — creation/registration schema and verification contract.
- `references/metadata-repair.md` — lifecycle normalization semantics and commands.
