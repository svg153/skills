#!/usr/bin/env python3
"""Validate portable Agent Skill frontmatter across the catalog."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def fail(message: str) -> None:
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path.relative_to(ROOT)}: missing opening YAML frontmatter delimiter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        fail(f"{path.relative_to(ROOT)}: missing closing YAML frontmatter delimiter")
    try:
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        fail(f"{path.relative_to(ROOT)}: invalid YAML frontmatter: {exc}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)}: frontmatter must be a YAML mapping")
    return data


def main() -> None:
    runtime_names: dict[str, Path] = {}
    count = 0

    for skill_dir in sorted(path for path in SKILLS.iterdir() if path.is_dir()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_file.is_file():
            fail(f"{skill_dir.relative_to(ROOT)}: missing SKILL.md")

        data = frontmatter(skill_file)
        name = data.get("name")
        description = data.get("description")

        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            fail(
                f"{skill_file.relative_to(ROOT)}: name must be lowercase kebab-case; "
                f"got {name!r}"
            )
        if not isinstance(description, str) or not description.strip():
            fail(f"{skill_file.relative_to(ROOT)}: description must be a non-empty string")
        if len(description) > 1024:
            fail(f"{skill_file.relative_to(ROOT)}: description exceeds 1024 characters")

        previous = runtime_names.get(name)
        if previous is not None:
            fail(
                f"duplicate runtime skill name {name!r}: "
                f"{previous.relative_to(ROOT)} and {skill_file.relative_to(ROOT)}"
            )
        runtime_names[name] = skill_file
        count += 1

    print(f"OK: {count} SKILL.md files have valid, unique Agent Skill frontmatter")


if __name__ == "__main__":
    main()
