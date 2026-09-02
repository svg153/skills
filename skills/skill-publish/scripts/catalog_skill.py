#!/usr/bin/env python3
"""Plan, apply, and validate repository-native skill registration for svg153/skills."""

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

NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
OWNERSHIP_MODES = {"LOCAL", "MIRRORED_UPSTREAM", "CURATED_UPSTREAM"}
GENERATED_PATHS = (
    "plugin.json",
    "marketplace.json",
    ".agents/plugins/marketplace.json",
    ".codex-plugin/plugin.json",
    ".claude-plugin/plugin.json",
    ".claude-plugin/marketplace.json",
    ".cursor-plugin/marketplace.json",
    "gemini-extension.json",
)
STOPWORDS = {
    "a", "an", "and", "the", "to", "for", "of", "in", "on", "with", "or", "from",
    "skill", "skills", "agent", "agents", "use", "using", "create", "help", "when",
}


class SkillPlanError(RuntimeError):
    """User-correctable planning or application error."""


@dataclass(frozen=True)
class PlannedFile:
    path: str
    content: bytes
    kind: str

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
    raise SkillPlanError(message)


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


def load_yaml(path: Path) -> dict[str, Any]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"cannot read YAML {path}: {exc}")
    if not isinstance(data, dict):
        fail(f"{path}: expected a YAML mapping")
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
        data = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        fail(f"{path}: invalid frontmatter: {exc}")
    if not isinstance(data, dict):
        fail(f"{path}: frontmatter must be a mapping")
    return data


def discover_repo_root(start: Path, explicit: Path | None = None) -> Path:
    candidate = explicit.resolve() if explicit else start.resolve()
    candidates = [candidate] if explicit else [candidate, *candidate.parents]
    matches = [
        path for path in candidates
        if (path / "skills").is_dir()
        and (path / "skills.sh.json").is_file()
        and (path / "distribution.config.json").is_file()
        and (path / "scripts" / "generate-distribution.py").is_file()
    ]
    if not matches:
        fail("could not discover svg153/skills repository root; pass --repo-root")
    root = matches[0]
    if root.is_symlink() or (root / "skills").is_symlink():
        fail("repository root and canonical skills directory must not be symlinks")
    protected = [
        root / "skills.sh.json",
        root / "distribution.config.json",
        root / "scripts" / "generate-distribution.py",
    ]
    eval_root = root / "evals"
    if eval_root.exists():
        protected.append(eval_root)
    protected.extend(root / relative for relative in GENERATED_PATHS)
    for path in protected:
        if path.is_symlink():
            fail(f"repository registration surface must not be a symlink: {path.relative_to(root)}")
    return root


