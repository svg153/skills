---
name: imagen-a-slide
description: "Rebuild slide images (PNG, JPG, PDF or screenshots) as editable slides with the same design, in PPTX or single-file HTML. USE FOR: rebuild this slide image as an editable pptx, make an HTML from this slide, clean the background of a cover slide, replace drawn logos with official ones, hazme un pptx editable de esta imagen, hazme un HTML de esta diapositiva, rehacer esta slide, convertir esta imagen en diapositiva, limpiar el fondo de una portada, poner logos oficiales. DO NOT USE FOR: create a deck from scratch, edit an already editable pptx, extract a design system from a deck, crear una presentación desde cero, editar un pptx que ya es editable."
license: "MIT"
compatibility: "Windows with PowerShell 5.1. pptx output: desktop PowerPoint (Excel only for native charts). html output: Microsoft Edge only for the control PNG. Optional: Podman or Python with numpy, opencv and scikit-image for the numeric comparison."
metadata:
  author: "svg153"
  version: "2.2"
---

# Slide image → editable PPTX and/or single-file HTML

## Activation Contract

Use it when the user provides one or more **images of already designed slides** (PNG/JPG/WEBP, screenshots, an exported PDF, or a PPTX whose slides are just pictures) and wants them back **editable with the same design**: as PowerPoint (`pptx`, default), as one self-contained HTML file (`html`), or both (`both`; `ambos` is accepted as an alias). Optional argument: `[pptx|html|both] <image(s)>`. It also covers cleaning the background of a cover slide so editable texts can go on top, and replacing drawn logos with the official ones.

Do not use it to create a new presentation without a reference image, to edit a `.pptx` that is already editable, to extract the design system of an existing deck (that is `deck-design-system`), or outside Windows when `pptx` is requested.

Client data (logos, palette, grid) never lives inside this skill. It goes in a local profile (§1, "Client profiles").

**Reply in the user's language.** These instructions are in English; the conversation, the summaries and any text you write for the user follow the language the user writes in.

Goal: a slide that can be **edited as if it had been made by hand**. Never paste the whole slide as a picture and call it editable.

The flow separates **thinking** (main model) from **executing** (fixed engines + smaller models). Nobody writes PowerPoint or HTML code: you write a **JSON spec** (`references/spec.md`), shared by both outputs, and an engine renders it:

| Output (`$ARGUMENTS`) | Engine | Result |
|---|---|---|
| `pptx` (default) | `build_from_spec.ps1` | one `.pptx` per slide + control PNG |
| `html` | `build_html.ps1` | **one single `.html`** (viewer, spec and images inside; send it and it opens in any browser with no network) + control PNG |
| `both` | both, from the same spec | `.pptx` + `.html` |

If the user does not name the output, it is `pptx`. "Web presentation", "HTML", "to email and open in the browser" = `html`. Steps 0-4 are identical; only the build engine and the delivery change.

Everything is local: PowerShell 5.1 + PowerPoint (and Excel only for native charts in pptx); HTML only needs Edge for the control PNG. No Node, Python or containers are needed (only the optional `compare.ps1` step uses Podman or Python). **Never upload client images or texts to external services.** The only allowed download is public logos (§1).

Always run the scripts like this (quote paths with spaces):
`powershell -NoProfile -ExecutionPolicy Bypass -File "${CLAUDE_SKILL_DIR}/scripts/<script>.ps1" <args>`

Fixed identifiers (other scripts and the agents parse them, so they stay as they are): the safety line `presentaciones abiertas antes=N despues=N`, the doubts file `<name>_dudas.md` and the `dudas=` count, and the JSON keys of the comparison (`size_sugerido`, `avisos`, `dx`, `dy`…).

