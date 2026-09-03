# Governance

## Project purpose

`svg153/skills` is a portable catalog of Agent Skills with explicit provenance, lifecycle ownership, reproducible upstream synchronization, cross-agent packaging, and catalog-level behavioral evaluation.

## Roles

### Maintainer

The repository owner (`@svg153`) is the final maintainer for catalog policy, repository infrastructure, releases of repository-owned tooling, and merge decisions.

### Contributors

Contributors may propose new skills, improve local skills, repair catalog tooling, add integrations, or improve documentation and tests through pull requests.

### Upstream maintainers

For `MIRRORED_UPSTREAM` entries, the external upstream remains authoritative for the mirrored payload. This catalog must not present local packaging, evals, or metadata as if they were authored or endorsed by the upstream project.

## Decision model

Routine changes are decided through pull-request review and repository validation. For changes that alter the catalog contract, prefer an ADR or issue that records the alternatives, trade-offs, and migration impact before implementation.

The following are treated as catalog-contract changes:

- changing lifecycle ownership semantics;
- changing which files are canonical versus generated;
- introducing a new synchronization authority;
- changing behavioral-eval ownership boundaries;
- adding a new distribution surface that requires persistent metadata;
- changing security or provenance guarantees.

When evidence is incomplete, prefer the smallest reversible change over creating a second source of truth.

## Skill ownership

Every skill must fit exactly one lifecycle mode:

- `LOCAL` — authored and authoritative here;
- `CURATED_UPSTREAM` — upstream provenance retained, local adaptation authoritative;
- `MIRRORED_UPSTREAM` — stable upstream payload authoritative and replaceable by generic synchronization.

Generated manifests, catalog pages, and integration evals are derived/catalog-owned surfaces. They do not supersede `SKILL.md` plus `metadata.yaml` as canonical catalog state.

## Contributions and review

Before opening a pull request, follow [CONTRIBUTING.md](CONTRIBUTING.md). Reviews prioritize:

1. provenance and licensing correctness;
2. security and least privilege;
3. deterministic/reproducible behavior;
4. compatibility with existing consumers;
5. avoiding duplicate sources of truth;
6. useful tests or behavioral evidence for high-impact changes.

A contribution can be declined even when technically correct if it introduces disproportionate maintenance cost or weakens those invariants.

## Community expectations

Be specific, evidence-oriented, and respectful. Review the change rather than the person. Disagreement is resolved by documenting constraints and trade-offs, not by escalating tone.

Security-sensitive reports follow [SECURITY.md](SECURITY.md) rather than ordinary public issue discussion.
