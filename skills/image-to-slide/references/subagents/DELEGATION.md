# Delegating work between models

Delegating pays off when the task **produces a lot of mechanical output** (specs and coordinates), **can be checked objectively** (render and comparison) and **there are several in parallel**. It does not pay off when preparing the brief costs more than doing the task: the subagent has to read the skill and the image, about 15-20k tokens to start.

| Task | Who | Parallel? | Why |
|---|---|---|---|
| Classify native/hybrid, theme, grid, what is a logo | Opus (main) | – | Design judgment; a mistake here carries through everything |
| OCR, background cleaning, build | Script (anyone runs it) | Yes | Deterministic |
| JSON spec: measure, transcribe, lay out | **Sonnet** `slide-spec-writer` | Yes, 1 per slide | Mechanical and long; the OCR gives it geometry and sizes |
| Simple SVG icons | Sonnet, inside the spec | – | Simple shapes; a mistake shows immediately in the render |
| Complex SVG illustration | Opus or an Opus subagent | Yes | Smaller models compose worse |
| Boxes for `clean_bg` | Sonnet proposes, Opus checks the PNG | Yes | Easy to verify |
| Visual QA, source vs render | **Haiku** `slide-qa` | Yes, 1 per render | Comparing and listing is cheap; Haiku only reports, it does not decide |
| Final fixes and delivery | Opus | – | Quality judgment |
| New rules in `references/` | Opus, only when maintaining the skill | – | Distilling generic rules from failures, never client data |

## When NOT to delegate
- A short slide or a tweak (move 10 px, change a color): edit the spec and rebuild.
- Anything that depends on the conversation context and cannot be written into the brief.

## Brief template for `slide-spec-writer`
```
Skill: <absolute path of the skill folder (${CLAUDE_SKILL_DIR})>
Source image: <path>            OCR: <path .ocr.json> (if already run)
Output: <folder>\<Name>.json  (output <Name>.pptx, png <Name>.png)
Final format: pptx | html | both  (with html, build and compare with build_html.ps1 -Spec <json> -Out <Name>.html -> <Name>_html.png; the main model assembles the whole-deck HTML at the end)
Strategy: native | hybrid (background: <path of the clean plate>)
Do NOT include (already in the background): <list>
Profile: <path>/perfil.json (if there is a client profile)
Logos: @logos/<file>.svg in <approximate position>
Theme/grid: Segoe UI; title <x,y,size>; colors <…>
Notes: <unsure data, unreadable text, what goes in italics…>
```

## Brief template for `slide-qa`
```
Source: <path of the original image>
Render: <path png>
Intentionally different: <e.g. "the illustration is a redrawn approximation">
```