| Script | Purpose |
|---|---|
| `build_from_spec.ps1 -Spec x.json` | spec → `.pptx` + `.png` per slide (+ `_dudas.md` if there are doubts) |
| `ocr.ps1 -Src img [-Out x.ocr.json]` | Local Windows OCR: the box of each line (numbered, `n`) and a font size computed **from the measured width** (`pt_regular`/`pt_bold`). Also writes `x.ocr.png`, the image with every line boxed and numbered: blue = text, red = no size (icons, symbols). Whatever is not boxed (most icons) is measured by reading the image. `-NoOverlay` skips it |
| `crop.ps1 -Src img -Out piece.png -Box "x0,y0,x1,y1" [-Transparent]` | Crops a region of the source as a movable `picture`: a photo or screenshot inside a card, a logo with no official SVG, or a complex icon not worth redrawing. `-Transparent` removes a **flat** background (no halo). Prints the spec line ready to paste. Not for taking a photo out of a gradient (use `clean_bg` for that) |
| `clean_bg.ps1 -Src img -Out background.png -Boxes "x0,y0,x1,y1;…"` | Erases texts and logos from an image and continues the gradient (background plate). Use **one box per block**, with ≥ 25 px margin left and right (box edges blend 12 px into the original) and ~20 px above and below (accents and descenders). Always look at the resulting PNG |
| `prepare_pptx.ps1 -Src flat.pptx -OutDir pages` | PPTX of pictures → `pages/sN.png` + `manifest.json` with the speaker notes |
| `prepare_pdf.ps1 -Src deck.pdf -OutDir pages [-Pages "1,3-5"]` | PDF (exported or scanned slides) → `pages/sN.png` + `manifest.json`, with the Windows PDF reader. Warns if a page is not 16:9 |
| `build_html.ps1 -Spec a.json[,b.json] -Out deck.html` | `html` output. The SAME spec → **one self-contained `.html`**: the viewer `html/deck.js` and `deck.css`, the spec and the images in base64, no network or dependencies. Keys: arrows to navigate, F full screen, N notes, E edit texts, P print/PDF. Writes `<stem>_html.png` with headless Edge (temporary profile) to pass to `compare.ps1`. Charts are built-in SVG, no Excel. Font: Segoe UI (on a Mac, the system font is used) |
| `bench.ps1 -SelfTest` / `bench.ps1 -Dir <bench>` | **Test bench.** `-SelfTest`: regression with the skill's own example (identical copy = 0 warnings; copy with 3 faults = exactly those 3), no client data. `-Dir`: real cases (`original.png` + `spec.json`, which is rebuilt, or + `render.png`, which is only compared), with `history.csv` and the change against the previous run. **Run it after changing a script, a rule or an example.** Keep the bench outside the skill: it holds client slides |
| `compare.ps1 -Src source.png -Render Name.png -Spec Name.json [-Slide N]` | **Optional.** Per-element numeric comparison: SSIM, offset `dx/dy` in source px and, for texts, the width ratio with a suggested font size. Writes `Name.compare.md` and the sheet `Name.compare.png` (source, render and differences). Uses the Podman container `imagen-a-slide-compare` (built on first use) or a local Python with numpy, opencv and scikit-image. If neither is available, skip this step. `compare.ps1 -Demo` is a self-test that needs no files. Pass as `-Spec` the spec the render was built from: the suggested size is computed from its `size`. **Without `-Spec`** it finds the differing zones by itself (useful to review old reconstructions or those of another tool) |

## 0. Safety rules (mandatory)
- PowerPoint has **a single instance**: COM attaches to the user's PowerPoint, which may be editing another presentation. **Never** `Quit()` or `Stop-Process POWERPNT`/`EXCEL`, and never write your own COM code outside the scripts. The scripts only close what they open and print `presentaciones abiertas antes=N despues=N` (open presentations before/after). If the two numbers differ, stop and tell the user.
- By default, **one file per slide**, because users often copy slides by hand into their main presentation. If the target is open, the engine saves `_v2`, `_v3`…
- Always fix the spec and rebuild. Never edit the `.pptx` or `.html` by hand.
- If the spec has a `chart`, PowerPoint needs a window: the engine opens the presentation minimized. If PowerPoint was not running, an empty PowerPoint window and some background Excel processes remain at the end. Tell the user they can close them; do not close them yourself.
- `build_html.ps1` does not touch PowerPoint: with `html` output there is no COM risk. It uses headless Edge with a temporary profile, never the user's.

