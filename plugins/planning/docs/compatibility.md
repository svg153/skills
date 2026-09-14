# Planning plugin compatibility evidence

Compatibility claims are recorded by **evidence level**, not inferred from manifest shape.

Last updated: 2026-09-14.

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
| GitHub MCP through Copilot CLI | remote `https://api.githubcopilot.com/mcp/` | `copilot mcp list --json` reports the plugin-provided GitHub MCP enabled | `MCP discovery verified` ✅ |
| Atlassian Rovo MCP v2 through Copilot CLI | remote `https://mcp.atlassian.com/v2/mcp` | #65 CI run `34900475614`, step `Validate GitHub Copilot CLI marketplace, plugin and MCP discovery` | `MCP discovery verified` ✅ |
| OpenAI Codex CLI | `@openai/codex` 0.153.4, Node 22, GitHub Actions Ubuntu runner | repo-local `.agents/plugins/marketplace.json` exposes `planning`; `codex plugin add planning@svg153-skills` installs and enables the **portable root Agent Plugin** | `install/discovery verified` ✅ |
| GitHub MCP through Codex CLI | same portable `plugins/planning/mcp.json` | `codex mcp list --json` reports `github`, `streamable_http`, enabled | `MCP discovery verified` ✅ |
| Atlassian Rovo MCP v2 through Codex CLI | same portable `plugins/planning/mcp.json`, `https://mcp.atlassian.com/v2/mcp` | #65 CI run `34900475614`, step `Validate Codex CLI portable Agent Plugin and MCP discovery` | `MCP discovery verified` ✅ |
| VS Code / Copilot | current Agent Plugins-capable release | not executed in this repository yet | pending |
| ChatGPT / Codex connected-plugin runtime | current supported surface | install/runtime not executed from an authenticated account yet | pending |
| additional Agent Plugins client | TBD | not executed yet | pending |

### Historical Atlassian v1 evidence

Before #65, the package used `https://mcp.atlassian.com/v1/mcp/authv2`. Copilot CLI and Codex CLI both loaded that plugin-provided MCP configuration successfully. That evidence remains useful as historical proof of the packaging path, but it does **not** prove Rovo MCP v2 authentication, tool contracts, or end-to-end behavior.

Rovo MCP v2 changes the provider contract. Atlassian exposes a smaller primary tool set and reaches other operations through its `discover` / `execute` convention; its public v2 Agent Skills encode those provider-native details. See [`atlassian-v2-boundary.md`](atlassian-v2-boundary.md).

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
copilot plugin marketplace browse svg153-skills
copilot plugin install planning@svg153-skills
copilot plugin list
copilot mcp list --json
```

It requires the marketplace to expose `planning`, the installed-plugin list to contain `planning`, and the MCP list to contain both `github` and `atlassian` as plugin-provided servers.

The observed Copilot CLI MCP representation normalizes the Agent Plugins `streamable-http` transport to its runtime `http` representation while preserving the configured endpoint. Entries report:

- `sourcePlugin: planning`;
- `sourcePluginVersion: 0.1.0`;
- `source: plugin`;
- `enabled: true`.

Fresh #65 CI run `34900475614` completed the marketplace/plugin/MCP discovery step successfully with the v2 endpoint in the generated package. This establishes v2 **MCP discovery** only; it does not establish OAuth or successful provider tool calls.

## Codex CLI evidence

The same workflow pins:

- Node 22;
- `@openai/codex@0.153.4`;
- an isolated empty `CODEX_HOME`;
- the repository-local Codex marketplace at `.agents/plugins/marketplace.json`.

It executes:

```bash
codex plugin marketplace add .
codex plugin list --available --json
codex plugin add planning@svg153-skills --json
codex plugin list --json
codex mcp list --json
```

Observed installation state on the validated package path:

- `pluginId: planning@svg153-skills`;
- `version: 0.1.0`;
- `installed: true`;
- `enabled: true`;
- installed from `plugins/planning` into the isolated Codex plugin cache.

Most importantly, `plugins/planning` contains **no Codex-specific runtime manifest**. Codex 0.153.4 installs its root Agent Plugins 1.0 `plugin.json`, discovers the shared `skills/` tree, and translates the same portable `mcp.json` used by Copilot.

Fresh #65 CI run `34900475614` completed the Codex portable-plugin/MCP discovery step successfully with the Rovo v2 URL. Provider authentication remains a separate gate.

## Remaining runtime gates

### GitHub MCP

Capture on a real authenticated client:

1. plugin installed from the marketplace;
2. GitHub MCP discovered;
3. client-managed GitHub auth completed;
4. read-only tool call returns a known repository/issue/project state;
5. no credential is written into plugin configuration.

### Atlassian Rovo MCP v2

Capture on a real authenticated client with access to a test Jira site/project:

1. plugin installed from the marketplace and v2 endpoint discovered;
2. Atlassian OAuth 2.1 flow completed by the client;
3. read-only v2 tool call returns a known Jira project/backlog/issue;
4. non-primary operations use the provider's v2 `discover` / `execute` contract when required;
5. no OAuth token is written into plugin configuration.

Do not infer that a client can consume Atlassian's provider-native Agent Skills merely because it can connect to Rovo MCP v2. Runtime `io.modelcontextprotocol/skills` support is a separate capability and is tracked architecturally in #64.

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
