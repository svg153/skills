# Repository-native skill creation contract

`skill-publish` treats registration as a deterministic repository transaction. The JSON spec is temporary input; it is not repository state and must not be committed as a competing authority.

## Common fields

Every spec uses `schemaVersion: 1` and requires:

- `name`: lowercase kebab-case catalog name;
- `ownership`: `LOCAL`, `MIRRORED_UPSTREAM`, or `CURATED_UPSTREAM`;
- `summary`: concise human-readable purpose;
- `use_for`: non-empty trigger/use-case phrases used for overlap detection and LOCAL description generation;
- `do_not_use_for`: explicit boundaries for authoring/eval design;
- `category`, `status`, and `tags`;
- `apm`: boolean;
- `evals`: boolean;
- `skills_sh_group`: exact existing grouping title or `null`;
- `allow_overlap_with`: explicit sibling catalog names when overlap is intentional.

When `evals` is true, also supply `eval_positive_prompt`, `eval_negative_prompt`, and `eval_behavior`.

## MCP composition is not a skill-registration field

Do **not** add MCP endpoints or credentials to a skill-publish spec or to `skills/<name>/metadata.yaml` merely because a skill can use those tools.

Agent Plugins MCP composition is a **package-level** concern. When an installable plugin intentionally carries one or more MCP connections, declare them in that package's `distribution.config.json` under optional `mcpServers`; `scripts/generate-distribution.py` validates the governed config and emits root `mcp.json`.

This separation prevents registering one skill from silently making an MCP mandatory for every other skill in the catalog bundle. Host-native connectors/APIs can remain optional access paths without being promoted into package dependencies.

See `docs/mcp-composition.md`.

## LOCAL

LOCAL skills are authored and authoritative in this repository. They require `license`, `author`, and a Markdown `body` beginning with a heading. Upstream fields are forbidden.

```json
{
  "schemaVersion": 1,
  "name": "example-local-skill",
  "ownership": "LOCAL",
  "summary": "Operate a distinct repository workflow safely.",
  "use_for": ["example repository operation"],
  "do_not_use_for": ["generic Git explanation"],
  "category": "github",
  "status": "active",
  "tags": ["agent-skills", "github"],
  "apm": false,
  "evals": true,
  "skills_sh_group": "GitHub & Open Source",
  "allow_overlap_with": [],
  "license": "MIT",
  "author": "svg153",
  "body": "# Example Local Skill\n\n## Activation Contract\n\nUse for the example operation.\n",
  "eval_positive_prompt": "Run the example repository operation for me.",
  "eval_negative_prompt": "Explain what a Git branch is.",
  "eval_behavior": "Pass only if the response follows the repository operation contract."
}
```

Generated lifecycle metadata uses `sync.enabled: false`, `strategy: local`, and `authoritative: local`.

## MIRRORED_UPSTREAM

Use this when upstream must remain authoritative and generic synchronization may replace every payload file except catalog-owned `metadata.yaml`. A regular local `source_dir` is required for the payload being registered; verify that it corresponds to the declared upstream/ref before planning.

```json
{
  "schemaVersion": 1,
  "name": "example-mirror",
  "ownership": "MIRRORED_UPSTREAM",
  "summary": "Mirror the stable upstream skill.",
  "use_for": ["example mirrored operation"],
  "do_not_use_for": ["locally divergent behavior"],
  "category": "software-development",
  "status": "active",
  "tags": ["agent-skills", "upstream"],
  "apm": false,
  "evals": true,
  "skills_sh_group": "Software Development",
  "allow_overlap_with": [],
  "source_dir": "/tmp/upstream/skills/example-mirror",
  "origin": "https://github.com/example/project",
  "origin_path": "skills/example-mirror",
  "origin_ref": "latest-release",
  "sync_interval": "weekly",
  "channel": "stable",
  "eval_positive_prompt": "Use the example mirrored operation.",
  "eval_negative_prompt": "Write a haiku.",
  "eval_behavior": "Pass only if the response follows the mirrored skill contract."
}
```

Generated lifecycle metadata uses `sync.enabled: true`, `strategy: download`, `authoritative: upstream`, plus the chosen interval/channel. Catalog behavioral evals remain under root `evals/` so upstream sync cannot overwrite them.

## CURATED_UPSTREAM

Use this when upstream is the provenance source but this repository intentionally owns future adaptation. `source_dir`, `origin`, and `origin_path` are required; `origin_ref` is optional but recommended for traceability. Automatic sync cadence/channel is forbidden.

```json
{
  "schemaVersion": 1,
  "name": "example-curated",
  "ownership": "CURATED_UPSTREAM",
  "summary": "Maintain a deliberate local adaptation of an upstream skill.",
  "use_for": ["example curated operation"],
  "do_not_use_for": ["automatic upstream mirroring"],
  "category": "research",
  "status": "active",
  "tags": ["agent-skills", "curated"],
  "apm": false,
  "evals": false,
  "skills_sh_group": "Research & Decisions",
  "allow_overlap_with": [],
  "source_dir": "/tmp/upstream/skills/example-curated",
  "origin": "https://github.com/example/project",
  "origin_path": "skills/example-curated",
  "origin_ref": "v1.2.3"
}
```

Generated lifecycle metadata uses `sync.enabled: false`, `strategy: manual`, and `authoritative: local`.

## Planning and approval

```bash
python skills/skill-publish/scripts/catalog_skill.py plan --spec /tmp/spec.json
```

The plan includes a repository fingerprint and hashes every proposed file. Its `approval_hash` binds normalized inputs and the current relevant repository state. Planning does not create the skill, evals, generated manifests, or registration entries.

After the exact plan is approved:

```bash
python skills/skill-publish/scripts/catalog_skill.py apply \
  --spec /tmp/spec.json \
  --approve <approval_hash>
```

`apply` recomputes the plan before writing. Any changed spec, relevant catalog state, new collision, or changed registration surface invalidates the previous hash.

## Validation contract

Successful application regenerates and checks derived distribution manifests, including optional package-level `mcp.json` when configured, validates skill frontmatter and catalog evals, validates `skills.sh.json`, and checks generic upstream selection. The report also lists client checks that must be executed before declaring the overall workflow complete:

- telemetry-disabled `npx skills` discovery;
- APM consumption when the skill is packaged for APM.

Repository CI additionally runs workflow-security checks, skill-publish unit tests, Agent Plugin MCP composition tests, catalog validation, Waza static verification, `npx skills` discovery, and the repository's APM smoke test.

A model-backed Waza run is evidence for behavior regression, not a universal quality score, and stays on the trusted scheduled/manual workflow defined by the catalog eval policy.

## Failure semantics

Planning fails before mutation for duplicate/case-insensitive names, runtime collisions, substantial unapproved trigger overlap, unknown overlap exceptions, unsafe upstream URLs/paths, ambiguous `skills.sh` groups, symlinks, existing destinations, or incomplete lifecycle fields.

During application, the new skill/eval roots and mutable derived registration surfaces are backed up or staged. A deterministic validation failure removes the new roots and restores the previous registration/generated content where practical.

Package-level MCP configuration failures are detected by distribution validation before a package can be considered clean. MCP credentials are never accepted as portable package data.
