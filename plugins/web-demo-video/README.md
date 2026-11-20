# web-demo-video Agent Plugin

A portable Agent Plugins 1.0 capability that records **product-demo videos of web pages that already exist**. It drives a real browser with Playwright from a JSON storyboard. Each video combines:

- the **real page** (nothing is rebuilt);
- **captions** in a bottom band over a dark gradient;
- a **fake visible cursor** (headless Chrome draws none);
- a gentle **camera zoom** (body transform around the viewport centre, at most about 1.1);
- **real interactions**: clicks, typing, selects, drags, scrolls;
- optional **offline voice-over** (Piper TTS), mixed with ffmpeg and normalised to -16 LUFS.

It is the opposite of rebuilding the interface as animated components. See [`docs/related-work.md`](docs/related-work.md).

```text
plugins/web-demo-video/
├── plugin.json                  generated (do not edit)
├── distribution.config.json     package identity
├── README.md
├── docs/
│   ├── related-work.md          launch-video-kit, Remotion, motion-content-production, Playwright recordVideo
│   └── roadmap.md               open work (TODO)
└── skills/
    └── web-demo-video/
        ├── SKILL.md
        ├── references/
        │   ├── storyboard.md    JSON schema and every action
        │   └── lessons.md       hard-won rules
        ├── scripts/
        │   ├── record.mjs       the engine
        │   ├── mix.mjs          voice lines + loudnorm -> webm and mp4
        │   ├── review.mjs       frames, sync frames, loudness report
        │   └── fix-piper-voice.mjs
        └── examples/
            ├── demo-site/index.html        fictitious static app
            └── storyboard.example.json     drives the demo site
```

## Install

```bash
copilot plugin marketplace add svg153/skills
copilot plugin install web-demo-video@svg153-skills
```

In Claude Code, add the `svg153/skills` marketplace and install `web-demo-video`. You can also copy `skills/web-demo-video/` into your skills folder.

## Quick start

```bash
# 1. a tools folder (nothing is vendored in the repo)
mkdir tools && cd tools && npm i playwright-core ffmpeg-static ffprobe-static && cd ..

S=plugins/web-demo-video/skills/web-demo-video
# 2. dry run, captions only, with screenshots in out/shots
node $S/scripts/record.mjs $S/examples/storyboard.example.json out --tools tools --no-voice --browser "<path to chrome>"
# 3. record with voice (needs Piper under tools/piper and a voice under tools/voices), mix, review
node $S/scripts/record.mjs $S/examples/storyboard.example.json out --tools tools --browser "<path to chrome>"
node $S/scripts/mix.mjs out --tools tools
node $S/scripts/review.mjs out
```

The example storyboard is in Spanish and expects the Piper voice `es_ES-davefx-medium`. For another language, change `config.voice.model` and the texts.

Outputs in `out/`: `<name>.webm` (silent recording), `<name>-voice.webm` and `<name>-voice.mp4` (with voice), `shots/`, `review/report.md`, `vo.json`, `timeline.json`.

## Requirements

| Need | For |
|---|---|
| Node.js 20+ and `playwright-core` | recording (always) |
| A Chromium-based browser (Chrome, Edge) or `npx playwright install chromium` | recording |
| A full ffmpeg and ffprobe (npm `ffmpeg-static`, `ffprobe-static`) | mixing, MP4, review. Playwright's bundled ffmpeg is not enough |
| [Piper](https://github.com/rhasspy/piper) and a voice model | optional offline voice-over. Without it you get captions only |

## Privacy

Everything runs locally. The voice is offline (Piper) and no text is sent anywhere. The plugin ships fictitious examples only; client pages, texts and screenshots must stay out of the repository. `tools/`, `out/` and `vo-cache/` are git-ignored.

## Limits

The agent cannot hear audio, so pronunciation and pacing always need a human listen. See [`docs/roadmap.md`](docs/roadmap.md) for open work.
