#!/usr/bin/env python3
"""Plan, apply, and validate governed capability Agent Plugin registration."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
SCRIPTS_ROOT = REPO_ROOT / "scripts"
if str(SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_ROOT))

from agent_plugin_mcp import MCPConfigError, normalize_mcp_servers  # noqa: E402
from apm_external_components import (  # noqa: E402
    ExternalComponentError,
    normalize_external_components,
    resolve_external_components,
)

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?$")
ROOT_GENERATED_PATHS = (
    "plugin.json",
    "marketplace.json",
    ".agents/plugins/marketplace.json",
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/marketplace.json",
    "gemini-extension.json",
)


class CapabilityPlanError(RuntimeError):
    """User-correctable capability planning or application error."""


@dataclass(frozen=True)
class PlannedFile:
    path: str
    content: bytes
    kind: str = "create"

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.content).hexdigest()


@dataclass
class Plan:
    root: Path
    spec: dict[str, Any]
    files: list[PlannedFile]
    public: dict[str, Any]
    approval_hash: str


def fail(message: str) -> "NoReturn":
    raise CapabilityPlanError(message)


def sha256_json(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def load_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"cannot read JSON {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"{path}: expected a JSON object")
    return data


def frontmatter(path: Path) -> dict[str, Any]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        fail(f"cannot read {path}: {exc}")
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


def discover_repo_root(start: Path, explicit: Path | None = None) -> Path:
    candidate = explicit.resolve() if explicit else start.resolve()
    candidates = [candidate] if explicit else [candidate, *candidate.parents]
    matches = [
        path
        for path in candidates
        if (path / "skills").is_dir()
        and (path / "plugins").is_dir()
        and (path / "scripts" / "generate-capability-plugin.py").is_file()
        and (path / "scripts" / "generate-distribution.py").is_file()
    ]
    if not matches:
        fail("could not discover svg153/skills repository root; pass --repo-root")
    root = matches[0]
    for path in (root, root / "skills", root / "plugins"):
        if path.is_symlink():
            fail(f"canonical repository path must not be a symlink: {path}")
    return root


def _nonempty(raw: dict[str, Any], field: str) -> str:
    value = raw.get(field)
    if not isinstance(value, str) or not value.strip():
        fail(f"spec.{field} must be a non-empty string")
    return value.strip()


def _string_list(value: Any, field: str, *, required: bool = False) -> list[str]:
    if value is None and not required:
        return []
    if not isinstance(value, list) or (required and not value):
        fail(f"spec.{field} must be a non-empty string array")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            fail(f"spec.{field} items must be non-empty strings")
        clean = item.strip()
        if clean not in result:
            result.append(clean)
    return result


def normalize_spec(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("schemaVersion") != 1:
        fail("spec.schemaVersion must be 1")
    name = raw.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        fail("spec.name must be lowercase kebab-case")
    version = raw.get("version")
    if not isinstance(version, str) or not SEMVER_RE.fullmatch(version):
        fail("spec.version must be semantic X.Y.Z")
    author = raw.get("author")
    if not isinstance(author, dict) or not isinstance(author.get("name"), str) or not author["name"].strip():
        fail("spec.author.name is required")
    normalized_author = {"name": author["name"].strip()}
    if author.get("url") is not None:
        if not isinstance(author["url"], str) or not author["url"].strip():
            fail("spec.author.url must be a non-empty string when set")
        normalized_author["url"] = author["url"].strip()

    spec: dict[str, Any] = {
        "schemaVersion": 1,
        "name": name,
        "version": version,
        "description": _nonempty(raw, "description"),
        "author": normalized_author,
        "license": _nonempty(raw, "license"),
        "keywords": _string_list(raw.get("keywords"), "keywords"),
        "skill_sources": _string_list(raw.get("skill_sources"), "skill_sources", required=True),
    }
    try:
        spec["externalSkillComponents"] = normalize_external_components(
            raw.get("externalSkillComponents", [])
        )
    except ExternalComponentError as exc:
        fail(f"spec.externalSkillComponents: {exc}")

    repository = raw.get("repository", "https://github.com/svg153/skills")
    homepage = raw.get("homepage", f"https://github.com/svg153/skills/tree/main/plugins/{name}")
    for field, value in (("repository", repository), ("homepage", homepage)):
        if not isinstance(value, str) or not value.strip():
            fail(f"spec.{field} must be a non-empty string")
        spec[field] = value.strip()

    if "mcpServers" in raw:
        try:
            normalize_mcp_servers(raw["mcpServers"])
        except MCPConfigError as exc:
            fail(f"spec.mcpServers: {exc}")
        spec["mcpServers"] = raw["mcpServers"]
    else:
        spec["mcpServers"] = {}
    return spec


def existing_runtime_identities(root: Path) -> dict[str, str]:
    identities: dict[str, str] = {}
    root_skills = root / "skills"
    for skill_dir in sorted(root_skills.iterdir(), key=lambda p: p.name.casefold()):
        skill_file = skill_dir / "SKILL.md"
        if not skill_dir.is_dir() or not skill_file.is_file():
            continue
        if skill_dir.is_symlink() or skill_file.is_symlink():
            fail(f"canonical skill source must not be symlinked: {skill_dir.relative_to(root)}")
        name = frontmatter(skill_file).get("name")
        if isinstance(name, str):
            identities[name.casefold()] = f"skills/{skill_dir.name}"
    plugins = root / "plugins"
    for package in sorted(plugins.iterdir(), key=lambda p: p.name.casefold()):
        skills_root = package / "skills"
        if not package.is_dir() or not skills_root.is_dir():
            continue
        if package.is_symlink() or skills_root.is_symlink():
            fail(f"capability source must not be symlinked: {package.relative_to(root)}")
        for skill_dir in sorted(skills_root.iterdir(), key=lambda p: p.name.casefold()):
            skill_file = skill_dir / "SKILL.md"
            if not skill_dir.is_dir() or not skill_file.is_file():
                continue
            if skill_dir.is_symlink() or skill_file.is_symlink():
                fail(f"capability skill must not be symlinked: {skill_dir.relative_to(root)}")
            name = frontmatter(skill_file).get("name")
            if isinstance(name, str):
                identity = name.casefold()
                if identity in identities:
                    fail(f"existing repository has duplicate runtime identity {name!r}")
                identities[identity] = f"plugins/{package.name}/skills/{skill_dir.name}"
    return identities


def resolve_source(spec_path: Path, raw_path: str) -> Path:
    source = Path(raw_path)
    candidate = spec_path.parent / source if not source.is_absolute() else source
    if candidate.is_symlink():
        fail(f"skill source must not be a symlink: {candidate}")
    return candidate.resolve()


def ensure_staging_source(root: Path, source: Path) -> None:
    if not source.is_dir():
        fail(f"skill source does not exist: {source}")
    if source.is_symlink():
        fail(f"skill source must not be a symlink: {source}")
    try:
        rel = source.relative_to(root)
    except ValueError:
        return
    if rel.parts and rel.parts[0] in {"skills", "plugins"}:
        fail(
            "capability skill_sources must be unregistered staging directories, not existing "
            f"canonical repository sources: {rel.as_posix()}"
        )


def source_payload(
    root: Path,
    spec_path: Path,
    source_paths: list[str],
    existing: dict[str, str],
    capability_name: str,
) -> tuple[list[PlannedFile], list[str]]:
    files: list[PlannedFile] = []
    runtime_names: list[str] = []
    seen: set[str] = set()
    for raw_path in source_paths:
        source = resolve_source(spec_path, raw_path)
        ensure_staging_source(root, source)
        skill_file = source / "SKILL.md"
        if not skill_file.is_file() or skill_file.is_symlink():
            fail(f"skill source must contain a regular SKILL.md: {source}")
        fm = frontmatter(skill_file)
        runtime_name = fm.get("name")
        if not isinstance(runtime_name, str) or not NAME_RE.fullmatch(runtime_name):
            fail(f"{skill_file}: invalid skill name")
        identity = runtime_name.casefold()
        if identity in seen:
            fail(f"duplicate runtime skill in capability spec: {runtime_name!r}")
        if identity in existing:
            fail(f"runtime skill {runtime_name!r} already exists at {existing[identity]}")
        seen.add(identity)
        runtime_names.append(runtime_name)

        for path in sorted(source.rglob("*")):
            rel = path.relative_to(source)
            if any(part in {".git", "node_modules"} for part in rel.parts):
                continue
            if path.is_symlink():
                fail(f"skill source contains symlink: {source}/{rel}")
            if path.is_dir():
                continue
            if rel.as_posix() == "metadata.yaml":
                continue
            target = f"plugins/{capability_name}/skills/{runtime_name}/{rel.as_posix()}"
            files.append(PlannedFile(target, path.read_bytes()))
    return files, runtime_names


def render_distribution_config(spec: dict[str, Any]) -> bytes:
    config: dict[str, Any] = {
        "schemaVersion": 1,
        "name": spec["name"],
        "version": spec["version"],
        "description": spec["description"],
        "author": spec["author"],
        "repository": spec["repository"],
        "homepage": spec["homepage"],
        "license": spec["license"],
        "keywords": spec["keywords"],
    }
    if spec["mcpServers"]:
        config["mcpServers"] = spec["mcpServers"]
    if spec["externalSkillComponents"]:
        config["externalSkillComponents"] = spec["externalSkillComponents"]
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def repo_fingerprint(root: Path) -> str:
    paths: list[Path] = [
        root / "distribution.config.json",
        root / "scripts" / "generate-distribution.py",
        root / "scripts" / "generate-capability-plugin.py",
        root / "scripts" / "agent_plugin_mcp.py",
    ]
    for optional in (
        root / "scripts" / "apm_external_components.py",
        root / "dependencies" / "external-skills" / "apm.lock.yaml",
        root / "dependencies" / "external-skills" / "apm-policy.yml",
    ):
        if optional.is_file():
            paths.append(optional)
    for base in (root / "skills", root / "plugins"):
        for skill_file in sorted(base.rglob("SKILL.md")):
            if any(part in {".git", "node_modules"} for part in skill_file.parts):
                continue
            paths.append(skill_file)
    for config in sorted((root / "plugins").glob("*/distribution.config.json")):
        paths.append(config)
    digest = hashlib.sha256()
    for path in sorted(set(paths), key=lambda p: p.relative_to(root).as_posix()):
        if path.is_symlink():
            fail(f"repository fingerprint surface must not be symlinked: {path.relative_to(root)}")
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def build_plan(root: Path, spec: dict[str, Any], spec_path: Path) -> Plan:
    package = root / "plugins" / spec["name"]
    if package.exists() or package.is_symlink():
        fail(f"capability {spec['name']!r} already exists")
    existing_packages = {
        p.name.casefold(): p.name for p in (root / "plugins").iterdir() if p.is_dir()
    }
    if spec["name"].casefold() in existing_packages:
        fail(f"case-insensitive capability collision with {existing_packages[spec['name'].casefold()]!r}")

    existing = existing_runtime_identities(root)
    source_files, runtime_names = source_payload(
        root, spec_path, spec["skill_sources"], existing, spec["name"]
    )
    files = [
        PlannedFile(
            f"plugins/{spec['name']}/distribution.config.json",
            render_distribution_config(spec),
        ),
        *source_files,
    ]

    try:
        resolved_components = resolve_external_components(
            root, spec["externalSkillComponents"]
        )
    except ExternalComponentError as exc:
        fail(f"spec.externalSkillComponents: {exc}")

    staged_identities = {name.casefold() for name in runtime_names}
    for component in resolved_components:
        identity = component["target"].casefold()
        if identity in existing:
            fail(
                f"external runtime skill {component['target']!r} already exists at "
                f"{existing[identity]}"
            )
        if identity in staged_identities:
            fail(
                f"external runtime skill {component['target']!r} collides with a local "
                "capability skill"
            )
        staged_identities.add(identity)

    for item in files:
        relative = Path(item.path)
        if relative.is_absolute() or ".." in relative.parts:
            fail(f"unsafe planned path: {item.path}")
        if (root / item.path).exists() or (root / item.path).is_symlink():
            fail(f"plan would overwrite existing path: {item.path}")

    operations = [
        {
            "path": item.path,
            "kind": item.kind,
            "sha256": item.sha256,
            "bytes": len(item.content),
        }
        for item in sorted(files, key=lambda i: i.path)
    ]
    public: dict[str, Any] = {
        "schemaVersion": 1,
        "name": spec["name"],
        "version": spec["version"],
        "skills": runtime_names,
        "mcp_servers": sorted(spec["mcpServers"]),
        "external_skill_components": [
            {
                "dependency": item["dependency"],
                "target": item["target"],
                "resolved_commit": item["resolved_commit"],
                "content_hash": item["content_hash"],
            }
            for item in resolved_components
        ],
        "repo_fingerprint": repo_fingerprint(root),
        "files": operations,
        "generated_package_files": [
            f"plugins/{spec['name']}/plugin.json",
            *([f"plugins/{spec['name']}/mcp.json"] if spec["mcpServers"] else []),
            *(
                [f"plugins/{spec['name']}/external-components.json"]
                if spec["externalSkillComponents"]
                else []
            ),
        ],
        "generated_root_files": ["marketplace.json", ".agents/plugins/marketplace.json"],
        "validations": [
            f"python scripts/generate-capability-plugin.py --config plugins/{spec['name']}/distribution.config.json --check",
            "python scripts/generate-capability-plugin.py --all --check",
            "python scripts/generate-distribution.py --check",
        ],
        "post_apply_client_checks": [
            f"DISABLE_TELEMETRY=1 npx -y skills@latest add ./plugins/{spec['name']} --list",
            f"copilot plugin install {spec['name']}@svg153-skills",
            f"codex plugin add {spec['name']}@svg153-skills --json",
        ],
    }
    approval_hash = sha256_json({"spec": spec, "plan": public})
    public["approval_hash"] = approval_hash
    return Plan(root, spec, files, public, approval_hash)


def run_command(root: Path, command: list[str]) -> dict[str, Any]:
    process = subprocess.run(
        command,
        cwd=root,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        check=False,
    )
    result = {
        "command": " ".join(command),
        "returncode": process.returncode,
        "output": process.stdout[-6000:],
    }
    if process.returncode != 0:
        raise CapabilityPlanError(
            f"validation failed: {' '.join(command)}\n{process.stdout[-6000:]}"
        )
    return result


def restore_file(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(previous)


def apply_plan(plan: Plan, *, run_validations: bool = True) -> dict[str, Any]:
    root = plan.root
    name = plan.spec["name"]
    package = root / "plugins" / name
    if package.exists() or package.is_symlink():
        fail(f"capability {name!r} appeared after planning; plan is stale")

    root_generated = [root / relative for relative in ROOT_GENERATED_PATHS]
    backups = {path: path.read_bytes() if path.is_file() else None for path in root_generated}
    results: list[dict[str, Any]] = []
    stage = Path(tempfile.mkdtemp(prefix=".capability-publish-stage-", dir=root))
    try:
        for item in plan.files:
            destination = stage / item.path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(item.content)

        staged_package = stage / "plugins" / name
        if not staged_package.is_dir():
            fail("staged plan is missing capability package")
        package.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged_package, package)

        if run_validations:
            commands = [
                [
                    sys.executable,
                    "scripts/generate-capability-plugin.py",
                    "--config",
                    f"plugins/{name}/distribution.config.json",
                ],
                [
                    sys.executable,
                    "scripts/generate-capability-plugin.py",
                    "--config",
                    f"plugins/{name}/distribution.config.json",
                    "--check",
                ],
                [sys.executable, "scripts/generate-distribution.py"],
                [sys.executable, "scripts/generate-distribution.py", "--check"],
                [sys.executable, "scripts/generate-capability-plugin.py", "--all", "--check"],
            ]
            for command in commands:
                results.append(run_command(root, command))
    except Exception:
        if package.exists():
            shutil.rmtree(package)
        for path, previous in backups.items():
            restore_file(path, previous)
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    return {
        "status": "applied",
        "name": name,
        "skills": plan.public["skills"],
        "mcp_servers": plan.public["mcp_servers"],
        "external_skill_components": plan.public["external_skill_components"],
        "approval_hash": plan.approval_hash,
        "files": [item.path for item in sorted(plan.files, key=lambda i: i.path)],
        "validation_results": results,
        "post_apply_client_checks": plan.public["post_apply_client_checks"],
    }


def plan_from_spec(
    spec_path: Path,
    *,
    repo_root: Path | None = None,
    start: Path | None = None,
) -> Plan:
    root = discover_repo_root(start or Path.cwd(), repo_root)
    return build_plan(root, normalize_spec(load_json(spec_path)), spec_path.resolve())


def check_existing(root: Path, name: str) -> dict[str, Any]:
    if not NAME_RE.fullmatch(name):
        fail("name must be lowercase kebab-case")
    config = root / "plugins" / name / "distribution.config.json"
    if not config.is_file():
        fail(f"plugins/{name}/distribution.config.json does not exist")
    results = [
        run_command(
            root,
            [
                sys.executable,
                "scripts/generate-capability-plugin.py",
                "--config",
                f"plugins/{name}/distribution.config.json",
                "--check",
            ],
        ),
        run_command(root, [sys.executable, "scripts/generate-distribution.py", "--check"]),
    ]
    return {"status": "valid", "name": name, "validation_results": results}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repo-root", type=Path, help="Explicit svg153/skills repository root")
    sub = result.add_subparsers(dest="command", required=True)
    plan_cmd = sub.add_parser("plan", help="Create a zero-write deterministic capability plan")
    plan_cmd.add_argument("--spec", required=True, type=Path)
    apply_cmd = sub.add_parser("apply", help="Apply an unchanged approved capability plan")
    apply_cmd.add_argument("--spec", required=True, type=Path)
    apply_cmd.add_argument("--approve", required=True)
    check_cmd = sub.add_parser("check", help="Validate an existing capability package")
    check_cmd.add_argument("--name", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "plan":
            print(
                json.dumps(
                    plan_from_spec(args.spec, repo_root=args.repo_root).public,
                    indent=2,
                    ensure_ascii=False,
                )
            )
            return 0
        if args.command == "apply":
            plan = plan_from_spec(args.spec, repo_root=args.repo_root)
            if args.approve != plan.approval_hash:
                fail(
                    "approval hash does not match the current plan; inputs or repository state "
                    "changed, so generate and approve a fresh dry-run"
                )
            print(json.dumps(apply_plan(plan), indent=2, ensure_ascii=False))
            return 0
        root = discover_repo_root(Path.cwd(), args.repo_root)
        print(json.dumps(check_existing(root, args.name), indent=2, ensure_ascii=False))
        return 0
    except CapabilityPlanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
