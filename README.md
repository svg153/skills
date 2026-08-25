# Skills Library

Centralized Agent Skills library with origin tracking, reproducible upstream synchronization, and portable installation across compatible agents.

[![skills.sh](https://skills.sh/b/svg153/skills)](https://skills.sh/svg153/skills)

## Install with `npx skills`

The Vercel `skills` CLI discovers every valid `SKILL.md` in this public repository.

```bash
# Inspect the catalog
npx skills@latest add svg153/skills --list

# Install one skill
npx skills@latest add svg153/skills --skill github-build-or-reuse
npx skills@latest add svg153/skills --skill social-publishing

# Install globally for a specific agent
npx skills@latest add svg153/skills --skill social-publishing --agent codex --global
```

You can also pass the full GitHub URL or a direct path to one skill directory.

## skills.sh discovery

`skills.sh` and the `npx skills` CLI use the same Agent Skills ecosystem. There is no required GitHub label or topic that automatically enrolls a repository. Public skills become rankable through anonymous `npx skills add` install telemetry; search/index ingestion can lag behind successful CLI discovery.

This repository includes `skills.sh.json` for catalog grouping and CI exercises the `skills` CLI with telemetry disabled so validation does not inflate install counts.

## Structure

Each catalog entry normally contains:

```text
skills/<name>/
├── SKILL.md          # Portable Agent Skill
├── metadata.yaml     # Catalog provenance and lifecycle policy
├── templates/        # Optional reusable templates
├── scripts/          # Optional helpers
├── references/       # Optional specs/examples
└── assets/           # Optional supporting assets
```

`SKILL.md` is portable runtime behavior. `metadata.yaml` belongs to this catalog and is not required by the Agent Skills specification.

## Metadata and lifecycle

Example:

```yaml
name: skill-name
origin: https://github.com/original/repo
origin_path: skills/skill-name
origin_ref: latest-release
category: github
status: active
sync:
  enabled: true
  interval: weekly        # daily | weekly | monthly | manual
  strategy: download      # download | manual | local
  authoritative: upstream # upstream | local
  channel: stable         # optional catalog policy
tags:
  - agent-skills
```

### `download`

For an externally maintained skill whose upstream files should replace the catalog copy. Automatic sync requires all three:

```yaml
sync:
  enabled: true
  strategy: download
  authoritative: upstream
```

`origin_ref: latest-release` resolves only stable `vX.Y.Z` tags and deliberately ignores prereleases and unpublished `main` changes.

### `manual`

The catalog records the origin, but automation does not overwrite the local copy. Use this for skills that need curation, adaptation, or upstream layouts that cannot be mirrored safely.

### `local`

The skill is authored in this repository. No upstream synchronization applies.

## Upstream synchronization

There is no per-skill workflow anymore. The generic workflow scans metadata and invokes the same scripts for every eligible entry.

```bash
# Show all automatically managed upstream skills
./scripts/sync-upstreams.sh --list

# Sync every auto-managed skill now
./scripts/sync-upstreams.sh --all

# Sync only entries due for today's metadata interval
./scripts/sync-upstreams.sh --due

# Sync one download-managed skill
./scripts/sync-upstream-skill.sh github-build-or-reuse

# Non-destructively compare managed skills with their upstreams
./scripts/check-updates.sh
```

`.github/workflows/sync-upstream-skills.yml` runs daily. The metadata `interval` decides whether a skill is due; manual workflow dispatch processes every auto-managed skill.

## Why `sync-all.sh` is separate

`sync-all.sh` solves a different direction of synchronization:

```text
svg153/skills -> local Hermes runtime (/hermes-home/skills)
```

It pulls this repository and manages local symlinks. By contrast, `sync-upstream-skill.sh` and `sync-upstreams.sh` perform:

```text
external upstream -> svg153/skills catalog
```

Keeping those directions separate prevents a runtime-specific Hermes operation from becoming part of portable upstream lifecycle logic.

## Adding a skill

1. Create `skills/<name>/SKILL.md` with valid `name` and `description` frontmatter.
2. Add `metadata.yaml` for catalog provenance.
3. Add supporting files only when they materially help the skill.
4. Choose `local`, `manual`, or `download` lifecycle semantics deliberately.
5. Run repository validation and `npx skills@latest add . --list` before merging.
6. Submit a PR.

## Categories

| Category | Description |
| --- | --- |
| `software-development` | Coding patterns, frameworks, workflows |
| `devops` | Docker, CI/CD, infrastructure |
| `github` | GitHub workflows, PRs, reviews |
| `mlops` | ML operations, model serving, training |
| `creative` | Social, design, writing and content workflows |
| `data-science` | Data analysis, notebooks, visualization |
| `research` | Research and evidence gathering |
| `productivity` | Docs, presentations, spreadsheets |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md).
