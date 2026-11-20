---
name: web-demo-video
description: "Record a product-demo video of a web page that already exists by driving a real browser with Playwright from a storyboard: captions, a visible cursor, gentle zoom, real clicks and typing, optional offline voice-over. USE FOR: record a demo video of this web app, screen recording with captions and voice-over of an existing site, narrated walkthrough of my dashboard, make a product demo from these pages, graba un vídeo demo de esta web, vídeo de demostración con subtítulos y voz en off, grabar un recorrido de mi página con cursor y zoom, demo narrada de una aplicación web existente. DO NOT USE FOR: rebuild the UI as animated components (Remotion), promo or launch videos made from scratch, motion graphics, edit an existing video file, record a desktop app or the whole screen, vídeo promocional desde cero, animaciones con Remotion, editar un vídeo ya grabado."
license: "MIT"
compatibility: "Node.js 20+ with playwright-core (npm i playwright-core) and a Chromium-based browser. Mixing and review need a full ffmpeg/ffprobe (npm ffmpeg-static, ffprobe-static). Optional offline voice: Piper TTS plus a voice model."
metadata:
  author: "svg153"
  version: "0.1"
---

# Web demo video: record the real page, not a copy

## Activation Contract

Use it when the user has a **web page or app that already exists** (a URL, or local HTML files) and wants a **demo video** of it: real interactions, captions, optionally a voice-over. The page is recorded as it is. Nothing is rebuilt.

Do not use it to build a video from scratch out of animated components (that is Remotion, or `motion-content-production`), to make a promo or launch video, to edit a video that already exists, or to record a desktop app or the full screen. If the user has no page yet, build the page first, then come back.

**Reply in the user's language.** These instructions are in English; the conversation and the captions follow the language the user asks for.

Privacy rules (always):

- **Offline voice by default** (Piper). Never send a script, captions or page content to a cloud TTS or any online service unless the user asks for it explicitly, because the scripts often describe private material.
- **Never put client data in examples, committed files or this plugin**: names, URLs, texts, screenshots. Examples stay fictitious.
- Recordings of internal pages stay on the user's machine. Do not upload them.

What each video combines: the real page; captions in a bottom band over a dark gradient; a fake visible cursor (headless Chrome draws none); a gentle camera zoom (max about 1.1); real clicks, typing, selects, drags and scrolls; optional voice-over mixed with ffmpeg.

Ideas taken from `launch-video-kit`: voice first then edit, one WAV per line, loudness normalised to -16 LUFS, camera still and moving only just before the next framing, big captions over a darkened lower band, and verifying by measuring (frames, loudness) instead of trusting. See `docs/related-work.md` in the plugin.

## Files

| Path (under `${CLAUDE_SKILL_DIR}`) | Purpose |
|---|---|
| `scripts/record.mjs <storyboard.json> <outDir> [--tools dir] [--no-voice] [--preview] [--browser exe]` | Engine. Drives the browser and writes `<name>.webm`, `vo.json`, `timeline.json`, `shots/` |
| `scripts/mix.mjs <outDir> [--ffmpeg p] [--ffprobe p] [--tools dir]` | Lays the voice lines on the video, loudnorm, writes `<name>-voice.webm` and `.mp4` |
| `scripts/review.mjs <outDir> [--every N]` | Frames every N s, a sync frame per voice line, loudness report, black/freeze/silence detectors (PASS/WARN) |
| `scripts/lint.mjs <storyboard.json> [--tools dir]` | Offline storyboard validation; exit 1 on errors. `record.mjs` runs it first |
| `scripts/export.mjs <outDir> [--aspect 16:9/1:1/9:16] [--soft-subs] [--gif] [--gif-fps N] [--gif-width N] [--gif-from S] [--gif-seconds S]` | `.srt` and `.vtt` from the captions, an MP4 with scene chapters (optional mov_text track), an aspect preset, a two-pass-palette GIF. Writes to `<outDir>/export/` |
| `scripts/fix-piper-voice.mjs <voice.onnx.json>` | Patches voices that Piper for Windows 2023.11.14-2 rejects |
| `references/storyboard.md` | The storyboard JSON: config and every action |
| `references/lessons.md` | Hard-won rules. Read before the first recording |
| `examples/` | A fictitious site and a storyboard that drives it |

## Setup (once)

1. `npm i playwright-core` next to the scripts, or in a tools directory passed with `--tools`. Do not vendor binaries.
2. A Chromium-based browser: set `config.executablePath`, `--browser`, or the env var `WEB_DEMO_VIDEO_BROWSER`. Without any of them, Playwright's own chromium is used (`npx playwright install chromium`).
3. For mixing and review: `npm i ffmpeg-static ffprobe-static` in the same tools directory. Playwright's bundled ffmpeg is not enough (`references/lessons.md`).
4. Optional voice: Piper under `<tools>/piper/` and a voice under `<tools>/voices/`. If Piper for Windows rejects the voice JSON, run `scripts/fix-piper-voice.mjs`. On Windows prefer Piper over SAPI, which usually has English voices only.

## Workflow

1. **Inventory the site.** List its screens and, for each, the use case it serves ("who does what with it"). If the page shows a "generated on" or "stale" banner, regenerate the site first. Open it and note stable selectors.
2. **Write the storyboard: story first, voice lines first.** Write the narration as one short line per beat before any selector. Each line is a caption plus its `say`. Then add the actions that make the line true. Follow `references/storyboard.md`. Put pronunciation fixes (acronyms, product names, versions) in `config.pronunciation`.
3. **Dry run with screenshots.** `node record.mjs story.json out --no-voice` is fast and tests every selector. Give captions a `shot` name and read `out/shots/*.png`: the caption must not hide the thing it talks about, and no native dropdown should be open. Fix selectors and wording.
4. **Record.** Same command with voice on (drop `--no-voice`). Voice lines are cached by text, so re-recording only synthesises what changed.
5. **Mix.** `node mix.mjs out --tools <dir>`. It prints the video length, the logged end and the head start. Without voice it only converts.
6. **Review by measuring.** `node review.mjs out`. Open the sync frames: the caption on screen at each line start must match the voice line in the report. Check the overview frames for half-loaded pages, stale captions and clipped zoom. Loudness should be about -16 LUFS integrated with peak under -1 dBFS. A subagent can review the frames in parallel, one per batch, with the report as its checklist.
6b. **Export (optional).** `node export.mjs out --tools <dir>` writes `.srt`/`.vtt` and an MP4 with one chapter per scene. Add `--aspect 9:16` for vertical, `--soft-subs` for a selectable subtitle track, `--gif` for a clip. Check with `ffprobe -show_chapters`.
7. **Deliver**, and say plainly what was **not** verified. The agent cannot hear audio: pronunciation, pacing and voice quality need a human listener. State the video path, duration, loudness numbers and what was checked on frames.

## Rules

- Prefer real interactions (`click`, `type`, `select`, `drag`) over `evaluate`. `evaluate` is an escape hatch for site-specific needs only.
- One idea per caption. Hold time is `max(2.8 s, 70 ms per character, voice + 0.7 s)`.
- Remove the caption (`uncaption`) before moving to a new section. `scroll` and `goto` already do it.
- Keep zoom at or below 1.1 and return to 1 before leaving the section.
- If something fails, fix the storyboard, not the output. Never edit the video by hand.
