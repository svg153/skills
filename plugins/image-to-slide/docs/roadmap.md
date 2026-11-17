# image-to-slide roadmap (TODO)

This is open work, ordered by value. Every item states **why** it matters and **what counts as done**. Durable rules for maintainers live in `skills/image-to-slide/references/maintenance.md`. This file only covers what is not done yet.

Status legend: `[ ]` open, `[~]` partly done, `[x]` done (kept for one release, then removed).

## P1: robustness of the pptx engine

- [ ] **Native charts without Excel.**
  - Why: current Office builds (seen on 16.0.20527) return `E_FAIL` from `Shapes.AddChart2` in a windowless presentation. The engine works around this by opening a minimized window. That window, and the embedded `EXCEL.EXE /automation -Embedding` processes, can stay open after the build. That breaks the "isolated, invisible build" goal for agents.
  - How: write the chart part as OpenXML (`c:chartSpace` plus an embedded xlsx cache) and add it without starting Excel. `ykuwai/ppt-mcp` did this two ways, by pasting the chart package from the clipboard and by copying from a generated one-slide pptx (see `related-work.md`). Prefer the file route: the clipboard belongs to the user.
  - Done when: `examples/ejemplo_completo.json` builds its two charts with no window and no `EXCEL.EXE` left running, the values read back correctly, and "Edit data" still works in PowerPoint.
- [ ] **Report the windowless-chart regression upstream.**
  - Why: there is no public issue or documentation for it. Minimal repro: in a presentation created with `Presentations.Add(msoFalse)`, `AddChart2(-1, xlColumnClustered, …)` returns `E_FAIL`. The same call with `Presentations.Add(msoTrue)` works.
  - Done when: the report is filed through PowerPoint Feedback, its link is noted here, and `maintenance.md` is updated if Microsoft answers.
- [ ] **COM call timeouts.**
  - Why: `ppt-mcp` #299 shows that releasing the reference to a closed chart workbook can block forever.
  - Done when: each COM step that can hang has a timeout and a clear error, and a hung build never leaves a presentation open.
- [ ] **Target lock.**
  - Why: an agent must never write into the user's own deck.
  - How: tag the presentation the engine creates (for example with a custom document property) and check the tag before every write. This mirrors `ppt_activate_presentation` in `ppt-mcp`.
  - Done when: a test with another deck open shows the engine never touches it, beyond the current before/after count.

## P2: html output

- [ ] **Embed an open font** (for example Inter or Noto Sans, subset to the characters used, as a `woff2` data URI). Why: outside Windows, Segoe UI falls back to the system font and line breaks move. Done when: the comparison shows no new overflow on macOS or Linux renders.
- [ ] **"Download edited copy" button.** Why: text edited with `E` is lost on reload. Done when: the button saves a new self-contained `.html` with the edits included.
- [ ] **Test the interactive features in a real browser.** So far only the headless screenshots are verified. Check keyboard navigation, edit mode and print to PDF (one slide per page) in Edge, Chrome and Firefox.
- [ ] **Shapes and charts missing from the viewer:** `donut`, `can`, `cube` and `cloud` shapes, and `scatter` charts. Done when: `references/spec.md` no longer lists them as limitations.

## P3: process and quality

- [ ] **Model-backed eval runs.** `evals/image-to-slide` currently passes static validation only. Run the Waza suite with a model from trusted state and keep the raw evidence. Add one positive task where the output is `both`.
- [ ] **Neutrality check in CI.** Add a deterministic check that fails when this plugin contains absolute user paths (`X:\Users\…`, `/Users/…`, `/home/…`) or e-mail addresses. Client names stay in a local, git-ignored deny-list (`local/forbid.txt`) that a pre-push hook can use. A local version of this check existed before the catalog migration.
- [ ] **Commit identity.** Commit to this repository only with the public noreply address. Set it per checkout: `git config user.email <user>@users.noreply.github.com`.
- [ ] **Profile from `deck-design-system`.** Generate a client profile (`perfil.json`: palette, fonts, header grid, logos) from the `design.md` that `deck-design-system` produces. Rebuilt slides would then follow the deck's own system with no manual theme work. See `related-work.md`.
- [ ] **pptx on macOS.** Explore driving PowerPoint for Mac over Apple Events, as `ppt-mcp` does. Until then, macOS users get the `html` output.

## Decided not to do (for now)

- **Bundling a PowerPoint MCP server in `mcp.json`.**
  - The fixed engine already covers the build. An MCP would add a stdio server with a broad tool surface and no detected license.
  - The catalog's MCP policy requires provenance and a justification for stdio.
  - Reconsider if users want to keep editing interactively after the build. Even then, recommend an MCP server as an optional companion, not as a dependency (see `related-work.md`).
- **Replacing the spec + engine design with direct MCP calls.** Free-form tool calls are what the spec avoids: a deterministic build, a numeric comparison, and small models that only fill a JSON.