def normalize_list(value: Any, field: str, *, required: bool = True) -> list[str]:
    if value is None and not required:
        return []
    if not isinstance(value, list) or (required and not value):
        fail(f"spec.{field} must be a non-empty list")
    result: list[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            fail(f"spec.{field} items must be non-empty strings")
        clean = " ".join(item.split())
        if clean not in result:
            result.append(clean)
    return result


def normalize_spec(raw: dict[str, Any]) -> dict[str, Any]:
    if raw.get("schemaVersion") != 1:
        fail("spec.schemaVersion must be 1")
    name = raw.get("name")
    if not isinstance(name, str) or not NAME_RE.fullmatch(name):
        fail("spec.name must be lowercase kebab-case")
    ownership = raw.get("ownership")
    if ownership not in OWNERSHIP_MODES:
        fail(f"spec.ownership must be one of {sorted(OWNERSHIP_MODES)}")

    summary = raw.get("summary")
    category = raw.get("category")
    status = raw.get("status")
    if not isinstance(summary, str) or not summary.strip():
        fail("spec.summary is required")
    if not isinstance(category, str) or not category.strip():
        fail("spec.category is required")
    if not isinstance(status, str) or not status.strip():
        fail("spec.status is required")

    spec: dict[str, Any] = {
        "schemaVersion": 1,
        "name": name,
        "ownership": ownership,
        "summary": " ".join(summary.split()),
        "use_for": normalize_list(raw.get("use_for"), "use_for"),
        "do_not_use_for": normalize_list(raw.get("do_not_use_for"), "do_not_use_for"),
        "category": category.strip(),
        "status": status.strip(),
        "tags": normalize_list(raw.get("tags"), "tags"),
        "apm": raw.get("apm"),
        "evals": raw.get("evals"),
    }
    if not isinstance(spec["apm"], bool):
        fail("spec.apm must be boolean")
    if not isinstance(spec["evals"], bool):
        fail("spec.evals must be boolean")

    group = raw.get("skills_sh_group")
    if group is not None and (not isinstance(group, str) or not group.strip()):
        fail("spec.skills_sh_group must be a non-empty string when set")
    spec["skills_sh_group"] = group.strip() if isinstance(group, str) else None

    allowed = normalize_list(raw.get("allow_overlap_with"), "allow_overlap_with", required=False)
    for item in allowed:
        if not NAME_RE.fullmatch(item):
            fail("spec.allow_overlap_with entries must be lowercase kebab-case")
    spec["allow_overlap_with"] = sorted(set(allowed))

    if spec["evals"]:
        for field in ("eval_positive_prompt", "eval_negative_prompt", "eval_behavior"):
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"spec.{field} is required when spec.evals is true")
            spec[field] = " ".join(value.split())

    if ownership == "LOCAL":
        for field in ("license", "author", "body"):
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"spec.{field} is required for LOCAL skills")
            spec[field] = value.strip() if field != "body" else value.strip() + "\n"
        if not spec["body"].lstrip().startswith("#"):
            fail("spec.body must begin with a Markdown heading")
        forbidden = ("source_dir", "origin", "origin_path", "origin_ref", "sync_interval", "channel")
        present = [field for field in forbidden if raw.get(field) not in (None, "")]
        if present:
            fail(f"LOCAL skills must not set upstream fields: {', '.join(present)}")
    else:
        for field in ("source_dir", "origin", "origin_path"):
            value = raw.get(field)
            if not isinstance(value, str) or not value.strip():
                fail(f"spec.{field} is required for {ownership}")
            spec[field] = value.strip()
        origin = spec["origin"].rstrip("/")
        if not re.fullmatch(r"https://github\.com/[^/\s]+/[^/\s]+(?:\.git)?", origin):
            fail("spec.origin must be an HTTPS GitHub repository URL")
        spec["origin"] = origin
        origin_path = spec["origin_path"]
        if "\\" in origin_path:
            fail("spec.origin_path must use POSIX separators")
        origin_parts = [part for part in origin_path.strip("/").split("/") if part and part != "."]
        if any(part == ".." for part in origin_parts):
            fail("spec.origin_path must not contain '..'")
        spec["origin_path"] = "/" if origin_path.strip() in {"", "/"} else "/".join(origin_parts)
        origin_ref = raw.get("origin_ref")
        if origin_ref is not None and (not isinstance(origin_ref, str) or not origin_ref.strip()):
            fail("spec.origin_ref must be a non-empty string when set")
        spec["origin_ref"] = origin_ref.strip() if isinstance(origin_ref, str) else None
        if spec["origin_ref"] is not None:
            ref = spec["origin_ref"]
            if not re.fullmatch(r"[A-Za-z0-9._/-]+", ref) or ".." in ref.split("/"):
                fail("spec.origin_ref contains unsafe characters or traversal")
        if ownership == "MIRRORED_UPSTREAM":
            for field in ("origin_ref", "sync_interval", "channel"):
                value = raw.get(field)
                if not isinstance(value, str) or not value.strip():
                    fail(f"spec.{field} is required for MIRRORED_UPSTREAM")
                spec[field] = value.strip()
            if spec["sync_interval"] not in {"daily", "weekly", "monthly"}:
                fail("spec.sync_interval must be daily, weekly, or monthly")
            if spec["channel"] not in {"stable", "edge"}:
                fail("spec.channel must be stable or edge")
        else:
            if raw.get("sync_interval") not in (None, "", "manual"):
                fail("CURATED_UPSTREAM uses manual synchronization; omit sync_interval or use 'manual'")
            if raw.get("channel") not in (None, ""):
                fail("CURATED_UPSTREAM must not set an automatic sync channel")
    return spec


