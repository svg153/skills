# Planning Agent Plugin

A portable Agent Plugins 1.0 capability for planning and backlog management across **GitHub and Jira** without introducing a third project-management database.

The plugin packages:

```text
plugins/planning/
├── plugin.json
├── mcp.json
├── distribution.config.json
├── docs/compatibility.md
└── skills/
    ├── planning/
    │   ├── SKILL.md
    │   └── references/provider-contract.md
    └── backlog-management/
        ├── SKILL.md
        └── references/operations.md
```

## Why this exists

Existing tools already solve the provider access problem:

- GitHub provides its official remote MCP server;
- Atlassian provides the official Rovo MCP server for Jira/Confluence;
- project-management tools such as Agents Board and AgentPM demonstrate that planning behavior + MCP tooling can form a coherent agent capability.

This plugin deliberately does **not** build another board, database, GitHub wrapper, or Jira wrapper. Its differentiating layer is provider-neutral planning/orchestration while GitHub/Jira remain the systems of record.

## Skills

### `planning`

Turns a new initiative/feature/migration into a dependency-aware work graph, chooses an authoritative provider per work item, and optionally persists the authorized plan.

### `backlog-management`

Reads, triages, links, prioritizes, and updates existing GitHub/Jira backlog state without taking over code implementation.

The split is intentional: planning new work and operating an existing backlog have different activation boundaries. Repository implementation/PR/release work should be handed to delivery capabilities such as `github-repo-autopilot` rather than duplicated here.

## MCP composition

`mcp.json` composes existing official servers:

| Server | Transport | Endpoint | Auth |
| --- | --- | --- | --- |
| GitHub MCP | Streamable HTTP | `https://api.githubcopilot.com/mcp/` | Client-managed GitHub OAuth/PAT flow |
| Atlassian Rovo MCP | Streamable HTTP | `https://mcp.atlassian.com/v1/mcp/authv2` | Client-managed OAuth 2.1 |

No credentials are committed. `distribution.config.json` records endpoint provenance/purpose/review metadata; generated `mcp.json` contains only the portable Agent Plugins shape.

## Install / test with GitHub Copilot CLI

Copilot CLI supports installing a plugin from a GitHub repository subdirectory:

```bash
copilot plugin install svg153/skills:plugins/planning
```

For local development:

```bash
copilot plugin install ./plugins/planning
copilot plugin list
```

Authentication is completed through the client/provider flow. Installing this repository does not grant GitHub or Atlassian access by itself.

CI verifies the local package with a pinned Copilot CLI and requires `planning` to appear in `copilot plugin list`. See [`docs/compatibility.md`](docs/compatibility.md) for the client/version/evidence matrix.

## Degraded operation

The skills are independent from either MCP server:

| GitHub | Jira | Behavior |
| --- | --- | --- |
| available | available | Cross-provider planning with one authoritative provider per work item |
| available | unavailable | GitHub-backed work continues; Jira-owned persistence is reported blocked |
| unavailable | available | Jira-backed work continues; GitHub-owned persistence is reported blocked |
| unavailable | unavailable | Plan/advisory mode only; no claims about current provider state |

A provider failure must not silently move its records into the remaining provider or cause unrelated skills to disappear.

## Mutation boundary

Read-only discovery/planning is preferred first. External mutations occur only when the user explicitly asked to create/update planning records.

Once the user has given that scoped instruction, the skills should execute it without adding redundant confirmation prompts for every ticket. Provider-returned identifiers are retained for subsequent links and relationships.

## Source-of-truth rule

Do not create GitHub/Jira twins for the same mutable work item unless the user explicitly requires mirroring **and** a synchronization mechanism exists.

Recommended cross-provider pattern:

```text
JIRA-123    program/customer/organizational record
   |
   +----> GH #456   repository implementation work
   +----> GH #457   another implementation slice
```

Cross-links are traceability, not implicit synchronization.

## Generate and validate

The package manifests are derived from `distribution.config.json` and the local `skills/` tree:

```bash
python scripts/generate-capability-plugin.py \
  --config plugins/planning/distribution.config.json

python scripts/generate-capability-plugin.py \
  --config plugins/planning/distribution.config.json \
  --check
```

Repository CI also validates skill frontmatter, MCP security/provenance policy, generated-manifest drift, cross-agent skill discovery, and Copilot CLI plugin installation.

## Status

This is an **experimental pilot** for `svg153/skills#36`.

- Agent Plugins/Agent Skills conformance: verified.
- `npx skills` discovery: verified.
- GitHub Copilot CLI 1.0.83 install/discovery: verified in CI.
- GitHub MCP authenticated tool call: pending.
- Atlassian MCP authenticated tool call: pending.
- end-to-end cross-provider mutation scenario: pending.

Do not treat install/discovery evidence as proof that every client can authenticate to both remote MCP servers. Runtime evidence is recorded separately per client and version in [`docs/compatibility.md`](docs/compatibility.md).

## References

- Agent Plugins 1.0: https://agent-plugins.org/specification
- GitHub MCP Server: https://github.com/github/github-mcp-server
- GitHub MCP setup: https://docs.github.com/en/copilot/how-tos/provide-context/use-mcp-in-your-ide/set-up-the-github-mcp-server
- Atlassian Rovo MCP: https://support.atlassian.com/atlassian-ai-gateway/docs/use-rovo-mcp-with-other-supported-mcp-clients/
- Pilot issue: https://github.com/svg153/skills/issues/36
