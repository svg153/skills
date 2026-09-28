---
name: svg153-writing-style
description: "Trigger: write like me, my style, my voice, LinkedIn post. Rewrite Spanish text in svg153's natural technical-conversational voice."
license: MIT
metadata:
  author: svg153
  version: "1.0.0"
---

# SVG153 Writing Style

## Activation Contract

Use when writing or rewriting publishable text that should sound like svg153, especially LinkedIn posts, technical reflections, community content, emails, and long-form explanations. Combine with `social-publishing` when platform, fact-checking, attribution, or publishing strategy also matters.

Do not use merely for factual answers where voice imitation is irrelevant.

## Hard Rules

- Treat current user-provided writing samples as the highest-priority style evidence.
- Write primarily in Spanish unless the user asks otherwise.
- Prefer medium or long paragraphs that connect ideas naturally instead of stacked one-line punchlines.
- Preserve exploratory reasoning, qualifications, side thoughts, rhetorical questions, and transitions such as `al final`, `de hecho`, `pero`, `y ahí`, `a lo mejor`, `lo mismo`, or `es por ello` when they fit naturally. Do not insert them mechanically.
- Keep vocabulary direct and technical when needed; avoid grandiloquent language, marketing slogans, corporate filler, generic engagement bait, and AI-sounding copy.
- Do not over-polish the prose into a different voice. Natural repetition or a slightly oral cadence is acceptable when it helps authenticity.
- Keep product names, technologies, dates, links, and technical claims correctly spelled and factually precise.
- Correct accidental spelling and grammar errors. Never add fake typos, missing letters, swapped vowels, or other artificial mistakes to simulate human authorship.
- Never add invisible characters, watermark-like markers, or provenance tricks to the text.
- For text intended for another application, do not use em dashes.
- When a character limit exists, remove repetition and secondary detail before shortening sentence structure so aggressively that the author's cadence disappears.

## Decision Gates

| Situation | Action |
| --- | --- |
| Current user sample exists | Mirror its paragraph length, connectors, vocabulary, and degree of informality first. |
| No current sample | Use the defaults in this skill without inventing quirks. |
| Social post | Keep the tone conversational, reflective, technical, and slightly oral. |
| Formal document | Reduce fillers and repetition, but preserve the author's reasoning cadence. |
| Hard character limit | Count characters and leave practical headroom when possible. |

## Execution Steps

1. Extract recurring sentence length, paragraph rhythm, connectors, technical vocabulary, and how the author introduces uncertainty or alternatives.
2. Draft the text preserving the author's reasoning order instead of converting it into marketing copy.
3. Remove slogan-like lines, excessive micro-paragraphs, generic hooks, and unnecessary superlatives.
4. Compare the result against the user's latest sample and restore any cadence lost during editing.
5. Enforce platform constraints such as character limits, links, and formatting.

## Output Contract

Return one ready-to-paste version by default. If a hard character limit applies, verify it before returning and state the approximate character count outside the artifact when useful.

## References

- `../social-publishing/SKILL.md` - complementary workflow for evidence, attribution, platform adaptation, and publishing quality.
