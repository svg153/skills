# wayback-evidence-capture

This portable Agent Skill prints **already archived** Wayback Machine pages to browser-rendered PDF and PNG. The original archive time and subsequent rendering time are kept separate, and each resulting file gets a SHA-256 hash.

## Install and run

```bash
python -m pip install playwright
python -m playwright install chromium
python scripts/capture.py --manifest /path/to/private-manifest.json --output-dir /path/to/private-evidence
```

Create the input from `references/manifest_example.json`. Input manifests and outputs are **case material**: do not commit customer names, claims, addresses, receipts, order IDs, or private URLs to a public repository.

`capture_results.json` includes source/archive/render metadata and per-file SHA-256. Errors are recorded and cause a nonzero exit status. Inspect each PDF and screenshot; automation cannot prove the full text was captured correctly. This utility does not initiate archiving or issue certified timestamps.

## Tests

```bash
python tests/test_mock.py
```

This test uses locally installed Chromium (`/usr/bin/chromium`). For alternative environments, configure the CLI to use a Playwright-managed Chromium or alter the smoke test path. No external access is required for unit tests. A live snapshot requires outbound HTTPS.

## Reuse

Use this script only when a browser rendering is necessary. For programmatic capture/discovery at scale, investigate the existing tools [nordicintel/wayback-verify](https://github.com/nordicintel/wayback-verify) or [akamhy/waybackpy](https://github.com/akamhy/waybackpy) before creating API clients.