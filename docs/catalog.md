# Public skills catalog

The public catalog is generated from the same canonical state used by the rest of the repository:

- `skills/<name>/SKILL.md` for runtime name and description;
- `skills/<name>/metadata.yaml` for provenance and lifecycle;
- `skills.sh.json` for curated groupings;
- optional `apm.yml` for APM install availability.

No separate catalog database or hand-maintained page registry exists.

## Build locally

```bash
python -m pip install 'PyYAML>=6,<7'
python scripts/generate-catalog.py
python -m http.server --directory _site 8000
```

Open `http://localhost:8000`.

A zero-write validation build is available for CI and local checks:

```bash
python scripts/generate-catalog.py --check
```

It renders the complete site in a temporary directory, requires one detail page per catalog entry, validates internal links, and then removes the temporary output.

## Information model

Each detail page surfaces factual repository metadata rather than inferred quality claims:

- catalog and runtime skill names;
- description and group;
- local / mirrored upstream / curated upstream ownership;
- upstream origin/path/ref;
- status, category, synchronization strategy, authority, interval and channel;
- tags;
- `npx skills` installation;
- APM installation only when an `apm.yml` actually exists;
- source links.

The index provides client-side search and group filtering. `catalog.json` exposes the same derived data for machine consumption.

## GitHub Pages

`.github/workflows/deploy-pages.yml` publishes `_site` through the official GitHub Pages Actions flow. The site uses relative links, so it is safe at the project-site base path `https://svg153.github.io/skills/` without framework-specific base-path configuration.

The deployment workflow follows the repository security baseline: immutable action SHAs, non-persisted checkout credentials, read-only build permissions, bounded jobs, and Pages/OIDC write access only in the deploy job.

If Pages has never been enabled for the repository, GitHub requires **Settings → Pages → Source → GitHub Actions** once. `GITHUB_TOKEN` cannot enable Pages itself; GitHub's `actions/configure-pages` documents that automatic enablement requires a PAT or GitHub App token with administrative/Pages write permissions.

## Reuse decision

We evaluated `jongio/create-gh-pages-site` and its `skills-catalog` Astro template before implementation. We reuse its key design constraints—correct project-site paths, official Pages Actions deployment, immutable action SHAs, local preview, real catalog content and explicit Pages enablement—but intentionally use a dependency-light static generator here.

Reason: this catalog is a deterministic projection of existing YAML/Markdown metadata. Introducing Astro plus a Node lockfile would add a second build toolchain without giving us server-side behavior we need. The generated UX remains searchable, responsive and metadata-rich while Python + PyYAML are already part of repository validation.
