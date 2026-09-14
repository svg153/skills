# Atlassian Rovo MCP v2 ownership boundary

This note records the provider-ownership audit performed for `svg153/skills#65` while migrating the planning capability from Rovo MCP v1 to v2.

## Decision

Keep `planning` and `backlog-management` as local **cross-provider orchestration skills**. Do not copy, fork, or embed Atlassian's provider-native Agent Skills into this plugin.

Rovo MCP v2 and Atlassian's public skill catalog own Jira/Confluence-specific mechanics. This plugin owns the behavior that spans GitHub and Jira or expresses our planning/source-of-truth policy.

## Why v2 changes the boundary

Atlassian's current endpoint is:

```text
https://mcp.atlassian.com/v2/mcp
```

The v2 server exposes a smaller primary tool surface. Some operations are discovered and invoked through the provider's `discover` / `execute` convention. Atlassian's own v2 Agent Skills document those provider-native details and are versioned alongside the v2 contract.

That is a stronger ownership signal than keeping provider tool names or exact invocation recipes inside our cross-provider skills.

## Current upstream skills reviewed

### `spec-to-backlog`

Provider-native responsibilities include:

- read a Confluence specification;
- resolve Jira project and configured issue types;
- use v2 Jira/Confluence tool contracts;
- create an Epic/parent followed by child implementation tickets;
- handle v2 non-primary operations through `discover` / `execute`.

### `triage-issue`

Provider-native responsibilities include:

- search Jira for possible duplicate bugs;
- reason over Jira-specific bug/history fields;
- offer provider-specific create/comment actions.

### `jira-sprint-dashboard` and other Atlassian skills

These are similarly provider-native workflows around Jira/Confluence state. New upstream skills may appear without requiring this plugin to mirror them.

## Local skills reviewed

### `planning` — **KEEP local**

The skill remains provider-neutral and does not hard-code Rovo v1 tool names. Its differentiating responsibilities are:

- turn a new demand into a provider-neutral work graph;
- choose one authoritative provider for each mutable work item;
- split ownership across GitHub/Jira when justified;
- preserve cross-provider links rather than create unsynchronized twins;
- degrade safely when one provider is unavailable;
- hand approved work to repository delivery rather than absorb implementation.

There is conceptual overlap with Atlassian `spec-to-backlog`, but not duplicate ownership. `spec-to-backlog` is Jira/Confluence-specific; `planning` decides whether Jira should own the item at all and may map implementation work to GitHub instead.

### `backlog-management` — **KEEP local**

The skill also avoids hard-coded Rovo v1 tool names. Its differentiating responsibilities are:

- inspect an existing backlog across GitHub and/or Jira;
- preserve one source of truth per work item;
- repair cross-provider traceability and drift;
- avoid moving blocked provider-owned records into another provider as a workaround;
- prioritize/clean up using the owning project's conventions;
- stop at the delivery boundary.

There is conceptual overlap with Jira hygiene/triage workflows, but the local skill's cross-provider authority/degradation contract is not provider-native behavior.

## Keep / delegate / remove matrix

| Concern | Decision | Owner |
| --- | --- | --- |
| Cross-provider work graph | keep | `planning` |
| One authoritative provider per mutable item | keep | `planning` / `backlog-management` |
| GitHub ↔ Jira traceability | keep | local plugin |
| Provider outage/degraded behavior | keep | local plugin |
| Jira v2 exact tool names/arguments | delegate | Atlassian/Rovo MCP |
| `discover` / `execute` mechanics for non-primary tools | delegate | Atlassian/Rovo MCP + upstream skills |
| Jira issue-type metadata quirks | delegate | Atlassian/Rovo MCP + upstream skills |
| Confluence read/write contract details | delegate | Atlassian/Rovo MCP + upstream skills |
| Jira-only bug triage workflow | delegate when available | Atlassian `triage-issue` |
| Confluence spec -> Jira-only backlog | delegate when available | Atlassian `spec-to-backlog` |
| Manual copies of upstream Atlassian skills | remove/avoid | none |

## Why we are not depending on MCP-served Atlassian skills yet

The new MCP Skills extension can eventually let a compatible host discover provider-native skills directly from a connected MCP server. Client support is still mixed, so this plugin must not require that runtime capability to perform its core cross-provider workflow.

For now:

```text
planning plugin
├── local planning/backlog orchestration skills
├── GitHub MCP
└── Atlassian Rovo MCP v2
```

A future compatible host may additionally discover Atlassian-native skills from the provider. That should enrich the provider layer rather than replace the local orchestration layer.

## Migration consequence

The v1 -> v2 migration therefore requires:

1. update the endpoint/provenance in canonical package config;
2. regenerate the portable MCP manifest;
3. refresh Copilot/Codex discovery evidence against the v2 endpoint;
4. collect authenticated v2 tool-call evidence separately;
5. leave the two local `SKILL.md` files provider-neutral unless a concrete regression proves they need a v2-specific reference.

This avoids turning a protocol migration into unnecessary skill churn.

## References

- Atlassian MCP server: https://github.com/atlassian/atlassian-mcp-server
- Upstream skills: https://github.com/atlassian/atlassian-mcp-server/tree/main/skills
- Rovo MCP v2 endpoint: https://mcp.atlassian.com/v2/mcp
- MCP Skills runtime architecture: ../../../docs/mcp-skills-runtime.md
