# MCP-served Agent Skills

This document is the operational companion to [ADR 0003](adr/0003-mcp-served-skills-runtime.md). It explains how this catalog treats Agent Skills discovered from MCP servers through the official `io.modelcontextprotocol/skills` extension.

## Four different concerns

Do not collapse these mechanisms into one lifecycle:

| Concern | Mechanism | Owns |
| --- | --- | --- |
| Portable behavior | Agent Skills | `SKILL.md` and skill resources |
| Capability installation/composition | Agent Plugins | packaged skills + optional MCP connections |
| External file/package supply chain | APM + Renovate | immutable dependency refs, policy, reviewed updates |
| Provider/runtime access | MCP | tools, resources, provider data |
| Runtime skill discovery | MCP Skills extension | discovery and lazy delivery of provider-owned Agent Skills |

The MCP Skills extension changes **how a host obtains a skill at runtime**. It does not replace the Agent Skills format and does not automatically turn the remote skill into an APM dependency.

## Origin decision matrix

Use this matrix when deciding where a new skill belongs.

| Question | Preferred owner |
| --- | --- |
| Is the behavior mainly about using one MCP/provider correctly? | Provider/MCP repository |
| Does it orchestrate multiple providers or encode our product/workflow policy? | Local capability/plugin |
| Is it a third-party standalone skill we intentionally install or republish? | Upstream, consumed through APM/Renovate when governance is needed |
| Is the same provider skill available through MCP and standalone? | Keep one canonical upstream; treat the two forms as delivery surfaces |

Examples:

- Atlassian-specific Jira tool conventions belong naturally with Atlassian/Rovo MCP.
- Cross-provider `planning` behavior that chooses GitHub vs Jira ownership remains in `plugins/planning`.
- GitHub Stars contribution workflows that exist specifically to orchestrate the Stars MCP belong canonically in the Stars MCP repository.

## Runtime flow

A compatible host may use the extension approximately as follows:

```text
connect MCP server
      |
      v
server advertises io.modelcontextprotocol/skills
      |
      v
skills/list            discover metadata + resource manifest
      |
      +--> skills/get  direct lookup / refresh when needed
      |
      v
resources/read         load SKILL.md and other files lazily
      |
      v
host validation / approval / activation
```

`skills/get` is not necessarily a mandatory step after every `skills/list`; it supports authoritative direct lookup/refresh. Loading `SKILL.md` also does not grant permissions by itself. Host/tool/code-execution policy still applies.

## One canonical source, multiple deliveries

Allowed:

```text
provider repository
└── skills/foo/SKILL.md     canonical
       |
       +--> served by MCP
       +--> packaged standalone for legacy/non-supporting clients
```

Avoid:

```text
provider repository/skills/foo/SKILL.md    editable copy A
svg153/skills/skills/foo/SKILL.md           editable copy B
```

If this catalog republishes a compatibility copy, it should be materialized from an immutable upstream commit/release through the existing provenance/APM path, not copied manually.

## APM boundary

Use APM/Renovate when this repository has made a **build-time dependency decision** about an external file/package payload.

Do not use APM merely because a connected MCP advertises a skill at runtime.

```text
MCP runtime skill
  -> runtime origin/update semantics
  -> no automatic APM entry

Standalone external skill intentionally consumed here
  -> Renovate/APM lock/policy
  -> optional governed mirror/distribution
```

A skill can participate in both paths when a compatibility fallback is valuable, but they remain different planes.

## Collision and origin policy

For MCP-served skills, the display `name` is not a globally unique identity. Preserve the server origin and skill URI.

If a host sees both a standalone copy and an MCP-served form:

1. never assume same name means same bytes or same authority;
2. do not silently shadow, concatenate, or merge instruction bodies from different origins;
3. retain origin/version/integrity evidence where the host exposes it;
4. if the content is byte-identical, treat the two forms as delivery alternatives and activate only one;
5. if the content differs, surface an origin/version conflict instead of pretending they are equivalent;
6. keep the standalone path until the target clients prove equivalent discovery, activation and update behavior;
7. avoid catalog-side renaming solely to hide a runtime collision.

Not every host currently provides origin-aware deduplication. Until that behavior is proven on a named host/version, avoid enabling both forms of the same logical skill in one agent session.

## Trust and hashes

Static MCP Skills manifests can advertise resource sizes and SHA-256 digests. These are useful for snapshot consistency and change detection.

They are not independent publisher attestation when the same server provides both the bytes and the digest. Continue to apply server-origin trust, host approval, permission and execution policy.

