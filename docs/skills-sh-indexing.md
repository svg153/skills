# skills.sh indexing

This public repository is a multi-skill Agent Skills catalog. CI validates that the current Vercel `skills` CLI can discover the catalog without parser skips.

## Verified discovery

```bash
# Discover every valid skill in the catalog
npx -y skills@latest add svg153/skills --list

# Example: install a locally maintained skill
npx -y skills@latest add svg153/skills --skill social-publishing
```

The repository also includes `skills.sh.json` for catalog grouping. That file improves repository presentation metadata but does not force the externally operated skills.sh search index to crawl the source immediately.

## Provenance note

Not every directory in this catalog is authored here.

For example, `github-build-or-reuse` is synchronized from its authoritative community upstream:

```text
ghspain/github-build-or-reuse
  -> stable release
  -> svg153/skills/skills/github-build-or-reuse
```

If skills.sh duplicate detection identifies the catalog copy as a duplicate/mirror, the expected canonical source for that skill is `ghspain/github-build-or-reuse`. Other entries such as `social-publishing` are maintained directly in this catalog.

The catalog intentionally keeps origin and lifecycle policy in each `metadata.yaml` so mirrors are not presented as independently authored projects.

## Indexing status

- Source repository: `svg153/skills`
- Public Agent Skills catalog: yes
- Root `skills.sh.json`: yes
- Current `npx skills` discovery: CI validated
- External skills.sh search/index: ingestion pending verification

Do not generate artificial installations to manipulate ranking. If direct CLI discovery succeeds but public search remains absent/stale, request a crawl/re-index from `vercel-labs/skills`.

## Prepared upstream issue

**Title**

```text
[Listing]: Index svg153/skills Agent Skills catalog
```

**Body**

```markdown
## Summary

Please index the public `svg153/skills` Agent Skills catalog so its skills become discoverable through skills.sh and `npx skills find`.

Repository: https://github.com/svg153/skills

## Verified

- The repository is public.
- Skills use standard `skills/<name>/SKILL.md` layout with valid `name` / `description` frontmatter.
- The repository includes a root `skills.sh.json` grouping manifest.
- CI runs the current Vercel CLI with telemetry disabled and verifies catalog discovery without parser skips.

Direct discovery:

```bash
npx -y skills@latest add svg153/skills --list
```

Example local skill install:

```bash
npx -y skills@latest add svg153/skills --skill social-publishing
```

### Provenance / duplicate handling

The catalog includes both locally maintained skills and explicitly tracked upstream mirrors. In particular, `github-build-or-reuse` is synchronized from the authoritative repository `ghspain/github-build-or-reuse`; if duplicate detection applies, that GH Spain repository should remain the canonical source/attribution for that skill.

Direct CLI discovery is correct. If the catalog/skills are still absent from public search, could you please crawl/re-index `svg153/skills`?
```

## After indexing

Once the repository page is confirmed live, add the skills.sh badge to the README. Until then, do not render a `not found`/inaccessible badge as if it were a valid installation metric.
