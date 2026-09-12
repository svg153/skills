#!/usr/bin/env python3
"""Resolve and materialize capability-scoped external Agent Skills from APM lock state."""

from __future__ import annotations

import filecmp
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Any

import yaml

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
CONTENT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
MANIFEST_NAME = "external-components.json"


class ExternalComponentError(RuntimeError):
    """Fail-closed external component declaration or materialization error."""


def fail(message: str) -> "NoReturn":
    raise ExternalComponentError(message)


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot read {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path}: expected a YAML mapping")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read {path}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path}: expected a JSON object")
    return value


def parse_locator(locator: str) -> tuple[str, str]:
    parts = [part for part in locator.strip("/").split("/") if part]
    if len(parts) < 3 or any(part in {".", ".."} for part in parts):
        fail(
            "external dependency locator must be owner/repo/path with no path traversal: "
            f"{locator!r}"
        )
    return "/".join(parts[:2]), "/".join(parts[2:])


def normalize_external_components(value: Any) -> list[dict[str, str]]:
    if value in (None, []):
        return []
    if not isinstance(value, list):
        fail("externalSkillComponents must be an array")

    result: list[dict[str, str]] = []
    seen_targets: set[str] = set()
    seen_dependencies: set[str] = set()
    allowed = {"dependency", "target", "license", "attribution"}
    for index, raw in enumerate(value):
        if not isinstance(raw, dict):
            fail(f"externalSkillComponents[{index}] must be an object")
        unknown = set(raw) - allowed
        if unknown:
            fail(
                f"externalSkillComponents[{index}] has unsupported fields: "
                + ", ".join(sorted(unknown))
            )
        normalized: dict[str, str] = {}
        for field in ("dependency", "target", "license", "attribution"):
            item = raw.get(field)
            if not isinstance(item, str) or not item.strip():
                fail(f"externalSkillComponents[{index}].{field} must be a non-empty string")
            normalized[field] = item.strip()

        parse_locator(normalized["dependency"])
        if not NAME_RE.fullmatch(normalized["target"]):
            fail(
                f"externalSkillComponents[{index}].target must be lowercase kebab-case"
            )
        target_id = normalized["target"].casefold()
        if target_id in seen_targets:
            fail(f"duplicate external component target: {normalized['target']!r}")
        if normalized["dependency"] in seen_dependencies:
            fail(f"duplicate external dependency: {normalized['dependency']!r}")
        seen_targets.add(target_id)
        seen_dependencies.add(normalized["dependency"])
        result.append(normalized)
    return result


def _normalize_repo_slug(value: str) -> str:
    result = value.strip()
    if result.startswith("https://github.com/"):
        result = result[len("https://github.com/") :]
    if result.endswith(".git"):
        result = result[:-4]
    return result.strip("/")


def resolve_external_components(
    repo_root: Path, declarations: list[dict[str, str]]
) -> list[dict[str, str]]:
    if not declarations:
        return []

    lock_path = repo_root / "dependencies" / "external-skills" / "apm.lock.yaml"
    policy_path = repo_root / "dependencies" / "external-skills" / "apm-policy.yml"
    lock = _load_yaml(lock_path)
    policy = _load_yaml(policy_path)

    allow = policy.get("dependencies", {}).get("allow", [])
    if not isinstance(allow, list) or not all(isinstance(item, str) for item in allow):
        fail(f"{policy_path}: dependencies.allow must be a string array")
    allowed = set(allow)

    dependencies = lock.get("dependencies", [])
    if not isinstance(dependencies, list):
        fail(f"{lock_path}: dependencies must be an array")

    resolved: list[dict[str, str]] = []
    for declaration in declarations:
        locator = declaration["dependency"]
        if locator not in allowed:
            fail(f"external dependency is not allowlisted by APM policy: {locator}")
        repo_slug, virtual_path = parse_locator(locator)
        matches = [
            item
            for item in dependencies
            if isinstance(item, dict)
            and _normalize_repo_slug(str(item.get("repo_url", ""))) == repo_slug
            and str(item.get("virtual_path", "")).strip("/") == virtual_path
        ]
        if len(matches) != 1:
            fail(
                f"expected exactly one APM lock entry for {locator}; found {len(matches)}"
            )
        dependency = matches[0]
        commit = str(dependency.get("resolved_commit", ""))
        ref = str(dependency.get("resolved_ref", ""))
        content_hash = str(dependency.get("content_hash", ""))
        if not COMMIT_RE.fullmatch(commit):
            fail(f"APM lock entry for {locator} has invalid resolved_commit")
        if not ref:
            fail(f"APM lock entry for {locator} is missing resolved_ref")
        if not CONTENT_HASH_RE.fullmatch(content_hash):
            fail(f"APM lock entry for {locator} has invalid content_hash")

        resolved.append(
            {
                **declaration,
                "repo_url": repo_slug,
                "virtual_path": virtual_path,
                "resolved_ref": ref,
                "resolved_commit": commit,
                "content_hash": content_hash,
            }
        )
    return resolved


