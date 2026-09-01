---
name: agent-skill-release-lifecycle
description: "Publish and maintain Agent Skills as genuinely consumable releases: validate packaging, version stable artifacts, test multiple clients, synchronize downstream catalogs, register with skills.sh without inflating telemetry, distinguish detail-page availability from search indexing, configure GitHub discovery metadata, and clean up temporary release probes. Use when releasing, distributing, publishing, indexing, cataloging, or improving discoverability of an Agent Skill."
---

# Agent Skill Release Lifecycle

Treat publication as a lifecycle, not as “the SKILL.md exists”. A release is complete only when the intended stable artifact is installable, downstream consumers resolve it, discovery surfaces are accurate, and temporary registration/debug machinery has been removed.

## Hard rules

- Keep one canonical skill source. Downstream catalogs should reference or synchronize that source rather than diverging copies manually.
- Prefer a stable semantic-version release for reproducible installs. Do not recommend pinning a release that predates the behavior being documented.
- Validate the exact release candidate, not only `main`, across every distribution path the project claims to support.
- Never inflate skills.sh install counts. At most perform a legitimate install needed to validate/register the release; use telemetry-disabled installs for routine CI.
- Treat a skills.sh detail page and skills.sh search indexing as separate states. A `200` detail page does not prove Finder/API search can discover the skill.
- Do not add a marketplace/directory badge until its target page is verifiably live.
- Keep GitHub description/topics in the repository's existing policy-as-code source when one exists. If a manual fallback is required, read values from that source rather than duplicating them in scripts.
- Do not claim search visibility until a real query surfaces the project.
- Remove one-shot registration workflows and temporary probes once their purpose is fulfilled.

## Release sequence

1. **Identify the canonical artifact.** Locate the authoritative `SKILL.md`, client metadata, plugin manifests, evals, changelog, release notes, catalog metadata, and any upstream/downstream relationship.
2. **Determine version impact.** If activation, behavior, output contract, packaging, or client compatibility changed, choose an appropriate semantic version. Keep version declarations consistent everywhere.
3. **Validate the release candidate.** Run repository validators plus relevant Agent Skills specification checks. Exercise supported clients such as `gh skill`, `npx skills`, APM, plugin manifests, or project-specific installers when available.
4. **Publish the stable release.** Tag/release the exact validated commit. Confirm the published tag contains the expected skill version and behavior.
5. **Fix pinned documentation.** Update README/examples so reproducible commands resolve the new stable release rather than an older tag.
6. **Synchronize downstream catalogs.** If another catalog follows `latest-release`, verify what actually changed inside the canonical skill directory and advance the consumer through its normal sync/validation path.
7. **Register directory discovery legitimately.** If skills.sh has not seen the repository, perform one real public-CLI install with telemetry enabled only when needed. Routine CI should disable telemetry so validations do not alter public counts.
8. **Probe directory states separately.** Verify the canonical repository/skill page and the public search API/Finder independently. Respect documented cache windows before diagnosing an indexing gap.
9. **Improve native GitHub discovery.** Set a concise intent-rich repository description and focused topics. Verify conceptual searches, not only exact-name searches.
10. **Escalate external indexing defects.** When a directory page is live but search remains absent beyond its documented cache window, preserve reproducible evidence and link matching upstream incidents. Do not manufacture more installs as a workaround.
11. **Clean up.** Remove telemetry registration jobs after their single use. Remove read-only probes after indexing is stable. Close tracking issues only after live verification.

## Verification matrix

For each claimed distribution surface, record the observed state rather than assuming equivalence:

| Surface | Verify |
| --- | --- |
| Stable Git tag/release | tag points to intended commit; canonical skill reports expected version |
| `gh skill` | preview/install/pinned install resolves expected skill |
| `npx skills` | repository discovery and install succeeds |
| Client/plugin manifest | manifest version, source and prompts match release |
| Downstream catalog | synchronized canonical contents and catalog validation pass |
| skills.sh detail page | canonical URL returns the expected skill page |
| skills.sh search/Finder | API/CLI search returns exact source + skill |
| GitHub About | description/topics equal intended metadata |
| GitHub search | at least one realistic conceptual query surfaces repository |

## skills.sh diagnostics

When the CLI install succeeds but search does not:

1. Confirm the install genuinely discovered the expected canonical skill.
2. Confirm telemetry was enabled only for the legitimate registration event.
3. Probe the canonical skills.sh repository and skill URLs.
4. Query the public search API/Finder for the exact skill name and source.
5. Wait only the service's documented cache interval, not an arbitrary delay.
6. If the detail page is live but search remains absent, classify it as an indexing/search-layer issue and capture the response plus timestamps.
7. File or link an upstream issue when permissions allow; otherwise keep a local tracking issue with enough evidence for a maintainer to reproduce it.
8. Do not loop installs to force ranking or indexing.

## GitHub metadata fallback

Repository description/topics typically require repository-administration write access. A normal workflow `GITHUB_TOKEN` may not expose that permission. Before creating new credentials:

1. inspect existing Safe Settings/repository-settings/policy-as-code infrastructure;
2. use its source of truth if it is active;
3. diagnose missing credentials from actual workflow logs;
4. when an operator already has an authenticated `gh` session with administration rights, prefer a small script that reads the central policy and applies/verifies live metadata;
5. keep automated credential-dependent jobs in a clean skipped state when credentials are intentionally absent.

## Completion report

Report separately:

- stable release/version actually published;
- client/install validations actually passed;
- downstream catalogs synchronized;
- skills.sh detail-page state;
- skills.sh search-index state;
- GitHub description/topics live state;
- conceptual-search visibility;
- external blockers with evidence;
- temporary workflows/issues removed or intentionally retained.

Never collapse “page exists”, “install works”, “search indexed”, and “GitHub SEO applied” into one generic “published” status.
