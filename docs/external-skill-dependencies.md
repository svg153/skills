# External Agent Skill dependencies

This catalog separates **dependency consumption** from **catalog mirroring**. APM and Renovate are dependency-management tools; they do not replace the catalog's provenance or lifecycle model.

## Ownership model

| Catalog relationship | Authority | Update path |
| --- | --- | --- |
| `LOCAL` | `svg153/skills` | normal repository development |
| `CURATED_UPSTREAM` | local adaptation | human-reviewed upstream comparison; never automatically overwritten |
| `MIRRORED_UPSTREAM` | upstream payload | APM lock + Renovate PR + catalog materialization + validators/evals |
| external dependency that is not republished | external package | consume through APM without copying into `skills/` |

`metadata.yaml` remains authoritative for provenance, ownership and synchronization semantics. `apm.yml` declares dependency coordinates; `apm.lock.yaml` records immutable resolution and integrity state.

## Pilot layout

```text
dependencies/external-skills/
├── apm.yml
├── apm.lock.yaml
└── apm-policy.yml

skills/github-build-or-reuse/
├── SKILL.md
└── metadata.yaml
```

The APM project is intentionally isolated from the repository root. The catalog uses `apm lock`, not `apm install`, so lock resolution does not create `.agents/skills`, `.claude/skills`, or any other host-specific runtime copy. The committed lock therefore records `deployments: []` for this resolver-only use case.

## Update flow

```text
upstream stable release
  -> Renovate native APM manager updates apm.yml
  -> APM refreshes apm.lock.yaml
  -> PR records exact resolved commit/content hash
  -> catalog materializer checks or applies that exact locked commit
  -> metadata.yaml is preserved
  -> normal catalog validation/evals run
  -> derived Agent Plugin / host distribution is regenerated as needed
```

Renovate is intentionally configured with `automerge: false`. An Agent Skill patch release can change agent instructions materially, so SemVer alone is not sufficient evidence for automatic merge.

## Lock and mirror verification

The lock is regenerated deterministically with pinned APM CLI 0.29.1 in CI. The official Linux release archive is SHA-256 verified before execution.

The catalog-specific mirror check is:

```bash
python scripts/materialize-apm-mirror.py github-build-or-reuse --check
```

To update the canonical mirror after reviewing a Renovate dependency PR:

```bash
python scripts/materialize-apm-mirror.py github-build-or-reuse --apply
python scripts/generate-distribution.py
```

The materializer:

- only accepts `https://github.com/<owner>/<repo>` origins in this pilot;
- requires `sync.enabled: true`, `strategy: download` and `authoritative: upstream`;
- resolves the matching package from `apm.lock.yaml` rather than resolving `latest-release` independently;
- verifies the locked ref still resolves to the exact locked commit, refusing moved tags;
- preserves catalog-owned `metadata.yaml`;
- compares the complete upstream payload to the local mirror.

## APM audit in a resolver-only catalog

`apm audit --ci` normally replays an APM install and compares APM-deployed files with the workspace. That is correct for a normal APM consumer, but this catalog deliberately keeps `deployments: []` to avoid a second runtime source of truth.

Therefore CI uses:

```bash
apm audit --ci --no-drift --policy ./apm-policy.yml --no-fail-fast
```

This retains APM's lock/config/integrity checks and explicit policy enforcement while disabling only APM's deployment-drift replay. Canonical mirror drift is enforced separately by `materialize-apm-mirror.py --check` against `skills/<name>/`.

For repositories that actually install APM dependencies into runtime targets, the normal recommendation remains `apm audit --ci` **without** `--no-drift`.

## Supply-chain policy

`dependencies/external-skills/apm-policy.yml` is fail-closed for the pilot. It allowlists the upstream package, requires pinned constraints and integrity hashes, denies package scripts, and does not implicitly trust self-defined/transitive MCPs.

The policy is deliberately scoped to the external-skill resolver. A future organization-wide APM policy should be evaluated separately rather than assuming this pilot policy is sufficient for every repository.

## Migration from scheduled direct sync

The existing scheduled `sync-upstream-skills.yml` remains active during the pilot. It should only be retired for an APM-managed mirror after all of the following are demonstrated:

1. Renovate detects a real newer stable release and opens a dependency PR.
2. The PR refreshes the APM lock to the intended immutable commit.
3. Materialization from that lock reproduces the expected mirror exactly.
4. Existing skills validation, provenance checks, distribution generation and relevant behavioral/routing evals pass.
5. Rollback is proven by reverting the dependency/lock PR and rematerializing the previous lock.

Only then should the old direct-to-`main` synchronization path stop managing that mirror.