def description_for(spec: dict[str, Any]) -> str:
    description = f"Trigger: {'; '.join(spec['use_for'])}. {spec['summary']}"
    if len(description) > 250:
        fail("generated SKILL.md description exceeds 250 chars; shorten summary/use_for")
    return description


def render_local_skill(spec: dict[str, Any]) -> bytes:
    description = json.dumps(description_for(spec), ensure_ascii=False)
    license_text = json.dumps(spec["license"], ensure_ascii=False)
    author = json.dumps(spec["author"], ensure_ascii=False)
    body = spec["body"].lstrip()
    text = (
        "---\n"
        f"name: {spec['name']}\n"
        f"description: {description}\n"
        f"license: {license_text}\n"
        "metadata:\n"
        f"  author: {author}\n"
        '  version: "1.0"\n'
        "---\n\n"
        f"{body}"
    )
    return text.encode("utf-8")


def source_payload(spec: dict[str, Any], spec_path: Path) -> tuple[list[PlannedFile], str, str | None]:
    source = Path(spec["source_dir"])
    source = (spec_path.parent / source).resolve() if not source.is_absolute() else source.resolve()
    if not source.is_dir():
        fail(f"source_dir does not exist: {source}")
    if source.is_symlink():
        fail("source_dir must not be a symlink")
    skill_file = source / "SKILL.md"
    if not skill_file.is_file() or skill_file.is_symlink():
        fail("source_dir must contain a regular SKILL.md")
    fm = frontmatter(skill_file)
    runtime_name = fm.get("name")
    if not isinstance(runtime_name, str) or not NAME_RE.fullmatch(runtime_name):
        fail("source SKILL.md has an invalid runtime name")
    license_value = fm.get("license")
    license_text = str(license_value).strip() if license_value is not None else None

    files: list[PlannedFile] = []
    for path in sorted(source.rglob("*")):
        rel = path.relative_to(source)
        if any(part in {".git", "node_modules"} for part in rel.parts):
            continue
        if path.is_symlink():
            fail(f"source payload contains symlink: {rel}")
        if path.is_dir():
            continue
        if rel.as_posix() == "metadata.yaml":
            continue
        files.append(PlannedFile(f"skills/{spec['name']}/{rel.as_posix()}", path.read_bytes(), "create"))
    return files, runtime_name, license_text


def render_metadata(spec: dict[str, Any]) -> bytes:
    name = spec["name"]
    ownership = spec["ownership"]
    if ownership == "LOCAL":
        origin, origin_path, origin_ref = "https://github.com/svg153/skills", f"skills/{name}", None
        sync = {"enabled": False, "interval": "manual", "strategy": "local", "authoritative": "local"}
    elif ownership == "MIRRORED_UPSTREAM":
        origin, origin_path, origin_ref = spec["origin"], spec["origin_path"], spec["origin_ref"]
        sync = {"enabled": True, "interval": spec["sync_interval"], "strategy": "download", "authoritative": "upstream", "channel": spec["channel"]}
    else:
        origin, origin_path, origin_ref = spec["origin"], spec["origin_path"], spec.get("origin_ref")
        sync = {"enabled": False, "interval": "manual", "strategy": "manual", "authoritative": "local"}

    metadata: dict[str, Any] = {"name": name, "origin": origin, "origin_path": origin_path}
    if origin_ref:
        metadata["origin_ref"] = origin_ref
    metadata.update({"category": spec["category"], "status": spec["status"], "sync": sync, "tags": spec["tags"]})
    return yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True).encode("utf-8")