## 1. Classify (main model; do not delegate)
Ask only if it is unclear what matters most: **editability** (default), **visual fidelity** or **a corporate template**. For each slide decide:

| Content | Strategy |
|---|---|
| Text, cards, diagrams (boxes and arrows), tables, charts | **native**: everything as elements; tables and charts ALWAYS native |
| Photo, **any illustration with shadows, volume or gradients** (3D calendars, clipboards, glowing clouds), artistic backgrounds | **hybrid**: a clean background plate from `clean_bg` (no texts or company logos) as `background.image`, and everything else on top. More faithful and cheaper than redrawing. **Never** crop the photo with a fade: it leaves a vertical seam |
| Flat, simple illustration, or one the user wants to edit piece by piece | **native** with `svg` elements |

- **Company logos** (yours, your clients'…): always as an element, with the official SVG. The skill only ships `@logos/ejemplo_cliente.svg`, a fictitious example logo. Real logos go in a **client profile** (next point), never inside this skill.
- **Client profiles**: a client's data (logos, palette, grid, confidentiality rules) lives outside this skill, in a local skill of its own (e.g. `imagen-a-slide-<client>`) with a `perfil.json`:
  - format: `{ "name": "...", "logos": "assets/logos", "theme": { "font", "headFont", "text", "bg" } }`;
  - the spec references it with `"profile": "<path>/perfil.json"`, or the environment variable `IMAGEN_A_SLIDE_PROFILE` is used;
  - the engines look up `@logos/<file>` first in the profile's logos and then in this skill's `assets/logos`, and the profile theme fills whatever the spec does not set;
  - the client skill invokes this one and adds its data (composition). This skill knows nothing about the client.
- For a logo you do not have yet, download the SVG from `https://commons.wikimedia.org/wiki/Special:FilePath/<File>.svg` (generic User-Agent, no user data), strip DOCTYPE and metadata, and keep only viewBox + paths.
- Logos drawn into the illustration itself (e.g. product icons drawn inside the photo or illustration) stay in the background. Logos in their own box or card become elements.
- **Shared theme and grid** for multi-slide decks: fix the font once (Segoe UI by default; never Aptos), the colors, and the title position and size. Pass the same values to every spec so the title does not jump between slides of the same type.

## 2. Measure (OCR = geometry; the model = text and meaning)
1. Run `ocr.ps1` on each image. Use its `x,y,w,h` for the text boxes, and `pt_bold`/`pt_regular` as the starting font size:
   - All-bold line: `pt_bold`, about 5 % less for large titles (> 30 pt).
   - Regular line: `pt_regular`.
   - A bold label followed by regular text: start 3-4 % below `pt_regular`, or it will overflow.
   - Letter-spaced labels: the OCR overestimates; compute the size from the cap height (px × 0.48 / 0.7) and adjust `charSpacing` until the width matches.
   - Small text (< 9 pt) inside small boxes: the OCR merges or misreads lines; measure it by reading the image.

   Round to 0.5 pt and recalibrate after the first build by comparing widths.
2. The OCR text loses accents and special letters (`soluciÃ©n`, `gesti6n`): **always take the final text from the image**. Join the lines of one paragraph into a single `text`, with `\n` where the image breaks the line.
3. Non-text elements (cards, icons, lines, logos) are measured by reading the image. Check `x.ocr.png` to see what the OCR found and what it missed.
   - Photos, screenshots or logos without an official SVG that are **separate** (inside a card, not blended into the background): `crop.ps1` and a `picture` element.
4. Whatever you cannot read with confidence goes to the slide's `doubts` or to `confidence < 0.7`, and ends up in `_dudas.md`.

## 3. Split the work (see `references/subagents/DELEGATION.md`)
- **1 simple slide**: do it yourself.
- **≥2 slides, or 1 long one**: one `slide-spec-writer` subagent (Sonnet) **per slide, in parallel**. Its brief (template in `references/subagents/DELEGATION.md`) includes the image, the output, the step-1 decision, the theme and grid, and this skill's path: `${CLAUDE_SKILL_DIR}`.
- The instructions of both subagents are in `references/subagents/slide-spec-writer.md` and `references/subagents/slide-qa.md`. If your client does not have them installed as agents, launch a generic subagent with `model: sonnet` (or `haiku` for QA) and tell it to follow that file, with `Skill: ${CLAUDE_SKILL_DIR}` in the brief.
- **Complex SVG illustrations**: yourself or an Opus subagent.
- **QA**: one `slide-qa` (Haiku) per render. You decide what gets fixed.
- **Checkpoint**: for a multi-slide deck, show the user the first slide, already reviewed, before launching the rest. That way a theme mistake is not repeated across the deck.

## 4. Build, compare, fix (max. 3 rounds)
Build → `compare.ps1` (if available) → look at the PNG next to the source image (or `slide-qa`) → fix the spec → build.
- `html` output: the build is `build_html.ps1 -Spec x.json -Out x.html` and the render is `x_html.png` (or `x_html_sN.png`). With `both`, iterate with one engine (pptx) and generate the other at the end; also compare the HTML render with `compare.ps1` (HTML vs PPTX usually gives 0 warnings: both honor the spec the same way).
- `compare.md` gives objective numbers: apply the `dx/dy` directly (subtract the offset from `x/y`) and the suggested `size`. More than 15 px or more than 5 % in width is a real fault.
- Pass `compare.md` to `slide-qa` so it focuses on what the numbers cannot see: wrong text, bold, or missing elements.
- For texts, SSIM is always low against a rasterized image (different anti-aliasing, different font), so it only warns below 0.45. What counts is `dx/dy` and the width, measured with the ink box.
- **The same width ratio on every text** (e.g. all ×0.87) means a font size miscalibrated across the slide: multiply every `size` by 1/ratio.
- Huge zones (illustrations or background) with large `dx/dy` may come from the background. Check them on the sheet before moving anything.

Priority:
1. Cut or overflowing text.
2. Wrong text, line breaks or bold in the wrong place.
3. Overlapping elements, or elements touching the slide edge.
4. Missing or extra elements, and duplicated text (in the background and native).
5. Position off by more than 15 px.
6. Colors and sizes.

Stop after 3 rounds or when only unavoidable font differences remain.

## 5. Delivery
- `pptx`: the `.pptx` files (one per slide unless a deck is requested) and `_dudas.md` if it exists.
- `html`: **one single `.html` with all the slides** (pass every spec to `build_html.ps1`, in order) and `_dudas.md` if it exists. Tell the user the keys (arrows, F full screen, N notes, E edit texts, P print/PDF), that edits made with E are not kept on reload, and that outside Windows Segoe UI is replaced by the system font.
- A short summary: the strategy of each slide and its limitations (substituted fonts, redrawn illustrations).
- If it has to fit a corporate template, use the `pptx` skill afterwards.

## 6. Local notes (optional)
**Do not modify this skill's files during normal use.** If the user wants to keep what was learned, write it only to a user-local notes file **outside the skill folder** (e.g. `~/.imagen-a-slide/notes.md`, or a path the user chooses), and only if the user asks for it or agrees.
- Record only generic technical patterns: what failed (font size, overflow, a `clean_bg` box…) and how it was fixed.
- **Never** record client or company names, slide texts or figures, logos, file paths, user names or images.

Maintaining the skill (changing a script, a rule or an example) is a separate task, not part of a conversion: follow `references/maintenance.md`.
