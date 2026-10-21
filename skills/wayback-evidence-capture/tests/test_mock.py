"""Offline smoke test for PDF + PNG creation and failure safeguards."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

root = Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
    t = Path(td)
    fixture = t / "fixture.html"
    fixture.write_text("<html><head><title>Archived page fixture</title></head><body>"
                       + "<h1>Example archive terms and conditions</h1>"
                       + ("Valid content to establish that the browser rendered the HTML. " * 16)
                       + "</body></html>", encoding="utf-8")
    manifest = {"captures": [{"id": "smoke", "original_url": "https://example.test/page",
               "snapshot_url": fixture.as_uri(), "snapshot_utc": "2026-10-19T20:20:36Z",
               "expected_phrases": ["EXAMPLE ARCHIVE", "terms and conditions"]}]}
    path = t / "manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")
    res = subprocess.run([sys.executable, str(root / "scripts/capture.py"), "--manifest", str(path),
                          "--output-dir", str(t / "out"), "--chromium-executable", "/usr/bin/chromium",
                          "--no-sandbox", "--allow-file-fixtures"], capture_output=True, text=True)
    assert res.returncode == 0, res.stderr
    summary = json.loads((t / "out/capture_results.json").read_text())
    assert summary["successes"] == 1, summary
    assert (t / "out/smoke.pdf").stat().st_size > 1500
    assert (t / "out/smoke.png").stat().st_size > 1500
    assert len(summary["records"][0]["pdf_sha256"]) == 64
    manifest["captures"][0]["expected_phrases"] = ["nonexistent critical statement"]
    path.write_text(json.dumps(manifest), encoding="utf-8")
    res2 = subprocess.run([sys.executable, str(root / "scripts/capture.py"), "--manifest", str(path),
                          "--output-dir", str(t / "negative"), "--chromium-executable", "/usr/bin/chromium",
                          "--no-sandbox", "--allow-file-fixtures"], capture_output=True, text=True)
    assert res2.returncode != 0, res2.stderr
    failure = json.loads((t / "negative/capture_results.json").read_text())
    assert failure["successes"] == 0
    assert not (t / "negative/smoke.pdf").exists()
    print("PASS: PDF/PNG generation, SHA-256 metadata and missing-evidence failure guard")