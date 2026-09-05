# ADR 0002: Agent Plugin-first distribution with skill-canonical runtime

- Status: Accepted
- Date: 2026-09-05
- Decision owners: `svg153/skills` maintainers
- Related: #33, #34, `ghspain/github-build-or-reuse#28`

## Context

The catalog already publishes one canonical Agent Skill tree and derives several distribution surfaces: Agent Plugins 1.0, Codex, Claude Code, Cursor, Gemini and skills.sh metadata.

Agent Plugins 1.0 now provides a vendor-neutral package boundary for the two portable component types defined by the standard: Agent Skills and MCP server configuration. Compatible clients can discover supported components from the same package, while distribution, marketplaces, permissions and client-specific capabilities remain outside the portable core.

That creates an opportunity to reduce duplicated host packaging, but it does not make every existing distribution surface redundant at once. In particular, skills.sh currently contributes public discovery/install reach that is not equivalent to a generated host adapter.

## Decision

Adopt **plugin-first, skill-canonical** architecture.

```text
Agent Plugin package                 <- preferred installable capability boundary
├── plugin.json
├── skills/*/SKILL.md                <- canonical portable behavior
├── mcp.json                         <- optional reusable MCP composition
└── client-specific extensions       <- only when portable v1 cannot express a need

External distribution/discovery
├── skills.sh                         <- keep while it adds material reach
├── Codex adapter                     <- compatibility only
├── Claude adapter                    <- compatibility only
├── Cursor adapter                    <- compatibility only
└── Gemini adapter                    <- compatibility only
```

### Primary package is not the same as source of truth

The Agent Plugin becomes the preferred **package/install boundary** for coherent capabilities.

`skills/<name>/SKILL.md` remains the canonical source of portable runtime behavior. Plugin metadata, host adapters and marketplace files must not duplicate or override the skill instructions.

Per-skill provenance/lifecycle remains in `skills/<name>/metadata.yaml`.

### Capability-level plugins are preferred when they add a real boundary

Do not mechanically create one plugin per skill.

A capability-level plugin is justified when grouping provides at least one of:

- an independent install/version boundary;
- a coherent set of multiple skills;
- optional MCP composition required by the capability;
- materially different permissions/network surface;
- a distinct release cadence or ownership boundary.

The existing catalog-wide bundle remains useful as a catalog distribution surface. Independent capability plugins may coexist with it.

## Adapter retirement policy

A host-specific adapter can move from `keep` to `deprecate` and then `retire` only when the native Agent Plugins path satisfies all applicable parity gates.

### Parity gates

1. **Install** — users can install the same capability without the adapter.
2. **Discovery** — the client discovers the expected skills/components.
3. **Runtime** — representative behavior is verified on a named client/version/date.
4. **Update/versioning** — pinned and upgrade paths are practical and documented.
5. **MCP/auth** — when the capability uses MCPs, supported transports and authentication work without leaking credentials.
6. **Governance** — enterprise/client policy controls remain equivalent enough for the target users.
7. **Reach** — any lost marketplace/discovery exposure is either replaced or explicitly accepted.

A generated manifest being syntactically valid is not sufficient evidence for retirement.

## Current adapter status

| Surface | Status | Retirement condition |
| --- | --- | --- |
| `plugin.json` | **primary** | Portable package contract; do not retire while Agent Plugins 1.x is the chosen standard |
| `skills/*/SKILL.md` | **canonical** | Runtime source, not an adapter |
| `skills.sh.json` | **keep** | Reassess only when equivalent practical discovery/install reach exists or skills.sh consumes Agent Plugins directly |
| `.codex-plugin/plugin.json` | **keep / candidate for first retirement** | Retire after native Agent Plugins install + runtime + update parity in Codex |
| `.claude-plugin/*` | **keep** | Retire after native Agent Plugins parity in Claude Code |
| `.cursor-plugin/*` | **keep** | Retire after native Agent Plugins parity in Cursor |
| `gemini-extension.json` | **keep** | Retire after native Agent Plugins parity in Gemini CLI |
| `marketplace.json` / `.agents/plugins/marketplace.json` | **keep** | Retire or reshape only after marketplace/distribution behavior has an equivalent native path |

## skills.sh is a separate decision

`skills.sh.json` is not treated like a host runtime adapter. Its value is primarily discovery/install reach.

Removing it today would save little maintenance because it is generated/validated metadata, while it could reduce discoverability. It therefore has a stricter retirement criterion: equivalent practical reach must be demonstrated, not merely manifest compatibility.

## MCP composition

Plugin-first distribution makes optional `mcp.json` composition a first-class design option. This does **not** imply writing custom MCP servers. A plugin may configure existing remote or local MCP servers and keep authentication client-managed.

Detailed generation, validation and security rules are tracked in #35.

## Consequences

### Positive

- One coherent package can carry behavior and tool configuration.
- Host-specific packaging becomes disposable compatibility glue rather than architecture.
- Versioning can align skill behavior and MCP composition.
- Client adoption can be measured before old surfaces are removed.
- skills.sh discovery remains protected during the transition.

### Costs

- For a transition period, several generated surfaces remain.
- Runtime compatibility must be tested per client; schema compatibility is insufficient.
- Marketplace/discovery remains partly ecosystem-specific in Agent Plugins 1.0.

## Migration sequence

1. Finish the `github-build-or-reuse` Agent Plugins pilot.
2. Make this plugin-first policy authoritative in catalog documentation and generation guidance.
3. Add reusable `mcp.json` composition support (#35).
4. Prove a multi-MCP planning capability (#36).
5. Record native runtime parity per host.
6. Deprecate and retire host adapters individually when all relevant gates pass.
7. Reassess skills.sh last.

## References

- Agent Plugins 1.0 specification: https://agent-plugins.org/specification
- GitHub Agent Plugins 1.0 announcement/support: https://github.blog/changelog/2026-08-12-agent-plugins-1-0-in-vs-code-copilot-cli-and-the-copilot-app/
