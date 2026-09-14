---
name: mcp-skills-provider
description: "Expose canonical Agent Skills from an MCP server through io.modelcontextprotocol/skills without creating a second behavior source of truth. Use when adding or auditing provider-side skills/list, skills/get, resources/read, manifest integrity, security boundaries, official conformance, evidence levels, and standalone fallback for mixed-client support."
---

# MCP Skills Provider

Implement Skills over MCP as a **delivery surface for existing canonical Agent Skills**, not as a second skill format, a second editable behavior tree, or a shortcut around authorization.

Use this skill when adapting an MCP server to `io.modelcontextprotocol/skills`, reviewing an existing server implementation, or designing the provider-side conformance/security evidence.

Do **not** use it for ordinary Agent Skill authoring with no MCP delivery requirement, for generic MCP server creation, or for client/host activation implementation. Protocol conformance alone never proves that a model-facing host will discover, select, load, and follow the served skill.

## Activation contract

When this skill applies, produce an implementation plan and evidence trail that preserves these separate concerns:

| Concern | Authority |
| --- | --- |
| Portable behavior | canonical `SKILL.md` + resources |
| MCP runtime delivery | connected provider/server |
| Host activation | client/host implementation and model behavior |
| Standalone compatibility | Agent Plugin/filesystem/package derived from the same canonical bytes |
| External build-time dependency governance | APM/Renovate or equivalent, only when intentionally consumed/republished |
| Tool authorization | deterministic server/host auth policy, never skill prose/frontmatter |

## Reuse-first discovery

Before writing protocol code:

1. Inspect the repository's current MCP SDK/version and server composition model.
2. Check the **current official MCP Skills extension documentation**, the official SDK's extension/resource primitives, and the official MCP conformance repository.
3. Search public implementations relevant to the language/framework. Prefer a maintained official SDK helper or extension abstraction over a custom router.
4. Reuse the repository's existing resource, URI, pagination, error, packaging, logging, and test infrastructure.
5. Record what is reused and what gap, if any, requires local adapter code.

Do not copy the Stars reference implementation mechanically. Its reusable lessons are the boundaries and evidence model; the target server's SDK/framework remains authoritative for implementation details.

## 1. Establish canonical ownership

Inventory every skill the server intends to expose:

- canonical root/directory;
- `SKILL.md` frontmatter `name` and `description`;
- supporting references/scripts/assets;
- whether the skill is provider-native or cross-provider orchestration;
- standalone delivery surfaces already in use.

Prefer provider ownership when the behavior mainly teaches correct use of that provider's tools/data. Keep genuinely cross-provider or product-policy orchestration with the capability that owns that orchestration.

Reject a design that creates independently editable copies such as:

```text
provider-server/skills/foo/SKILL.md   # copy A
central-catalog/skills/foo/SKILL.md   # copy B edited separately
```

Multiple delivery surfaces are acceptable only when they derive from one canonical source.

## 2. Choose the manifest model

For repository/package-backed skills, prefer a deterministic **static manifest** built from canonical bytes.

For each served resource, capture at least:

- stable `skill://...` URI;
- path relative to the skill root;
- MIME type;
- exact byte size;
- SHA-256 digest.

Make the canonical `SKILL.md` URI authoritative for the skill entry. Keep all parsed frontmatter fields that the protocol shape permits rather than maintaining a second metadata copy.

Enable optional directory-reading capabilities only when a real dynamic or large-directory use case requires them. Do not add a second recursive read surface merely because the extension permits one.

## 3. Build a fail-closed resource boundary

Only serve resources present in the manifest constructed from the canonical tree.

At minimum, test and reject:

- `..` traversal and encoded traversal aliases;
- absolute-path or separator tricks;
- symlinked skill roots/files that can escape the canonical tree;
- malformed or unterminated frontmatter;
- frontmatter `name` that disagrees with canonical directory identity;
- duplicate/ambiguous skill identities;
- unknown skill/resource URIs;
- invalid pagination cursors;
- post-manifest byte drift.

If canonical bytes change after the in-use manifest was built, fail closed rather than serving new bytes under stale digest/size metadata. Refresh/rebuild the catalog to obtain new integrity metadata.

## 4. Implement the official extension surface

Use the current official SDK mechanism whenever it exists.

The provider must expose the official extension identifier and the current required methods/resources. For the proven v1-style contract this means:

```text
server capabilities
└── io.modelcontextprotocol/skills

skills/list        -> discover paginated skill metadata/manifests
skills/get         -> authoritative direct lookup/refresh
resources/read     -> lazy content for manifest-authorized skill resources
```

Keep the transport adapter thin. Domain behavior and authorization belong outside the extension adapter.

Do not invent alternate method names, parallel tool-based protocols, or a custom skills index when the current official extension already defines the contract.

## 5. Preserve lazy loading and progressive disclosure

Discovery should return enough metadata for a host to decide what skill exists without loading every instruction body.

Load `SKILL.md` and supporting resources lazily through standard MCP Resources. Avoid fetching a mutable GitHub branch, package registry, or external catalog on every read when the canonical payload is already packaged with the server.

