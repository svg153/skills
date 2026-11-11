---
name: motion-content-production
description: "Trigger: motion graphics, animated video, GIF, WebM, video storyboard, event promo, Remotion. Produce evidence-aware audiovisual pieces through review gates and reusable templates."
license: MIT
metadata:
  author: svg153
  version: "1.0.0"
---

# Motion Content Production

## Activation Contract

Use for animated explainers, event promos, personal-brand reels, demos, video loops and GIF/WebM assets. For copy-only posts use `social-publishing`; for an existing slide deck design-system extraction use `deck-design-system`.

## Hard Rules

- Start from public or explicitly authorized source material; fact-check titles, claims, dates and project statuses. A private repository's existence does not authorize disclosing its code, screenshots, clients or metrics.
- Reuse an existing video project and licensed assets before creating a new rendering pipeline. Prefer Remotion when the project already uses React/TypeScript; use a lightweight image/GIF tool for simple loops.
- Never imply official vendor endorsement for a community project. Respect brand guidelines, image/voice consent and audio licenses.
- **Default stop after the current review gate**. Never render the complete video on a request for an idea, script or storyboard. If the user explicitly requests a finished video now, perform the checks without unnecessary approval rounds.
- Do not claim an MP4, GIF, soundtrack, preview, QA pass or publication unless the corresponding real artifact/action was verified.
- Ensure deterministic animation, legible text, safe areas, accessible contrast and reproducible output. No unseeded randomness in frame rendering.

## Decision Gates

| Request | Next deliverable | Stop point |
| --- | --- | --- |
| Idea, theme, event or project | 2-3 narrative directions with hook, audience, CTA and estimated length | Await creative selection |
| Approved story | Timed shot list + contact-sheet storyboard, factual/asset ledger | Await visual selection |
| Approved visuals | 5-8s motion test (or 1 complete GIF loop) with representative audio | Await motion feedback |
| Approved motion / explicit final-video request | Full render, sound, QA and requested platform variants | Deliver verified files |

## Execution Steps

1. Build a brief from the user's instructions, existing public projects, references and optional brand kit. If crucial information is unavailable, use labeled assumptions or ask one targeted question.
2. Pitch differentiated concepts with a critique of trade-offs. Include estimated duration and platform-specific format.
3. Once selected, write a **timecoded storyboard**: scene ID, message, visual, text, movement, audio, sources and privacy/licensing status. Produce actual keyframe previews when tooling permits.
4. Extract or propose design tokens (type, palette, grid, logo policy, motion language and aspect-ratio safe zones). Review before animation.
5. Render a short motion test; use previews to resolve pacing, readability, transitions and soundtrack/voice direction.
6. After approval or an explicit final render request, use the existing codebase to render MP4 and optionally WebM/GIF. Run the checks in `references/production-playbook.md` and export source/project files.
7. Report what was verified, what remains unverified, assets/sources used and the single most useful next iteration.

## Output Contract

At every gate, provide a reviewable artifact and precise feedback choices. At final delivery provide validated file links and, when possible, editable source, render commands, aspect ratio/FPS, rights notes and known limitations. Keep a simple versioned brief and storyboard so later changes affect only relevant scenes.

## References

- [Production playbook, storyboard contract and QA](references/production-playbook.md)