def render_apm(spec: dict[str, Any], license_text: str) -> bytes:
    value = {"name": spec["name"], "version": "1.0.0", "description": spec["summary"], "license": license_text, "includes": "auto", "dependencies": {"apm": [], "mcp": []}, "scripts": {}}
    return yaml.safe_dump(value, sort_keys=False, allow_unicode=True).encode("utf-8")


def render_evals(spec: dict[str, Any]) -> list[PlannedFile]:
    if not spec["evals"]:
        return []
    name = spec["name"]
    eval_spec = {"name": f"{name}-behavioral", "description": f"Catalog-owned behavioral evaluation suite for {name}.", "skill": name, "schemaVersion": "1.2", "version": "1.0", "config": {"trials_per_task": 1, "timeout_seconds": 300, "parallel": False, "executor": "copilot-sdk", "inject_skill_body": False}, "metrics": [{"name": "trigger_accuracy", "weight": 0.45, "threshold": 0.8}, {"name": "behavior_quality", "weight": 0.35, "threshold": 0.7}, {"name": "task_completion", "weight": 0.20, "threshold": 0.7}], "tasks": ["tasks/*.yaml"]}
    positive = {"id": f"{name}-positive", "name": f"{name} activates for its primary workflow", "inputs": {"prompt": spec["eval_positive_prompt"]}, "expected": {"should_trigger": True, "graders": [{"type": "trigger", "name": "activation", "config": {"skill_path": f"skills/{name}/SKILL.md", "mode": "positive", "threshold": 0.6}}, {"type": "prompt", "name": "behavior_contract", "config": {"prompt": spec["eval_behavior"]}}]}}
    negative = {"id": f"{name}-boundary", "name": f"{name} stays out of an explicit boundary", "inputs": {"prompt": spec["eval_negative_prompt"]}, "expected": {"should_trigger": False, "graders": [{"type": "trigger", "name": "boundary", "config": {"skill_path": f"skills/{name}/SKILL.md", "mode": "negative", "threshold": 0.6}}]}}
    return [
        PlannedFile(f"evals/{name}/eval.yaml", yaml.safe_dump(eval_spec, sort_keys=False, allow_unicode=True).encode(), "create"),
        PlannedFile(f"evals/{name}/tasks/{name}-positive.yaml", yaml.safe_dump(positive, sort_keys=False, allow_unicode=True).encode(), "create"),
        PlannedFile(f"evals/{name}/tasks/{name}-boundary.yaml", yaml.safe_dump(negative, sort_keys=False, allow_unicode=True).encode(), "create"),
    ]


