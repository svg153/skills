#!/usr/bin/env python3
"""Validate metadata.yaml lifecycle semantics for the skills catalog."""

from __future__ import annotations

from pathlib import Path
import sys
import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CATALOG_ORIGIN = "https://github.com/svg153/skills"


def error(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    count = 0
    for skill_dir in sorted(p for p in SKILLS.iterdir() if p.is_dir()):
        path = skill_dir / "metadata.yaml"
        if not path.is_file():
            error(f"{skill_dir.relative_to(ROOT)}: missing metadata.yaml")
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            error(f"{path.relative_to(ROOT)}: expected a YAML mapping")
        for field in ("name", "origin", "origin_path", "category", "status", "sync"):
            if data.get(field) in (None, ""):
                error(f"{path.relative_to(ROOT)}: missing {field}")
        if data["name"] != skill_dir.name:
            error(f"{path.relative_to(ROOT)}: metadata name must match catalog directory")
        sync = data["sync"]
        if not isinstance(sync, dict):
            error(f"{path.relative_to(ROOT)}: sync must be a mapping")
        strategy = sync.get("strategy")
        enabled = sync.get("enabled")
        interval = sync.get("interval")
        authority = sync.get("authoritative")
        channel = sync.get("channel")
        origin = str(data["origin"]).rstrip("/")

        if strategy == "local":
            if origin != CATALOG_ORIGIN:
                error(f"{path.relative_to(ROOT)}: local strategy must use catalog origin")
            expected_path = f"skills/{skill_dir.name}"
            if str(data["origin_path"]).lstrip("/") != expected_path:
                error(f"{path.relative_to(ROOT)}: local origin_path must be {expected_path}")
            if enabled is not False or interval != "manual" or authority != "local" or channel is not None:
                error(f"{path.relative_to(ROOT)}: local lifecycle must be disabled/manual/authoritative: local with no channel")
        elif strategy == "manual":
            if origin == CATALOG_ORIGIN:
                error(f"{path.relative_to(ROOT)}: catalog-authored skill must use strategy: local")
            if enabled is not False or interval != "manual" or authority != "local" or channel is not None:
                error(f"{path.relative_to(ROOT)}: curated lifecycle must be disabled/manual/authoritative: local with no channel")
        elif strategy == "download":
            if enabled is not True or authority != "upstream":
                error(f"{path.relative_to(ROOT)}: download lifecycle must be enabled and authoritative: upstream")
            if interval not in {"daily", "weekly", "monthly"}:
                error(f"{path.relative_to(ROOT)}: download interval must be daily, weekly, or monthly")
            if channel not in {"stable", "edge"}:
                error(f"{path.relative_to(ROOT)}: download lifecycle needs channel stable or edge")
            if not data.get("origin_ref"):
                error(f"{path.relative_to(ROOT)}: download lifecycle needs origin_ref")
            if origin == CATALOG_ORIGIN:
                error(f"{path.relative_to(ROOT)}: download lifecycle cannot point at the catalog itself")
        else:
            error(f"{path.relative_to(ROOT)}: unsupported sync.strategy {strategy!r}")
        count += 1
    print(f"OK: {count} metadata lifecycle files conform to catalog v2 semantics")


if __name__ == "__main__":
    main()
