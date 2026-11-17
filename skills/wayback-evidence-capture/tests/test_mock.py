"""Offline tests for manifest validation, PDF + PNG creation and failure safeguards.

Run from the skill directory:

    python -m unittest discover -s tests -p 'test_*.py'

The browser smoke test uses the Playwright-managed Chromium by default. Set
WAYBACK_CHROMIUM_EXECUTABLE to use another Chromium binary (for example
/usr/bin/chromium). It is skipped when Playwright or a browser is unavailable.
"""
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAPTURE = ROOT / "scripts" / "capture.py"

_spec = importlib.util.spec_from_file_location("wayback_capture", CAPTURE)
capture = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(capture)


def _browser_unavailable_reason() -> str | None:
    if importlib.util.find_spec("playwright") is None:
        return "playwright is not installed"
    executable = os.environ.get("WAYBACK_CHROMIUM_EXECUTABLE")
    if executable:
        return None if Path(executable).exists() else f"WAYBACK_CHROMIUM_EXECUTABLE not found: {executable}"
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            path = p.chromium.executable_path
    except Exception as ex:  # pragma: no cover - environment dependent
        return f"Playwright Chromium unavailable: {ex}"
    return None if Path(path).exists() else "run 'python -m playwright install chromium'"


def _valid_capture(**overrides) -> dict:
    item = {
        "id": "example",
        "original_url": "https://example.com/terms",
        "snapshot_url": "https://web.archive.org/web/20261019202036/https://example.com/terms",
        "snapshot_utc": "2026-10-19T20:20:36Z",
        "expected_phrases": ["terms and conditions"],
    }
    item.update(overrides)
    return item


class ValidateCaptureTest(unittest.TestCase):
    def test_accepts_matching_timestamp(self):
        capture.validate_capture(_valid_capture(), allow_fixtures=False)
        capture.validate_capture(_valid_capture(
            snapshot_url="https://web.archive.org/web/20261019202036id_/https://example.com/terms"),
            allow_fixtures=False)

    def test_rejects_timestamp_only_present_elsewhere_in_url(self):
        url = "https://web.archive.org/web/20250101000000/https://example.com/?ref=20261019202036"
        with self.assertRaisesRegex(ValueError, "timestamp does not match"):
            capture.validate_capture(_valid_capture(snapshot_url=url), allow_fixtures=False)

    def test_rejects_missing_timestamp_segment(self):
        with self.assertRaisesRegex(ValueError, "14-digit timestamp"):
            capture.validate_capture(_valid_capture(
                snapshot_url="https://web.archive.org/web/2026/https://example.com/terms"),
                allow_fixtures=False)

    def test_wayback_stamp_requires_exact_segment(self):
        self.assertEqual(capture.wayback_stamp("/web/20261019202036/https://example.com/"), "20261019202036")
        self.assertIsNone(capture.wayback_stamp("/web/202610192020361/https://example.com/"))
        self.assertIsNone(capture.wayback_stamp("/x/web/20261019202036/https://example.com/"))


