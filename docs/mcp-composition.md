# Agent Plugin MCP composition

Agent Plugins 1.0 defines optional MCP server configuration at plugin-root `mcp.json`. This catalog treats MCPs as a **package-level composition concern**, not as runtime instructions owned by an individual skill.

That distinction prevents one skill from silently making an MCP mandatory for every other skill in a catalog bundle.

## Canonical state

`distribution.config.json` may declare an optional `mcpServers` object. Each entry separates:

- `config` — the exact portable Agent Plugins server configuration that may be emitted to `mcp.json`;
- `provenance` — catalog-only trust/review metadata that is deliberately **not** emitted to the portable manifest.

Example:

```json
{
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
        "purpose": "Provide GitHub repository and planning tools required by the capability.",
        "reviewed": "2026-09-05"
      }
    }
  }
}
```

When no servers are configured, `mcp.json` is absent. When one or more servers are configured, `scripts/generate-distribution.py` deterministically emits:

```json
{
  "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
  "mcpServers": {
    "github": {
      "type": "streamable-http",
      "url": "https://api.githubcopilot.com/mcp/"
    }
  }
}
```

Provenance stays in canonical repository configuration so consumers receive only the standard portable shape.

## Supported transports

### `streamable-http`

Preferred for new remote MCP integrations.

- URL must be absolute HTTP(S).
- Non-loopback endpoints must use HTTPS.
- URL user information and fragments are rejected.
- Fixed non-secret headers are supported.
- Credential-bearing headers are rejected.

### `stdio`

Use when a capability intentionally depends on an existing local executable.

- `command` must be one bare executable token or a plugin-relative `./...` path.
- Shell command strings and absolute executable paths are rejected.
- `args`, `env`, and `cwd` support Agent Plugins `${PLUGIN_ROOT}` / `${PLUGIN_DATA}` semantics.
- `PLUGIN_ROOT` and `PLUGIN_DATA` cannot be overridden.
- Secret-like environment variable names are rejected because portable package data is not a credential mechanism.

### `sse`

Legacy compatibility only. New integrations should use Streamable HTTP.

A catalog entry using `sse` must provide `provenance.legacyReason` explaining why the deprecated transport remains necessary.

## Authentication

Agent Plugins 1.0 intentionally defines no portable OAuth configuration or credential reference.

Therefore:

- OAuth/PAT/API-key acquisition is client-managed;
- tokens and passwords must never be committed to `mcp.json`, `distribution.config.json`, fixed headers, or stdio `env`;
- an authorization failure affects that MCP server, not the independent skills or other MCP servers in the plugin.

This means a planning plugin can legitimately package knowledge plus connections to existing GitHub and Atlassian MCPs without implementing those servers or storing their credentials.

## Provenance contract

Each configured server requires:

| Field | Meaning |
| --- | --- |
| `kind` | `official`, `community`, or `local` |
| `owner` | Server/endpoint owner |
| `source` | HTTPS source repository or authoritative documentation |
| `purpose` | Why this capability needs the server |
| `reviewed` | ISO review date (`YYYY-MM-DD`) |
| `legacyReason` | Required only for `sse` |

The review date is evidence of inspection, not a guarantee that the remote endpoint can never change. Release/update workflows should re-check endpoint ownership and compatibility when MCP configuration changes.

## Failure boundaries

The Agent Plugins specification makes MCP failures non-fatal to independent components. The catalog preserves that model:

- invalid `mcp.json` must not invalidate valid Agent Skills;
- one invalid/unsupported server must not suppress other valid servers;
- connection/authentication failure must remain visible but must not make unrelated skills disappear.

Capability-specific skill instructions should define graceful degradation when a required provider is unavailable.

## Validation

Repository generation/CI validates the local policy before emitting `mcp.json`, including:

- supported transport and closed variant fields;
- remote HTTPS/loopback rules;
- command and path safety for stdio;
- no credential-like headers or environment variables;
- reserved Agent Plugins environment variables;
- server provenance and review date;
- explicit legacy justification for `sse`;
- shared Agent Plugins 1.0 schema version between `plugin.json` and `mcp.json`.

Run:

```bash
python scripts/generate-distribution.py
python scripts/generate-distribution.py --check
python -m unittest discover -s tests -p 'test_skill_publish*.py' -v
```

## Design boundary

Do not add `mcpServers` to individual skill lifecycle metadata merely because a skill can use a tool. Package MCP composition is justified only when the **installable capability contract** should carry that tool connection.

For optional host-native access paths, keep the skill portable and let the host supply its native connector/API instead of unnecessarily making one MCP endpoint part of the package.

The first intended end-to-end multi-MCP proof is the planning plugin tracked in #36.

## References

- Agent Plugins 1.0 specification: https://agent-plugins.org/specification
- MCP schema: https://agent-plugins.org/schemas/1.0.0/mcp.schema.json
