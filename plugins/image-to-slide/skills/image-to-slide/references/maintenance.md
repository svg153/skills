# Maintenance and distilled rules

Rules that came out of real failures and still apply. They complement `SKILL.md` and `references/spec.md` and do not repeat what is already there.

## Rules for writing specs
- Semibold title: set `"font": "Segoe UI Semibold"` on the element, not `bold`.
- Check dash typography: a hyphen (`-`) where the source has a long dash (`—`) is a text fault, not a style detail.
- When the OCR sizes and `compare` agree (width ratio 0.97-1.03), do not "round by eye": they are usually right the first time.
- A text that overflows its card is reported by `compare` as `OVERFLOWS its box by N px`: lower `size` to the suggested value before moving anything.
- The specs in `examples/` are the template the subagents copy: if a sizing rule changes, fix the examples too.

## Numeric comparison (`compare.ps1`)
- Always launch Podman from PowerShell (`compare.ps1`), not from Git Bash: Git Bash rewrites `/w/...` style paths passed to `podman run`.
- The container image is built from `container/Containerfile` on first use (or with `compare.ps1 -Build`). Without Podman, `compare.ps1` uses a local Python; without either, the step is skipped.
- A card reported with low SSIM only because of its text shows up under "No warning of its own" with its culprit (`afectado_por`): fix the child, not the card.

## Native charts (pptx)
- Some PowerPoint builds no longer insert charts into a windowless presentation: the engine opens it minimized when the spec has a `chart`. Do not change that without testing charts again.
- With a cold Excel, the first chart can silently keep Excel's sample data: the engine re-reads series 1 and retries, and fails with a clear message if the values still do not match.
- Future alternative if the window is a problem: write the chart XML (OpenXML) without Excel.

## Rules for editing the scripts (PowerShell 5.1)
- `.ps1` files are **ASCII only**: PowerShell 5.1 breaks accents in UTF-8 files without BOM. Accented texts go in the JSON, which is read as UTF-8.
- Numbers and CSV always use the **invariant culture**: with a Spanish locale, `-f` and `Export-Csv` write decimal commas.
- Do not rewrite code with .NET regex replacements: `$_` in the replacement text means "the whole input".
- Inside a string, `"$var:"` is a syntax error: use `"${var}:"`.
- Compute expressions into variables before passing them to `New-Object` (`$c.Width + 6` is split into two arguments).
- `@(@(a,b,c,d))` with a single element is flattened: pass box lists as text (`"x0,y0,x1,y1;…"`).
- A function returns any uncaptured COM value to the output stream: end those calls with `| Out-Null`.
- `$true -eq 'number'` is true: check types with `-is [string]`.
- `Start-Process` does not quote arguments: quote them yourself when there are spaces.
- After `ChartData.Activate()`, read `$sh.Chart.ChartData.Workbook` again (with retries); a reference saved before activation is null.
- Headless Edge captures always use a temporary `--user-data-dir`, never the user's profile.
- Never `Quit()` or `Stop-Process` PowerPoint or Excel (rule 0 in `SKILL.md`).
- Keep the fixed identifiers listed in `SKILL.md` (`antes=N despues=N`, `_dudas.md`, `dudas=`, the comparison JSON keys) unchanged: scripts and agents parse them.

## Client data
- No real data in the skill: no client or company names, logos, texts, figures, paths or user names. Not even as an example in a comment.
- Client data goes in a local profile outside this skill (see `SKILL.md` §1, "Client profiles").

## Test bench
- After changing a script, a rule or an example, run `bench.ps1 -SelfTest` (and `bench.ps1 -Dir <bench>` if you have a bench). If a case gets worse, revert or fix before accepting the change.
- The real bench always lives **outside the skill**: it holds real slides. Each case is a folder with `original.png` + `spec.json` + its resources.
- Two consecutive runs with no changes must show a change of 0: the process is deterministic.
