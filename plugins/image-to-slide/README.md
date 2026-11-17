# image-to-slide Agent Plugin

A portable Agent Plugins 1.0 capability that rebuilds **slide images** (PNG, JPG, WEBP, screenshots, an exported PDF or a PPTX whose slides are only pictures) as **editable slides with the same design**.

There are two outputs, and both come from the same JSON spec:

- **pptx** (default): native PowerPoint objects for text, shapes, arrows, tables, charts, groups and notes. Built by desktop PowerPoint on Windows.
- **html**: **one self-contained `.html` file**. The viewer, spec and images are embedded, so it needs no network. Send it as a single file and open it in any browser.

The model only writes the spec. Fixed engines render it, so nobody writes PowerPoint or HTML code by hand.

```text
plugins/image-to-slide/
├── plugin.json                  generated (do not edit)
├── distribution.config.json     package identity
├── README.md
├── docs/
│   ├── roadmap.md               open work and ideas (TODO)
│   └── related-work.md          PowerPoint MCP servers, deck-design-system, what to borrow
├── local/                       git-ignored: your private tests, bench and client profiles
└── skills/
    └── image-to-slide/
        ├── SKILL.md
        ├── references/          spec format, maintenance rules, subagent prompts
        ├── scripts/             engines, OCR, background cleaning, crop, compare, bench
        ├── html/                single-file viewer (deck.js + deck.css)
        ├── container/           minimal image for the optional numeric comparison
        ├── examples/            fictitious, tested specs (no real data)
        └── assets/logos/        a fictitious example logo only
```

## Install

```bash
copilot plugin marketplace add svg153/skills
copilot plugin install image-to-slide@svg153-skills
```

In Claude Code, add the `svg153/skills` marketplace and install `image-to-slide`. You can also copy `skills/image-to-slide/` into your skills folder.

## Requirements

| Output | Needs |
|---|---|
| `pptx` | Windows, PowerShell 5.1 and desktop PowerPoint. Excel is needed only for native charts |
| `html` | Microsoft Edge, used only for the control PNG. The resulting file opens in any browser |
| optional comparison | Podman or a local Python with numpy, opencv and scikit-image. Without either, the step is skipped |

Everything runs locally. The skill never uploads images or texts. OCR uses the engine built into Windows.

## Safety

- PowerPoint runs as a single instance, so the engine attaches to the user's PowerPoint. It never calls `Quit()` and never kills processes. It closes only what it opened and prints `presentaciones abiertas antes=N despues=N` (open presentations before and after).
- Native charts need a document window on current Office builds. The engine opens that window minimized, then reads the chart values back to check them. See [`docs/roadmap.md`](docs/roadmap.md).

## Client data and local tests

The plugin is **client- and company-agnostic**. It ships no real names, logos, texts, figures, paths or user names, not even in examples.

- **Client branding** (logos, palette, header grid) goes in a local profile outside the skill. `SKILL.md` §1 explains how.
- **Private tests and real benches** go in `local/` in this folder, or anywhere outside the repository. `local/` is git-ignored, and so are build outputs written next to the examples.
- Run `bench.ps1 -SelfTest` after any change. It uses only the fictitious examples. Real cases run with `bench.ps1 -Dir <your bench>`.

## Relationship with `deck-design-system`

The two skills run in opposite directions and complement each other:

- `deck-design-system` takes **editable decks** and extracts their design system: PDFs, `design.md` and a Slidev template.
- `image-to-slide` takes **pictures of slides** and turns them back into an editable deck.

The Activation Contracts and eval tasks keep their triggers apart. [`docs/related-work.md`](docs/related-work.md) describes how they can be chained.
