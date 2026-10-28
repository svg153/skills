---
name: google-workspace-quality
description: "Trigger: Google Docs formatting, Google Sheets design, Google Slides layout, Drive document creation and editing. Create polished, native Google Workspace deliverables with structural and visual QA."
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# Google Workspace Quality

## Activation Contract

Use when creating, materially editing, or restyling shared Google Docs, Google Sheets, or Google Slides. Complement the host's specialized Google Drive and artifact skills, not its authentication, API, data safety, or import rules. For reader-friendly structure, also use `cognitive-doc-design` where available.

## Hard Rules

- Default to **native Google Workspace files in Drive** for shared prose, tables, and presentations when the user has not specified a format. Choose Docs for prose, Sheets for tabular models, and Slides for a deck.
- An **explicit Markdown request wins**: produce and preserve a real `.md` file suitable for local coding workflows. Never silently convert it into a Google Doc. Similarly respect requested DOCX, XLSX, PPTX, or other formats.
- Honor the destination folder, existing file, ownership, sharing state, wording, styles, data, formulas, links, validation, charts, comments, and supported native objects. Edit in place only when authorized; copy templates when creating a new document.
- Use real native headings, lists, tables, hyperlinks and images in Docs; formulas, number formats, validation, freeze panes, filters and conditional formatting in Sheets; editable native text and shapes in Slides. Markdown-like glyphs are not equivalent to native structure.
- Prefer an existing approved Google connector and host skills over adding a new CLI, MCP server, credentials, or OAuth scopes.
- Do not report visual quality from API success alone. Verify structure and rendering where available. Clearly distinguish verified checks from unverified layout.

## Decision Gates

| Destination | Preferred operation |
| --- | --- |
| Existing native file | Read the relevant structure and minimally edit with the native API; preserve neighbors |
| New file from a native template | Copy the template natively, populate it and check retained elements |
| New Doc without a template | Follow host Docs creation rules, apply semantic paragraph styles, and inspect rendered pages |
| New Sheet without a template | Follow host spreadsheet authoring/import route, then repair and verify native Sheet controls |
| New Slides without a template | Follow host presentations authoring route and inspect each delivered slide |
| Explicit Markdown output | Deliver `.md` as requested; do not transform its source notation into Docs formatting |

## Execution Steps

1. Locate the target file and folder. Read relevant tabs, sheets, template styles, formulas, controls and user-supplied examples before writing.
2. Plan an accessible information hierarchy and restrained, consistent visual styling. Check `references/quality-checklist.md` for surface-specific acceptance criteria.
3. Apply the host's native Docs, Sheets or Slides tool workflow, including revision protection, range and index safety, and preserving unrelated content.
4. Re-read changed sections and verify semantics, outlines, tables, links, formulas, validation, references, and adjacent unchanged structures.
5. Visually inspect Docs and Slides in their rendered pages; inspect Sheets in the authenticated UI when possible, otherwise use a qualified spreadsheet render plus API-level formatting checks. Fix clipping, spacing and layout issues, then recheck.
6. Deliver the verified native link or explicitly requested file format. State what was validated, what could not be rendered, and any conversion limitations.

## Output Contract

Return a usable file in the requested destination, a concise description of changes, and accurate structural and visual QA status. Never claim a native file was created, a conversion preserved all controls, or visual QA passed without evidence.

## References

- [Google Workspace quality checklist](references/quality-checklist.md)
- Host-native Google Drive/Docs/Sheets/Slides skills for exact API and import contracts
- `cognitive-doc-design` for information architecture, not native Google formatting
