# External Agent Skill dependencies

This catalog separates **dependency consumption** from **catalog mirroring**. APM and Renovate manage external dependency state; they do not replace the catalog's provenance/lifecycle model or Agent Plugin distribution.

## Ownership model

| Catalog relationship | Authority | Update path |
| --- | --- | --- |
| `LOCAL` | `svg153/skills` | normal repository development |
| `CURATED_UPSTREAM` | local adaptation | human-reviewed upstream comparison; never automatically overwritten |
| `MIRRORED_UPSTREAM` | upstream payload | Renovate dependency PR + APM lock + catalog materialization + validators/evals |
| external dependency that is not republished | external package | consume through APM without copying into `skills/` |

`metadata.yaml` remains authoritative for provenance, ownership and synchronization semantics. `apm.yml` declares dependency coordinates; `apm.lock.yaml` records immutable resolution and integrity state; `apm-policy.yml` constrains trusted dependency behavior.

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

The APM project is intentionally isolated from the repository root. The catalog uses `apm lock`, not `apm install`, so lock resolution does not create `.agents/skills`, `.claude/skills`, or any other host-specific runtime copy. The committed lock records `deployments: []` for this resolver-only use case.

## Immutable manifest pins + Renovate

The pilot uses Renovate's native APM `pinDigests` support. A dependency is declared as an immutable commit while retaining the human release tag in a trailing comment:

```yaml
dependencies:
  apm:
    - ghspain/github-build-or-reuse/skills/github-build-or-reuse#24af1931681bb03b0282472c4d4b6900359418c7 # v1.2.3
```

Renovate's APM manager understands this form and tracks the tag comment while updating the commit digest, analogous to SHA-pinned GitHub Actions. This gives us an immutable manifest pin without inventing a second catalog lock format.

`apm.lock.yaml` still adds dependency resolution and content integrity evidence. For the current pilot it records the same commit as both `resolved_ref` and `resolved_commit`, plus the APM `content_hash`.

## Update flow

```text
upstream stable release
  -> Renovate native APM manager updates the digest + release-tag comment in apm.yml
  -> reviewed PR is opened; no automerge
  -> repository-owned `apm lock` refreshes apm.lock.yaml
  -> PR records exact resolved commit/content hash
  -> catalog materializer checks or applies that exact locked commit
  -> metadata.yaml is preserved
  -> normal catalog validation/evals run
  -> derived Agent Plugin / host distribution is regenerated as needed
```

Renovate is intentionally configured with `automerge: false`. An Agent Skill patch release can change agent instructions materially, so SemVer alone is not sufficient evidence for automatic merge.

## Why Renovate lockfile maintenance remains disabled here

Renovate's native APM manager currently refreshes artifacts for a package-file change through normal APM consumer semantics, where APM also owns deployed harness directories. This catalog deliberately uses APM only as a **dependency resolver and integrity lock**: the canonical runtime mirror remains `skills/<name>/` and the lock records `deployments: []`.

For that reason `renovate.json` keeps `lockFileMaintenance.enabled: false`. We do not create an artificial runtime target merely to make install/update-based artifact maintenance succeed, because doing so would reintroduce host-specific runtime copies and weaken the single-source-of-truth model.

A Renovate upstream change is being evaluated instead of growing permanent repository-specific update glue. Renovate PR #45683 already corrects APM lockfile-maintenance semantics for normal consumers and explicitly documents `apm lock --update` as the lock-only primitive; that mode is intentionally not used by default there because normal APM consumers need deployed harness files refreshed too. Our resolver-only catalog is the concrete use case for an opt-in lock-only path.

## Lock and mirror verification

CI uses checksum-verified Microsoft APM CLI **0.30.0** through `scripts/install-apm-ci.sh`. The version and Linux x86_64 release archive SHA-256 are centralized in that installer so workflows do not carry independent toolchain pins.

The current digest-pinned resolver path has been validated with APM 0.30.0 for:

- `apm lock`;
- `apm lock export --format cyclonedx`;
- `apm policy status --check`;
- `apm audit --ci --no-drift`;
- canonical mirror parity.

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
- supports both human refs and digest-pinned commit refs;
- when a human tag/ref is locked, verifies it still resolves to the exact locked commit and refuses moved tags;
- when a commit digest is locked, fetches exactly that immutable commit rather than treating the SHA as a branch name;
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

## Capability-scoped external components

Agent Plugin capabilities may also **embed** a selected APM dependency as a portable
skill while keeping APM as the only resolution/integrity authority. This is distinct
from a root-catalog `MIRRORED_UPSTREAM` entry.

The package declaration uses `externalSkillComponents` with an APM locator, runtime
target, license and attribution. It deliberately carries no independent version/ref/
digest. `scripts/apm_external_components.py` resolves the locator only through the
committed resolver policy + lock, checks the exact immutable commit, and materializes
the upstream skill subtree into the capability package.

Generated `external-components.json` records the resolved commit/content hash and
attribution for review/distribution, but is derived evidence rather than a lock.
`generate-capability-plugin.py --check` also compares the packaged payload to the
locked source so local edits cannot silently fork upstream instructions.

The generic mechanism is landed before enrolling design dependencies. In particular,
Phase 3 does **not** add Emil Kowalski or web-quality skills to the allowlist while
the first genuine hosted Renovate update proof in #46 is still pending.



## Migration from scheduled direct sync

The existing scheduled `sync-upstream-skills.yml` remains active during the pilot. It should only be retired for an APM-managed mirror after all of the following are demonstrated:

1. Renovate detects a real newer stable release and opens a dependency PR.
2. A trusted lock-refresh path updates APM state to the intended immutable commit without deploying duplicate runtime copies.
3. Materialization from that lock reproduces the expected mirror exactly.
4. Existing skills validation, provenance checks, distribution generation and relevant behavioral/routing evals pass.
5. Rollback is proven by reverting the dependency/lock PR and rematerializing the previous lock.
6. The entry is explicitly marked as APM-managed so the generic scheduled synchronizer skips only migrated mirrors.

Only then should the old direct-to-`main` synchronization path stop managing that mirror.
