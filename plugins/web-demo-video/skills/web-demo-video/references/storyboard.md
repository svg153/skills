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
| `viewport` | `{width:1280,height:720}` | Browser viewport and video size. Caption font sizes scale with the width. Use `1920x1080` for visibly sharper text (see lessons.md) |
| `executablePath` | Playwright's chromium | Path of a Chromium-based browser (also `--browser` or env `WEB_DEMO_VIDEO_BROWSER`, which win) |
| `channel` | none | Playwright channel such as `chrome`, used when no executable is given |
| `headless` | `true` | Run without a window |
| `baseDir` | `.` | Folder for relative `file` paths, relative to the storyboard |
| `language` | none | Informational: language of captions and voice |
| `voice` | none | `{ model, piper?, lengthScale?, sentenceSilence?, polish?, trimDb? }`. No `voice` (or `--no-voice`) means captions only. `model` is an absolute path or a file under `<tools>/voices/`. `piper` defaults to `<tools>/piper/piper.exe`. `lengthScale` defaults to `1.1` (about 155 words/min in Spanish with davefx; 1.0 is about 165) and `sentenceSilence` to `0.25` s. `polish` (default `true`, needs ffmpeg-static in the tools dir) trims leading and trailing silence below `trimDb` (default `-45`) and loudnorms each line to -16 LUFS / TP -1.5 |
| `music` | none | `{ file, volume?, duckTo?, fadeIn?, fadeOut? }`. Background bed, looped and trimmed to the video length, high-passed at 100 Hz. `volume` (default `0.25`) and `duckTo` (default `0.08`) are linear gains: the music sits at `volume` and glides to `duckTo` from 0.25 s before each voice line to 0.6 s after it. `fadeIn` / `fadeOut` in seconds (defaults 1.5 / 2.5). `file` is absolute or relative to `baseDir`. `mix.mjs --music <file>` overrides it. `scripts/make-music-bed.mjs` makes a royalty-free test bed |
| `pronunciation` | `[]` | List of `[regex, replacement, flags?]` applied to the text sent to the TTS only. Flags default to `g` |
| `style` | see below | Caption and title tokens |
| `maxZoom` | `1.1` | Upper bound for any `zoom` scale |
| `cursor` | `{path:"bezier", ripple:true}` | `path`: `bezier` (curved, eased, small overshoot, seeded so re-records match) or `straight` (old straight line). `ripple`: a ring that expands at every mouse press |

`style` tokens: `background` (title card, default `#04122e`), `accent` (label and subtitle colour, `#7fd6ff`), `text` (`#ffffff`), `bandRgb` (the gradient colour as `"r,g,b"`, `"4,18,46"`), `font`, `captionPx`, `labelPx`, `titlePx`, `subtitlePx`.

## Actions

Every step has an `action` and these fields. Selectors are Playwright selectors (CSS, `text=...`, `role=...`). Only the first match is used.

| Action | Fields | What it does |
|---|---|---|
| `title` | `title`, `subtitle`, `say` | Shows a dark card (a `data:` URL page) and holds it for `max(3.5 s, voice + 0.9 s)` |
| `goto` | `url` or `file`, `waitMs?` | Navigates, waits for load, removes any caption, wakes the fake cursor |
| `caption` | `label`, `text`, `say?`, `shot?`, `extraMs?` | Shows the caption. Spoken text is `say`, or `text` when `say` is missing, or nothing when `say` is `false`. `shot` saves a screenshot right after the fade-in. Holds `max(2.8 s, 70 ms x chars, voice + 0.7 s) + extraMs` |
| `uncaption` | none | Fades the caption out |
| `click` | `selector`, `focus?` | Glides the cursor to the element centre, then real mouse down and up (the cursor shrinks on press and a ripple ring shows). `focus: true` (or a scale, default 1.06) zooms gently around the click point while pressing, then back out |
| `type` | `selector`, `text`, `delayMs?` (45), `clear?` | Clicks, then types key by key. `clear: true` empties the field first (use with `text: ""` to only clear) |
| `select` | `selector`, `value` | Glides to the `<select>`, then `selectOption` (no open native dropdown) |
| `scroll` | `to`, `offset?` (80), `keepCaption?`, `ms?` | Smooth scroll so `to` sits `offset` px from the top. `to` is a selector or `"text:Heading"` (first h1-h6 containing the text). Removes the caption first unless `keepCaption` |
| `zoom` | `selector?`, `scale?` (1.1) | Brings `selector` to mid-screen, then zooms the body around the **viewport centre**. Capped by `maxZoom` |
| `unzoom` | none | Back to 1 |
| `spotlight` | `selector`, `padding?` (10), `radius?` (12), `ms?` (900) | Dims the whole page except the element (rounded hole with an accent outline that glides to the next element). Stays, and follows scrolling, until `unspotlight`. Do not combine with `zoom` |
| `unspotlight` | none | Fades the dim away |
| `drag` | `selector`, `dx`, `dy`, `grip?`, `steps?`, `ms?` | Mouse down on the element, move by `dx,dy`, release. `grip`: `center` (default) or `right-edge` (3 px inside the right edge, for resize handles) |
| `hscroll` | `container`, `toSelector`, `offset?`, `ms?` | Scrolls a horizontally scrollable container so `toSelector` sits `offset` px from its left edge |
| `hover` | `selector`, `ms?` | Moves the cursor onto the element and waits |
| `wait` | `ms` | Plain pause |
| `shot` | `name` | Screenshot now (`shots/NN-name.png`) |
| `evaluate` | `js`, `ms?` | **Escape hatch.** Evaluates `js` in the page (an expression; wrap statements in `(() => { ... })()`). Use it only for site-specific needs that no action covers, and keep it out of examples that others will copy |

