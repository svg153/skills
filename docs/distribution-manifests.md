# Cross-agent distribution manifests

`skills/` plus each skill's `metadata.yaml` remain the canonical catalog state.
The files listed below are compatibility/distribution surfaces and are generated;
they are not independent registries.

## Generate and verify

```bash
python -m pip install 'PyYAML>=6,<7'
python scripts/generate-distribution.py
python scripts/generate-distribution.py --check
```

`--check` is zero-write and exits non-zero when a generated file is missing or
stale. CI runs it on pull requests.

## Generated surfaces

| Surface | Purpose | Registration model |
| --- | --- | --- |
| `plugin.json` | Portable Agent Plugins v1 package | Bundle; compliant clients discover every immediate `skills/*/SKILL.md` automatically |
| `marketplace.json` | Generic marketplace compatibility | One repository bundle |
| `.agents/plugins/marketplace.json` | Agent-plugin marketplace compatibility | One repository bundle |
| `.codex-plugin/plugin.json` | Codex compatibility metadata | `skills: ./skills/` |
| `.claude-plugin/plugin.json` | Claude Code compatibility metadata | `skills: ./skills/` |
| `.claude-plugin/marketplace.json` | Claude marketplace compatibility | One repository bundle |
| `.cursor-plugin/marketplace.json` | Cursor marketplace compatibility | One repository bundle |
| `gemini-extension.json` | Gemini CLI extension metadata | Repository bundle metadata |

The bundle model is intentional. Agent Plugins v1 discovers skills from the
fixed `skills/` directory, so adding a valid canonical skill does not require a
second hand-maintained per-skill registry. The generator still incorporates the
canonical skill names into portable plugin discovery keywords, which makes
catalog additions observable to drift validation.

## Source of truth

`distribution.config.json` stores repository-level package identity only:
package name, display name, version, author, repository URL and description.
It does **not** own skill provenance, update policy or synchronization.

Per-skill lifecycle remains in `skills/<name>/metadata.yaml`, including:

- upstream origin/path/ref;
- local/manual/download strategy;
- authority;
- synchronization interval/channel;
- category/status/tags.

The generator validates that every immediate `skills/` directory has both a
valid `SKILL.md` and `metadata.yaml`, that both declare the directory name, and
that case-insensitive identities do not collide.

## Compatibility policy

The portable `plugin.json` follows Agent Plugins v1.0.0:
https://agent-plugins.org/specification

Host-specific manifests are compatibility adapters. They are generated from the
same repository configuration and should be removed or changed when a host
standardizes on the portable Agent Plugins format rather than maintained as a
separate catalog.

The layout and safety approach were informed by:
https://github.com/jongio/skills/tree/main/skills/create-skills-repo

We deliberately do not adopt its `.skills-repo/state.json` ownership model
because this repository already has provenance-aware lifecycle metadata and
generic upstream synchronization.
