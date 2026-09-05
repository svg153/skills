#!/usr/bin/env python3
"""Generate a portable Agent Plugins capability package from package-local config."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

from agent_plugin_mcp import MCPConfigError, PLUGIN_SCHEMA, mcp_manifest_from_distribution_config

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")


class CapabilityPluginError(RuntimeError):
    pass


def fail(message: str) -> "NoReturn":
    raise CapabilityPluginError(message)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path}: invalid JSON: {exc}")
    if not isinstance(data, dict):
        fail(f"{path}: expected an object")
    return data


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path}: missing opening YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        fail(f"{path}: missing closing YAML frontmatter")
    try:
        value = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        fail(f"{path}: invalid frontmatter: {exc}")
    if not isinstance(value, dict):
        fail(f"{path}: frontmatter must be a mapping")
    return value


def normalize_config(config: dict, config_path: Path) -> dict:
    if config.get("schemaVersion") != 1:
        fail(f"{config_path}: schemaVersion must be 1")
    required = ("name", "version", "description", "author", "repository", "homepage", "license")
    missing = [field for field in required if field not in config]
    if missing:
        fail(f"{config_path}: missing fields: {', '.join(missing)}")
    if not isinstance(config["name"], str) or not NAME_RE.fullmatch(config["name"]):
        fail(f"{config_path}: name must be lowercase kebab-case")
    if not isinstance(config["version"], str) or not SEMVER_RE.fullmatch(config["version"]):
        fail(f"{config_path}: version must be semantic X.Y.Z")
    for field in ("description", "repository", "homepage", "license"):
        if not isinstance(config[field], str) or not config[field].strip():
            fail(f"{config_path}: {field} must be a non-empty string")
    author = config["author"]
    if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
        fail(f"{config_path}: author.name is required")
    if "url" in author and (not isinstance(author["url"], str) or not author["url"].strip()):
        fail(f"{config_path}: author.url must be a non-empty string when present")
    keywords = config.get("keywords", [])
    if not isinstance(keywords, list) or not all(isinstance(item, str) and item.strip() for item in keywords):
        fail(f"{config_path}: keywords must be a string array")
    return config


def discover_skills(package_root: Path) -> list[str]:
    skills_root = package_root / "skills"
    if not skills_root.is_dir() or skills_root.is_symlink():
        fail(f"{skills_root}: package must contain a regular skills/ directory")
    names: list[str] = []
    seen: set[str] = set()
    for directory in sorted(skills_root.iterdir(), key=lambda item: item.name.casefold()):
        if not directory.is_dir():
            continue
        if directory.is_symlink():
            fail(f"{directory}: symlinked skill directories are not portable")
        skill_file = directory / "SKILL.md"
        if not skill_file.is_file() or skill_file.is_symlink():
            fail(f"{directory}: missing regular SKILL.md")
        data = frontmatter(skill_file)
        name = data.get("name")
        if not isinstance(name, str) or not NAME_RE.fullmatch(name):
            fail(f"{skill_file}: invalid skill name")
        if name != directory.name:
            fail(f"{skill_file}: skill name must match directory {directory.name!r}")
        identity = name.casefold()
        if identity in seen:
            fail(f"{skills_root}: duplicate skill identity {name!r}")
        seen.add(identity)
        names.append(name)
    if not names:
        fail(f"{skills_root}: no skills discovered")
    return names


def render(config: dict, skill_names: list[str]) -> dict[Path, str]:
    keywords = sorted({"agent-plugins", "agent-skills", *config.get("keywords", []), *skill_names})
    plugin = {
        "$schema": PLUGIN_SCHEMA,
        "name": config["name"],
        "version": config["version"],
        "description": config["description"],
        "author": config["author"],
        "homepage": config["homepage"],
        "repository": config["repository"],
        "license": config["license"],
        "keywords": keywords,
    }
    outputs = {Path("plugin.json"): json.dumps(plugin, indent=2, ensure_ascii=False) + "\n"}
    try:
        mcp = mcp_manifest_from_distribution_config(config)
    except MCPConfigError as exc:
        fail(f"MCP configuration: {exc}")
    if mcp is not None:
        outputs[Path("mcp.json")] = json.dumps(mcp, indent=2, ensure_ascii=False) + "\n"
    return outputs


def check(package_root: Path, outputs: dict[Path, str]) -> int:
    drift: list[str] = []
    for relative, expected in outputs.items():
        path = package_root / relative
        if not path.is_file():
            drift.append(f"{relative}: missing")
        elif path.read_text(encoding="utf-8") != expected:
            drift.append(f"{relative}: stale")
    mcp_path = package_root / "mcp.json"
    if Path("mcp.json") not in outputs and mcp_path.exists():
        drift.append("mcp.json: stale; package config declares no MCP servers")
    if drift:
        for item in drift:
            print(f"DRIFT: {item}", file=sys.stderr)
        return 1
    print(f"OK: {package_root} portable capability package is clean")
    return 0


def write(package_root: Path, outputs: dict[Path, str]) -> int:
    changed = 0
    for relative, content in outputs.items():
        path = package_root / relative
        if path.exists() and path.read_text(encoding="utf-8") == content:
            continue
        path.write_text(content, encoding="utf-8")
        print(f"WROTE: {path}")
        changed += 1
    mcp_path = package_root / "mcp.json"
    if Path("mcp.json") not in outputs and mcp_path.exists():
        mcp_path.unlink()
        print(f"REMOVED: {mcp_path}")
        changed += 1
    print(f"OK: {changed} file(s) updated")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    config_path = args.config.resolve()
    if config_path.name != "distribution.config.json":
        fail("capability config must be named distribution.config.json")
    package_root = config_path.parent
    config = normalize_config(load_json(config_path), config_path)
    skill_names = discover_skills(package_root)
    outputs = render(config, skill_names)
    return check(package_root, outputs) if args.check else write(package_root, outputs)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except CapabilityPluginError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(2)
