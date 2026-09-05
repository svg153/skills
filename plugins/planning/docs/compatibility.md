# Planning plugin compatibility evidence

Compatibility claims are recorded by **evidence level**, not inferred from manifest shape.

Last updated: 2026-09-05.

## Evidence levels

| Level | Meaning |
| --- | --- |
| `conformance` | Package/manifests pass deterministic local/spec validation |
| `install/discovery verified` | A named client/version installs the plugin and discovers it/its skills |
| `MCP discovery verified` | The named client loads the declared MCP server configuration from the plugin |
| `authenticated tool call verified` | Provider auth succeeds and at least one real tool call returns provider state |
| `end-to-end verified` | A representative planning workflow crosses skills + provider tools successfully |

Do not promote a lower evidence level to a stronger claim.

## Current matrix

| Surface | Version / environment | Evidence | Status |
| --- | --- | --- | --- |
| Agent Plugins package | Agent Plugins 1.0.0 | `plugin.json` + `mcp.json` deterministic generation and policy tests | `conformance` ✅ |
| Agent Skills | pinned `agentskills/skills-ref` validation | both `planning` and `backlog-management` validate | `conformance` ✅ |
| `npx skills` | `skills@latest`, telemetry disabled | both packaged skills discovered from `plugins/planning` | `install/discovery verified` ✅ |
| GitHub Copilot CLI | `@github/copilot` 1.0.83, Node 22, GitHub Actions Ubuntu runner | repository marketplace exposes `planning`; `planning@svg153-skills` installs and `copilot plugin list` discovers it | `install/discovery verified` ✅ |
| GitHub MCP through Copilot CLI | remote `https://api.githubcopilot.com/mcp/` | `copilot mcp list --json` reports `sourcePlugin: planning`, version `0.1.0`, enabled | `MCP discovery verified` ✅ |
| Atlassian Rovo MCP through Copilot CLI | remote `https://mcp.atlassian.com/v1/mcp/authv2` | `copilot mcp list --json` reports `sourcePlugin: planning`, version `0.1.0`, enabled | `MCP discovery verified` ✅ |
| VS Code / Copilot | current Agent Plugins-capable release | not executed in this repository yet | pending |
| Codex / ChatGPT plugin path | current supported surface | not executed in this repository yet | pending |
| additional Agent Plugins client | TBD | not executed yet | pending |

## Copilot CLI evidence

Repository workflow: `.github/workflows/capability-plugin-validate.yml`.

The CI check pins:

- Node 22;
- `@github/copilot@1.0.83`;
- the plugin source to the checked-out repository marketplace.

### Marketplace-first installation

An earlier direct-install smoke test succeeded but Copilot CLI 1.0.83 emitted this product warning:

> Direct plugin installs are deprecated; future releases will support marketplace installs only.

The repository therefore moved the durable validation path to the marketplace immediately rather than normalizing a deprecated install route.

The current test executes:

```bash
copilot plugin marketplace add .
copilot plugin marketplace browse svg153-skills --json
copilot plugin install planning@svg153-skills
copilot plugin list
copilot mcp list --json
```

It requires the marketplace to expose `planning`, the installed-plugin list to contain `planning`, and the MCP list to contain both `github` and `atlassian` as plugin-provided servers.

The observed Copilot CLI MCP representation normalizes the Agent Plugins `streamable-http` transport to its runtime `http` representation while preserving the configured endpoint. Both entries report:

- `sourcePlugin: planning`;
- `sourcePluginVersion: 0.1.0`;
- `source: plugin`;
- `enabled: true`.

This proves the package is accepted by a real Copilot CLI plugin loader **and** that its two MCP configurations are loaded from the plugin. It does **not** prove provider authentication because the workflow intentionally has only `contents: read` permission and no user/provider credentials.

## Remaining runtime gates

### GitHub MCP

Capture on a real authenticated client:

1. plugin installed from the marketplace;
2. GitHub MCP discovered;
3. client-managed GitHub auth completed;
4. read-only tool call returns a known repository/issue/project state;
5. no credential is written into plugin configuration.

### Atlassian Rovo MCP

Capture on a real authenticated client with access to a test Jira site/project:

1. plugin installed from the marketplace;
2. Atlassian MCP discovered;
3. OAuth 2.1 flow completed by the client;
4. read-only tool call returns a known Jira project/backlog/issue;
5. no OAuth token is written into plugin configuration.

### End-to-end cross-provider scenario

The final pilot scenario should use non-sensitive test data and prove:

1. `planning` reads relevant state from GitHub and Jira;
2. it proposes a work graph with one authoritative provider per mutable work item;
3. cross-provider records are linked rather than duplicated;
4. a user explicitly authorizes a scoped mutation;
5. at least one provider mutation succeeds and its returned ID is retained;
6. the result includes degraded/unverified state if the second provider operation cannot complete.

## Security boundary

Do not add CI secrets merely to turn these rows green. Authenticated runtime tests belong in a trusted/manual environment with least-privilege test accounts or provider-approved CI auth. The portable plugin must remain free of PATs, OAuth tokens, API keys, passwords, and credential-bearing headers.
