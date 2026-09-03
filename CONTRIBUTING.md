# Contributing to SVG153 Skills

This repository is a portable Agent Skills catalog. Keep runtime behavior in each skill and keep catalog provenance/lifecycle policy in `metadata.yaml`.

Before contributing, read [GOVERNANCE.md](GOVERNANCE.md), [NOTICE.md](NOTICE.md), and [SECURITY.md](SECURITY.md). Security-sensitive reports do not belong in normal public issues.

## Preferred path: `skill-publish`

For a new or newly registered skill, use the repository-native transactional workflow instead of editing all surfaces manually.

1. Search the existing catalog for overlapping names, triggers and use cases.
2. Choose exactly one ownership mode: `LOCAL`, `MIRRORED_UPSTREAM`, or `CURATED_UPSTREAM`.
3. Build the spec described in `skills/skill-publish/references/creation-contract.md`.
4. Run a zero-write plan and review its `approval_hash`:

```bash
python skills/skill-publish/scripts/catalog_skill.py plan --spec /path/to/spec.json
```

5. Apply only that unchanged approved plan:

```bash
python skills/skill-publish/scripts/catalog_skill.py apply \
  --spec /path/to/spec.json \
  --approve <approval_hash>
```

6. Run the reported client checks and submit a PR.

For lifecycle cleanup of existing entries, use:

```bash
python skills/skill-publish/scripts/metadata_repair.py plan
python skills/skill-publish/scripts/metadata_repair.py apply --approve <approval_hash>
```

## Manual fallback

Manual registration remains supported when developing or repairing the tooling itself:

1. Create `skills/<name>/SKILL.md` using lowercase kebab-case for directory and runtime name unless a documented catalog/runtime identity distinction is required.
2. Add `metadata.yaml` with real provenance and explicit lifecycle semantics.
3. Add only supporting files that materially help runtime behavior (`references/`, `scripts/`, `templates/`, `assets/`).
4. Add `agents/openai.yaml` only when presentation metadata is useful and public-safe.
5. Add `apm.yml` only when the skill should be independently consumable through APM.
6. Add/update a catalog-owned Waza suite under `evals/<catalog-name>/` for high-impact behavior.
7. Regenerate distribution manifests from canonical state; never patch generated manifests independently.

## Lifecycle semantics

### `LOCAL`

```yaml
sync:
  enabled: false
  interval: manual
  strategy: local
  authoritative: local
```

Use only for skills authored and maintained in this catalog. Local entries use `origin: https://github.com/svg153/skills` and `origin_path: skills/<name>`.

### `CURATED_UPSTREAM`

```yaml
sync:
  enabled: false
  interval: manual
  strategy: manual
  authoritative: local
```

Use when upstream provenance matters but local adaptation is authoritative. Manual is **not** an enabled synchronization mode.

### `MIRRORED_UPSTREAM`

```yaml
origin_ref: latest-release
sync:
  enabled: true
  interval: weekly
  strategy: download
  authoritative: upstream
  channel: stable
```

Use when generic synchronization may replace the mirrored payload. Keep catalog-specific evals outside the mirrored directory.

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
...
```

Imported or synchronized skills retain their real license; a public repository is not permission to copy incompatible content. The root repository license never overrides a more specific skill or upstream license; see [NOTICE.md](NOTICE.md).

## Validation

Before merging:

```bash
python -m pip install 'PyYAML>=6,<7'
python scripts/validate-workflow-security.py
python scripts/validate-skills.py
python scripts/validate-metadata-lifecycle.py
python skills/skill-publish/scripts/metadata_repair.py check
python scripts/generate-distribution.py --check
python scripts/validate-evals.py
DISABLE_TELEMETRY=1 npx -y skills@latest add . --list
./scripts/sync-upstreams.sh --list
```

If an entry has `apm.yml`, also verify its standalone APM consumption path.

## Behavioral evals

Waza suites live under `evals/<catalog-name>/`.

- Include positive and negative/boundary cases.
- Positive cases need behavioral grading, not only trigger selection.
- PR checks are deterministic and secret-free.
- Model-backed runs execute only from trusted repository state.
- For upstream-authoritative mirrors, upstream owns intrinsic behavior; catalog evals should focus on integration/routing concerns.
- Preserve raw JSON/JUnit/transcript evidence; do not publish a context-free universal quality score.

The framework selection evidence is preserved in `docs/adr/0001-behavioral-skill-evaluations.md`; obsolete comparison prototypes are not production inputs.

## Review criteria

- `SKILL.md` has valid, unique runtime frontmatter.
- `metadata.yaml` records real provenance and one valid lifecycle mode.
- Imported content is attributable and legally reusable.
- Public files contain no secrets/customer/private repository data.
- Generated distribution surfaces are current.
- `npx skills` discovers the skill without parser skips.
- Automatic upstream entries use only the generic synchronization mechanism.
- High-impact behavior has appropriate Waza coverage.
