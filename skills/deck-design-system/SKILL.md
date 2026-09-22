---
name: deck-design-system
description: "Trigger: pptx to pdf; extract deck design system; design.md from slides; slidev template from deck; publish deck pages site. Turn a presentation into PDFs, assets, a documented design system and a reusable Slidev template, published with Pages."
license: "MIT"
metadata:
  author: "svg153"
  version: "1.0"
---

# Deck Design System

## Activation Contract

Use when the user provides one or more presentation files (`.pptx`) from an event, team or any source and wants to view them as PDF, extract their assets and design system, document it as `design.md`, rebuild it as a reusable Slidev template, and/or publish everything to a GitHub repository with a GitHub Pages site.

Do not use for authoring a brand-new presentation with no source deck, or for plain file conversion with no design intent.

## Hard Rules

- Work in a scratch workspace first; publish to a new repository (confirm org/name when not given). Never write into existing checkouts.
- Attribute the source: record origin repo, release tag, release ID, publish date, license and immutable `releases/download/<tag>/<file>` asset URLs. Pin the exact version consumed.
- Deduplicate byte-identical media (language variants often ship identical assets) and document the dedup.
- Verify every GitHub mutation through the API (repo, topics, Pages build) — permission denials can be silent.
- Ship a LICENSE matching the source license with attribution. Never commit secrets or redundant oversized media.

## Decision Gates

| User wants | Run phases |
| --- | --- |
| PDFs only | 1–2, stop |
| Design system documented | 1–5 |
| Reusable template | 1–6 |
| Public site + repo | 1–9 |

## Execution Steps

Follow `references/pipeline.md` phase by phase; check `references/gotchas.md` before debugging anything:

1. Convert `.pptx` → PDF with headless LibreOffice in Docker (`assets/convert_pdfs.sh`).
2. Extract assets (media, theme, masters, layouts, slides) with `assets/extract_assets.sh`; dedupe identical media.
3. Render per-slide PNG previews and a palette swatch (`assets/render_previews.py`, `assets/make_palette.py`).
4. Run quantitative analysis → `analysis.json` (`assets/analyze_design.py`): trust actual run usage over theme XML.
5. Write `design.md` from `assets/templates/design.md.template`: palette, typography, layouts, patterns, CSS/JSON tokens, tool mapping.
6. Build a Slidev template implementing the design (token CSS, custom layouts, real brand fonts); verify in a real browser before shipping.
7. Publish the repo (`gh repo create`), LICENSE with attribution, topics; verify via API.
8. Pin the source release in the README (`assets/templates/readme-pinned-release.md.template`).
9. Ship GitHub Pages from `docs/`: `.nojekyll`, `--base /<repo>/deck/`, `404.html` SPA fallback, enable + poll build + curl-verify, set repo homepage.

## Output Contract

Return: artifact paths (`pdf/`, `previews/`, `assets/`, `analysis.json`, `design.md`, template dir), repo and Pages URLs, the pinned source release, dedup notes, and any skipped phase with its reason.

## References

- `references/pipeline.md` — exact commands per phase.
- `references/gotchas.md` — Slidev v51 syntax, Vite base rewriting, Pages and environment quirks.
