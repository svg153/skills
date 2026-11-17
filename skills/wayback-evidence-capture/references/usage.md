# wayback-evidence-capture usage

`scripts/capture.py` prints **already archived** Wayback Machine pages to browser-rendered PDF and PNG. The original archive time and subsequent rendering time are kept separate, and each resulting file gets a SHA-256 hash.

## Install and run

Run from the skill directory:

```bash
python -m pip install 'playwright==1.65.2'
python -m playwright install chromium
python scripts/capture.py --manifest /path/to/private-manifest.json --output-dir /path/to/private-evidence
```

Create the input from [`manifest_example.json`](manifest_example.json). Input manifests and outputs are **case material**: do not commit customer names, claims, addresses, receipts, order IDs, or private URLs to a public repository.

`--chromium-executable` is optional; without it the Playwright-managed Chromium is used. `--no-sandbox` is only needed in some containerized Linux environments.

`capture_results.json` includes source/archive/render metadata and per-file SHA-256. Errors are recorded and cause a nonzero exit status. The `snapshot_utc` timestamp must match the exact `/web/<YYYYMMDDHHMMSS>/` segment of both the requested and the resolved snapshot URL. `snapshot_utc` must be ISO-8601 UTC (`Z` or `+00:00`); other offsets and impossible dates are rejected. Results also record `tool_version`, `playwright_version`, `browser_version` and `manifest_sha256`. Stale `<id>.pdf`/`<id>.png` files from an earlier run are deleted before each capture, and the Wayback toolbar (`#wm-ipp`) is excluded from the text used for length and phrase checks.

The snapshot URL must have `http://` or `https://` right after the timestamp (`/web/<ts>/https://...`). Timestamp-only forms such as `/web/<ts>/example.com/` are rejected on purpose: this is intentional fail-closed behavior, so write the full original URL in the manifest.

Inspect each PDF and screenshot; automation cannot prove the full text was captured correctly. This utility does not initiate archiving or issue certified timestamps.

## Tests

```bash
python -m unittest discover -s tests -p 'test_*.py'
```

Manifest validation tests need only the standard library. The browser smoke test renders a local HTML fixture offline and is skipped when Playwright or a Chromium browser is unavailable. It uses the Playwright-managed Chromium by default; set `WAYBACK_CHROMIUM_EXECUTABLE` to use another Chromium-based binary (for example `/usr/bin/chromium`). A live snapshot requires outbound HTTPS.

## Reuse

Use this script only when a browser rendering is necessary. For programmatic capture/discovery at scale, investigate the existing tools [nordicintel/wayback-verify](https://github.com/nordicintel/wayback-verify) or [akamhy/waybackpy](https://github.com/akamhy/waybackpy) before creating API clients.
