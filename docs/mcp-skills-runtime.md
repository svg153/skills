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
2. do not silently shadow one origin;
3. retain origin/version/integrity evidence where the host exposes it;
4. keep the standalone path until the target clients prove equivalent discovery, activation and update behavior;
5. avoid catalog-side renaming solely to hide a runtime collision.

## Trust and hashes

Static MCP Skills manifests can advertise resource sizes and SHA-256 digests. These are useful for snapshot consistency and change detection.

They are not independent publisher attestation when the same server provides both the bytes and the digest. Continue to apply server-origin trust, host approval, permission and execution policy.

## Current pilots

### Planning / Atlassian

Tracked in #65 and parent #36.

- Move the plugin from Rovo MCP v1 to v2.
- Audit overlap between our cross-provider skills and Atlassian's provider-native v2 skills.
- Do not make the portable planning plugin depend on runtime MCP Skills until target clients actually support the extension.

### GitHub Stars MCP

Tracked in `svg153/github-stars-contrib-mcp-server#48`.

The Stars repository already owns four canonical skills tightly coupled to its MCP tools. It will be the reference implementation for:

- static skill manifests;
- `skills/list` and `skills/get`;
- lazy `resources/read`;
- hash/path/security tests;
- compatible-client evidence;
- standalone compatibility distribution from the same canonical source.

Lessons from that pilot must be fed back into #64 before this catalog treats the model as fully proven.

## References

- MCP Skills overview: https://modelcontextprotocol.io/extensions/skills/overview
- MCP Skills Working Group: https://github.com/modelcontextprotocol/ext-skills
- Agent Skills specification: https://agentskills.io/specification
- Agent Plugins specification: https://agent-plugins.org/specification
