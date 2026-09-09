---
name: skill-publish
description: "Create, register, or repair skills and governed capability Agent Plugins in svg153/skills through zero-write plans, explicit ownership, approval hashes, rollback, catalog registration, and validation. Use for catalog lifecycle work, not ordinary skill prose edits or releases."
license: MIT
metadata:
  author: svg153
  version: "2.2"
---

# Skill Publish

Manage catalog registration in `svg153/skills` without inventing lifecycle policy, duplicating an existing capability, or mutating repository state before the exact plan is approved.

## Activation Contract

Use this skill when the job is to create, register, or repair catalog lifecycle state, including:

- a new locally authored skill;
- an external skill that should remain upstream-authoritative and synchronize automatically;
- an upstream-derived skill that will intentionally diverge and be maintained locally;
- a capability-level Agent Plugin whose package-local skills and optional MCP composition should be installed/versioned together;
- registration involving `metadata.yaml`, `skills.sh`, APM packaging, behavioral evals, or generated cross-agent manifests;
- normalization of legacy lifecycle metadata already present in the catalog.

Do **not** use it merely to edit the prose or behavior of an already registered `SKILL.md`; use `skill-creator`/the owning workflow instead. Do not use it for tag/release/indexing work after registration; hand that phase to `agent-skill-release-lifecycle`.

## Hard Rules

1. Search existing catalog names, runtime names, capability packages, descriptions, triggers, and use cases before planning new state. Prefer extending an existing skill/capability when overlap is substantial.
2. Root catalog skills choose exactly one ownership mode: `LOCAL`, `MIRRORED_UPSTREAM`, or `CURATED_UPSTREAM`.
3. Capability skills are canonical under `plugins/<capability>/skills/*`; never create a second root/runtime copy merely to package them.
4. Never silently invent provenance, authority, synchronization cadence, channel, license, MCP provenance, or APM/eval policy.
5. A zero-write `plan` is the mandatory mutation boundary and must produce an approval hash.
6. Apply only the unchanged plan whose hash was approved; repository or input drift requires a new plan.
7. Reject case-insensitive catalog/runtime/capability collisions, unsafe paths, symlinked canonical surfaces, source symlinks, and silent overwrites.
8. Generated distribution manifests come from canonical catalog/package state. Never patch them independently.
9. Keep catalog behavioral evals under `evals/<runtime-name>/`; do not place local eval policy in an upstream-authoritative mirrored payload.
10. Apply transactionally where practical and roll back registration/repair if deterministic validation fails.
11. This skill does not commit, push, merge, tag, or publish releases.

## Ownership Decision

| Mode | Authority | Sync strategy | Use when |
| --- | --- | --- | --- |
| `LOCAL` | local | `local`, disabled | The skill is authored and maintained in this catalog. |
| `MIRRORED_UPSTREAM` | upstream | `download`, enabled | Stable upstream payload remains authoritative. |
| `CURATED_UPSTREAM` | local | `manual`, disabled | Upstream provenance is retained but local adaptation must not be overwritten. |

## Create or register a root catalog skill

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

## Create or register a capability Agent Plugin

Use a capability only when multiple skills, shared MCP/tooling, permissions, versioning, or ownership create a meaningful installable boundary. Do not mechanically create one plugin per skill.

1. Author the runtime skills in temporary **unregistered staging directories**. Do not point the capability publisher at existing root `skills/*` or existing `plugins/*` and copy them.
2. Define package metadata, `skill_sources`, and optional governed `mcpServers` using `references/capability-contract.md`.
3. Produce the zero-write plan:

```bash
python skills/skill-publish/scripts/catalog_capability.py plan \
  --spec /path/to/capability-spec.json
```

4. Review package identity/version, canonical runtime names, MCP provenance, every proposed file, generated surfaces and post-apply checks.
5. Approve the exact `approval_hash` and apply:

```bash
python skills/skill-publish/scripts/catalog_capability.py apply \
  --spec /path/to/capability-spec.json \
  --approve <approval_hash>
```

6. The transaction writes canonical runtime behavior to `plugins/<capability>/skills/*`, then generates package manifests and root marketplaces. A validation failure removes the new package and restores previous generated root state.
7. Run the reported client/install checks. Authenticated MCP/tool-call evidence remains a separate runtime gate.

For an existing capability:

```bash
python skills/skill-publish/scripts/catalog_capability.py check --name <capability>
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
- `skill-publish`: lifecycle/package choice, plan, register/repair, regenerate and validate.
- `skill-registry`: workspace index only; not repository authority.
- `agent-skill-release-lifecycle`: tag/release, downstream sync, skills.sh indexing and post-merge discoverability.

Canonical root `skills/`, capability-local `plugins/*/skills/`, root `metadata.yaml`, package `distribution.config.json`, `skills.sh.json` and catalog-owned evals remain source state. Do not introduce `.skills-repo/state.json`, duplicate runtime trees, or another competing authority.

## Output Contract

Report the chosen root-skill ownership mode or capability boundary, overlap/collision findings, exact approval hash, whether it was applied unchanged, canonical runtime path(s), MCP provenance when present, changed/generated files, validation results, client checks actually run, and remaining Git/release/runtime-auth work. Never report a dry-run as applied, install/discovery as authenticated tool execution, or registration as a published release.

## References

- `references/creation-contract.md` — root skill creation/registration schema and verification contract.
- `references/capability-contract.md` — capability Agent Plugin transaction, canonical package skills, optional MCP composition and validation.
- `references/metadata-repair.md` — lifecycle normalization semantics and commands.
