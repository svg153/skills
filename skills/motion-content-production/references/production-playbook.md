# Production playbook

## 0. Intake and reuse

Check the existing repository and its `README`, package scripts, pinned dependencies, license, skill setup and output assets. For this catalog's author, an example starting point is [svg153/remotion-test](https://github.com/svg153/remotion-test); it is a reusable starting point, not a dependency. If the repository cannot be read, say so before choosing a new engine. Do not copy upstream code or brands without confirming their licenses/usage rights.

Minimal brief:
- Goal and a single viewer takeaway
- Viewer, distribution channel and CTA
- Duration range and aspect ratios (16:9, 9:16, square)
- Source links with last-verified date and public/private classification
- Design system or authorized brand assets; language and subtitles
- Music, speech and footage ownership/licensing
- Stage currently approved: story, storyboard, design, motion, final

## 1. Storytelling gate

Offer 2-3 meaningfully different concepts. Each proposal has:
- Hook (first 1-3 seconds)
- Problem/tension and pay-off
- Primary evidence or real visual proof
- Closing CTA, duration and platform
- Creative risk / reason it might fail

Never inflate project status, GitHub metrics, event attendance, speaking roles or client outcomes.

## 2. Storyboard gate

Use this compact schema, stored as YAML/JSON/Markdown if the project can keep files. Do not make source information the visible on-screen text.

```yaml
project: github-community-event-teaser
version: 1
status: storyboard-review
platform: linkedin
format: "9:16"
fps: 30
duration_seconds: 20
brand: "GitHub Community Spain (community, not official vendor endorsement)"
scenes:
  - id: hook
    start_seconds: 0
    duration_seconds: 3
    spoken_message: "What changes when agents join your CI pipeline?"
    on_screen_text: "Agents + CI/CD"
    visual: "Nodes connect across a pipeline"
    motion: "Quick reveal, 0.4 s ease"
    audio: "Subtle electronic hit"
    evidence: "Proposed creative line; not a factual claim"
    rights: "Self-made graphics"
    approval: pending
```

Check for overlapping timings, untranslatable jargon, low-density keyframes, captions exceeding safe regions and scenes with no clear viewer benefit. Present a contact sheet with one to three still frames per shot. Static storyboard is **not** a motion test.

## 3. Design and motion gates

Use supplied design tokens when authorized; otherwise propose a reversible visual direction. Maintain:
- shared semantic tokens for backgrounds, type hierarchy, accents and margins
- meaningful motion hierarchy (key action before decoration)
- consistent easing, shot transitions and speaker labels
- captions / subtitles and audio alternatives when applicable
- clear visual markers distinguishing proposal, current project, released tool and verified event

Prefer editing text, scene data and tokens without touching transition implementation. Reuse Remotion `Sequence`, `interpolate`, `spring` and still-image rendering when relevant. Use seeded random sources if particles/noise are needed. Test a 5-8 second representative sample, not an easy opening card only.

## 4. Rendering and QA

Suggested Remotion command shapes; discover actual composition IDs first:

```bash
npm ci
npm run lint
npx remotion compositions src/index.ts
npx remotion still src/index.ts <CompositionId> out/keyframe.png --frame=30
npx remotion render src/index.ts <CompositionId> out/final.mp4 --codec=h264 --pixel-format=yuv420p
```

Build a one-loop GIF/WebM/MP4 from its own short composition, not by trimming a long video blindly. GIF loses audio and color fidelity; prefer MP4/WebM for high-quality embeds and GIF only for compatibility. Verify exact CLI flags against the installed Remotion version.

Verify all of: source validity; duration/FPS/dimensions; representative first/middle/last frames; margin and text cropping in every requested ratio; audio levels, silence and synchronization; no flash/flicker surprises; licenses and consent; actual file existence and decode; file size and social-platform limits.

Declare explicitly if a runtime or encoder is unavailable. Never label a storyboard image, code file or unrendered composition as a finished video.

## 5. Hand-off / iteration

Record version, approved gate, scene IDs changed, output format and verification status. Return the smallest useful next decision: storyline A/B, visual treatment, motion pacing or final approval. Publication or upload requires an explicit instruction and appropriate access.
