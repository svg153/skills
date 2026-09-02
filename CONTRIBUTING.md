# Contributing to Skills Library

This repository is a portable Agent Skills catalog. Keep runtime behavior in each skill and keep catalog provenance/lifecycle policy in `metadata.yaml`.

## Adding a skill

1. Create `skills/<name>/SKILL.md` using lowercase kebab-case for both the directory and frontmatter `name`.
2. Add `metadata.yaml` with origin, category, status, tags, and deliberate lifecycle semantics.
3. Add only supporting files that materially help runtime behavior (`references/`, `scripts/`, `templates/`, `assets/`, evals, or platform metadata).
4. Add `agents/openai.yaml` when OpenAI/ChatGPT/Codex presentation metadata is useful; do not put private repository names, customer data, tokens, or secrets in public metadata.
5. Add `apm.yml` only when the skill should also be consumable as a standalone Microsoft APM dependency.
6. If the skill comes from another project, preserve attribution and verify that its license allows the intended reuse. Do not treat a public GitHub repository as permission to copy.
7. Add or update a catalog-owned behavioral suite under `evals/<name>/` when the skill is high-impact or changes behavior already protected by evals.
8. Run validation and submit a PR.

## Portable `SKILL.md`

Minimum shape:

```markdown
---
name: skill-name
description: "What the skill does and when an agent should use it."
license: MIT
---

# Skill Name

## Activation Contract

When this skill should run and important non-trigger cases.

## Hard Rules

Non-negotiable behavior, safety, evidence, and privacy constraints.

## Execution Steps

1. Do the work in the smallest reliable sequence.
2. Verify important claims and outputs.
3. Keep unknown facts explicitly unknown.

## Output Contract

Define what a successful response or artifact must contain.
```

`license` should describe the actual skill's terms. Imported or synchronized skills retain their upstream license; do not change it merely to match the catalog.

## `metadata.yaml`

Catalog metadata is not part of the Agent Skills runtime specification. It records provenance and update policy.

```yaml
name: skill-name
origin: https://github.com/original/repo
origin_path: skills/skill-name
origin_ref: latest-release
category: github
status: active
sync:
  enabled: true
  interval: weekly
  strategy: download
  authoritative: upstream
  channel: stable
tags:
  - agent-skills
```

### Lifecycle strategies

- **`local`** — authored and maintained in `svg153/skills`; no external sync.
- **`manual`** — an origin is recorded, but changes are curated rather than overwritten automatically.
- **`download`** — the external upstream is authoritative and the generic sync scripts replace the catalog copy. Automatic download entries must use `sync.enabled: true` and `authoritative: upstream`.

For stable external projects, prefer `origin_ref: latest-release` so the catalog follows stable `vX.Y.Z` releases instead of unpublished `main` changes.

There is intentionally no per-skill synchronization workflow. `.github/workflows/sync-upstream-skills.yml` reads these metadata fields and delegates to the generic `scripts/sync-upstreams.sh` / `scripts/sync-upstream-skill.sh` path.

## Distribution checks

Before merging a new or changed skill:

```bash
python -m pip install 'PyYAML>=6,<7'
python scripts/validate-skills.py
DISABLE_TELEMETRY=1 npx -y skills@latest add . --list
./scripts/sync-upstreams.sh --list
```

If an entry has `apm.yml`, also verify it can be consumed as the intended standalone APM package.

`npx skills` discovery working locally does not guarantee immediate ingestion by the external skills.sh search index. Do not generate artificial installs to influence ranking; use the upstream indexing process when search lags behind a valid repository.

## Behavioral evals

Catalog behavioral suites use Waza and live under `evals/<catalog-name>/`.

- Keep evals outside `skills/<name>/` for `download` + `authoritative: upstream` entries. The mirrored payload must remain replaceable by upstream synchronization.
- Every covered skill needs a positive trigger case and a negative/boundary case.
- Positive cases need a behavioral grader in addition to trigger selection.
- PR validation is deterministic and receives no model credential.
- Model-backed runs happen only from the trusted scheduled/manual workflow.
- Treat JSON/JUnit/transcript artifacts as regression evidence, not as a universal public quality score.

Run the repository contract validator before submitting eval changes:

```bash
python scripts/validate-evals.py
```

With Waza installed, also run deterministic spec coverage:

```bash
waza spec verify --skill skills/<name> --eval evals/<name>/eval.yaml
```

See `docs/evals.md` for credential setup, retained results, and local model-backed execution.

## Categories

Pick one most-specific catalog category. Current categories include:

- `software-development`
- `devops`
- `github`
- `mlops`
- `creative`
- `data-science`
- `research`
- `productivity`

## Review criteria

- [ ] `SKILL.md` has valid `name` and non-empty `description` frontmatter.
- [ ] The runtime name is unique across the catalog.
- [ ] The skill has an accurate license or a documented upstream licensing position.
- [ ] `metadata.yaml` records the real source and lifecycle policy.
- [ ] Imported content is attributable and legally reusable.
- [ ] Public files contain no secrets, private/customer data, or unnecessary private-repository references.
- [ ] Supporting files are relevant to the runtime skill rather than repository clutter.
- [ ] `npx skills` discovers the skill without parser skips.
- [ ] Automatic upstream entries use the generic sync mechanism; no new one-off workflow is introduced.
- [ ] Covered high-impact behavior has positive and negative/boundary eval cases.
