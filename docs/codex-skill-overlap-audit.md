# Codex skills provenance and overlap audit

**Audit date:** 2026-09-23
**Catalog baseline:** `main` at `c9c4450`
**Scope:** User-level skills in the local `.codex/skills` directory other than the two delivery skills proposed in [PR #83](https://github.com/svg153/skills/pull/83), compared with this repository's catalog and related open PRs. This is an evidence-based inventory, not authorization to redistribute or delete anything.

## Executive summary

- No exact-name collision exists between the nine other user-level skills and catalog entries.
- All nine `SKILL.md` files match named public upstream files after normalizing line endings and trailing whitespace (the eight skills traced to Addy Osmani, Matt Pocock, and NextLevelBuilder, plus Archify). These are not authored by `svg153` based on the available evidence.
- Six skills live under Codex's `.system` folder (`imagegen`, `openai-docs`, `plugin-creator`, `review-agent`, `skill-creator`, `skill-installer`). Treat them as host/bundled skills, not candidate user-owned catalog content.
- The nearest functional collision is `github-repo-autopilot` versus the two delivery skills in PR #83. Focused helper skills mostly complement the delivery modes, although `chained-pr` and `work-unit-commits` encode a much stricter 400-line ceiling that conflicts with the personal workflow's concept-sized PR guidance.
- Recommendation: do not bulk-import the remaining skills yet. Resolve delivery-mode routing after #83/#78, wait for design-related PRs #79/#82 before deciding on UI skills, and import upstream skills only in source/provenance-coherent slices with licenses, support files, and triggers reviewed.

## Provenance inventory

The source comparison checked each local `SKILL.md` against the current upstream file on 2026-09-23. “Exact” below means normalized content matches; it does not establish the historical installation event or that every auxiliary file in the local folder came from that revision. Source commit links pin the comparison snapshot.

| Local skill | Evidence and likely ownership | Catalog disposition |
|---|---|---|
| `archify` | Frontmatter names author `tt-a1i`, MIT, and its Cocoon-AI basis; `skill-release.json` names `tt-a1i/archify`. Local `SKILL.md` matches [`archify/ SKILL.md` at `9e35d2b`](https://github.com/tt-a1i/archify/blob/9e35d2b0b39b155553ba9fcfe0b4f2a5198dd993/archify/SKILL.md). Local package is about 8.3 MB / 219 files and includes code, generated assets, and `THIRD_PARTY_NOTICES.md` with mark/font caveats. | Third-party package, not a small standalone prompt. Defer; if wanted, evaluate a pinned upstream package and preserve its own license/notices and third-party assets. |
| `code-review-and-quality` | Exact normalized match to [addyosmani/agent-skills at `bcab6a1`](https://github.com/addyosmani/agent-skills/blob/bcab6a1b8503100e8618c3b4e32cc78de43de769/skills/code-review-and-quality/SKILL.md); upstream repository declares MIT. | Third-party. Candidate only after restoring/rewriting missing cross-skill references (see portability notes). |
| `codebase-design` | Exact normalized match to [mattpocock/skills at `c55ee46`](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/codebase-design/SKILL.md); upstream repository declares MIT. Local `DEEPENING.md` and `DESIGN-IT-TWICE.md` also match files in the same upstream tree. | Third-party, distinct design vocabulary. No direct equivalent by name; check its relation to SDD/design-engineering before importing. |
| `diagnosing-bugs` | Exact normalized match to [mattpocock/skills at `c55ee46`](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/diagnosing-bugs/SKILL.md); upstream repository declares MIT. | Third-party. Complementary to the narrower `performance-auditor`; do not conflate bug diagnosis with repository-wide performance audit. |
| `domain-modeling` | Exact normalized match to [mattpocock/skills at `c55ee46`](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/domain-modeling/SKILL.md); upstream repository declares MIT. Local ADR/context templates also match files in the same upstream tree. | Third-party. Complements domain documentation; `domain-manager` in this catalog is for DNS/domains, not domain-driven design. |
| `frontend-ui-engineering` | Exact normalized match to [addyosmani/agent-skills at `bcab6a1`](https://github.com/addyosmani/agent-skills/blob/bcab6a1b8503100e8618c3b4e32cc78de43de769/skills/frontend-ui-engineering/SKILL.md); upstream repository declares MIT. | Third-party, but overlaps UI implementation guidance and the design-engineering initiative. Defer until #79/#82 settle the catalog's UI boundaries. |
| `incremental-implementation` | Exact normalized match to [addyosmani/agent-skills at `bcab6a1`](https://github.com/addyosmani/agent-skills/blob/bcab6a1b8503100e8618c3b4e32cc78de43de769/skills/incremental-implementation/SKILL.md); upstream repository declares MIT. | Third-party. Complementary thin-slice implementation advice; review its strict per-slice commit/rollback rules against the catalog's concept-level PR mode. |
| `tdd` | Exact normalized match to [mattpocock/skills at `c55ee46`](https://github.com/mattpocock/skills/blob/c55ee46073ed923f86ce59a5eb3b6d895095d1b7/skills/engineering/tdd/SKILL.md); upstream repository declares MIT. | Third-party. Distinct red/green testing method; the catalog's `go-testing` is language-specific, not a general TDD equivalent. |
| `ui-ux-pro-max` | Exact normalized match to [nextlevelbuilder/ui-ux-pro-max-skill at `dcc40ff`](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill/blob/dcc40ff5133ef78276117db0cc34e7b83cc8aeba/.claude/skills/ui-ux-pro-max/SKILL.md); upstream repository declares MIT. Local tree is about 3.6 MB / 73 files with large data sets and explicit data-provenance files. | Third-party. Defer against design-engineering and open UI PRs; if selected, review dataset provenance, attribution, size, and update authority first. |

## Similarity and discrepancy with catalog skills

| Catalog skill(s) | Similarity | Material difference / recommendation |
|---|---|---|
| `github-repo-autopilot` | **High** overlap with both `enterprise-agentic-delivery` and `personal-agentic-delivery`: autonomous backlog discovery, issues, implementation, tests, PRs, and merge loop. It is also broadly triggered for continuing a repository or clearing a backlog. | Autopilot is the generic repository operator; the new skills encode distinct delivery policies (enterprise traceability vs personal concept batching). PR #78, still open at audit time, adds reversible decisions and CI-unavailability behavior, increasing overlap further. Before treating all three as independently auto-routable, choose a clear router/ownership rule: keep Autopilot generic and require explicit mode selection, or consolidate the mode policies into it. Enterprise's implicit invocation is disabled in #83; personal and Autopilot are both implicit, so their broad triggers can still collide. |
| `branch-pr` | Medium overlap with the final PR-opening step. | It carries Gentle AI-specific mandatory approved-issue labels, PR labels, and branch rules. The delivery skills correctly say to derive actual repo conventions. Never apply the Gentle AI rules globally. Keep as a project-specific helper, not a replacement for either mode. |
| `issue-creation` | Medium overlap with creating missing roadmap issues. | It requires Gentle AI templates/status labels. Delivery modes instead reuse or update the canonical issue and synchronize its parent. Scope this helper to its source conventions. |
| `chained-pr`, `work-unit-commits` | Medium overlap in change sizing, commit sequence, reviewability. | They enforce a ~400 changed-line chaining boundary and highly granular, independently revertible slices. Personal delivery intentionally batches one coherent capability and tolerates roughly 5–7k lines when still reviewable. This is a real policy conflict, not mere duplication: keep them opt-in and source-project-scoped; do not silently load their threshold into personal delivery. |
| `cost-optimizer` | Low overlap. | It diagnoses token/cost efficiency; it does not own roadmap issue delivery. It complements personal mode. |
| `skill-publish` | Low functional overlap. | It manages skill catalog lifecycle, provenance, registration plans, manifests, and validation—not application roadmap implementation. Use it only when the deliverable is a skill/catalog change. |
| `community-pr-audit` | Partial overlap with `code-review-and-quality` by name/topic. | Community audit specializes in external contributor identity, injection, and trust risk; code-review-and-quality is a broad five-axis change review. They are complementary layers, not substitutes. |
| `performance-auditor` | Partial overlap with `diagnosing-bugs`. | The former is a React/Vite repository audit with a ranked improvement backlog; the latter is an evidence-first loop for reproducing and fixing a particular hard bug/regression. Keep both scopes distinct. |
| `domain-manager` / SDD design skills | Mostly a name-level ambiguity for `domain-modeling`. | `domain-manager` concerns domain purchase/DNS/GitHub Pages. Domain-modeling concerns product vocabulary, context, and ADRs. There is no direct functional duplicate, though SDD's design/spec flows should be checked for routing. |
| `plugins/design-engineering` and proposed `better-ui` | Medium-to-high overlap with `frontend-ui-engineering` and `ui-ux-pro-max`. | Design Engineering is the orchestrator for visual direction/audit/polish; frontend-ui is implementation craft; UIUX Pro Max is a searchable design dataset/tool. PRs #79/#82 are open and materially change these boundaries. Defer import/overlap verdict until those PRs settle. |

### Delivery-skill overlap decision

PR #83 remains open and unreviewed, while PR #78 is also open. This audit does **not** change either PR or choose whether the delivery skills should remain separate. It surfaces one specific follow-up for review: clarify invocation precedence between the broad `github-repo-autopilot` trigger and the personal/enterprise mode triggers before adding more broad workflow skills. If the user wants distinct explicit entry points, preserve them; otherwise consider consolidating their policy text into Autopilot rather than maintaining three overlapping loops.

## Portability and publication risks

The global copies are not a clean, self-contained catalog payload in every case:

- `frontend-ui-engineering` refers to `../../references/accessibility-checklist.md`, which is absent in the audited local skills tree.
- `incremental-implementation` refers to `../../references/definition-of-done.md` and `git-workflow-and-versioning`; those paths/skills are absent under that root.
- `code-review-and-quality` refers to security/performance skills and checklists not present in the audited local skills tree.
- `tdd` routes review to `code-review`, but the installed skill is named `code-review-and-quality`.
- Most upstream-matched skills lack a local `LICENSE` file/frontmatter. The upstream repos report MIT, but any catalog entry must retain the actual upstream identity, pinned revision, license, and supporting files instead of claiming local authorship.
- `ui-ux-pro-max` and `archify` carry significant non-prose payloads; do not copy only `SKILL.md` and lose data/brand notices or provenance.

## Proposed next steps (not performed by this audit)

1. Review PR #83 alongside this delivery-mode routing finding; make any consolidation/trigger adjustment only after the maintainer decides whether the three workflow entry points are desired.
2. Wait for #79/#82, then decide if `frontend-ui-engineering`, `ui-ux-pro-max`, or neither adds a distinct durable layer to Design Engineering.
3. If importing engineering helpers, prefer provenance-grouped changes: Matt Pocock's `codebase-design`, `diagnosing-bugs`, `domain-modeling`, and `tdd`; Addy Osmani's `code-review-and-quality`, `frontend-ui-engineering`, and `incremental-implementation`. Pin upstream revisions, carry MIT attribution/license, and repair/reconcile cross-skill references.
4. Treat `archify` and `ui-ux-pro-max` as separate, higher-payload candidates; do not bundle them with small prompt skills.
5. Keep `.system` skills out of this user-skill migration unless there is a distinct, approved upstream redistribution plan.

## Decision record — CODEX

- **Question:** Should the remaining skills in the Codex user directory be copied to this public catalog immediately, or first be classified for source, overlap, and portability?
- **Options:** Bulk-copy the nine; copy only the skills not matching catalog names; or document evidence and defer publication decisions until provenance and routing conflicts are reviewed.
- **Decision:** Publish this read-only audit as a separate documentation PR; do not copy or alter any additional skill payload in this change.
- **Why:** Several skills are exact third-party upstream content, some include sizeable assets or incomplete local references, and the broad delivery triggers conflict. A content-only bulk import could misstate ownership or create redundant/contradictory routing.
- **Scope:** One audit document. No edits to PR #83, existing catalog skills, Codex source files, or `.system` files.
- **Follow-up:** The maintainer can choose individual migration groups after reviewing this evidence and after the open design/delivery PRs settle.