## Behaviour that is built in

- The camera uses a spring-like ease (slight overshoot). It zooms only on `zoom` and `click` with `focus`, and resets by itself when the page scrolls or navigates, so it never stays zoomed into the wrong place.
- The recording opens on a dark `data:` card, so the first frames are never a half-loaded page.
- Overlays (caption, cursor, zoom helper) are injected into every page and recreated after each navigation. The cursor is woken by a 1 px mouse move.
- A voice line starts 0.35 s after its caption appears. The line is logged in `vo.json`; `mix.mjs` converts that to audio delays.
- `timeline.json` entries carry `scene` and `end` (when the caption faded) and `vo.json` carries `scenes` (name and start) and `language`: `export.mjs` builds subtitles and chapters from them. No new storyboard fields.
- Voice lines are all synthesised before the browser starts (so Piper/ffmpeg time never freezes the recording) and cached in `<outDir>/vo-cache` by model, speed, silence, trim and text. `vo.json` logs `dur` (trimmed) and `rawDur` (as Piper wrote it).
- The final mix is loudnorm -16 LUFS, then a limiter at -1.5 dBFS so the decoded peak stays under -1 dBFS.
- Unknown actions and missing selectors stop the run with a message that names the scene.

## Robustness features

### `config.holdAfterActionMs` and `holdMs`

After every interactive action (`click`, `type`, `select`, `drag`, `hscroll`, `hover`) the engine waits `config.holdAfterActionMs` (default `400`) so actions never feel rushed. A step can override it with `holdMs`; `0` disables it. It comes on top of the action's own wait.

### `expect` (per step)

Checked after the step and its hold. Retried every 100 ms until `timeoutMs` (default 3000). One object or a list of objects:

| Key | Passes when |
|---|---|
| `visible` | the selector is visible |
| `hidden` | the selector is not visible |
| `text` | `[selector, substring]`: the element's text contains the substring (case sensitive) |
| `url` | the page URL contains the substring |
| `timeoutMs` | wait limit for this check |

```json
{ "action": "click", "selector": "#send", "expect": { "text": ["#ok", "Order sent"] } }
```

A failed `expect` (or any step that throws, such as a selector that matches nothing; Playwright's timeout is 8 s) stops the run with exit code 1. The message names the scene and step, prints the step JSON and saves `shots/FAIL-s<scene>-step<n>-<action>.png`. No video is written for a failed run.

### `lint.mjs`

`node lint.mjs story.json [--tools dir] [--strict]` checks the storyboard without a browser: unknown actions or fields (fields starting with `_` are comments), missing required fields, captions that wrap (warn above one line, error above two; about `0.85 x width / (0.5 x captionPx)` characters per line), a `click`/`drag` followed straight by another click/drag or ending the scene with no hold, a `zoom` never undone by `unzoom` before the scene ends (error), `goto` files and the voice model that do not exist. Exit 1 on errors (or on warnings with `--strict`). `record.mjs` runs it first; `--no-lint` skips it.

### `--preview`

`node record.mjs story.json out --preview [--preview-div 4]`: no video and no voice. Every pause is divided by 4 (or `--preview-div`), CSS transitions and smooth scrolling are made instant so shots still show the final state, and the caption `shot`s are saved. Writes `preview-steps.json` (seconds per step). Use it to iterate on selectors and `expect`s. About 2.7x faster on the example (28 s against 77 s): mouse glides and page loads do not shrink.

### Outputs

- `steps.json` (`preview-steps.json` in preview): `{ totalSec, steps: [{ scene, step, action, start, sec }] }` on the script clock. `review.mjs` uses it to ignore title cards.
- `vo.json` has a new field **`cue`** (seconds, script clock): when the first real page (title card or site) was committed. Before it there is only the dark opening card. In the video file that moment is `lead + cue`, where `lead` is in `mix.json`. `timeline.json` stays a plain array of captions. Consumers may trim `lead + cue` seconds from the start.
