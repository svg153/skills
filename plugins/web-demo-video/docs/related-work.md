# Related work and what to borrow

Reviewed 2026-11-20. This file covers what each project does, how it overlaps with `web-demo-video`, and which of its ideas is worth taking. Open items go to [`roadmap.md`](roadmap.md).

## `launch-video-kit`

[`borjaperfra/launch-video-kit`](https://github.com/borjaperfra/launch-video-kit) (MIT) is a kit for launch videos. It rebuilds the product UI as Remotion compositions.

| | `launch-video-kit` | `web-demo-video` |
|---|---|---|
| Screen content | a **rebuilt** UI (React components) | the **real page**, recorded |
| Engine | Remotion render | Playwright `recordVideo` + ffmpeg |
| Interactions | scripted animation | real clicks, typing, drags, scrolls |
| Best for | polished launch or promo videos | demos of a page that exists and must be shown as it is |

**Overlap:** the narration workflow. **Borrowed ideas:**

- voice first, then edit to the voice;
- one WAV per line, so one changed line re-synthesises one file;
- loudness normalised to -16 LUFS;
- "camera still, travels just before the next framing";
- big captions over a darkened lower band;
- verify by measuring (frames, loudness) instead of trusting.

Not borrowed: the rebuilt UI. A rebuild drifts from the product and costs time every time the page changes.

## Remotion

[Remotion](https://www.remotion.dev/) renders video from React. It is the right tool when the video is **designed** (brand animation, motion graphics, a UI that does not exist yet). It is the wrong tool when the question is "show this existing page". If a user wants both, record the page here and compose the clip in Remotion as a layer.

## `skills/motion-content-production` (this catalog)

| | `motion-content-production` | `web-demo-video` |
|---|---|---|
| Input | an idea, a storyboard, evidence | a URL or local HTML that already exists |
| Output | motion graphics, GIF, WebM, event promos (Remotion) | a narrated demo of the real page |
| Direction | designed animation | recorded interaction |

**Overlap:** low. Both end in video, so the Activation Contracts keep them apart: animation made from scratch goes to `motion-content-production`; a recording of an existing site goes here. An eval task covers the boundary.

## Playwright `recordVideo`

Playwright can record a browser context to WebM (`recordVideo: { dir, size }`). It is the capture layer used here. What it does not give, and this plugin adds:

- no cursor in headless Chrome (a fake one is injected);
- the video starts at page creation, so the first frames can be a half-loaded page (the engine opens on a dark card);
- no audio (voice lines are mixed afterwards with a full ffmpeg);
- the bundled ffmpeg only encodes VP8 and lacks `fps` and `scale` filters.

## Piper

[Piper](https://github.com/rhasspy/piper) is a fast offline neural TTS. It keeps scripts on the machine, which is why it is the default. Known issue: see `fix-piper-voice.mjs` and `lessons.md`.

## `ghost-cursor` and `glidecut`

[`Xetera/ghost-cursor`](https://github.com/Xetera/ghost-cursor) (MIT): human-like mouse paths (Bezier curves, Fitts-style overshoot). `web-demo-video` re-implements the idea in a few lines (cubic Bezier, ease-in-out, overshoot and settle); no code copied. [`0xbobaaa/glidecut`](https://github.com/0xbobaaa/glidecut) (MIT): a spring-driven camera and "zoom on intent, reset on scroll or page change", which the zoom helper follows. [`dxdleady/playwright-demo-video`](https://github.com/dxdleady/playwright-demo-video) (MIT): spotlight and cursor helper API as inspiration.
## Framing

The browser-window mockup on a gradient background in `frame.mjs` follows the look of **hookforge** and **truedemo** (both MIT licensed). Only the idea was used; the implementation (Playwright-rendered PNG plus an ffmpeg alpha mask) is original.

## launch-video-kit: the audio chain

[borjaperfra/launch-video-kit](https://github.com/borjaperfra/launch-video-kit) (MIT; ideas only, no code copied). Ideas only: per-line loudnorm at -16 LUFS / TP -1.5, trimming head and tail silence of each TTS line, and verifying music ducking by measurement. The implementation here is original.
