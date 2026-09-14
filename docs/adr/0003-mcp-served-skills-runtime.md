# ADR 0003: MCP-served Agent Skills as a runtime delivery surface

- Status: Accepted (validated by Stars reference pilot)
- Date: 2026-09-14
- Decision owners: `svg153/skills` maintainers
- Related: #33, #44, #64, `svg153/github-stars-contrib-mcp-server#48`

## Context

The catalog already separates four concerns that are easy to conflate:

1. **Agent Skills** define portable behavior in `SKILL.md` plus optional references, scripts, and assets.
2. **Agent Plugins** package coherent capabilities and may compose existing MCP servers.
3. **APM + Renovate** govern build-time consumption, locking, integrity, and review of external skill dependencies.
4. **MCP** provides runtime tools, resources, and provider access.

The official MCP Skills extension, `io.modelcontextprotocol/skills`, adds a fifth mechanism: a connected MCP server can advertise Agent Skills and let a compatible host discover them through `skills/list`, look them up through `skills/get`, and load their files lazily through standard MCP resources.

This does not create a new skill format. The served payload remains an Agent Skill. It changes the **runtime delivery and origin** of that payload.

## Decision

Treat MCP-served Skills as a first-class **runtime delivery surface**, not as a new source-of-truth format or a replacement for Agent Plugins/APM.

```text
                         canonical Agent Skill
                         SKILL.md + resources
                                |
          +---------------------+----------------------+
          |                     |                      |
          v                     v                      v
 filesystem / plugin       MCP runtime            external dependency
 distribution              delivery               governance
          |                     |                      |
 Agent Plugin /            skills/list            APM manifest + lock
 marketplace /             skills/get             Renovate review
 skills.sh                 resources/read
```

### Origin and delivery classes

| Class | Canonical owner | Delivery/update path | Typical use |
| --- | --- | --- | --- |
| `local/plugin` | this repository or capability package | repository -> Agent Plugin/marketplace/filesystem | cross-provider or locally authored behavior |
| `external/APM` | external upstream | Renovate -> APM lock/policy -> optional governed mirror | external standalone skill intentionally consumed or republished |
| `MCP-served/runtime` | connected MCP/provider | MCP connection -> `skills/list` / `skills/get` -> `resources/read` | provider-native behavior coupled to that server's tools/data |

A single canonical skill may intentionally have more than one **delivery** surface. For example, a provider may serve a skill through MCP and also publish the same skill as a standalone package for clients that do not support MCP Skills. That is acceptable only when both surfaces derive from the same canonical content rather than becoming independently edited copies.

## Source-of-truth rules

### One authoring location

Do not maintain two editable copies such as:

```text
provider-mcp/skills/foo/SKILL.md
svg153/skills/skills/foo/SKILL.md
```

when both claim to be the same behavior.

Choose one canonical owner. Any compatibility mirror must be reproducibly derived from an immutable upstream ref and retain provenance.

### Provider-native vs orchestration behavior

Prefer the provider/MCP as canonical owner when a skill exists mainly to teach an agent how to use that provider's tools correctly.

Keep behavior local when it is genuinely cross-provider or product-specific orchestration. A `planning` workflow that decides ownership across GitHub and Jira is not equivalent to a Jira-native backlog skill and should not move into the Atlassian MCP merely because Atlassian serves related skills.

## Identity and collisions

A skill name is not a sufficient global identity. Hosts and catalog integrations must preserve **origin + skill URI** (or equivalent provider identity) for MCP-served skills.

When a host sees both a standalone skill and an MCP-served skill with the same display name:

- do not silently shadow, concatenate, or merge one with the other;
- retain origin information in diagnostics/UI where available;
- if content is byte-identical, treat the copies as alternate delivery surfaces and activate only one;
- if content differs, surface an origin/version conflict instead of pretending equivalence;
- prefer explicit host/provider resolution rules over catalog-side guessing;
- do not auto-delete the standalone path until equivalent runtime discovery, activation, update, and governance behavior is proven for the target clients.

The catalog should not mirror an MCP-served skill merely to make names unique.

## Relationship to APM + Renovate

APM/Renovate remains the build-time/external dependency supply-chain authority described in #44.

An MCP-served skill is **not automatically an APM dependency**. Its runtime availability and freshness are governed by the connected MCP server and host.

Use APM only when this repository intentionally consumes or republishes a standalone/file artifact from an external owner, for example to provide a compatibility fallback for clients that cannot discover MCP Skills.

This yields separate planes:

```text
BUILD TIME / SUPPLY CHAIN
external standalone skill
  -> Renovate
  -> APM manifest + lock + policy
  -> optional governed catalog mirror

RUNTIME
connected MCP server
  -> skills/list
  -> skills/get
  -> resources/read
  -> host approval / activation
```

Neither plane should pretend to be the other one's update authority.

## Relationship to Agent Plugins

Agent Plugins remain the install/composition boundary for coherent capabilities. A plugin may:

- package local/orchestration skills;
- configure one or more MCP servers;
- coexist with provider-native skills later discovered from those MCP servers.

Installing a plugin that configures an MCP does not guarantee that every client will consume that server's MCP-served skills. Client support for the extension must be tested separately.

Therefore plugin-packaged fallback behavior must not be removed solely because the server advertises `io.modelcontextprotocol/skills`.

The Stars pilot additionally proved that a provider repository can expose the exact same root `skills/*` tree as a portable Agent Plugin fallback. A second generated or host-specific editable skill tree is unnecessary when the package format already discovers the canonical directory directly.

## Runtime trust and integrity

