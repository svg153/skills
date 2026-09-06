# Planning authenticated runtime evidence

This procedure captures the remaining evidence for the planning Agent Plugin without committing provider credentials or confusing package discovery with authenticated tool use.

The portable package is already verified in GitHub Copilot CLI and OpenAI Codex CLI. This document starts at the stronger boundary: provider authentication, real read calls, scoped mutations, and a cross-provider scenario.

## Evidence rule

A claim advances only when its corresponding provider/client operation actually succeeds.

```text
plugin install
  -> skill discovery
  -> MCP discovery
  -> provider authentication
  -> read tool call
  -> explicitly authorized mutation
  -> cross-provider end-to-end scenario
```

Do not infer a later stage from an earlier one. In particular, an MCP shown as enabled but `not_logged_in` is **MCP discovery evidence**, not authentication evidence.

## Before testing

Use a non-sensitive GitHub repository/issue and a non-sensitive Jira project/issue. Prefer dedicated test records when a mutation is required.

Never paste or commit:

- OAuth access/refresh tokens;
- GitHub PATs or `GITHUB_TOKEN` values;
- Atlassian API tokens;
- `Authorization` headers;
- browser cookies;
- credential-store contents;
- full provider responses containing private/customer data.

The plugin itself must remain credential-free. Authentication belongs to the client/provider credential store.

## Codex CLI lane

The repository CI currently pins Codex CLI 0.153.4 for deterministic package/discovery evidence. Use the current supported version for a manual runtime run and record the actual version in the evidence JSON.

### 1. Install the plugin

From a checkout of this repository:

```bash
codex plugin marketplace add .
codex plugin add planning@svg153-skills --json
codex plugin list --json
codex mcp list --json
```

Before authentication, `github` and `atlassian` may legitimately report `auth_status: not_logged_in`.

### 2. Authenticate provider MCPs

Use the client-managed OAuth flow:

```bash
codex mcp login github
codex mcp login atlassian
codex mcp list --json
```

Complete browser consent using the intended test accounts. Do not copy tokens from the credential store into evidence.

If a provider rejects or blocks OAuth, record the stage as `blocked` with a non-sensitive error summary instead of weakening the plugin security model.

### 3. Read-only GitHub call

Start Codex and ask the planning capability to read a known non-sensitive GitHub planning record without modifying it. For this repository, issue `svg153/skills#36` is a suitable public read target.

Example intent:

```text
Use the planning capability. Read svg153/skills issue #36 through the GitHub provider and return only its identifier, title, state, and the next unmet runtime gate. Do not modify anything.
```

Record only a compact result summary and the public resource reference.

### 4. Read-only Jira call

Use a non-sensitive Jira test/project record available to the connected Atlassian account.

Example intent:

```text
Use the planning capability. Read Jira issue <TEST-KEY> through the Atlassian provider and return only its key, summary, status, and direct dependencies. Do not modify anything.
```

Do not commit private Jira descriptions/comments. Evidence should identify a safe test key and a sanitized result summary.

### 5. Scoped mutation

A mutation must be preceded by explicit user intent. Prefer a dedicated test issue/task.

Good evidence records:

- the operation requested;
- `explicitUserIntent: true`;
- the provider-returned issue/key/ID;
- a short sanitized result summary.

Do not count a dry-run, proposed mutation, or locally generated ID as provider mutation evidence.

## GitHub Copilot CLI lane

### 1. Install and authenticate Copilot CLI

```bash
copilot login
copilot plugin marketplace add .
copilot plugin install planning@svg153-skills
copilot plugin list
copilot mcp list --json
```

### 2. Re/authenticate plugin-provided MCPs

In an interactive Copilot CLI session, use:

```text
/mcp auth github
/mcp auth atlassian
```

GitHub documents `/mcp auth <server-name>` as the reauthentication path for remote OAuth MCP servers. Complete the browser/device flow without copying credentials into repository files.

Run the same read/mutation scenarios described for Codex and record the actual client version.

## Cross-provider end-to-end scenario

The final planning pilot should prove coordination, not duplication.

Recommended fixture:

```text
Jira TEST-123        authoritative program/customer planning record
    |
    +----> GitHub #N authoritative repository implementation child
```

The test should verify all of the following:

1. both provider reads succeed;
2. the plan identifies exactly one authoritative provider for each mutable work item;
3. the GitHub implementation item and Jira planning item are cross-linked rather than mirrored twins;
4. the user explicitly authorizes a scoped mutation;
5. at least one provider mutation succeeds and returns a real provider ID/key;
6. a failure in one provider is reported as degraded state rather than silently recreated in the other provider.

Only mark `endToEnd.status` as `verified` when these conditions are met.

## Capture sanitized evidence

Copy the template rather than editing it in place:

```bash
cp plugins/planning/evidence/TEMPLATE.json \
  plugins/planning/evidence/2026-09-07-codex-authenticated.json
```

Then:

- set `mode` to `evidence`;
- set the actual client/version/time/platform;
- update each stage to `verified`, `blocked`, `pending`, or `not-applicable`;
- keep evidence summaries compact and non-sensitive;
- never add credentials.

Validate before committing:

```bash
python scripts/validate-planning-runtime-evidence.py
```

The validator rejects common secret-bearing keys/value shapes and enforces stronger prerequisites for stronger claims. For example, a verified mutation requires verified provider authentication, explicit user intent, a real returned ID, and a result summary. End-to-end verification requires verified reads from both providers and at least one verified mutation.

## Provider/client references

- Codex MCP OAuth uses `codex mcp login <server>`: https://github.com/openai/codex
- GitHub Copilot CLI command reference and remote MCP OAuth reauthentication: https://docs.github.com/en/copilot/reference/copilot-cli-reference/cli-command-reference
- Copilot CLI authentication: https://docs.github.com/en/copilot/how-tos/copilot-cli/set-up-copilot-cli/authenticate-copilot-cli
- Atlassian Rovo MCP OAuth guidance: https://support.atlassian.com/atlassian-ai-gateway/docs/use-rovo-mcp-with-other-supported-mcp-clients/