def repo_fingerprint(root: Path) -> str:
    paths = [root / "skills.sh.json", root / "distribution.config.json", root / "scripts" / "generate-distribution.py", root / "scripts" / "validate-skills.py"]
    validate_evals = root / "scripts" / "validate-evals.py"
    if validate_evals.exists():
        paths.append(validate_evals)
    for skill_dir in sorted((root / "skills").iterdir(), key=lambda p: p.name.casefold()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.is_symlink():
            fail(f"canonical skill directory is a symlink: {skill_dir.name}")
        for filename in ("SKILL.md", "metadata.yaml"):
            path = skill_dir / filename
            if path.is_file():
                if path.is_symlink():
                    fail(f"canonical file is a symlink: {path.relative_to(root)}")
                paths.append(path)
    digest = hashlib.sha256()
    for path in sorted(set(paths), key=lambda p: p.relative_to(root).as_posix()):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def existing_identities(root: Path) -> tuple[dict[str, str], dict[str, str], dict[str, str]]:
    catalog, runtime, descriptions = {}, {}, {}
    for skill_dir in sorted((root / "skills").iterdir(), key=lambda p: p.name.casefold()):
        if not skill_dir.is_dir() or not (skill_dir / "SKILL.md").is_file():
            continue
        fm = frontmatter(skill_dir / "SKILL.md")
        catalog[skill_dir.name.casefold()] = skill_dir.name
        runtime_name = fm.get("name")
        if isinstance(runtime_name, str):
            runtime[runtime_name.casefold()] = skill_dir.name
        descriptions[skill_dir.name] = str(fm.get("description") or "")
    return catalog, runtime, descriptions


def meaningful_tokens(text: str) -> set[str]:
    tokens = set(re.findall(r"[a-z0-9][a-z0-9-]+", text.casefold()))
    return {token for token in tokens if token not in STOPWORDS and len(token) > 2}


def detect_overlaps(spec: dict[str, Any], descriptions: dict[str, str]) -> list[dict[str, str]]:
    allowed = set(spec["allow_overlap_with"])
    overlaps = []
    for candidate, description in descriptions.items():
        if candidate in allowed:
            continue
        desc_fold, desc_tokens = description.casefold(), meaningful_tokens(description)
        for phrase in spec["use_for"]:
            phrase_fold, phrase_tokens = phrase.casefold(), meaningful_tokens(phrase)
            substring = len(phrase_fold) >= 5 and phrase_fold in desc_fold
            overlap_score = len(phrase_tokens & desc_tokens) / len(phrase_tokens) if phrase_tokens else 0.0
            if substring or (len(phrase_tokens) >= 2 and overlap_score >= 0.8):
                overlaps.append({"skill": candidate, "phrase": phrase, "reason": "exact trigger phrase" if substring else f"token overlap {overlap_score:.2f}"})
                break
    return overlaps


def updated_skills_sh(root: Path, spec: dict[str, Any]) -> PlannedFile | None:
    group = spec.get("skills_sh_group")
    if not group:
        return None
    path = root / "skills.sh.json"
    data = load_json(path)
    groupings = data.get("groupings")
    if not isinstance(groupings, list):
        fail("skills.sh.json groupings must be a list")
    matches = [item for item in groupings if isinstance(item, dict) and isinstance(item.get("title"), str) and item["title"].casefold() == group.casefold()]
    if len(matches) != 1:
        fail(f"skills_sh_group {group!r} must match exactly one existing grouping")
    skills = matches[0].get("skills")
    if not isinstance(skills, list):
        fail(f"skills.sh.json grouping {group!r} has invalid skills list")
    if spec["name"] not in skills:
        skills.append(spec["name"])
    content = (json.dumps(data, indent=2, ensure_ascii=False) + "\n").encode()
    return None if content == path.read_bytes() else PlannedFile("skills.sh.json", content, "update")


def build_plan(root: Path, spec: dict[str, Any], spec_path: Path) -> Plan:
    name = spec["name"]
    target, eval_target = root / "skills" / name, root / "evals" / name
    if target.exists() or target.is_symlink():
        fail(f"skill {name!r} already exists; extend/update it instead of creating a duplicate")
    if spec["evals"] and (eval_target.exists() or eval_target.is_symlink()):
        fail(f"eval suite already exists: evals/{name}")

    catalog, runtime, descriptions = existing_identities(root)
    if name.casefold() in catalog:
        fail(f"case-insensitive catalog collision with {catalog[name.casefold()]!r}")

    files: list[PlannedFile] = []
    if spec["ownership"] == "LOCAL":
        runtime_name, license_text = name, spec["license"]
        files.append(PlannedFile(f"skills/{name}/SKILL.md", render_local_skill(spec), "create"))
    else:
        source_files, runtime_name, license_text = source_payload(spec, spec_path)
        files.extend(source_files)

    if runtime_name.casefold() in runtime:
        fail(f"case-insensitive runtime name collision: {runtime_name!r} is already owned by {runtime[runtime_name.casefold()]!r}")
    unknown = sorted(set(spec["allow_overlap_with"]) - set(descriptions))
    if unknown:
        fail("allow_overlap_with references unknown catalog skills: " + ", ".join(unknown))
    overlaps = detect_overlaps(spec, descriptions)
    if overlaps:
        summary = ", ".join(f"{item['skill']} ({item['phrase']!r}: {item['reason']})" for item in overlaps)
        fail("substantial trigger/use-case overlap detected; prefer extending an existing skill or explicitly list an accepted sibling in allow_overlap_with: " + summary)

    files.append(PlannedFile(f"skills/{name}/metadata.yaml", render_metadata(spec), "create"))
    source_has_apm = any(item.path == f"skills/{name}/apm.yml" for item in files)
    if spec["apm"] and not source_has_apm:
        if not license_text:
            fail("cannot generate APM packaging because the skill license is unknown")
        files.append(PlannedFile(f"skills/{name}/apm.yml", render_apm(spec, license_text), "create"))
    files.extend(render_evals(spec))
    group_update = updated_skills_sh(root, spec)
    if group_update:
        files.append(group_update)

    for item in files:
        destination = root / item.path
        if item.kind == "create" and (destination.exists() or destination.is_symlink()):
            fail(f"plan would overwrite existing path: {item.path}")
        if ".." in Path(item.path).parts or Path(item.path).is_absolute():
            fail(f"unsafe planned path: {item.path}")

    operations = [{"path": item.path, "kind": item.kind, "sha256": item.sha256, "bytes": len(item.content)} for item in sorted(files, key=lambda i: i.path)]
    public = {
        "schemaVersion": 1,
        "name": name,
        "ownership": spec["ownership"],
        "runtime_name": runtime_name,
        "repo_fingerprint": repo_fingerprint(root),
        "accepted_overlap_exceptions": spec["allow_overlap_with"],
        "files": operations,
        "regenerate": list(GENERATED_PATHS),
        "validations": ["python scripts/generate-distribution.py --check", "python scripts/validate-skills.py", "python scripts/validate-evals.py", "python -m json.tool skills.sh.json", "bash scripts/sync-upstreams.sh --list"],
        "post_apply_client_checks": ["DISABLE_TELEMETRY=1 npx -y skills@latest add . --list", *([f"apm install skills/{name} --target agent-skills --verbose"] if spec["apm"] or source_has_apm else [])],
    }
    approval_hash = sha256_json({"spec": spec, "plan": public})
    public["approval_hash"] = approval_hash
    return Plan(root, spec, files, public, approval_hash)


def safe_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.parent.is_symlink():
        fail(f"refusing write through symlinked parent: {path.parent}")
    path.write_bytes(content)


def restore_file(path: Path, previous: bytes | None) -> None:
    if previous is None:
        path.unlink(missing_ok=True)
    else:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(previous)


def run_command(root: Path, command: list[str]) -> dict[str, Any]:
    process = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    result = {"command": " ".join(command), "returncode": process.returncode, "output": process.stdout[-6000:]}
    if process.returncode != 0:
        raise SkillPlanError(f"validation failed: {' '.join(command)}\n{process.stdout[-6000:]}")
    return result


def apply_plan(plan: Plan, *, run_validations: bool = True) -> dict[str, Any]:
    root, name = plan.root, plan.spec["name"]
    skill_dir, eval_dir = root / "skills" / name, root / "evals" / name
    if skill_dir.exists() or skill_dir.is_symlink():
        fail(f"skill {name!r} appeared after planning; plan is stale")
    if plan.spec["evals"] and (eval_dir.exists() or eval_dir.is_symlink()):
        fail(f"evals/{name} appeared after planning; plan is stale")

    backup_paths = [root / "skills.sh.json", *(root / item for item in GENERATED_PATHS)]
    backups = {path: path.read_bytes() if path.is_file() else None for path in backup_paths}
    created_roots: list[Path] = []
    results: list[dict[str, Any]] = []
    stage = Path(tempfile.mkdtemp(prefix=".skill-publish-stage-", dir=root))
    try:
        for item in plan.files:
            safe_write(stage / item.path, item.content)
        staged_skill = stage / "skills" / name
        if not staged_skill.is_dir():
            fail("staged plan is missing the new skill directory")
        skill_dir.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged_skill, skill_dir)
        created_roots.append(skill_dir)
        staged_eval = stage / "evals" / name
        if staged_eval.exists():
            eval_dir.parent.mkdir(parents=True, exist_ok=True)
            os.replace(staged_eval, eval_dir)
            created_roots.append(eval_dir)
        for item in plan.files:
            if item.kind == "update":
                destination = root / item.path
                destination.parent.mkdir(parents=True, exist_ok=True)
                os.replace(stage / item.path, destination)

        if run_validations:
            commands = [[sys.executable, "scripts/generate-distribution.py"], [sys.executable, "scripts/generate-distribution.py", "--check"], [sys.executable, "scripts/validate-skills.py"]]
            if (root / "scripts" / "validate-evals.py").is_file():
                commands.append([sys.executable, "scripts/validate-evals.py"])
            commands.extend([[sys.executable, "-m", "json.tool", "skills.sh.json"], ["bash", "scripts/sync-upstreams.sh", "--list"]])
            for command in commands:
                results.append(run_command(root, command))
    except Exception:
        for created in reversed(created_roots):
            if created.exists():
                shutil.rmtree(created)
        for path, previous in backups.items():
            restore_file(path, previous)
        raise
    finally:
        shutil.rmtree(stage, ignore_errors=True)

    return {"status": "applied", "name": name, "approval_hash": plan.approval_hash, "files": [item.path for item in sorted(plan.files, key=lambda i: i.path)], "validation_results": results, "post_apply_client_checks": plan.public["post_apply_client_checks"]}


