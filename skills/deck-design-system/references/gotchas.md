# Gotchas — hard-won lessons from a real deck pipeline

## Slidev (v51.8.2)

- `--` click fragments were **removed** in v51. Use full-line slot sugar `::name::` instead. Slots auto-close at the next slot or end of block; a bare `::` renders literally.
- Code groups (`<<<` with line highlighting ranges beyond basics) are not fully supported; prefer plain fenced blocks with `{1|2-3}` notation.
- `<v-click>` works inside custom layouts; wrap the whole layout content when in doubt.
- Vue HTML comments (`<!-- -->`) inside custom layout templates render as **text vnodes** — use JS comments in `<script>` or remove them.
- `useSlideContext()` gives `$frontmatter` as a plain object; there is no `$slide` global.

## Vite base rewriting

- CSS `url('/fonts/…')` **is** rewritten with the deploy base → fonts must live in the deployed deck directory via `public/`.
- Frontmatter and JS string paths are **not** rewritten. For dynamic assets use:
  `import.meta.env.BASE_URL.replace(/\/$/, '') + '/' + src.replace(/^\//, '')`
  (pattern from a working `layouts/feature.vue`).
- Always build with `--base /<repo>/deck/` when deploying under a path.

## GitHub Pages

- Pages serves `404.html` for deep links → copy `index.html` to `404.html` as SPA fallback. `_redirects` files are ignored.
- Enable Pages via API: `POST repos/<o>/<r>/pages` (first time) or `PUT` (reconfigure), then poll `pages/builds/latest` until `status == "built"`, then curl-verify.
- Org custom domains (e.g. ghspain → githubcommunity.es) serve the same content at two URLs; document and verify both.
- Landing galleries that load previews from `raw.githubusercontent.com` work CORS-friendly but lazy-load → scroll the page before counting loaded images.

## Environment quirks

- Never pipe git output to `Select-Object` in PowerShell (breaks paging/state); use `git --no-pager` or `| cat`.
- PowerShell strips `$_` and `$var` inside inline WSL/bash one-liners → write a `.ps1`/`.sh` file or use single-quoted here-strings.
- Files created on Windows get CRLF → strip `\r` (`sed -i 's/\r$//'`) before running under WSL bash; `set -euo pipefail\r` fails with "invalid option name".
- WSL services bind to the WSL IP, not localhost — curl the WSL IP when verifying dev servers from Windows.
- Use `?v=N` cache busters when re-checking updated assets in a browser.
- `robocopy` argument order is SOURCE DEST (opposite of cp).
- For HTTPS push: `gh auth setup-git`. Fresh clones may need `-c user.name` / `-c user.email` on the commit.

## Analysis principles

- Theme XML lies: actual `srgbClr`/`latin typeface` usage in slides is the ground truth. Report both, rank by usage.
- Dedupe media across language variants before reporting sizes; identical images otherwise inflate the asset inventory.
- Slide size comes from `ppt/presentation.xml` `sldSz` (EMU); divide by 914400 for inches.
