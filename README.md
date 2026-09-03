# SVG153 Skills

Cross-agent catalog of reusable Agent Skills with provenance-aware lifecycle management, reproducible upstream synchronization, behavioral evals, and generated distribution surfaces.

**Public catalog:** https://svg153.github.io/skills/

## Install

Inspect or install with the cross-agent `skills` CLI:

```bash
npx skills@latest add svg153/skills --list
npx skills@latest add svg153/skills --skill github-build-or-reuse
npx skills@latest add svg153/skills --skill social-publishing --agent codex --global
```

Selected entries can also be consumed as Microsoft APM packages. For example:

```bash
apm install svg153/skills/skills/social-publishing --target agent-skills
apm install --frozen
apm audit
```

## One source of truth, multiple consumers

Canonical state lives in:

```text
skills/<name>/SKILL.md       portable runtime behavior
skills/<name>/metadata.yaml  catalog provenance + lifecycle
skills.sh.json               curated grouping/discovery
```

The repository deterministically derives plugin/marketplace surfaces for Agent Plugins, Codex, Claude Code, Cursor, and Gemini. Generated manifests are outputs, not independent configuration.

```bash
python scripts/generate-distribution.py
python scripts/generate-distribution.py --check
```

## Lifecycle model

Every catalog entry has one explicit ownership mode:

| Ownership | Metadata | Meaning |
| --- | --- | --- |
| `LOCAL` | `strategy: local`, disabled, `authoritative: local` | Authored and maintained here. |
| `CURATED_UPSTREAM` | `strategy: manual`, disabled, `authoritative: local` | Upstream provenance retained, local adaptation authoritative. |
| `MIRRORED_UPSTREAM` | `strategy: download`, enabled, `authoritative: upstream` | Stable upstream payload can replace the local mirror. |

`origin_ref: latest-release` resolves only stable `vX.Y.Z` releases. It deliberately ignores prereleases and unpublished `main` changes.

Validate lifecycle state with:

```bash
python scripts/validate-metadata-lifecycle.py
python skills/skill-publish/scripts/metadata_repair.py check
```

## Add or register a skill

Use `skill-publish` as the normal path instead of manually touching every catalog surface.

1. Decide `LOCAL`, `MIRRORED_UPSTREAM`, or `CURATED_UPSTREAM`.
2. Prepare the spec described in `skills/skill-publish/references/creation-contract.md`.
3. Produce a zero-write plan:

```bash
python skills/skill-publish/scripts/catalog_skill.py plan --spec /path/to/spec.json
```

4. Review and approve the exact hash, then apply:

```bash
python skills/skill-publish/scripts/catalog_skill.py apply \
  --spec /path/to/spec.json \
  --approve <approval_hash>
```

The workflow handles canonical metadata, optional APM/eval scaffolding, skills.sh registration, derived manifests, collision checks and rollback on validation failure.

Legacy metadata can be normalized with the same approval boundary:

```bash
python skills/skill-publish/scripts/metadata_repair.py plan
python skills/skill-publish/scripts/metadata_repair.py apply --approve <approval_hash>
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for the manual/fallback contract.

## Upstream synchronization

Automatic synchronization is intentionally generic: no per-skill sync workflows.

```bash
./scripts/sync-upstreams.sh --list
./scripts/sync-upstreams.sh --all
./scripts/sync-upstreams.sh --due
./scripts/sync-upstream-skill.sh github-build-or-reuse
./scripts/check-updates.sh
```

`.github/workflows/sync-upstream-skills.yml` runs daily; each `MIRRORED_UPSTREAM` entry's metadata controls whether it is due.

## Behavioral evals

Catalog-owned behavioral suites live under `evals/<catalog-name>/` and use Waza. PR validation is deterministic and requires no model credential; trusted scheduled/manual runs execute model-backed suites and retain machine-readable evidence.

For upstream-authoritative mirrors, evals stay outside `skills/<name>/` so synchronization cannot overwrite catalog policy or imply upstream authorship.

See [docs/evals.md](docs/evals.md) and [ADR 0001](docs/adr/0001-behavioral-skill-evaluations.md).

## Public catalog

The GitHub Pages site is generated from canonical metadata, not maintained separately:

```bash
python scripts/generate-catalog.py --output /tmp/skills-catalog --base-path /skills
python scripts/validate-catalog.py --site-dir /tmp/skills-catalog --base-path /skills
```

Published at https://svg153.github.io/skills/.

## Optional Hermes integration

Hermes is a local consumer, not part of portable catalog lifecycle logic. Its helper therefore lives under `integrations/hermes/`:

```bash
./integrations/hermes/sync-all.sh full
```

This direction is separate from upstream synchronization:

```text
external upstream -> svg153/skills catalog -> local Hermes runtime
```

## External discovery

`npx skills` discovery and `skills.sh` search ingestion are separate concerns. CI runs `npx skills` with telemetry disabled and never generates artificial installs to influence ranking.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). Runtime behavior belongs in `SKILL.md`; catalog provenance/lifecycle belongs in `metadata.yaml`; generated distribution files must remain derived outputs.