class ExpectedStampTest(unittest.TestCase):
    def test_accepts_z_and_explicit_utc_offset(self):
        self.assertEqual(capture.expected_stamp("2026-10-19T20:20:36Z"), "20261019202036")
        self.assertEqual(capture.expected_stamp("2026-10-19T20:20:36+00:00"), "20261019202036")

    def test_rejects_non_utc_offsets(self):
        for value in ("2026-10-19T20:20:36+02:00", "2026-10-19T20:20:36-05:00", "2026-10-19T20:20:36"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "UTC"):
                capture.expected_stamp(value)

    def test_rejects_impossible_dates_and_garbage(self):
        for value in ("2026-13-45T25:61:61Z", "2026-02-30T10:00:00Z", "20261019202036", "not a date"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                capture.expected_stamp(value)

    def test_wayback_path_requires_http_scheme_after_timestamp(self):
        # Intentional fail-closed behavior, documented in references/usage.md.
        self.assertIsNone(capture.wayback_stamp("/web/20261019202036/example.com/terms"))


class ManifestErrorPathsTest(unittest.TestCase):
    def _run(self, manifest_text: str) -> subprocess.CompletedProcess:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "manifest.json"
            path.write_text(manifest_text, encoding="utf-8")
            return subprocess.run([sys.executable, str(CAPTURE), "--manifest", str(path),
                                   "--output-dir", str(Path(td) / "out")], capture_output=True, text=True)

    def test_entry_without_id_is_a_readable_error_not_a_traceback(self):
        res = self._run(json.dumps({"captures": [{"original_url": "https://example.com"}]}))
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("Invalid manifest entry #1", res.stderr)
        self.assertNotIn("Traceback", res.stderr)

    def test_non_utc_snapshot_is_rejected_cleanly(self):
        res = self._run(json.dumps({"captures": [_valid_capture(snapshot_utc="2026-10-19T22:20:36+02:00")]}))
        self.assertNotEqual(res.returncode, 0)
        self.assertIn("UTC", res.stderr)
        self.assertNotIn("Traceback", res.stderr)

    def test_invalid_json_and_non_object_entries(self):
        for text in ("{not json", json.dumps({"captures": ["x"]}), json.dumps([])):
            with self.subTest(text=text):
                res = self._run(text)
                self.assertNotEqual(res.returncode, 0)
                self.assertNotIn("Traceback", res.stderr)


class _FailingBrowser:
    def new_page(self, **kwargs):
        raise RuntimeError("browser crashed")


class CaptureOneErrorPathsTest(unittest.TestCase):
    @unittest.skipIf(importlib.util.find_spec("playwright") is None, "playwright is not installed")
    def test_new_page_failure_returns_error_record_and_removes_stale_files(self):
        with tempfile.TemporaryDirectory() as td:
            out = Path(td)
            (out / "example.pdf").write_bytes(b"stale")
            (out / "example.png").write_bytes(b"stale")
            record = capture.capture_one(_FailingBrowser(), _valid_capture(), out, 1000)
            self.assertEqual(record["status"], "error")
            self.assertIn("browser crashed", record["error"])
            self.assertFalse((out / "example.pdf").exists())
            self.assertFalse((out / "example.png").exists())


_BROWSER_SKIP_REASON = _browser_unavailable_reason()


@unittest.skipIf(_BROWSER_SKIP_REASON is not None, _BROWSER_SKIP_REASON or "")
class BrowserSmokeTest(unittest.TestCase):
    def _run(self, manifest_path: Path, output_dir: Path) -> subprocess.CompletedProcess:
        cmd = [sys.executable, str(CAPTURE), "--manifest", str(manifest_path),
               "--output-dir", str(output_dir), "--no-sandbox", "--allow-file-fixtures"]
        executable = os.environ.get("WAYBACK_CHROMIUM_EXECUTABLE")
        if executable:
            cmd += ["--chromium-executable", executable]
        return subprocess.run(cmd, capture_output=True, text=True)

    def test_pdf_png_hashes_and_missing_evidence_guard(self):
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

            res = self._run(path, t / "out")
            self.assertEqual(res.returncode, 0, res.stderr)
            summary = json.loads((t / "out" / "capture_results.json").read_text(encoding="utf-8"))
            self.assertEqual(summary["successes"], 1, summary)
            self.assertGreater((t / "out" / "smoke.pdf").stat().st_size, 1500)
            self.assertGreater((t / "out" / "smoke.png").stat().st_size, 1500)
            self.assertEqual(len(summary["records"][0]["pdf_sha256"]), 64)
            self.assertEqual(len(summary["manifest_sha256"]), 64)
            self.assertTrue(summary["browser_version"])
            self.assertEqual(summary["tool_version"], capture.TOOL_VERSION)

            manifest["captures"][0]["expected_phrases"] = ["nonexistent critical statement"]
            path.write_text(json.dumps(manifest), encoding="utf-8")
            res2 = self._run(path, t / "negative")
            self.assertNotEqual(res2.returncode, 0, res2.stderr)
            failure = json.loads((t / "negative" / "capture_results.json").read_text(encoding="utf-8"))
            self.assertEqual(failure["successes"], 0)
            self.assertFalse((t / "negative" / "smoke.pdf").exists())


if __name__ == "__main__":
    unittest.main()