MCP Skills manifests can carry hashes and sizes for static resources. Treat these as snapshot/integrity evidence, not independent proof of publisher trust: the server supplies both the bytes and their advertised digest.

A host must continue to apply its own approval, tool-permission, code-execution, and origin policies. Reading a remote `SKILL.md` does not grant the skill authority to bypass the user's or application's existing mutation/safety boundaries.

Likewise, skill frontmatter such as `allowed-tools` remains metadata/instructions. The serving MCP must not reinterpret it as server-side authorization to expose or execute otherwise unauthorized tools.

## Repository policy

For `svg153/skills`:

- root and capability `SKILL.md` files remain canonical portable behavior where this repository owns the behavior;
- `distribution.config.json` remains package/MCP-composition configuration, not MCP-served skill metadata;
- `metadata.yaml` and APM state continue to govern catalog lifecycle/provenance for file-based catalog entries;
- provider-native MCP skills should normally remain at the provider and be consumed at runtime when the client supports the extension;
- a standalone fallback may be mirrored only when it adds real compatibility/discovery value and uses the existing immutable APM/Renovate path;
- host/runtime support claims require named client/version evidence and must distinguish MCP connection, MCP resource support, Skills discovery, lazy resource loading and actual skill activation.

## Stars reference-pilot validation

`svg153/github-stars-contrib-mcp-server#48` implemented the full sequence through child issues #49-#52 and validated the architectural decision with executable evidence.

### What the pilot proved

- The official MCP Python SDK 2.x extension primitives are sufficient for `io.modelcontextprotocol/skills`; no protocol fork or FastMCP wrapper was required.
- A repository-backed skill catalog can build deterministic static manifests containing exact SHA-256 digests and byte sizes, then serve only those authorized resources lazily through standard MCP Resources.
- Manifest drift must fail closed. Rebuilding the catalog after canonical bytes change produces new integrity metadata.
- Traversal, encoded traversal aliases, symlink escape, malformed frontmatter, unknown resource URIs and invalid/duplicate identities can be rejected before content crosses the MCP boundary.
- Optional `directoryRead` is not required for a complete static manifest model and can remain undeclared until a real need exists.
- Official SEP-2640 enumeration, manifest and directory-boundary scenarios from `modelcontextprotocol/conformance` pass against the real Stars Streamable HTTP server.
- Protocol conformance is not host activation. Structural/unit evidence, protocol round-trip, extension discovery, lazy resource loading and actual model-context activation remain separate evidence levels.
- A portable Agent Plugin can expose the same canonical root `skills/*` tree as the fallback for clients without MCP Skills support.
- No central mirror is needed merely because an MCP serves a skill. A future `MIRRORED_UPSTREAM` copy in this catalog must still justify discovery/install value and use the immutable #44 APM/Renovate path.

### Default implementation guidance derived from the pilot

For future provider integrations:

1. reuse official SDK extension/resource primitives before introducing adapters;
2. prefer static manifests and manifest-bound reads for repository/package-backed skills;
3. leave optional directory reads disabled unless the payload genuinely requires them;
4. preserve origin independently from name and digest;
5. keep authorization outside skill text/frontmatter;
6. maintain layered evidence and never infer host activation from conformance alone;
7. derive standalone/plugin fallback from the same canonical payload;
8. use APM only after an explicit build-time consumption/republishing decision;
9. fail visibly on duplicate-origin content conflicts rather than silently merging instructions.

## Pilot and migration sequence

1. [x] Document this boundary in the catalog (#64).
2. [x] Move the planning pilot to Atlassian Rovo MCP v2 and audit provider-native overlap (#65).
3. [x] Implement the extension in a server we control: `svg153/github-stars-contrib-mcp-server#48`.
4. [x] Prove discovery, lazy loading, integrity checks, security boundaries, and an official compatible inspection/conformance path separately.
5. [x] Prove a standalone compatibility path from the same canonical Stars skill source without manual duplication.
6. [x] Feed those implementation lessons back into #64 before closing it.
7. [ ] Consider upstream examples/proposals or adapter retirement only as separate evidence-driven follow-up work.

## Consequences

### Positive

- Keeps Agent Skills as the portable behavior contract.
- Lets provider-specific know-how travel with provider tools when clients support the extension.
- Avoids forcing APM into runtime MCP delivery.
- Avoids manually duplicated standalone and MCP copies.
- Gives Agent Plugins a cleaner orchestration role instead of making them own every provider-specific instruction.
- Provides a repeatable conformance/security pattern for future MCP-served skill providers.

### Costs

- Mixed client support requires dual delivery paths for some skills during the transition.
- Collision/origin handling becomes a host/runtime concern that must be observed rather than guessed away.
- Runtime MCP content can change independently from a plugin release, so compatibility evidence must state the server/client version/date.
- Passing protocol conformance still does not prove that a specific host injects and activates the skill in model context.

## References

- MCP Skills overview: https://modelcontextprotocol.io/extensions/skills/overview
- MCP Skills Working Group: https://github.com/modelcontextprotocol/ext-skills
- MCP conformance suite: https://github.com/modelcontextprotocol/conformance
- Agent Skills specification: https://agentskills.io/specification
- Agent Plugins 1.0 specification: https://agent-plugins.org/specification
- ADR 0002: `docs/adr/0002-plugin-first-distribution.md`
- Stars pilot evidence: https://github.com/svg153/github-stars-contrib-mcp-server/blob/main/docs/mcp-skills-evidence.md
- Stars standalone distribution: https://github.com/svg153/github-stars-contrib-mcp-server/blob/main/docs/skills-distribution.md