For static packaged skills, runtime availability should not depend on APM, Renovate, a central catalog, or GitHub being online.

## 6. Keep integrity separate from trust

A SHA-256 digest and byte size prove snapshot consistency between an advertised manifest and returned bytes. They do **not** independently prove publisher identity when the same server supplies both digest and content.

Preserve server/provider origin independently from:

- display `name`;
- skill URI;
- digest;
- standalone package identity.

Host approval, transport/auth trust and code-execution policy still apply.

## 7. Keep skill metadata separate from authorization

Treat frontmatter such as `allowed-tools` as Agent Skills metadata/instructions only.

The Skills extension must not:

- register new provider tools because a skill names them;
- widen scopes or bypass auth;
- authorize mutation/publish operations;
- reinterpret skill prose as a server policy grant.

Existing authentication, review, confirmation and mutation controls remain authoritative.

A useful implementation assertion is: **the Skills delivery adapter contributes skill methods/resources, not privileged provider tools or tool-call interception.**

## 8. Prove behavior in evidence layers

Never collapse different proof levels into one "supports Skills" claim.

### Level 1 — structural/security tests

Validate catalog construction, frontmatter, URI rules, deterministic ordering, manifests, traversal/symlink handling, malformed inputs, drift and authorization separation.

### Level 2 — real SDK protocol round-trip

Use the official SDK client against the real server object or transport to prove:

- extension discovery;
- `skills/list` pagination;
- direct `skills/get` without requiring a previous list call;
- `resources/read` of canonical and supporting files;
- digest/size equality with exact returned bytes;
- protocol error shapes for invalid inputs.

### Level 3 — official MCP conformance

Run the current official `modelcontextprotocol/conformance` Skills scenarios against the real serving transport. Pin the tested conformance revision in reproducible CI when appropriate, and store sanitized evidence/logs.

Do not write a private conformance harness when the upstream suite already covers the contract.

### Level 4 — interoperability/inspection

Use an official or standards-aware inspector/client to verify the deployed transport when that adds evidence beyond in-process tests.

### Level 5 — host model-context activation

Claim automatic activation only after a **named host/version/model** actually discovers and makes the skill available to the model, and the experiment demonstrates the loading/selection behavior being claimed.

Level 1-4 success is not Level 5.

## 9. Preserve standalone fallback from the same source

Mixed client support may require both:

```text
canonical skills/*
  ├── MCP-served/runtime
  └── standalone Agent Plugin / filesystem / package
```

Prefer a package format that can consume the canonical `skills/*` tree directly. Do not generate host-specific editable copies merely for compatibility.

If a central catalog intentionally republishes the provider skill, derive that mirror from an immutable upstream ref through the catalog's existing dependency/provenance process.

Do not add APM/Renovate merely because an MCP advertises the skill. APM belongs to the **build-time external dependency/republishing decision**, not to runtime MCP freshness.

## 10. Define duplicate-origin behavior

When a host can see standalone and MCP-served forms of the same logical skill:

1. preserve origin and URI;
2. do not assume equal `name` means equal bytes/authority;
3. never concatenate instruction bodies silently;
4. if content/integrity is equivalent, treat them as alternate delivery paths and activate one;
5. if content differs, surface an origin/version conflict;
6. keep the standalone fallback until target hosts prove equivalent discovery, activation and update behavior.

## Implementation sequence

Use an ordered issue/PR sequence for non-trivial migrations:

1. **catalog foundation** — canonical discovery, frontmatter validation, URIs, manifests, digests and safe reads;
2. **protocol adapter** — official extension capability, list/get and standard resource delivery;
3. **conformance/security evidence** — negative tests, SDK round-trips and official conformance CI;
4. **standalone compatibility** — same-source package/fallback and duplicate-origin policy;
5. **architecture feedback** — feed implementation findings back into reusable docs/skills/upstream working group.

Merge each stage only after its own validation is green; do not implement later stages on an unstable protocol foundation unless a stacked-PR strategy is intentional and documented.

## Completion report

Report separately:

- canonical skill source and ownership;
- official SDK/upstream components reused;
- extension methods/capabilities implemented;
- manifest/hash/resource security tests passed;
- official conformance scenarios/revision passed;
- standalone fallback path and whether it duplicates any editable behavior;
- authorization boundary evidence;
- duplicate-origin policy;
- actual host activation evidence, or an explicit **not proven** statement;
- upstream gaps/findings worth contributing back.

## References to inspect, not blindly copy

- Official MCP Skills overview and current SEP/spec text.
- `modelcontextprotocol/conformance` current Skills scenarios.
- `modelcontextprotocol/ext-skills` working-group findings/client-support research.
- This repository's `docs/adr/0003-mcp-served-skills-runtime.md` and `docs/mcp-skills-runtime.md`.
- Stars reference implementation: `svg153/github-stars-contrib-mcp-server` issues #48-#57 and its `docs/mcp-skills-evidence.md`.
