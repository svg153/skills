# Governed capability Agent Plugin creation contract

Use a capability package when several portable skills and/or a shared tool contract form one coherent installable unit. Do not create one plugin mechanically for every skill.

`skill-publish` treats capability creation as a deterministic repository transaction:

```text
temporary unregistered skill sources
        ↓
catalog_capability.py plan
        ↓
approval_hash
        ↓
catalog_capability.py apply
        ↓
plugins/<capability>/
├── distribution.config.json   # package source state
├── skills/*/SKILL.md          # canonical portable behavior
├── plugin.json                # generated
└── mcp.json                   # generated only when MCPs are declared
        ↓
root generated marketplaces
```

The JSON creation spec is temporary input. It must not become a competing repository authority.

## When to create a capability

Prefer a capability package when at least one of these is true:

- multiple skills must be installed and versioned together;
- the skills intentionally share one or more MCP connections;
- permissions/tooling/versioning form a meaningful package boundary;
- the capability has independent install/discovery value.

Keep an ordinary root `skills/<name>/` entry when no coherent package boundary exists.

## Canonical runtime rule

Capability skills become canonical under:

`plugins/<capability>/skills/<runtime-name>/SKILL.md`

`skill_sources` are **unregistered staging directories** used only for the approved transaction. They must not point at existing `skills/*` or `plugins/*` trees in this repository.

Do not copy an existing root catalog skill into a capability while leaving the root copy authoritative. A deliberate migration needs its own reviewed plan because it affects identity, discovery, eval paths and lifecycle.

The publisher rejects runtime-name collisions across both root catalog skills and existing capability skills.

## Spec

Every spec uses `schemaVersion: 1` and requires:

- `name`: capability package name, lowercase kebab-case;
- `version`: semantic package version;
- `description`;
- `author`: object with `name` and optional `url`;
- `license`;
- `keywords`: optional string list;
- `skill_sources`: one or more unregistered skill directories containing `SKILL.md`.

Optional:

- `repository`, defaulting to `https://github.com/svg153/skills`;
- `homepage`, defaulting to the capability path in this repository;
- `mcpServers`: governed package-level MCP composition using the same format as `distribution.config.json`.

Example:

```json
{
  "schemaVersion": 1,
  "name": "delivery-triage",
  "version": "0.1.0",
  "description": "Triage delivery work using portable workflow knowledge and GitHub tooling.",
  "author": {
    "name": "svg153",
    "url": "https://github.com/svg153"
  },
  "license": "MIT",
  "keywords": ["delivery", "triage"],
  "skill_sources": [
    "/tmp/delivery-triage",
    "/tmp/delivery-status"
  ],
  "mcpServers": {
    "github": {
      "config": {
        "type": "streamable-http",
        "url": "https://api.githubcopilot.com/mcp/"
      },
      "provenance": {
        "kind": "official",
        "owner": "GitHub",
        "source": "https://github.com/github/github-mcp-server",
        "purpose": "Read and manage GitHub delivery state.",
        "reviewed": "2026-09-09"
      }
    }
  }
}
```

## MCP composition

MCPs are package-level dependencies, never fields in a root skill lifecycle record.

The existing Agent Plugins MCP validator is reused during planning. It rejects unsafe transports/paths, credential-like headers or environment variables, invalid provenance, and unreviewed legacy SSE.

Authentication remains client-managed. Do not put PATs, OAuth tokens, API keys, cookies or Authorization headers in the spec or generated package.

No custom MCP is required merely because a capability uses tools. Prefer official/community MCPs when they already provide the needed capability.

## APM-locked external skill components

A capability may declare reviewed external skill payloads with `externalSkillComponents`.
The declaration contains **no version, ref, commit, or digest**: those values come only
from `dependencies/external-skills/apm.lock.yaml`.

```json
{
  "externalSkillComponents": [
    {
      "dependency": "owner/repo/skills/example",
      "target": "example",
      "license": "MIT",
      "attribution": "Upstream project / author"
    }
  ]
}
```

Rules:

- `dependency` must be exactly allowlisted by `apm-policy.yml` and resolve to exactly
  one committed APM lock entry.
- `target` is a runtime skill identity, not an arbitrary filesystem path.
- materialized `plugins/<capability>/skills/<target>/` payloads are derived artifacts;
  the declaration plus APM policy/lock remain the authority.
- `external-components.json` is generated provenance evidence recording the exact
  lock commit/content hash, license and attribution; it is not another lock.
- path traversal, symlink payloads, local/root/plugin identity collisions, missing
  locks, malformed hashes and unallowlisted dependencies fail closed.
- `--check` compares the materialized payload against the exact locked commit and
  detects manifest drift. Removing a declaration removes only a target previously
  recorded as externally managed.
- capability planning resolves lock evidence into the approval hash before mutation;
  lock or policy drift therefore invalidates the reviewed plan.



## Planning and approval

Create a zero-write plan:

```bash
python skills/skill-publish/scripts/catalog_capability.py plan \
  --spec /path/to/capability.json
```

Review:

- package name/version;
- canonical runtime skill identities;
- MCP list/provenance;
- every proposed source file;
- repository fingerprint;
- generated files;
- post-apply client checks.

Approve only the exact returned `approval_hash`.

Apply:

```bash
python skills/skill-publish/scripts/catalog_capability.py apply \
  --spec /path/to/capability.json \
  --approve <approval_hash>
```

Any relevant repository/runtime/source change requires a fresh plan.

## Transaction and rollback

Application stages the package first, then moves the complete capability root into `plugins/<name>/`.

It generates/checks the package and root distribution surfaces. If deterministic validation fails, the new capability is removed and previous generated root distribution files are restored.

`plugin.json`, `mcp.json`, root marketplaces and host adapters are generated outputs; never edit them as primary source state.

## Existing capability check

```bash
python skills/skill-publish/scripts/catalog_capability.py check \
  --name planning
```

Repository CI additionally uses:

```bash
python scripts/generate-capability-plugin.py --all --check
```

so every `plugins/*/distribution.config.json` participates in the structural gate automatically.

## Behavioral evals

Embedded capability skills may have catalog-owned Waza suites under `evals/<runtime-name>/`. The eval resolver supports canonical capability paths such as:

`plugins/<capability>/skills/<runtime-name>/SKILL.md`

Model-backed runs remain trusted/manual/scheduled evidence and do not replace authenticated provider runtime evidence.

## Discovery boundaries

- Agent Plugin marketplaces and package-local `npx skills` discovery expose capability packages.
- Root `skills.sh.json` remains a separate discovery surface for root catalog skills.
- Creating a capability does not silently move, remove or rewrite existing skills.sh registrations.
- Adapter retirement remains governed by runtime/update parity; package creation is not evidence that a host-specific adapter can be removed.
