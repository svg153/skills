# Pipeline — deck to design system to published site

Nine phases. Each phase is independently stoppable; the SKILL.md Decision Gates table says which phases to run. All commands assume a scratch workspace with this layout:

```
work/
  decks/          # original .pptx files (one or more, e.g. language variants)
  pdf/            # phase 1 output
  assets/         # phase 2 output: assets/<deck>/ppt/...
  previews/       # phase 3 output
  analysis.json   # phase 4 output
  design.md       # phase 5 output
  slidev-template/  # phase 6 output
```

## Phase 1 — PPTX → PDF

Windows-native LibreOffice is unreliable for batch conversion; use Docker (WSL2 backend on Windows):

```bash
assets/convert_pdfs.sh decks/ pdf/
```

Uses `instructure/libreoffice:26.2` headless. Verify: one PDF per pptx, page counts match slide counts.

## Phase 2 — Extract assets

```bash
assets/extract_assets.sh decks/ assets/
```

Pulls `ppt/media`, `ppt/theme`, `ppt/slideMasters`, `ppt/slideLayouts`, `ppt/slides` per deck. Then dedupe byte-identical media (language variants ship identical images):

```bash
find assets/ -type f -path '*/ppt/media/*' -exec md5sum {} + | sort | uniq -w32 -d
```

Document what was deduped in the final report.

## Phase 3 — Previews and palette

```bash
pip install pypdfium2 Pillow
assets/render_previews.py pdf/ previews/ 1500
assets/make_palette.py analysis.json previews/palette.png 20
```

Previews feed the landing gallery and visual verification; the palette PNG embeds in design.md.

## Phase 4 — Quantitative analysis

```bash
pip install Pillow
assets/analyze_design.py assets/ analysis.json
```

Produces a JSON **array** of deck objects: `slide_size`, `theme` (palette/fonts), `slide_count`, `color_usage_top`, `distinct_colors`, `font_usage`, `font_size_pt_top`, `layout_usage`, `media_by_type`, `media_total_mb`, `notable_media`.

Key principle: **trust actual run usage over theme XML** — decks routinely override theme colors with literal `srgbClr` values and theme fonts with explicit `latin typeface`.

## Phase 5 — design.md

Fill `assets/templates/design.md.template` using analysis.json + visual inspection of previews. Required sections: canvas & format, palette (hex + role + usage), typography (families/weights/scale), layout archetypes, visual patterns, tokens (CSS custom props + JSON), tool mapping (Slidev/Bento/OpenSlide), reuse checklist. Embed `palette.png` and reference 2–3 preview images per archetype.

## Phase 6 — Slidev template

- Scaffold Slidev (pin the version; v51.8.2 known-good — see gotchas before writing any slide syntax).
- Implement tokens as CSS custom properties in `styles/index.css`.
- Custom layouts in `layouts/` for each archetype; brand fonts as real webfonts in `public/fonts/` (e.g. from `github/mona-sans` releases v2.0.27 webfonts zip) with `@font-face`.
- Build one example deck exercising every layout.
- **Verify in a real browser** (dev server + screenshot each layout) before shipping. Never trust the build alone.

## Phase 7 — Publish repo

```bash
gh repo create <org>/<name> --public --source . --push   # or push the prepared tree
gh api -X PUT repos/<org>/<name>/topics -f 'names[]=design-system' ...
```

Include MIT LICENSE (or match the source license) with attribution to the origin repo. Verify the repo, description and topics via the API after every mutation — permission denials can be silent.

## Phase 8 — Pin the source release

```bash
gh api repos/<origin>/<repo>/releases --jq '.[0] | {tag_name, id, published_at, assets: [.assets[] | {name, size, browser_download_url}]}'
```

Fill `assets/templates/readme-pinned-release.md.template` with tag, release ID, date, license and immutable `releases/download/<tag>/<file>` URLs. Pinning documents exactly which version was consumed.

## Phase 9 — GitHub Pages

```bash
mkdir -p docs && touch docs/.nojekyll
npx slidev build --base /<repo>/deck/ --out dist
cp -r dist/* docs/deck/
cp docs/deck/index.html docs/deck/404.html   # SPA fallback for deep links
gh api -X POST repos/<org>/<repo>/pages -f 'source[branch]=main' -f 'source[path]=/docs'
# if Pages already configured: gh api -X PUT ... same fields
```

Then poll until built and verify:

```bash
gh api repos/<org>/<repo>/pages/builds/latest --jq '.status'   # wait for "built"
curl -fsI https://<org>.github.io/<repo>/deck/                  # expect 200
gh api -X PATCH repos/<org>/<repo> -f 'homepage=https://<org>.github.io/<repo>/deck/'
```

If the org has a custom domain (e.g. ghspain → githubcommunity.es), document both URLs and verify both.
