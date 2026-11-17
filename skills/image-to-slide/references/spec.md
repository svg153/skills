# Spec JSON (shared by `build_from_spec.ps1` → pptx and `build_html.ps1` → html)

`html` output: the spec is the same; `output` and `png` are ignored (names come from `-Out`).
In the HTML, 1 CSS px = 1 pt, and text follows PowerPoint semantics (no default margin, line wrapping only with `wrap` or when not left-aligned).
Limitations of the HTML viewer (acceptable; warn the user if the slide uses them):
- `donut`, `can`, `cube` and `cloud` come out as a rectangle.
- `chart` `scatter` is not supported.
- The dashed border of a rectangular shape always comes out as `dashed`.

## Units and conventions
- Coordinates in **source image px** (`sourceWidth`, default 2000). The engine converts them to a 16:9 slide of 960×540 pt (×0.48 if the source is 2000 px wide).
- Font sizes in **pt**. Colors as 6-digit hex without `#`.
- `elements` is in **layer order**: the first one ends up at the back.
- Texts in UTF-8 (accents, `≈`, `€` are fine). `\n` = line break within the paragraph.
- Paths are relative to the JSON's folder. `@logos/<file>.svg` = logo looked up first in the client profile (if any) and then in the skill's `assets/logos`.

## Document
```json
{ "sourceWidth": 2000,
  "output": "Nombre.pptx",           // if it exists and is open -> Nombre_v2.pptx
  "png": "Nombre.png",               // only with 1 slide; with several: Nombre_s1.png, Nombre_s2.png…
  "theme": { "font": "Segoe UI", "headFont": "Segoe UI", "text": "374151", "bg": "FFFFFF" },
  "background": { "color": "FFFFFF" },   // or { "image": "fondo_limpio.png" }
  "profile": "C:/ruta/perfil.json",      // optional: client profile (logos + theme); also IMAGE_TO_SLIDE_PROFILE
  "elements": [ … ],
  "notes": "speaker notes", "doubts": [ "illegible text in…" ] }
```
For several slides in one file: `"slides": [ { "background", "elements", "notes", "doubts" }, … ]`.

## Common fields
`name` (name in the selection pane; always set it), `group` (elements with the same value are grouped), `rotate` (degrees), `alt` (alt text for images), `confidence` (0-1; < 0.7 goes to the doubts).

## Element types
### `text`
`x y w h`, `text` **or** `paragraphs:[{text, size, bold, italic, color, align, bullet: true|"number", level}]`, `size`, `color`, `bold`, `italic`, `font`, `role` (`title`/`subtitle` use `theme.headFont`), `align` left|center|right|justify, `anchor` top|middle|bottom, `lineSpacing` (exact pt), `spaceAfter` (pt), `charSpacing` (pt), `wrap`, `fill`, `margin`,
`runs:[{match, all, bold, italic, underline, color, size, gradient:[c1,c2]}]` (formats the first occurrence of `match`, or all of them if `all: true`).
- If `wrap` is false (the default) and the text is left-aligned, the line breaks are yours (`\n`) and nothing is reflowed.
- With `align` center or right, line wrapping is enabled automatically.
- Bullets: `bullet: true`. Never type `•` in the text.

### `shape` (and its alias `rect`)
`shape`: rect, roundRect, ellipse, triangle, rtTriangle, diamond, parallelogram, trapezoid, hexagon, octagon, plus, regularPentagon, homePlate/pentagon, chevron, rightArrow, leftArrow, upArrow, downArrow, leftRightArrow, star5, donut, can, cube, cloud, flowChartProcess, flowChartDecision, flowChartTerminator.
Fields: `x y w h`, `fill` (null = no fill), `fillTransparency` 0-1, `line` ("HEX" or `{color, width, dash}`), `lineWidth`, `radius` 0-0.5 (roundRect), `shadow` true.
Text inside the shape: the same fields as `text`, set on the shape itself.
`rect` with `radius > 0` = roundRect.

### `line`
`x1 y1 x2 y2`, `color`, `width` (pt), `dash` solid|dash|dot|squareDot|dashDot|longDash, `beginArrow`/`endArrow` none|triangle|arrow|stealth|diamond|oval.

### `picture` / `svg`
`picture`: `path` (png/jpg/svg). `svg`: `svg` with the full inline markup, for icons.
For a piece cropped from the source (photo in a card, logo without an official SVG): `crop.ps1 -Box "x0,y0,x1,y1" [-Transparent]` prints the `picture` line with `x y w h` already set; add `name` and `alt`.
`x y w [h]`: without `h` it keeps the aspect ratio.
Icons: stroke, viewBox `0 0 24 24`, `stroke-width` 1.7 and the theme color. No `<use>`, filters or `<text>`; linear and radial gradients do work.
Icon size: the drawing fills about 3/4 of the viewBox, so set `w` ≈ icon width in the source × 1.3 and center it on the original icon's center (not its corner).
The engine warns if an image covers more than 80 % of the slide: it is only accepted as a clean background.

### `table`
`x y w h`, `rows` (array of rows; each cell is a text or `{text, bold, color, fill, align, size}`), `colW` (px), `size`, `color`, `fill`, `align`, `header: {fill, color, bold}` (first row), `border: {color, width}`.

### `chart` (native, needs Excel)
`chartType`: bar | line | pie | doughnut | area | scatter. `dir` col|bar, `stacked`, `markers`.
`series:[{name, labels:[…], values:[…]}]`, `title`, `colors:[…]` (per series; in pie/doughnut, per slice), `showValue`, `valueFormat` ("0", "0.0%"…), `showLegend`, `estimated` (true if you eyeballed the bars: goes to the doubts).

## Tested recipes
- **Card with icon**:
  - `shape` roundRect with fill F3F4F6, radius 0.14 and shadow.
  - `svg` of ~75 px, vertically centered.
  - vertical `line`, 8 px from the card's edge at the top and bottom.
  - `text` with the same box as the card, `anchor: middle` and the bold label in `runs`.
- **Centered box** with several lines of different sizes: `text` with `align: center` and `paragraphs`, each with its own `size`.
- **Gradient word** (e.g. «degradado»): `runs:[{match:"degradado", gradient:["14B8A6","2563EB"]}]`.
- **Spaced label** («S E C C I Ó N»): write the text normally and add `charSpacing` 4-5.
- **Complete, tested examples**: `examples/ejemplo_tarjetas.json` (cards and logos) and `examples/ejemplo_completo.json` (diagram, table, bullets, charts and two slides).
