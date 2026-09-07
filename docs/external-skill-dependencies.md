# External Agent Skill dependencies

This catalog separates **dependency consumption** from **catalog mirroring**. APM and Renovate are dependency-management tools; they do not replace the catalog's provenance or lifecycle model.

## Ownership model

| Catalog relationship | Authority | Update path |
| --- | --- | --- |
| `LOCAL` | `svg153/skills` | normal repository development |
| `CURATED_UPSTREAM` | local adaptation | human-reviewed upstream comparison; never automatically overwritten |
| `MIRRORED_UPSTREAM` | upstream payload | Renovate version PR + APM lock + catalog materialization + validators/evals |
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
  -> Renovate native APM manager updates the version in apm.yml
  -> reviewed PR is opened; no automerge
  -> repository-owned `apm lock` refreshes apm.lock.yaml
  -> PR records exact resolved commit/content hash
  -> catalog materializer checks or applies that exact locked commit
  -> metadata.yaml is preserved
  -> normal catalog validation/evals run
  -> derived Agent Plugin / host distribution is regenerated as needed
```

Renovate is intentionally configured with `automerge: false`. An Agent Skill patch release can change agent instructions materially, so SemVer alone is not sufficient evidence for automatic merge.

### Why Renovate lockfile maintenance is disabled

Renovate's native APM manager delegates lockfile refresh to `apm install`. That behavior is correct for normal APM consumers, where APM also owns deployment into a target runtime. This catalog deliberately uses APM only as a **dependency resolver and integrity lock**: the canonical runtime mirror remains `skills/<name>/` and the lock records `deployments: []`.

For that reason `renovate.json` has `lockFileMaintenance.enabled: false`. We do not add an artificial APM target merely to make Renovate's install-based lock maintenance succeed, because doing so would reintroduce a host-specific runtime copy and weaken the single-source-of-truth model.

During the pilot the safe split is:

1. Renovate discovers a newer stable APM dependency and proposes the `apm.yml` version change.
2. A repository-owned/trusted step refreshes `apm.lock.yaml` using `apm lock`.
3. The catalog materializer updates or checks the canonical mirror from that lock.
4. The resulting PR must pass all normal validation and relevant evals before merge.

A later iteration may automate steps 2–3 with a tightly scoped trusted workflow or self-hosted Renovate post-upgrade command, but only if it preserves the same approval and no-duplicate-runtime guarantees.

## Lock and mirror verification

The lock is regenerated deterministically with pinned APM CLI 0.29.1 in CI. The official Linux release archive is SHA-256 verified before execution.

The catalog-specific mirror check is:

```bash
python scripts/materialize-apm-mirror.py github-build-or-reuse --check
```

To update the canonical mirror after reviewing a Renovate dependency PR:

```bash
cd dependencies/external-skills
apm lock
cd ../..
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

`dependencies/external-skills/apm-policy.yml` is fail-closed for the pilot. It allowlists the exact upstream package locator, requires pinned constraints and integrity hashes, denies package scripts, and does not implicitly trust self-defined/transitive MCPs.

The policy is deliberately scoped to the external-skill resolver. A future organization-wide APM policy should be evaluated separately rather than assuming this pilot policy is sufficient for every repository.

## Migration from scheduled direct sync

The existing scheduled `sync-upstream-skills.yml` remains active during the pilot. It should only be retired for an APM-managed mirror after all of the following are demonstrated:

1. Renovate detects a real newer stable release and opens a dependency PR.
2. The trusted lock-refresh path updates APM state to the intended immutable commit without deploying duplicate runtime copies.
3. Materialization from that lock reproduces the expected mirror exactly.
4. Existing skills validation, provenance checks, distribution generation and relevant behavioral/routing evals pass.
5. Rollback is proven by reverting the dependency/lock PR and rematerializing the previous lock.

Only then should the old direct-to-`main` synchronization path stop managing that mirror.
