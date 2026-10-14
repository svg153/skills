# APM 0.33.0 and Renovate maintenance review

Validated on 2026-10-14 against catalog commit
`d1bb730eeae9761209456356b08b075b69ca02ca` and Renovate PR
[#45683](https://github.com/renovatebot/renovate/pull/45683), commit
`d82f7648e64dea7bed64bd3d6b8d6aa5867600ac`.

Design: [#44](https://github.com/svg153/skills/issues/44).
Prior implementation: [#48](https://github.com/svg153/skills/pull/48).
The later trusted completion, cleanup and rollback mechanisms are reused.

## Toolchain and method

Released APM 0.33.0 (`18c4c43`), Linux x86_64 archive verified against the
GitHub release asset digest:
`e6374402c74318f7c8bef97a90d8572d049fdab0dc3871492c6b0647ae9e881f`.

All experiments used disposable local checkouts. No harness target was added
to the catalog. Consumer experiments explicitly selected Claude and used the
same public `github-build-or-reuse` dependency, with no MCP server configuration.

The exact PR manager was exercised through its real `updateArtifacts` function,
with Git initialized/synced first, `binarySource: global` and `constraints.apm:
0.33.0`. This executed the real CLI and collected actual Git file changes.
It was not a hosted Renovate discovery run. The temporary consumer fixtures do
not represent the catalog's canonical deployment model.

## Results

| Experiment | Observed result |
| --- | --- |
| Catalog: `apm lock --update` on current SHA | Exit 0; manifest and existing lock byte-identical; `deployments: []`; no harness copies |
| Catalog: explicit policy + CycloneDX + audit | Export succeeds; explicit local policy succeeds; all 30 audit checks pass with `--no-drift` |
| Catalog: exact manager maintenance path | Returns `artifactError` containing `No harness detected` |
| Catalog: exact manager ordinary update path | Also returns `artifactError` containing `No harness detected` |
| Consumer: old delete-lock + install | Drops deployment ledger from 7 entries to 0; audit exits 1 with 6 files of drift |
| Consumer: keep-lock + install --update | Keeps all 7 deployment entries and immutable SHA; audit exits 0 |
| Exact manager: range `^1.2.2` with old 1.2.2 resolution | Maintenance resolves 1.2.3, preserves manifest bytes, returns both changed lock and deployed SKILL.md, keeps 7 ledger entries |
| Exact manager: ordinary manifest change to real 1.2.2 SHA | Returns both lock and deployed SKILL.md; manifest update remains separate from artifact results |
| Resolver: real-release 1.2.3 -> 1.2.2 -> 1.2.3 | `apm lock` follows declared SHA; `lock --update` on old SHA does not advance it; no deployments; returns byte-for-byte to normalized lock |
| Trusted completion with 0.33.0 | Policy/audit/SBOM, cleanup, materialization, distribution, catalog validators and skills discovery pass |
| Existing mirror rollback test with normalized 0.33 lock | Published 1.2.2 rollback and 1.2.3 restore converge byte-for-byte |
| PR manager `pnpm check --all lib/modules/manager/apm` | Passes lint/format and tests (2 test files) on Node 24.19.0 |

The initial round trip differed only in `apm_version`, from 0.30.0 to 0.33.0.
Updating this metadata makes subsequent tests deterministic; dependency SHA and
content hash remain unchanged. The CLI intentionally preserves the old lock
bytes for a no-op before a semantic rewrite.

Organization-policy discovery warned that `svg153/.github-private` was not
available. The explicit committed local policy passed; these results do not
claim validation of any inaccessible remote policy. Consumer audit confirms
deployment drift only, not an organization policy certification.

## Decision

The PR fixes the ownership-loss bug for normal consumers. `apm install --update`
is appropriate there, and changing it globally to `apm lock --update` would leave
deployment refresh outside the manager.

APM already supplies the resolver-only primitive. Hosted Renovate still needs
an explicit opt-in that selects `apm lock` after manifest updates and
`apm lock --update` for maintenance. An empty deployment ledger alone is not
an intent signal. This follow-up should not block the current consumer fix.

Keep the catalog's reviewed SHA + tag-comment proposals, trusted lock completion,
and disabled lockfile maintenance. Do not fabricate a target, enable automerge,
or cut over the legacy synchronizer based on these experiments. Detection of
the next genuine upstream release remains a separate acceptance criterion.

## Reproduction in this repository

Install the checksum-pinned CLI using `scripts/install-apm-ci.sh`, then run:

```bash
python tests/test_apm_resolver_refresh.py
python scripts/complete-apm-renovate-update.py github-build-or-reuse
bash tests/test_apm_mirror_rollback.sh
```

The first test uses temporary projects and asserts immutable maintenance plus
the two real-release round trip. Completion and rollback mutate the checkout;
run them in a clean disposable checkout of this change, where the normalized
0.33.0 lock is already committed.

AI assistance was used for implementation and evidence synthesis. Commands were
executed directly; hosted discovery and model-backed behavioral evals were not
run as part of this review.
