# Google Workspace quality checklist

Apply checks proportional to the requested change. A supplied native template or file convention takes precedence over new-file defaults.

## Google Docs

- Use a semantic TITLE and an appropriate HEADING_1 / HEADING_2 hierarchy. Confirm section headings appear in the Docs outline rather than as literal Markdown markers.
- Prefer readable body paragraphs with consistent spacing and native list numbering. Do not create blank lines merely to simulate paragraph spacing.
- Render comparisons as native tables rather than lines containing pipe characters. Preserve existing column widths, table cells, and multiline content.
- Preserve existing links, smart chips, dropdowns, tab structure, image aspect ratios, and list continuity outside the edit.
- Inspect PDF-rendered pages for clipping, split tables, isolated headings, unwanted empty pages, image scale, and captions; compare DOCX imports against their source if conversion was used.
- For a purely formatting-only request, preserve wording verbatim.

## Google Sheets

- Separate input, calculated, summary and reference data when creating a model. Match existing layout when editing.
- Default to a restrained native style: light headers, dark readable text, subtle borders, proper numeric/date formats, and limited accent colors.
- Use filters and frozen rows for genuinely scrollable tables. Do not add these indiscriminately to small matrices.
- Prefer native validations and rule-based conditional formatting for states and options, rather than individually painted cells.
- Verify affected formulas, references, dropdowns, charts, protections, and controls after structural changes.
- Check changed columns for clipping, inappropriate wrapping, unreadable numbers, distorted merges, or unexpectedly wide sheets. Never autofit the entire workbook as a side effect.
- Prefer authenticated native UI visual QA. When only XLSX rendering is available, disclose that Google-only controls may not render identically.

## Google Slides

- Preserve master/layout systems and user-specified template conventions.
- Keep narrative text and meaning-bearing tables/charts as editable native elements where supported, not screenshots.
- Visually inspect every delivered slide for overflowing text, alignment, image proportions, contrast, stale placeholders, and consistent typography.

## Format and delivery rules

- Shared text document with no format instruction: Google Docs.
- Shared spreadsheet or calculations with no format instruction: Google Sheets.
- Shared presentation with no format instruction: Google Slides.
- User explicitly requests Markdown for working with code: produce the real `.md` file, maintaining code fences, links, syntax, and portability.
- Do not infer that mentioning code inside a Google Doc means Markdown is required.
- Existing native file: edit in place if requested. New artifact: use the user-specified folder and confirm the final Google link.
- Report separately native semantic checks and actual visual QA. No render or UI access means visual QA is **not verified**.

## Acceptance scenarios

1. `Próximos pasos` appears as a navigable heading, not literal `## Próximos pasos`.
2. A decision comparison remains a native table with readable widths.
3. Inserting rows into a tracking Sheet preserves formulas and option dropdowns.
4. The user asks for `README.md`: deliver Markdown rather than a Google Doc even if other work usually lives in Drive.
5. If visual rendering was unavailable, report that limitation instead of claiming the document looks correct.
