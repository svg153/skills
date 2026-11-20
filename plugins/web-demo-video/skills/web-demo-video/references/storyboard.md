# Storyboard format

A storyboard is one JSON file: a `config` block and a list of `scenes`, each with `steps`. Relative paths (`baseDir`, `file`) are resolved from the storyboard file's folder (or from `baseDir`, which is itself relative to it). See `examples/storyboard.example.json`.

```json
{
  "config": { "viewport": { "width": 1280, "height": 720 }, "voice": { "model": "es_ES-davefx-medium.onnx" } },
  "scenes": [
    { "name": "Intro", "steps": [
      { "action": "title", "title": "My product", "subtitle": "A short tour", "say": "My product. A short tour." },
      { "action": "goto", "file": "site/index.html" },
      { "action": "caption", "label": "Home", "text": "The home page shows what matters today", "shot": "home" }
    ] }
  ]
}
```

## `config`

| Key | Default | Meaning |
|---|---|---|
| `name` | `demo` | Base name of the output files |
| `viewport` | `{width:1280,height:720}` | Browser viewport and video size. Caption font sizes scale with the width |
| `executablePath` | Playwright's chromium | Path of a Chromium-based browser (also `--browser` or env `WEB_DEMO_VIDEO_BROWSER`, which win) |
| `channel` | none | Playwright channel such as `chrome`, used when no executable is given |
| `headless` | `true` | Run without a window |
| `baseDir` | `.` | Folder for relative `file` paths, relative to the storyboard |
| `language` | none | Informational: language of captions and voice |
| `voice` | none | `{ model, piper?, lengthScale?, sentenceSilence? }`. No `voice` (or `--no-voice`) means captions only. `model` is an absolute path or a file under `<tools>/voices/`. `piper` defaults to `<tools>/piper/piper.exe` |
| `pronunciation` | `[]` | List of `[regex, replacement, flags?]` applied to the text sent to the TTS only. Flags default to `g` |
| `style` | see below | Caption and title tokens |
| `maxZoom` | `1.1` | Upper bound for any `zoom` scale |

`style` tokens: `background` (title card, default `#04122e`), `accent` (label and subtitle colour, `#7fd6ff`), `text` (`#ffffff`), `bandRgb` (the gradient colour as `"r,g,b"`, `"4,18,46"`), `font`, `captionPx`, `labelPx`, `titlePx`, `subtitlePx`.

## Actions

Every step has an `action` and these fields. Selectors are Playwright selectors (CSS, `text=...`, `role=...`). Only the first match is used.

| Action | Fields | What it does |
|---|---|---|
| `title` | `title`, `subtitle`, `say` | Shows a dark card (a `data:` URL page) and holds it for `max(3.5 s, voice + 0.9 s)` |
| `goto` | `url` or `file`, `waitMs?` | Navigates, waits for load, removes any caption, wakes the fake cursor |
| `caption` | `label`, `text`, `say?`, `shot?`, `extraMs?` | Shows the caption. Spoken text is `say`, or `text` when `say` is missing, or nothing when `say` is `false`. `shot` saves a screenshot right after the fade-in. Holds `max(2.8 s, 70 ms x chars, voice + 0.7 s) + extraMs` |
| `uncaption` | none | Fades the caption out |
| `click` | `selector` | Glides the cursor to the element centre, then real mouse down and up |
| `type` | `selector`, `text`, `delayMs?` (45), `clear?` | Clicks, then types key by key. `clear: true` empties the field first (use with `text: ""` to only clear) |
| `select` | `selector`, `value` | Glides to the `<select>`, then `selectOption` (no open native dropdown) |
| `scroll` | `to`, `offset?` (80), `keepCaption?`, `ms?` | Smooth scroll so `to` sits `offset` px from the top. `to` is a selector or `"text:Heading"` (first h1-h6 containing the text). Removes the caption first unless `keepCaption` |
| `zoom` | `selector?`, `scale?` (1.1) | Brings `selector` to mid-screen, then zooms the body around the **viewport centre**. Capped by `maxZoom` |
| `unzoom` | none | Back to 1 |
| `drag` | `selector`, `dx`, `dy`, `grip?`, `steps?`, `ms?` | Mouse down on the element, move by `dx,dy`, release. `grip`: `center` (default) or `right-edge` (3 px inside the right edge, for resize handles) |
| `hscroll` | `container`, `toSelector`, `offset?`, `ms?` | Scrolls a horizontally scrollable container so `toSelector` sits `offset` px from its left edge |
| `hover` | `selector`, `ms?` | Moves the cursor onto the element and waits |
| `wait` | `ms` | Plain pause |
| `shot` | `name` | Screenshot now (`shots/NN-name.png`) |
| `evaluate` | `js`, `ms?` | **Escape hatch.** Evaluates `js` in the page (an expression; wrap statements in `(() => { ... })()`). Use it only for site-specific needs that no action covers, and keep it out of examples that others will copy |

## Behaviour that is built in

- The recording opens on a dark `data:` card, so the first frames are never a half-loaded page.
- Overlays (caption, cursor, zoom helper) are injected into every page and recreated after each navigation. The cursor is woken by a 1 px mouse move.
- A voice line starts 0.35 s after its caption appears. The line is logged in `vo.json`; `mix.mjs` converts that to audio delays.
- Voice lines are cached in `<outDir>/vo-cache` by model and text.
- Unknown actions and missing selectors stop the run with a message that names the scene.
