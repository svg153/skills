# Planning provider contract

The planning skill reasons over one provider-neutral work graph, then maps each item to one authoritative provider.

## Provider-neutral work item

Track only fields needed for planning decisions:

| Field | Meaning |
| --- | --- |
| `provider` | `github` or `jira` when persisted |
| `id` | Provider-confirmed issue number/key/ID after persistence |
| `title` | Outcome-oriented summary |
| `type` | initiative/epic/story/task/decision when the provider/project supports the distinction |
| `status` | Provider-native state normalized only for reasoning |
| `parent` | Provider-confirmed parent when supported |
| `depends_on` | Blocking work items/decisions |
| `priority` | Provider/project convention; do not invent unsupported fields |
| `iteration` | Sprint/iteration/milestone when the project actually uses one |
| `repository_or_project` | Owning GitHub repository/project or Jira project |
| `delivery_links` | PRs, commits, external provider records, docs |

Do not force every field onto every provider.

## GitHub ownership

Use the GitHub MCP when repository-native engineering planning is authoritative.

Prefer existing GitHub primitives rather than inventing hidden state:

- Issues for durable work items;
- sub-issues/parent relationships where supported and useful;
- Projects fields/views for portfolio/backlog state when the project already uses them;
- milestones/iterations according to the repository/project convention;
- linked pull requests and closing relationships for delivery traceability;
- issue/PR comments for concise decision evidence when appropriate.

### GitHub read-first checks

Before creating work, inspect relevant open issues and project items for semantic overlap. When planning against an existing repository, also inspect contribution/project conventions before choosing labels, fields, issue types, or hierarchy.

### GitHub mutations

Only mutate when user intent authorizes external changes. Use provider-confirmed issue/project IDs for follow-up operations. If a Project field or issue relationship is unavailable, preserve the plan and report the missing mapping instead of silently approximating it with unrelated metadata.

## Jira ownership

Use the Atlassian MCP when Jira is the organizational or delivery source of truth.

Prefer project-native Jira concepts and workflows:

- issue types actually configured in the target project;
- parent/epic relationships as supported by that Jira project;
- project status/workflow transitions rather than invented generic states;
- sprint/backlog placement only where the project supports those concepts;
- issue links/dependencies when exposed by the provider;
- comments/links for cross-provider delivery evidence.

### Jira read-first checks

Resolve the target site/project before mutation. Search existing issues semantically and by relevant identifiers. Do not assume every Jira project uses Scrum, epics, story points, the same issue types, or the same status names.

### Jira mutations

OAuth/account access is client-managed. If authentication or a required Jira operation is unavailable, preserve the intended work graph and mark the Jira persistence step as blocked rather than switching systems without authorization.

## Cross-provider patterns

### GitHub engineering + Jira program record

Use when Jira owns program/customer coordination and GitHub owns repository implementation.

```text
JIRA-100  Program/feature record
  ├─ link -> GH #210 implementation slice A
  └─ link -> GH #211 implementation slice B
```

Keep status semantics in their owning provider. Cross-links provide traceability; they are not a synchronization protocol.

### Jira delivery + GitHub PR traceability

When Jira owns the implementation ticket, do not create a duplicate GitHub issue solely to link a PR. Link the PR/branch/commit to the Jira record through the conventions already used by the team.

### GitHub-only or Jira-only

Do not use the second provider merely because the plugin exposes its MCP. Tool availability is not a requirement to create records there.

## Degraded behavior

| Available tools | Behavior |
| --- | --- |
| GitHub + Jira | Inspect both where relevant; persist each item only in its chosen system of record |
| GitHub only | Continue GitHub-backed planning; retain Jira-targeted items as unpersisted/blocking where Jira ownership is required |
| Jira only | Continue Jira-backed planning; retain GitHub-targeted items as unpersisted/blocking where repository ownership is required |
| Neither | Plan-only mode; no claims about live provider state or duplicate checks |

A provider outage must not make the independent skill disappear or imply that the other provider should receive duplicate records.

## Authentication and secrets

The Agent Plugin declares official remote MCP endpoints without Authorization headers. The client owns OAuth/PAT setup and credential storage. Never request that users paste credentials into issue bodies, skill files, plugin manifests, or generated planning artifacts.
