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
- **Sync is measured with two magenta marks, not estimated.** The recording opens and closes with a 0.8 s magenta screen, and the script logs when each one ended (`syncAt`, `syncEndAt`). `mix.mjs` finds both in the video (frames at 50 fps, 4x4 px), trims before the first, retimes the video by `k = video span / script span` and cuts just before the second. Then video time = script time − `syncAt`, at the start and at the end.
- **The recording does not run at wall-clock speed.** Measured: 4.3 % slow on an 87 s demo, so a fixed offset left the voice almost 4 s early by the end. The old estimate `videoDuration − loggedEnd` was also off by up to 5 s, because closing the context adds a variable lag at the end. Recordings without marks still mix with that estimate and a warning.
- **With the video in a filter graph, `-shortest` does not stop an `apad`ded audio:** ffmpeg ran forever and ate 9 GB. Bound the audio with `atrim` to the video length instead.
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

## Audio

- **Synthesise before recording.** Piper plus ffmpeg cost seconds per line. Doing it while the page records froze the page and made a 112 s demo 212 s long. `record.mjs` now pre-synthesises every line.
- **Piper pads each line** with 0.1-0.6 s of silence at both ends. Trim it (`silenceremove`, head then reverse and head again for the tail: `stop_periods` would also cut at the pause between sentences) or lines start late against their caption.
- **Normalise each line, then the mix.** Per-line loudnorm evens the lines out; the final loudnorm sets the programme to -16 LUFS.
- **loudnorm alone does not guarantee the peak.** The measured mix peak was -0.8 dBFS in the MP4 after AAC. Put `alimiter` at 0.84 (-1.5 dB) after it.
- **Do not use `aresample` after loudnorm in a per-line filter** ("Cannot select channel layout"); set `-ar`/`-ac` on the output instead.
- **Duck music with a volume envelope built from the voice timeline**, not a sidechain: the depth is exact and does not depend on the voice level. Verify with `volumedetect` over a range with a line versus a gap.
- **Music loops cleanly** if every frequency and the tremolo complete whole cycles in the loop length (`make-music-bed.mjs`, 8 s).
- **Integrated LUFS drops when music is added** (-16.4 voice only, -19.2 with a bed 12 dB under the voice) because the music-only blocks pass the gate and dilute the average. The voice itself stays at -16: measure `volumedetect` over a line window instead (measured: 12 lines, with and without music within 0.1 dB).
- **Mono voice to stereo:** `pan=stereo|c0=0.707*c0|c1=0.707*c0`. A plain upmix lowers the level 3 dB, a full-level pan raises the stereo LUFS 3 dB.
- **The head start between video and script clock is not constant** (0.28 s, 2.25 s and 4.94 s on three runs of the same storyboard on a busy machine). That is why sync uses the magenta marks (see Recording).
- **Piper speed:** davefx at `lengthScale` 1.0 reads about 165 words/min, 1.1 about 155, 1.2 about 148. 1.1 with 0.25 s sentence silence is the clear-narration default. See the sweep in the prototype notes.

## Measuring

- **Loudness:** `ebur128` integrated about -16 LUFS, true peak below -1 dBFS. `review.mjs` reports both.
- **Sync:** extract the frame at `line start + offset (+ about 0.9 s)` and confirm the caption on screen is the one the line reads.
- **You cannot hear the result.** Say so when you deliver. A human has to check pronunciation and pacing.

## Reliability

- **A failed `expect` must stop the run and leave a screenshot.** A wrong selector or a page that did not change otherwise produces a nice-looking video of the wrong thing. Add one `expect` after each step that changes state.
- **Iterate with `--preview`, record once.** Preview skips the video and the voice and divides the holds by 4, but a full run still takes minutes.
- **Screenshots after shortened holds need instant transitions.** In preview the caption fade (0.45 s) and smooth scrolls would be half done at the shot, so preview disables them.
- **Dark title cards are not "black frames".** `blackdetect` flags them; `review.mjs` ignores the title windows and the opening card (before `lead + cue`).
- **Frozen is fine under a fresh caption.** A still page while a caption is read is normal; only long stills with no new caption count as dead air.
- **Silence between voice lines is normal; silence inside a line is not.** `silencedetect` hits are only reported when they fall inside a line's span.
- **Silent action runs show up as dead air.** The example storyboard has 8-9 s stretches with no voice; add a short caption with `say` when it matters.

## Exports

- **Subtitle times = logged time + the head start.** The video starts before the script clock, so `export.mjs` adds the same `lead` as `mix.mjs` (read from `mix.json`). Cues end when the caption fades (`timeline.json` `end`), never overlap, and wrap to two lines above 42 characters.
- **Chapters need the first one at 0.** Scene 1 is stretched back to 0 s so the title card is covered. Verify with `ffprobe -show_chapters`. MP4 also shows an extra `bin_data` stream: that is the QuickTime chapter track, not an error.
- **9:16 and 1:1 pad, they do not crop.** A desktop page is 16:9; a centred crop to 9:16 drops 68% of the width, so the cursor and clicks leave the frame. The page is scaled to the output width over a blurred, darkened copy of itself. The caption band stays attached to the page, so in 9:16 it sits mid-frame, not at the bottom.
- **GIFs are big.** A 2-minute 16:9 demo at 10 fps and 640 px is about 7 MB. Export a clip (`--gif-from`, `--gif-seconds`) at 8 fps and 480 px, two passes (`palettegen` then `paletteuse`, bayer dither, rectangle diffs).
- **Soft subtitles are mov_text** and need an MP4. Set the track language from `config.language` (`es` becomes `spa`).
## Sharpness and framing

- **`deviceScaleFactor: 2` does not work with Playwright video.** With a 2560x1440 `recordVideo.size` the page is drawn at 1x in the top-left corner and the rest is grey. Do not use it.
- **A 1920x1080 viewport is the way to a sharper video.** Text strokes are finer and less blocky than at 1280x720. The layout is the one of a bigger screen (more content fits), and caption sizes scale with the width. Cost on the example: WebM 6.3 MB vs 4.8 MB (+32%), same duration and same record time (recording is real-time bound). Default stays 1280x720; use 1920x1080 for the final take.
- **Framed output** (`frame.mjs`): render the static window (background, shadow, title bar) as a PNG with Playwright, a second PNG as the mask, then overlay with ffmpeg `alphamerge`. Expect slow encodes on a busy machine (about 5 min for 75 s at 1080p, `-preset medium`).
- **Example calendar:** an element that is scrolled sideways hides the first bars. Keep the drag step with the container at scroll 0 (`hscroll` back to `#track` offset 0) and make the whole timeline fit the drag shot.
- Ids built with `replace(/[^a-z]/g,'')` drop accented letters (`Calabacín` became `calabacn`): normalise with NFD first.
