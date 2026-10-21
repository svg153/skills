# Skill publisher description limit

## Objective and authorized scope
Align LOCAL description generation with the repository validator and Agent Skills specification (1024 characters), unless investigation reveals a specific binding reason for the old 250 limit. User authorizes an independent PR in svg153/skills, not merge, installation or global changes.

## Route and controls
- Delegated direct: publisher code/tests/docs are independent of the seven description edits in PR #97; one bounded Luna writer saves parent context. Parent owns integration, commits and publication.
- Baseline: origin/main e633213. Branch: fix/skill-publish-description-limit. Delivery: single-pr; forecast 100-200 authored additions plus deletions.
- RDD: disabled/unmanaged, inherited global OFF; do not enable reviews or change settings.
- TDD: no effective application TDD configuration established. Inspect relevant project configuration; preserve any explicit setting. Add boundary regression tests and observe pre-fix failures as verification, without asserting or changing a global TDD preference.
- Risk: item 1 (publisher/validator shared description contract). Preserve plan/apply approval hashes, rollback, overlap detection and all other registration behavior.
- Memory mirror pending: runtime registration unavailable after compaction. Local file is the recovery source; no unattributed memory writes.

## Tasks
- [x] T1: Investigate the 250 limit, update only the description generation cap/diagnostic and its documentation, and test the public planning boundary.
  - Acceptance: >250 and exactly 1024 characters accepted; 1025 rejected before writes; Unicode counts characters, not UTF-8 bytes; complete generated prefix counts toward the cap; generated frontmatter agrees with the actual validator.
  - Checks: focused publisher tests (including pre-fix failure evidence), full Python suite, validators, git diff --check; parent independently reruns at least one worker command.
  - Commit: pending. Rollback: revert publisher guard, new boundary tests, contract documentation and this recovery file only.
  - Observed: Luna reported pre-fix failures under the old guard, then 13 publisher tests and 74 full-suite tests passing. Parent independently reran both commands: 13/13 and 74/74 passed, plus frontmatter (48), eval (11 suites on main-based branch), distribution (8 manifests) and diff checks. No unrelated behavior change found in structural diff review.
- [ ] T2: Publish a separate PR with observed evidence, limitations and a CODEX decision record; leave open for user review.
  - Checks: clean committed branch, PR diff confined to publisher contract, CI status reported honestly.

## Progress and next step
Task file created before source writes. T1 implementation and verification are complete locally; no commit/publication was performed. The former 250 guard was introduced by the initial publisher commit `73decb2` and is not referenced by the current validator; current repository validation and the Agent Skills specification use 1024 characters. Focused tests were red before the fix and green after it. Full unittest and applicable validators pass; the canonical `bash scripts/sync-upstreams.sh --list` invocation is unavailable in this Windows shell because the script is checked out with CRLF and bash reads `pipefail` with a trailing carriage return, while a read-only CRLF-stripped invocation passed. Parent must independently rerun at least one worker command, inspect the diff, commit, and publish the separate PR.