def manifest_data(resolved: list[dict[str, str]]) -> dict[str, Any]:
    return {
        "schemaVersion": 1,
        "authority": "dependencies/external-skills/apm.lock.yaml",
        "components": [
            {
                "dependency": item["dependency"],
                "target": item["target"],
                "license": item["license"],
                "attribution": item["attribution"],
                "repo_url": item["repo_url"],
                "virtual_path": item["virtual_path"],
                "resolved_ref": item["resolved_ref"],
                "resolved_commit": item["resolved_commit"],
                "content_hash": item["content_hash"],
            }
            for item in resolved
        ],
    }


def render_manifest(resolved: list[dict[str, str]]) -> str:
    return json.dumps(manifest_data(resolved), indent=2, ensure_ascii=False) + "\n"


def _frontmatter_name(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path}: missing YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        fail(f"{path}: missing closing YAML frontmatter")
    try:
        value = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        fail(f"{path}: invalid frontmatter: {exc}")
    if not isinstance(value, dict) or not isinstance(value.get("name"), str):
        fail(f"{path}: frontmatter name is required")
    return value["name"]


def _payload_files(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if any(part in {".git", "node_modules"} for part in relative.parts):
            continue
        if path.is_symlink():
            fail(f"external component payload contains a symlink: {relative.as_posix()}")
        if path.is_dir():
            continue
        result[relative.as_posix()] = path
    return result


def _compare_payload(source: Path, target: Path) -> list[str]:
    if not target.is_dir() or target.is_symlink():
        return ["missing materialized target"]
    source_files = _payload_files(source)
    target_files = _payload_files(target)
    messages: list[str] = []
    for name in sorted(source_files.keys() - target_files.keys()):
        messages.append(f"missing locally: {name}")
    for name in sorted(target_files.keys() - source_files.keys()):
        messages.append(f"extra locally: {name}")
    for name in sorted(source_files.keys() & target_files.keys()):
        if not filecmp.cmp(source_files[name], target_files[name], shallow=False):
            messages.append(f"content differs: {name}")
    return messages


def _checkout_locked_source(resolved: dict[str, str], temp: Path) -> Path:
    checkout = temp / "upstream"
    origin = f"https://github.com/{resolved['repo_url']}.git"
    subprocess.run(["git", "init", str(checkout)], check=True, capture_output=True, text=True)
    subprocess.run(
        ["git", "-C", str(checkout), "remote", "add", "origin", origin],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        [
            "git",
            "-C",
            str(checkout),
            "fetch",
            "--depth",
            "1",
            "origin",
            resolved["resolved_commit"],
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    subprocess.run(
        ["git", "-C", str(checkout), "checkout", "--detach", "FETCH_HEAD"],
        check=True,
        capture_output=True,
        text=True,
    )
    actual = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual != resolved["resolved_commit"]:
        fail(
            f"locked external component resolved to {actual}, expected "
            f"{resolved['resolved_commit']}"
        )
    source = checkout / resolved["virtual_path"]
    skill_file = source / "SKILL.md"
    if not skill_file.is_file() or skill_file.is_symlink():
        fail(f"locked external component has no regular SKILL.md: {resolved['dependency']}")
    return source


def _existing_runtime_identities(repo_root: Path, package_root: Path) -> dict[str, str]:
    identities: dict[str, str] = {}
    for skill_file in sorted((repo_root / "skills").glob("*/SKILL.md")):
        if skill_file.is_symlink():
            fail(f"root runtime skill is symlinked: {skill_file.relative_to(repo_root)}")
        name = _frontmatter_name(skill_file)
        identities[name.casefold()] = str(skill_file.parent.relative_to(repo_root))
    plugins = repo_root / "plugins"
    if plugins.is_dir():
        for skill_file in sorted(plugins.glob("*/skills/*/SKILL.md")):
            if package_root in skill_file.parents:
                continue
            if skill_file.is_symlink():
                fail(f"capability runtime skill is symlinked: {skill_file.relative_to(repo_root)}")
            name = _frontmatter_name(skill_file)
            identity = name.casefold()
            if identity in identities:
                fail(f"repository already has duplicate runtime identity {name!r}")
            identities[identity] = str(skill_file.parent.relative_to(repo_root))
    return identities


def _previous_components(package_root: Path) -> dict[str, dict[str, Any]]:
    manifest = package_root / MANIFEST_NAME
    if not manifest.is_file():
        return {}
    value = _load_json(manifest)
    components = value.get("components", [])
    if not isinstance(components, list):
        fail(f"{manifest}: components must be an array")
    result: dict[str, dict[str, Any]] = {}
    for item in components:
        if isinstance(item, dict) and isinstance(item.get("target"), str):
            result[item["target"].casefold()] = item
    return result


def sync_external_components(
    repo_root: Path,
    package_root: Path,
    resolved: list[dict[str, str]],
    *,
    check_only: bool,
) -> list[str]:
    manifest_path = package_root / MANIFEST_NAME
    previous = _previous_components(package_root)
    external_targets = {item["target"].casefold(): item for item in resolved}
    identities = _existing_runtime_identities(repo_root, package_root)
    drift: list[str] = []

    for identity, item in external_targets.items():
        if identity in identities:
            fail(
                f"external component target {item['target']!r} collides with "
                f"{identities[identity]}"
            )

    skills_root = package_root / "skills"
    skills_root.mkdir(parents=True, exist_ok=True)

    for identity, item in external_targets.items():
        target = skills_root / item["target"]
        prior = previous.get(identity)
        if target.exists() and prior is None:
            fail(
                f"external component target {item['target']!r} already exists but is not "
                "recorded as a previously materialized external component"
            )
        if prior is not None and prior.get("dependency") != item["dependency"]:
            fail(
                f"external component target {item['target']!r} changed dependency from "
                f"{prior.get('dependency')!r} to {item['dependency']!r}"
            )

        with tempfile.TemporaryDirectory(prefix="capability-external-") as temporary:
            source = _checkout_locked_source(item, Path(temporary))
            source_name = _frontmatter_name(source / "SKILL.md")
            if source_name != item["target"]:
                fail(
                    f"locked skill name {source_name!r} does not match declared target "
                    f"{item['target']!r}"
                )
            _payload_files(source)
            differences = _compare_payload(source, target)
            if differences:
                if check_only:
                    drift.extend(f"{item['target']}: {message}" for message in differences)
                else:
                    if target.exists():
                        if target.is_symlink():
                            fail(f"refuse to replace symlinked target: {target}")
                        shutil.rmtree(target)
                    shutil.copytree(source, target)

    stale_targets = set(previous) - set(external_targets)
    for identity in sorted(stale_targets):
        prior = previous[identity]
        target_name = str(prior.get("target", identity))
        target = skills_root / target_name
        if check_only:
            if target.exists():
                drift.append(f"{target_name}: stale materialized external component")
        elif target.exists():
            if target.is_symlink():
                fail(f"refuse to remove symlinked stale target: {target}")
            shutil.rmtree(target)

    expected_manifest = render_manifest(resolved) if resolved else None
    if expected_manifest is None:
        if check_only and manifest_path.exists():
            drift.append(f"{MANIFEST_NAME}: stale; no external components are declared")
        elif not check_only and manifest_path.exists():
            manifest_path.unlink()
    elif check_only:
        if not manifest_path.is_file():
            drift.append(f"{MANIFEST_NAME}: missing")
        elif manifest_path.read_text(encoding="utf-8") != expected_manifest:
            drift.append(f"{MANIFEST_NAME}: stale")
    else:
        manifest_path.write_text(expected_manifest, encoding="utf-8")

    return drift
