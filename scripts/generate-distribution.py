#!/usr/bin/env python3
"""Generate cross-agent distribution manifests from canonical catalog state."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
CONFIG_PATH = ROOT / "distribution.config.json"
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")

GENERATED_PATHS = (
    Path("plugin.json"),
    Path("marketplace.json"),
    Path(".agents/plugins/marketplace.json"),
    Path(".codex-plugin/plugin.json"),
    Path(".claude-plugin/plugin.json"),
    Path(".claude-plugin/marketplace.json"),
    Path(".cursor-plugin/marketplace.json"),
    Path("gemini-extension.json"),
)


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def read_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"{path.relative_to(ROOT)}: cannot read YAML: {exc}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)}: expected a YAML mapping")
    return data


def read_frontmatter(path: Path) -> dict:
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


def load_config() -> dict:
    try:
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{CONFIG_PATH.relative_to(ROOT)}: invalid JSON: {exc}")
    required = (
        "schemaVersion",
        "name",
        "displayName",
        "version",
        "description",
        "author",
        "repository",
        "homepage",
        "category",
    )
    missing = [key for key in required if key not in config]
    if missing:
        fail(f"{CONFIG_PATH.relative_to(ROOT)}: missing keys: {', '.join(missing)}")
    if config["schemaVersion"] != 1:
        fail(f"{CONFIG_PATH.relative_to(ROOT)}: unsupported schemaVersion")
    if not NAME_RE.fullmatch(config["name"]):
        fail(f"{CONFIG_PATH.relative_to(ROOT)}: name must be lowercase kebab-case")
    author = config["author"]
    if not isinstance(author, dict) or not author.get("name") or not author.get("url"):
        fail(f"{CONFIG_PATH.relative_to(ROOT)}: author requires name and url")
    return config


def reject_symlink(path: Path) -> None:
    if path.is_symlink():
        fail(f"{path.relative_to(ROOT)}: symlinks are not allowed in canonical skill registration")


def discover_skills() -> tuple[list[str], list[str]]:
    if not SKILLS.is_dir():
        fail("skills/: canonical skill directory is missing")

    catalog_names: list[str] = []
    runtime_names: list[str] = []
    seen_catalog: dict[str, Path] = {}
    seen_runtime: dict[str, Path] = {}

    for skill_dir in sorted(SKILLS.iterdir(), key=lambda path: path.name.casefold()):
        if not skill_dir.is_dir():
            continue
        reject_symlink(skill_dir)

        skill_file = skill_dir / "SKILL.md"
        metadata_file = skill_dir / "metadata.yaml"
        reject_symlink(skill_file)
        reject_symlink(metadata_file)

        if not skill_file.is_file():
            fail(f"{skill_dir.relative_to(ROOT)}: missing SKILL.md")
        if not metadata_file.is_file():
            fail(f"{skill_dir.relative_to(ROOT)}: missing metadata.yaml")

        frontmatter = read_frontmatter(skill_file)
        metadata = read_yaml(metadata_file)
        runtime_name = frontmatter.get("name")
        metadata_name = metadata.get("name")

        if not isinstance(runtime_name, str) or not NAME_RE.fullmatch(runtime_name):
            fail(f"{skill_file.relative_to(ROOT)}: invalid runtime skill name {runtime_name!r}")
        if metadata_name != skill_dir.name:
            fail(
                f"{metadata_file.relative_to(ROOT)}: metadata name {metadata_name!r} "
                f"must match catalog directory {skill_dir.name!r}"
            )
        if not NAME_RE.fullmatch(skill_dir.name):
            fail(f"{skill_dir.relative_to(ROOT)}: invalid catalog directory name")

        catalog_identity = skill_dir.name.casefold()
        previous_catalog = seen_catalog.get(catalog_identity)
        if previous_catalog is not None:
            fail(
                f"case-insensitive catalog collision: {previous_catalog.relative_to(ROOT)} "
                f"and {skill_dir.relative_to(ROOT)}"
            )
        seen_catalog[catalog_identity] = skill_dir

        runtime_identity = runtime_name.casefold()
        previous_runtime = seen_runtime.get(runtime_identity)
        if previous_runtime is not None:
            fail(
                f"case-insensitive runtime skill collision: {previous_runtime.relative_to(ROOT)} "
                f"and {skill_file.relative_to(ROOT)}"
            )
        seen_runtime[runtime_identity] = skill_file

        catalog_names.append(skill_dir.name)
        runtime_names.append(runtime_name)

    if not catalog_names:
        fail("skills/: no skills discovered")
    return catalog_names, runtime_names


def dump(value: object) -> str:
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def render(config: dict, catalog_names: list[str], runtime_names: list[str]) -> dict[Path, str]:
    description = config["description"]
    author = config["author"]
    bundle = config["name"]
    version = config["version"]

    keywords = sorted(
        {
            "agent-skills",
            "ai-agents",
            "cross-agent",
            "github-copilot",
            "codex",
            "claude-code",
            "cursor",
            "gemini-cli",
            *catalog_names,
            *runtime_names,
        }
    )

    portable_plugin = {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json",
        "name": bundle,
        "version": version,
        "description": description,
        "author": author,
        "homepage": config["homepage"],
        "repository": config["repository"],
        "keywords": keywords,
    }

    root_marketplace = {
        "name": bundle,
        "owner": author,
        "metadata": {"description": description},
        "plugins": [
            {
                "name": bundle,
                "source": "./",
                "description": description,
                "version": version,
            }
        ],
    }

    host_plugin = {
        "name": bundle,
        "version": version,
        "description": description,
        "author": author,
        "repository": config["repository"],
        "skills": "./skills/",
    }

    return {
        Path("plugin.json"): dump(portable_plugin),
        Path("marketplace.json"): dump(root_marketplace),
        Path(".agents/plugins/marketplace.json"): dump(
            {
                "name": bundle,
                "interface": {"displayName": config["displayName"]},
                "plugins": [
                    {
                        "name": bundle,
                        "source": {"source": "local", "path": "./"},
                        "policy": {
                            "installation": "AVAILABLE",
                            "authentication": "ON_INSTALL",
                        },
                        "category": config["category"],
                    }
                ],
            }
        ),
        Path(".codex-plugin/plugin.json"): dump(host_plugin),
        Path(".claude-plugin/plugin.json"): dump(host_plugin),
        Path(".claude-plugin/marketplace.json"): dump(
            {
                "name": bundle,
                "description": description,
                "owner": author,
                "plugins": [
                    {
                        "name": bundle,
                        "source": "./",
                        "description": description,
                        "version": version,
                    }
                ],
            }
        ),
        Path(".cursor-plugin/marketplace.json"): dump(
            {
                "name": bundle,
                "owner": {"name": author["name"]},
                "metadata": {"description": description},
                "plugins": [
                    {
                        "name": bundle,
                        "source": "./",
                        "description": description,
                    }
                ],
            }
        ),
        Path("gemini-extension.json"): dump(
            {
                "name": bundle,
                "version": version,
                "description": description,
            }
        ),
    }


def check(outputs: dict[Path, str]) -> int:
    drift: list[str] = []
    for relative, expected in outputs.items():
        target = ROOT / relative
        if not target.is_file():
            drift.append(f"{relative}: missing")
            continue
        actual = target.read_text(encoding="utf-8")
        if actual != expected:
            drift.append(f"{relative}: stale")
    if drift:
        for item in drift:
            print(f"DRIFT: {item}", file=sys.stderr)
        print(
            "Run `python scripts/generate-distribution.py` and commit the generated files.",
            file=sys.stderr,
        )
        return 1
    print(f"OK: {len(outputs)} cross-agent manifests match canonical catalog state")
    return 0


def write(outputs: dict[Path, str]) -> int:
    changed = 0
    for relative, content in outputs.items():
        target = ROOT / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        previous = target.read_text(encoding="utf-8") if target.exists() else None
        if previous == content:
            continue
        target.write_text(content, encoding="utf-8")
        print(f"WROTE: {relative}")
        changed += 1
    print(f"OK: {changed} manifest(s) updated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="report generated-manifest drift without writing files",
    )
    args = parser.parse_args()

    config = load_config()
    catalog_names, runtime_names = discover_skills()
    outputs = render(config, catalog_names, runtime_names)
    unknown = set(outputs) ^ set(GENERATED_PATHS)
    if unknown:
        fail(f"internal generated-path mismatch: {sorted(str(path) for path in unknown)}")
    print(f"Catalog skills discovered: {len(catalog_names)}")

    if args.check:
        return check(outputs)
    return write(outputs)


if __name__ == "__main__":
    raise SystemExit(main())
