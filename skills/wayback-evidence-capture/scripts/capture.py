#!/usr/bin/env python3
"""Print verified Wayback snapshot pages to PDF and PNG using Playwright.

A browser PDF is a *later rendering* of an archived page, not a new certified
capture or an immutable representation of the original site's HTML.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import re
import sys
import unicodedata
from urllib.parse import urlparse

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def norm(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.lower()) if not unicodedata.combining(c))


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def validate_capture(capture: dict, allow_fixtures: bool) -> None:
    for key in ("id", "original_url", "snapshot_url", "snapshot_utc"):
        if not isinstance(capture.get(key), str) or not capture[key]:
            raise ValueError(f"missing or invalid '{key}'")
    if not re.fullmatch(r"[a-zA-Z0-9_-]+", capture["id"]):
        raise ValueError("capture id must be alphanumeric/hyphen/underscore")
    url = capture["snapshot_url"]
    expected_time = capture["snapshot_utc"].replace("-", "").replace(":", "").replace("T", "")[:14]
    parsed = urlparse(url)
    if parsed.scheme == "file" and allow_fixtures:
        return
    original = urlparse(capture["original_url"])
    if original.scheme not in ("http", "https") or not original.hostname:
        raise ValueError("original URL must be HTTP(S) with a valid hostname")
    phrases = capture.get("expected_phrases")
    if not isinstance(phrases, list) or not phrases or not all(isinstance(x, str) and x.strip() for x in phrases):
        raise ValueError("expected_phrases must contain meaningful non-empty strings")
    if parsed.scheme != "https" or parsed.hostname != "web.archive.org":
        raise ValueError("snapshot URL must be https://web.archive.org/web/<YYYYMMDDHHMMSS>/...")
    if not re.search(r"/web/\d{14}(?:id_|if_|im_)?/https?://", url):
        raise ValueError("snapshot URL must include a 14-digit timestamp and original URL")
    if expected_time not in url:
        raise ValueError("snapshot timestamp does not match snapshot URL")


def capture_one(browser, item: dict, output_dir: Path, timeout_ms: int) -> dict:
    name = item["id"]
    page = browser.new_page(viewport={"width": 1400, "height": 900}, device_scale_factor=1)
    meta = {
        "id": name,
        "original_url": item["original_url"],
        "snapshot_url": item["snapshot_url"],
        "snapshot_utc": item["snapshot_utc"],
        "rendered_utc": now_utc(),
        "status": "error",
    }
    try:
        if item["snapshot_url"].startswith("file://"):
            # Offline smoke test only, never allowed for real evidence manifests.
            from urllib.parse import unquote
            file_path = Path(unquote(urlparse(item["snapshot_url"]).path))
            page.set_content(file_path.read_text(encoding="utf-8"), wait_until="load")
            status = 200
        else:
            response = page.goto(item["snapshot_url"], wait_until="domcontentloaded", timeout=timeout_ms)
            try:
                page.wait_for_load_state("networkidle", timeout=min(timeout_ms, 12000))
            except PlaywrightTimeoutError:
                page.wait_for_timeout(2500)
            status = response.status if response else 0
        # Refuse redirects to the live site or another archive timestamp.
        if not item["snapshot_url"].startswith("file://"):
            resolved = urlparse(page.url)
            expected_stamp = item["snapshot_utc"].replace("-", "").replace(":", "").replace("T", "")[:14]
            if resolved.scheme != "https" or resolved.hostname != "web.archive.org" or f"/web/{expected_stamp}" not in resolved.path:
                raise RuntimeError("resolved URL is not the requested Wayback snapshot")
        title = page.title()
        text = page.locator("body").inner_text(timeout=timeout_ms)
        matches = [q for q in item.get("expected_phrases", []) if norm(q) in norm(text)]
        meta.update({"http_status": status, "title": title, "body_chars": len(text),
                     "expected_matches": matches, "expected_total": len(item.get("expected_phrases", [])),
                     "resolved_url": page.url})
        error_markers = ["the wayback machine has not archived", "this page is not available",
                         "too many requests", "temporarily unavailable", "blocked from being crawled"]
        if status >= 400 or status == 0:
            raise RuntimeError(f"HTTP {status}, not a successful page")
        if len(text.strip()) < 400:
            raise RuntimeError(f"too little visible content: {len(text)} characters")
        if any(marker in norm(text[:1600]) for marker in error_markers):
            raise RuntimeError("appears to be an error page")
        if len(matches) < len(item.get("expected_phrases", [])):
            raise RuntimeError("expected evidence phrases absent; inspect the page before trusting the PDF")
        pdf = output_dir / f"{name}.pdf"
        png = output_dir / f"{name}.png"
        page.pdf(path=str(pdf), format="A4", print_background=True,
                 margin={"top": "9mm", "bottom": "9mm", "left": "8mm", "right": "8mm"})
        page.screenshot(path=str(png), full_page=True, animations="disabled")
        meta.update({"status": "success", "pdf_filename": pdf.name, "pdf_sha256": sha256(pdf),
                     "png_filename": png.name, "png_sha256": sha256(png)})
    except Exception as ex:
        meta["error"] = f"{type(ex).__name__}: {ex}"
    finally:
        page.close()
    return meta


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__)
    a.add_argument("--manifest", type=Path, required=True)
    a.add_argument("--output-dir", type=Path, required=True)
    a.add_argument("--chromium-executable", default=None)
    a.add_argument("--timeout-ms", type=int, default=45000)
    a.add_argument("--no-sandbox", action="store_true")
    a.add_argument("--allow-file-fixtures", action="store_true", help="Only for local tests")
    args = a.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    captures = manifest.get("captures", [])
    if not captures:
        raise SystemExit("Manifest has no captures")
    if len({x["id"] for x in captures}) != len(captures):
        raise SystemExit("Duplicate IDs")
    for x in captures:
        validate_capture(x, args.allow_file_fixtures)
    args.output_dir.mkdir(parents=True, exist_ok=True)
    records = []
    with sync_playwright() as p:
        launch_args = ["--no-sandbox"] if args.no_sandbox else []
        kw = {"headless": True, "args": launch_args}
        if args.chromium_executable:
            kw["executable_path"] = args.chromium_executable
        browser = p.chromium.launch(**kw)
        try:
            for item in captures:
                record = capture_one(browser, item, args.output_dir, args.timeout_ms)
                print(f"{record['id']}: {record['status']} {record.get('error', '')}", file=sys.stderr)
                records.append(record)
        finally:
            browser.close()
    summary = {
        "tool": "wayback-evidence-capture", "tool_version": "0.1.0",
        "run_utc": now_utc(), "requested": len(records),
        "successes": sum(x["status"] == "success" for x in records), "records": records,
        "warning": "PDF/PNG are later browser renderings of archived URLs, not independently certified captures."
    }
    (args.output_dir / "capture_results.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return 0 if summary["successes"] == len(records) else 1


if __name__ == "__main__":
    raise SystemExit(main())