`allowed-tools` and other skill metadata are also not server-side authorization. A server must not interpret skill text or frontmatter as permission to register, expose or invoke tools that its deterministic authentication/authorization policy would otherwise deny.

## Current pilots

### Planning / Atlassian

Tracked in #65 and parent #36.

- Planning now uses Atlassian Rovo MCP v2 rather than the legacy v1 endpoint.
- The provider-native overlap audit kept `planning` and `backlog-management` local because they own cross-provider GitHub/Jira orchestration.
- Jira/Rovo-native mechanics remain provider-owned and can be delegated to Atlassian Skills when target hosts prove MCP Skills support.
- The portable planning plugin does not yet depend on runtime MCP-served Atlassian Skills because client support remains mixed.

### GitHub Stars MCP — reference pilot proven

Tracked in `svg153/github-stars-contrib-mcp-server#48` and implemented through child issues #49-#52.

The pilot is now concrete evidence rather than an architectural hypothesis:

- the canonical four Stars skills remain only under the Stars repository's `skills/*` tree;
- the official MCP Python SDK 2.x `Extension`, `MethodBinding`, `ResourceBinding` and standard Resources primitives were sufficient to implement the extension; no custom protocol fork or FastMCP layer was required;
- `skills/list` and `skills/get` expose complete static manifests and `resources/read` loads exact skill bytes lazily;
- static resource manifests use SHA-256 plus byte size and fail closed when bytes drift after catalog construction;
- unsafe paths, encoded traversal aliases, symlink escapes, malformed frontmatter, unknown resources and duplicate/invalid identities fail closed;
- `directoryRead` was not needed for this static skill tree and remains intentionally undeclared;
- manifest `SKILL.md` Resource metadata uses the canonical skill `name` and `description`, matching the official SEP-2640 expectations;
- `allowed-tools` remains Agent Skills metadata and does not grant Stars server execution or mutation permissions;
- the official `modelcontextprotocol/conformance` SEP-2640 enumeration, manifest and directory-boundary scenarios pass against the real Streamable HTTP server;
- repository unit/quality gates and real SDK protocol round-trip tests pass separately from official conformance;
- protocol/discovery/resource evidence is explicitly separated from **actual host model-context activation**: levels 1-4 do not justify a level-5 activation claim;
- standalone compatibility uses the same root `skills/*` through an Agent Plugins v1 package instead of a second editable skill tree;
- a central `svg153/skills` mirror was deliberately **not** added merely because the skills are MCP-served. If republication later adds material discovery/install reach, it must use the existing immutable APM/Renovate mirror path from #44.

### Reusable policy derived from the Stars pilot

Use these defaults for future MCP Skills integrations unless evidence justifies an exception:

1. **Reuse the official SDK extension mechanism first.** Do not build a parallel method router or protocol adapter when the SDK already exposes extension methods/resources.
2. **Prefer static manifests for repository-backed skills.** Build the manifest once, serve only manifest-authorized resources, and fail closed on drift.
3. **Keep optional directory reads off until needed.** A complete static manifest plus normal Resources is simpler and passed the reference conformance suite.
4. **Treat hashes as consistency evidence, not identity.** Preserve provider/server origin independently.
5. **Treat skill metadata as instructions, not authorization.** Tool/auth policy remains deterministic and server/host-owned.
6. **Test evidence in layers.** Structural tests, MCP round-trips, extension discovery, lazy resource reads and host activation are different claims.
7. **Package fallback from the same source.** A standalone Agent Plugin may expose the exact canonical `skills/*` tree directly; do not generate host-specific editable copies.
8. **Add APM only for an intentional build-time dependency/republication decision.** MCP runtime discovery alone is not a reason to mirror a provider skill into this catalog.
9. **Do not merge duplicate origins silently.** Compare identity/origin/integrity and activate one delivery path or surface a conflict.

## References

- MCP Skills overview: https://modelcontextprotocol.io/extensions/skills/overview
- MCP Skills Working Group: https://github.com/modelcontextprotocol/ext-skills
- MCP conformance suite: https://github.com/modelcontextprotocol/conformance
- Agent Skills specification: https://agentskills.io/specification
- Agent Plugins specification: https://agent-plugins.org/specification
- Stars evidence: https://github.com/svg153/github-stars-contrib-mcp-server/blob/main/docs/mcp-skills-evidence.md
- Stars distribution policy: https://github.com/svg153/github-stars-contrib-mcp-server/blob/main/docs/skills-distribution.md
