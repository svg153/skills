# Cross-agent distribution manifests

`skills/` plus each skill's `metadata.yaml` remain the canonical catalog state.
The files listed below are compatibility/distribution surfaces and are generated;
they are not independent registries.

The catalog follows a **plugin-first, skill-canonical** model: Agent Plugins is the
preferred installable package boundary for coherent capabilities, while
`skills/<name>/SKILL.md` remains the canonical portable runtime behavior.

See [ADR 0002](adr/0002-plugin-first-distribution.md).

## Generate and verify

```bash
python -m pip install 'PyYAML>=6,<7'
python scripts/generate-distribution.py
python scripts/generate-distribution.py --check
```

`--check` is zero-write and exits non-zero when a generated file is missing or
stale. CI runs it on pull requests.

## Generated surfaces

| Surface | Role | Current policy |
| --- | --- | --- |
| `plugin.json` | Portable Agent Plugins v1 package | **Primary package boundary** |
| `skills/*/SKILL.md` | Portable Agent Skills | **Canonical runtime behavior; not an adapter** |
| `skills.sh.json` | Public discovery/install metadata | **Keep while it adds material reach** |
| `marketplace.json` | Generic marketplace compatibility | Keep until equivalent native distribution exists |
| `.agents/plugins/marketplace.json` | Agent-plugin marketplace compatibility | Keep until equivalent native distribution exists |
| `.codex-plugin/plugin.json` | Codex compatibility metadata | Candidate for retirement after native Agent Plugins parity |
| `.claude-plugin/plugin.json` | Claude Code compatibility metadata | Keep until native Agent Plugins parity |
| `.claude-plugin/marketplace.json` | Claude marketplace compatibility | Keep until native Agent Plugins parity |
| `.cursor-plugin/marketplace.json` | Cursor marketplace compatibility | Keep until native Agent Plugins parity |
| `gemini-extension.json` | Gemini CLI extension metadata | Keep until native Agent Plugins parity |

The bundle model remains useful for the catalog: Agent Plugins v1 discovers
skills from the fixed `skills/` directory, so adding a valid canonical skill does
not require a second hand-maintained per-skill registry. The generator still
incorporates canonical skill names into portable plugin discovery keywords,
which makes catalog additions observable to drift validation.

Independent capability plugins may also exist when they provide a meaningful
boundary: coherent multi-skill packaging, optional MCP composition, different
permissions/network surface, independent ownership, or an independent release
cadence. Do not create a plugin per skill mechanically.

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

## Adapter retirement policy

Host-specific generated files are compatibility adapters, not permanent
architecture. They may be deprecated and removed individually only after the
native Agent Plugins path clears the applicable parity gates:

1. installation works;
2. expected skills/components are discovered;
3. representative runtime behavior is verified on a named client/version/date;
4. version pinning and updates are practical;
5. MCP transport/auth works where the capability uses MCPs;
6. governance/policy controls remain sufficient;
7. lost marketplace/discovery reach is replaced or explicitly accepted.

A valid generated manifest alone is **not** runtime-parity evidence.

### skills.sh exception

`skills.sh.json` is evaluated separately because it primarily contributes
public discovery/install reach rather than a client runtime format. Keep it
until Agent Plugin-native discovery offers equivalent practical reach, or until
skills.sh directly consumes the portable Agent Plugins package. Removing a tiny
generated metadata file before then would save little and unnecessarily reduce
discoverability.

## MCP composition direction

Agent Plugins v1 defines optional MCP configuration at root `mcp.json`. A plugin
may compose existing remote or local MCP servers; the server does not need to be
implemented by the plugin author.

The catalog will add generated/validated optional MCP composition separately in
issue #35. Credentials remain client-managed and must not be embedded in
portable manifests.

## Compatibility policy

The portable `plugin.json` follows Agent Plugins v1.0.0:
https://agent-plugins.org/specification

Host-specific manifests remain generated from the same canonical configuration
only while they provide compatibility or distribution value. They should be
removed rather than maintained indefinitely once a host's native Agent Plugins
path satisfies the retirement gates above.

The layout and safety approach were informed by:
https://github.com/jongio/skills/tree/main/skills/create-skills-repo

We deliberately do not adopt its `.skills-repo/state.json` ownership model
because this repository already has provenance-aware lifecycle metadata and
generic upstream synchronization.
