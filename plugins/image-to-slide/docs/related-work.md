# Related work and what to borrow

Reviewed 2026-11-17. This file covers what each project does, what it overlaps with here, and which of its ideas is worth taking. Open items go to [`roadmap.md`](roadmap.md).

## `deck-design-system` (this catalog)

| | `deck-design-system` | `image-to-slide` |
|---|---|---|
| Input | editable `.pptx` decks | **pictures** of slides (PNG/JPG/WEBP, PDF, flat PPTX) |
| Output | PDFs, assets, `design.md`, Slidev template, Pages site | editable `.pptx` and/or one self-contained `.html` |
| Direction | deck → design system | image → deck |
| Shared ground | presentations, design fidelity | presentations, design fidelity |

**Overlap:** low. They meet only when the user has an editable deck and asks for "the same design". That case belongs to `deck-design-system`, unless the source is only an image. Both Activation Contracts state this, and an eval task covers it in each direction.

**Composition (worth doing):**
1. Flat or screenshot deck → `image-to-slide` → editable `.pptx` → `deck-design-system` → `design.md` and Slidev template. This recovers a design system even when only pictures exist.
2. `deck-design-system` `design.md` → `image-to-slide` client profile (palette, fonts, grid, logos). New rebuilds then follow that system. This is listed as a roadmap item.

## PowerPoint MCP servers

| Project | What it is | Platform | License | Notes |
|---|---|---|---|---|
| [`ykuwai/ppt-mcp`](https://github.com/ykuwai/ppt-mcp) | MCP server driving a live PowerPoint, 150+ tools | Windows (COM), macOS (Apple Events) | not detected by GitHub | Active; most of the chart findings below come from it |
| [`sbroenne/mcp-server-powerpoint`](https://github.com/sbroenne/mcp-server-powerpoint) | MCP server + `pptcli`, 140+ operations, "export to verify" | Windows (COM, .NET) | not detected by GitHub | VS Code extension available |

**Overlap:** these servers are general-purpose remote controls for PowerPoint. `image-to-slide` is one narrow pipeline with a deterministic engine:

> image → OCR → spec → build → numeric comparison → fix

The two approaches do not compete. An MCP server is useful **after** the build, to keep editing the deck interactively.

**Ideas to borrow (without switching to MCP):**
- **Charts without Excel.**
  - The `ppt-mcp` PRs #321 and #341 add charts by copying the chart from a generated file, or by pasting the GVML chart package. Either way, no Excel process starts, and "Edit data" still works because PowerPoint rebuilds the workbook from the chart caches.
  - Their measurements: AddChart2 plus Excel lost data and crashed Excel in several runs, while the Excel-free path had no crashes and 6/6 correct read-backs.
  - This is roadmap P1.
- **Read back after writing.**
  - Both projects verify instead of trusting COM: `ppt-mcp` reads chart values back, and `mcp-server-powerpoint` exports slides as images.
  - `image-to-slide` already does both: chart values are read back, and every build is rendered and compared.
  - Keep it that way: never report success without reading back.
- **Lock the target presentation** (`ppt_activate_presentation`). This is roadmap P1, under "target lock".
- **Timeouts and release order of COM references** (`ppt-mcp` #299, and `mcp-server-powerpoint` #108 on the chart data grid left open). This is roadmap P1, under COM call timeouts.
- **Clipboard hygiene:** if a clipboard route is ever used, save and restore every clipboard format, as `ppt-mcp` does. The file route is preferred.
- **macOS support through Apple Events.** This is roadmap P3.

**Recommending them to users:**
- Mention an MCP server only when the user wants to keep editing the generated deck through the agent.
- Present it as optional. Check its license before installing, since GitHub detected none for either project.
- Do not add it to this plugin's `mcp.json` without the catalog's provenance review (see `docs/mcp-composition.md` at the repository root).
