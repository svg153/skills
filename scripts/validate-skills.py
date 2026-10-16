#!/usr/bin/env python3
"""Validate portable Agent Skills against the Agent Skills specification."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
CATALOG_SKILLS = ROOT / "skills"
PLUGINS = ROOT / "plugins"

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
MAX_NAME_LENGTH = 64
MAX_DESCRIPTION_LENGTH = 1024
MAX_COMPATIBILITY_LENGTH = 500
ALLOWED_FIELDS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}


def relative(path: Path, root: Path = ROOT) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def parse_frontmatter(path: Path, root: Path = ROOT) -> tuple[dict | None, list[str]]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        return None, [f"{relative(path, root)}: cannot read file: {exc}"]

    lines = text.splitlines()
    if not lines or lines[0] != "---":
        return None, [f"{relative(path, root)}: missing opening YAML frontmatter delimiter"]

    try:
        closing = lines.index("---", 1)
    except ValueError:
        return None, [f"{relative(path, root)}: missing closing YAML frontmatter delimiter"]

    try:
        data = yaml.safe_load("\n".join(lines[1:closing]))
    except yaml.YAMLError as exc:
        return None, [f"{relative(path, root)}: invalid YAML frontmatter: {exc}"]

    if not isinstance(data, dict):
        return None, [f"{relative(path, root)}: frontmatter must be a YAML mapping"]

    non_string_keys = [key for key in data if not isinstance(key, str)]
    if non_string_keys:
        errors.append(
            f"{relative(path, root)}: frontmatter keys must be strings; "
            f"got {non_string_keys!r}"
        )

    return data, errors


def discover_skill_dirs(root: Path = ROOT) -> tuple[list[Path], list[str]]:
    errors: list[str] = []
    skill_dirs: list[Path] = []

    catalog = root / "skills"
    if not catalog.is_dir():
        return [], ["skills/: canonical skill directory is missing"]

    for skill_dir in sorted(path for path in catalog.iterdir() if path.is_dir()):
        skill_dirs.append(skill_dir)

    plugins = root / "plugins"
    if plugins.exists():
        if not plugins.is_dir():
            errors.append("plugins/: expected a directory")
        else:
            for plugin_dir in sorted(path for path in plugins.iterdir() if path.is_dir()):
                plugin_skills = plugin_dir / "skills"
                if not plugin_skills.exists():
                    continue
                if not plugin_skills.is_dir():
                    errors.append(
                        f"{relative(plugin_skills, root)}: expected a directory"
                    )
                    continue
                skill_dirs.extend(
                    sorted(path for path in plugin_skills.iterdir() if path.is_dir())
                )

    return skill_dirs, errors


def validate_skill_dir(skill_dir: Path, root: Path = ROOT) -> tuple[str | None, list[str]]:
    errors: list[str] = []
    skill_file = skill_dir / "SKILL.md"

    if not skill_file.is_file():
        return None, [f"{relative(skill_dir, root)}: missing SKILL.md"]

    data, parse_errors = parse_frontmatter(skill_file, root)
    errors.extend(parse_errors)
    if data is None:
        return None, errors

    extra_fields = {key for key in data if isinstance(key, str)} - ALLOWED_FIELDS
    if extra_fields:
        errors.append(
            f"{relative(skill_file, root)}: unexpected frontmatter fields: "
            f"{', '.join(sorted(extra_fields))}; allowed fields are "
            f"{', '.join(sorted(ALLOWED_FIELDS))}"
        )

    name = data.get("name")
    if not isinstance(name, str) or not name:
        errors.append(
            f"{relative(skill_file, root)}: name must be a non-empty string"
        )
        runtime_name = None
    else:
        runtime_name = name
        if len(name) > MAX_NAME_LENGTH:
            errors.append(
                f"{relative(skill_file, root)}: name exceeds "
                f"{MAX_NAME_LENGTH} characters ({len(name)})"
            )
        if not NAME_RE.fullmatch(name):
            errors.append(
                f"{relative(skill_file, root)}: name must contain only lowercase "
                "ASCII letters, numbers, and single hyphens, and must not start "
                "or end with a hyphen"
            )
        if name != skill_dir.name:
            errors.append(
                f"{relative(skill_file, root)}: name {name!r} must match parent "
                f"directory {skill_dir.name!r}"
            )

    description = data.get("description")
    if not isinstance(description, str) or not description.strip():
        errors.append(
            f"{relative(skill_file, root)}: description must be a non-empty string"
        )
    elif len(description) > MAX_DESCRIPTION_LENGTH:
        errors.append(
            f"{relative(skill_file, root)}: description exceeds "
            f"{MAX_DESCRIPTION_LENGTH} characters ({len(description)})"
        )

    if "license" in data:
        license_value = data["license"]
        if not isinstance(license_value, str) or not license_value.strip():
            errors.append(
                f"{relative(skill_file, root)}: license must be a non-empty string when provided"
            )

    if "compatibility" in data:
        compatibility = data["compatibility"]
        if not isinstance(compatibility, str) or not compatibility.strip():
            errors.append(
                f"{relative(skill_file, root)}: compatibility must be a non-empty string when provided"
            )
        elif len(compatibility) > MAX_COMPATIBILITY_LENGTH:
            errors.append(
                f"{relative(skill_file, root)}: compatibility exceeds "
                f"{MAX_COMPATIBILITY_LENGTH} characters ({len(compatibility)})"
            )

    if "metadata" in data:
        metadata = data["metadata"]
        if not isinstance(metadata, dict):
            errors.append(
                f"{relative(skill_file, root)}: metadata must be a mapping of string keys to string values"
            )
        else:
            for key, value in metadata.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    errors.append(
                        f"{relative(skill_file, root)}: metadata entries must use "
                        f"string keys and string values; got {key!r}: {value!r}"
                    )

    if "allowed-tools" in data:
        allowed_tools = data["allowed-tools"]
        if not isinstance(allowed_tools, str) or not allowed_tools.strip():
            errors.append(
                f"{relative(skill_file, root)}: allowed-tools must be a non-empty space-separated string when provided"
            )

    return runtime_name, errors


def validate_repository(root: Path = ROOT) -> tuple[int, list[str]]:
    skill_dirs, errors = discover_skill_dirs(root)
    runtime_names: dict[str, Path] = {}
    count = 0

    for skill_dir in skill_dirs:
        runtime_name, skill_errors = validate_skill_dir(skill_dir, root)
        errors.extend(skill_errors)
        if runtime_name is not None:
            previous = runtime_names.get(runtime_name)
            if previous is not None:
                errors.append(
                    f"duplicate runtime skill name {runtime_name!r}: "
                    f"{relative(previous / 'SKILL.md', root)} and "
                    f"{relative(skill_dir / 'SKILL.md', root)}"
                )
            else:
                runtime_names[runtime_name] = skill_dir
        count += 1

    if not skill_dirs:
        errors.append("no Agent Skills discovered")

    return count, errors


def main() -> int:
    count, errors = validate_repository()
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        print(
            f"FAILED: {len(errors)} Agent Skills specification violation(s) "
            f"across {count} skill directories",
            file=sys.stderr,
        )
        return 1

    print(
        f"OK: {count} Agent Skills comply with the portable frontmatter "
        "requirements and have unique runtime names"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
