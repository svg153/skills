# web-demo-video roadmap (TODO)

This is open work, ordered by value. Every item states **why** it matters and **what counts as done**. Durable rules live in `skills/web-demo-video/references/lessons.md`.

Status legend: `[ ]` open, `[~]` partly done, `[x]` done (kept for one release, then removed).

## P1: robustness

- [ ] **A `--check` mode that validates a storyboard without recording.**
  - Why: a typo in a selector currently shows up minutes into a recording.
  - How: load each page, resolve every selector and `text:` heading, and list the failures with the scene name.
  - Done when: `record.mjs story.json out --check` exits non-zero on a missing selector and names it.
- [ ] **Measure the head start instead of estimating it.**
  - Why: `offset = videoDuration - loggedEnd - 0.3` assumes a constant context-close latency.
  - How: flash a marker (a one-frame colour change on the title card) at a logged time and detect it in the video with ffmpeg.
  - Done when: `mix.mjs` reports the measured offset and the sync frames agree within one frame.
- [ ] **A scripted sync check.**
  - Why: today a person or subagent opens the sync frames and reads them.
  - How: OCR the caption area of each sync frame and compare it with the logged text.
  - Done when: `review.mjs` prints PASS or FAIL per line without a human.

## P2: capability

- [ ] **More voices and languages in the docs.** A tested table of Piper voices per language, with the pronunciation fixes each needs.
- [ ] **Cloud TTS as an explicit opt-in**, off by default, with a warning that scripts leave the machine.
- [ ] **Burned-in or sidecar subtitles** (`.vtt`) from `timeline.json`, for players that cannot show the band.
- [ ] **Mobile viewports and touch.** Done when a storyboard with `viewport` and `isMobile` taps instead of clicking and the cursor is hidden.
- [ ] **Chapter markers** in the MP4 from scene names.
- [x] **Camera and cursor polish:** Bezier cursor with overshoot, click ripple and press animation, `spotlight`/`unspotlight`, spring zoom that resets on scroll, click `focus`.
- [ ] Ideas from research: _(add here)_
