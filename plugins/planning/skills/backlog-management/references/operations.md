# Backlog provider operations

## Core rule

The same conceptual initiative may span GitHub and Jira, but each mutable work item has one authoritative provider.

Do not create a synchronization problem as a side effect of backlog cleanup.

## GitHub

Use GitHub for repository-native engineering work when that is the team's source of truth.

Relevant primitives may include:

- Issues and issue types;
- parent/sub-issue relationships;
- Projects fields and views;
- milestones/iterations according to local convention;
- assignees/labels when they already carry planning semantics;
- linked pull requests and closing relationships;
- issue links/comments for concise external traceability.

Do not assume every repository uses GitHub Projects or that every Project has the same fields. Inspect the actual project before updating fields.

## Jira

Use Jira for work whose authoritative workflow is the target Jira project.

Relevant primitives may include:

- configured issue types;
- parent/epic relationships;
- project workflows/transitions;
- sprint/backlog placement where available;
- issue links/dependencies;
- assignees/priorities/fields actually configured for the project;
- comments/external links for delivery traceability.

Do not assume every Jira project is Scrum, has epics, supports story points, or exposes identical transitions.

## Cross-provider traceability

Prefer links that state the relationship clearly:

- Jira program item -> GitHub implementation issue(s);
- GitHub issue -> Jira customer/program requirement;
- Jira implementation ticket -> GitHub pull request/commit;
- GitHub initiative -> Jira external dependency/approval record.

A link does not imply status synchronization. Do not automatically copy status, assignee, priority, or descriptions between providers without an explicit synchronization contract.

## Duplicate cleanup

When two records represent the same mutable work:

1. determine the intended authoritative provider from project/team convention and delivery ownership;
2. preserve the richer history/evidence where possible;
3. add cross-links if the secondary record still has reference value;
4. close/mark duplicate only according to provider/project conventions and user authorization;
5. do not erase useful decision history merely to reduce item count.

If authority is genuinely ambiguous and the user has not authorized choosing one, report the ambiguity instead of arbitrarily deleting or closing a record.

## Mutation safety

Before writing:

- resolve the exact provider target;
- read the current record if possible;
- use native field/transition values rather than guessed normalized labels;
- retain returned IDs after creates;
- apply parent/dependency relationships only after their referenced records exist;
- make failures visible and keep dependent writes from cascading incorrectly.

## Provider degradation

- GitHub failure blocks GitHub-owned writes only.
- Jira failure blocks Jira-owned writes only.
- Do not move a blocked work item into the remaining provider merely to complete the requested operation.
- Read-only recommendations remain possible when live tools are unavailable, but they must be labeled as unverified against current provider state.

## Handoff to delivery

Backlog management ends when the planning state is sufficiently clear. It should not implement work simply because the next item is obvious.

For GitHub repository execution, hand off the provider-confirmed issue/backlog context to a delivery skill such as `github-repo-autopilot` when available. Preserve the issue/ticket identifier so commits/PRs can maintain traceability.