def plan_from_spec(spec_path: Path, *, repo_root: Path | None = None, start: Path | None = None) -> Plan:
    root = discover_repo_root(start or Path.cwd(), repo_root)
    return build_plan(root, normalize_spec(load_json(spec_path)), spec_path.resolve())


def check_existing(root: Path, name: str) -> dict[str, Any]:
    if not NAME_RE.fullmatch(name):
        fail("name must be lowercase kebab-case")
    if not (root / "skills" / name / "SKILL.md").is_file():
        fail(f"skills/{name}/SKILL.md does not exist")
    results = [run_command(root, [sys.executable, "scripts/generate-distribution.py", "--check"]), run_command(root, [sys.executable, "scripts/validate-skills.py"])]
    if (root / "scripts" / "validate-evals.py").is_file():
        results.append(run_command(root, [sys.executable, "scripts/validate-evals.py"]))
    return {"status": "valid", "name": name, "validation_results": results}


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repo-root", type=Path, help="Explicit svg153/skills repository root")
    sub = result.add_subparsers(dest="command", required=True)
    plan_cmd = sub.add_parser("plan", help="Create a zero-write deterministic plan")
    plan_cmd.add_argument("--spec", required=True, type=Path)
    apply_cmd = sub.add_parser("apply", help="Apply an unchanged approved plan")
    apply_cmd.add_argument("--spec", required=True, type=Path)
    apply_cmd.add_argument("--approve", required=True)
    check_cmd = sub.add_parser("check", help="Validate an existing registered skill")
    check_cmd.add_argument("--name", required=True)
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    try:
        if args.command == "plan":
            print(json.dumps(plan_from_spec(args.spec, repo_root=args.repo_root).public, indent=2, ensure_ascii=False))
            return 0
        if args.command == "apply":
            plan = plan_from_spec(args.spec, repo_root=args.repo_root)
            if args.approve != plan.approval_hash:
                fail("approval hash does not match the current plan; inputs or repository state changed, so generate and approve a fresh dry-run")
            print(json.dumps(apply_plan(plan), indent=2, ensure_ascii=False))
            return 0
        root = discover_repo_root(Path.cwd(), args.repo_root)
        print(json.dumps(check_existing(root, args.name), indent=2, ensure_ascii=False))
        return 0
    except SkillPlanError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
