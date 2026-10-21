---
name: wayback-evidence-capture
description: "Trigger: Wayback snapshot PDF, archived website screenshot, offline web evidence. Render and verify fixed Wayback captures with hashes."
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# Wayback Evidence Capture

## Activation Contract

Use when an agent must export **existing, confirmed** Internet Archive Wayback snapshots to offline PDF and PNG, with provenance, validation, and SHA-256 hashes.

Do not use for screenshots of live websites, for fabricating a snapshot, or as a substitute for notarized/certified evidence.

## Hard Rules

- Require a full `https://web.archive.org/web/YYYYMMDDHHMMSS/...` snapshot URL; never silently replace it with a newer capture or a live page.
- Store case-specific source URLs, expected text, credentials, user records, and output separately from the **public** skill repository.
- Validate the resolved archive URL, HTTP status, nontrivial text, and required evidence phrases before marking a capture successful. Manually inspect every PDF/PNG afterward.
- Record the original source URL, archive timestamp, **later** rendering timestamp, hashes, and failures separately.
- Never claim a browser-generated PDF, a timestamp encoded in a URL, or a SHA-256 hash constitutes independent legal certification.

## Decision Gates

| Situation | Action |
| --- | --- |
| Confirmed Wayback captures | Use `scripts/capture.py` with a local case manifest |
| No confirmed archive URL | Obtain and confirm a snapshot first; a third-party archiving request alone is insufficient |
| Archive failed, redirected outside Wayback, or expected text absent | Fail closed; do not package as evidence |
| Legal admissibility/certified time proof required | Escalate to a qualified preservation/certification provider |

## Execution Steps

1. Copy `references/manifest_example.json` outside this repository and populate it with case-specific data. Require at least one meaningful `expected_phrases` check for each page.
2. Run `python -m pip install playwright` and `python -m playwright install chromium`.
3. Execute `python scripts/capture.py --manifest /private/path/manifest.json --output-dir /private/path/captures`.
4. Inspect `capture_results.json` and renderings. A nonzero exit code or an error record means the capture is not validated.
5. Store private results in access-controlled storage, keeping the untouched Wayback URLs and independent archiving confirmations.

## Output Contract

Report captured and failed counts, snapshot vs. render dates, paths to PDF/PNG/results, hashes, validation limits, and any manual checks still needed. Never publish case material in a skills catalog.

## References

- `references/manifest_example.json`: synthetic public example
- `README.md`: CLI and local tests
- Internet Archive Save Page Now: https://web.archive.org/save