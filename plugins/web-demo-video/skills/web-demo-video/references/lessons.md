# Lessons

Rules learned by recording real demos. Read them before the first recording.

## Tools

- **Playwright's bundled ffmpeg only encodes VP8** and has no `fps` or `scale` filters. For mixing, MP4 output and frame extraction, use a full ffmpeg, for example the npm packages `ffmpeg-static` and `ffprobe-static`. With Playwright's ffmpeg you can still extract frames with `-r 0.2 out/f%03d.png`.
- **On Windows PowerShell via Git Bash, `$_` gets mangled.** Put PowerShell code in `.ps1` files.
- **Windows SAPI usually has only English voices.** For other languages prefer Piper.
- **Piper for Windows, release 2023.11.14-2, fails with current voice JSONs** ("aɪ is not a single codepoint"). Fix: drop the multi-codepoint keys from `phoneme_id_map`. `scripts/fix-piper-voice.mjs` does it and keeps a `.bak`.
- **Offline by default.** Sending scripts to a cloud TTS can leak private data.

## Recording

- **The video starts at page creation.** Open on a dark `data:` URL title card so the first frames are not a half-loaded page. The engine always does this.
- **Voice and caption sync uses `offset = videoDuration - loggedEnd`.** The script logs each line's start on its own clock; the video clock started a little earlier. The mixer measures the video length, subtracts the logged end (and about 0.3 s for closing the context) and shifts every line by that.
- **Take review screenshots right after the caption fades in.** A shot taken earlier shows a half-transparent caption.
- **Remove the caption before scrolling to a new section.** Otherwise a stale caption sits over unrelated content. `scroll` and `goto` do it for you.
- **Zoom around the viewport centre with `html{overflow-x:hidden}`.** Do not put `overflow-x:hidden` on `body`: it breaks sticky headers. Zooming around the element centre caused horizontal clipping.
- **After each navigation the fake cursor is recreated.** Move the mouse 1 px so it shows up again.
- **Native `<select>` dropdowns render open in screenshots.** Glide the cursor to the select, then use `selectOption`.
- **Pages with a "stale" or "generated on" banner:** regenerate the site before recording, or the banner is in every frame.
- **A straight cursor line looks robotic.** The engine moves the real mouse along a seeded Bezier with easing and an overshoot, paced by wall clock (about 6 ms per move). `page.mouse.move(..., {steps})` is too fast to show in a 25 fps video.
- **Ripple colour must work on light and dark pages.** A pale accent ring vanishes on a white button: the ripple has a tinted fill and a thin dark outer line.
- **A zoom origin inside the viewport never shows blank space** (scaling up only crops), so click `focus` can zoom around the click point; the cursor then stays on the target.
- **Reset the zoom on scroll.** The transform origin is in page coordinates, so scrolling while zoomed moves the framing; the init script unzooms on any scroll or `popstate`/`hashchange`. New documents start unzoomed.
- **Spotlight is a rAF loop, not a transition.** The hole eases toward the element live rectangle, so it follows scroll. It is a fixed div outside `body`, so it does not follow `body` zoom.
- **Camera still, moves just before the next framing.** Zoom and scroll between captions, not during one.

## Measuring

- **Loudness:** `ebur128` integrated about -16 LUFS, true peak below -1 dBFS. `review.mjs` reports both.
- **Sync:** extract the frame at `line start + offset (+ about 0.9 s)` and confirm the caption on screen is the one the line reads.
- **You cannot hear the result.** Say so when you deliver. A human has to check pronunciation and pacing.
