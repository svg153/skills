#!/usr/bin/env python3
"""Plan, apply, or check metadata lifecycle normalization for svg153/skills."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import yaml

CATALOG_ORIGIN = "https://github.com/svg153/skills"


class RepairError(RuntimeError):
    pass


def load(path: Path) -> dict[str, Any]:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise RepairError(f"{path}: expected YAML mapping")
    return data


def dump(data: dict[str, Any]) -> bytes:
    return yaml.safe_dump(data, sort_keys=False, allow_unicode=True).encode("utf-8")


def normalized(data: dict[str, Any], name: str) -> tuple[dict[str, Any], str]:
    result = dict(data)
    result["name"] = name
    origin = str(result.get("origin") or "").rstrip("/")
    if not origin:
        raise RepairError(f"skills/{name}/metadata.yaml: missing origin")
    result["origin"] = origin
    sync = result.get("sync")
    if not isinstance(sync, dict):
        raise RepairError(f"skills/{name}/metadata.yaml: sync must be a mapping")
    strategy = sync.get("strategy")

    if strategy == "download":
        if sync.get("authoritative") != "upstream" or sync.get("enabled") is not True:
            raise RepairError(f"skills/{name}/metadata.yaml: ambiguous download lifecycle; repair it explicitly")
        return result, "MIRRORED_UPSTREAM"

    if origin == CATALOG_ORIGIN:
        result["origin_path"] = f"skills/{name}"
        result["sync"] = {
            "enabled": False,
            "interval": "manual",
            "strategy": "local",
            "authoritative": "local",
        }
        return result, "LOCAL"

    if strategy not in {"manual", "local"}:
        raise RepairError(f"skills/{name}/metadata.yaml: cannot infer lifecycle from strategy {strategy!r}")
    result["sync"] = {
        "enabled": False,
        "interval": "manual",
        "strategy": "manual",
        "authoritative": "local",
    }
    return result, "CURATED_UPSTREAM"


def fingerprint(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted((root / "skills").glob("*/metadata.yaml")):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + path.read_bytes() + b"\0")
    return digest.hexdigest()


def build_plan(root: Path) -> dict[str, Any]:
    changes: list[dict[str, Any]] = []
    for path in sorted((root / "skills").glob("*/metadata.yaml")):
        name = path.parent.name
        before = path.read_bytes()
        before_data = load(path)
        after_data, ownership = normalized(before_data, name)

        # Drift is semantic, not a formatting preference. A hand-authored YAML file
        # that already represents the canonical lifecycle must not be rewritten just
        # because PyYAML would serialize it differently.
        if after_data != before_data:
            after = dump(after_data)
            changes.append({
                "path": path.relative_to(root).as_posix(),
                "ownership": ownership,
                "before_sha256": hashlib.sha256(before).hexdigest(),
                "after_sha256": hashlib.sha256(after).hexdigest(),
                "content": after.decode("utf-8"),
            })
    public_changes = [{k: v for k, v in item.items() if k != "content"} for item in changes]
    public = {
        "schemaVersion": 1,
        "repo_fingerprint": fingerprint(root),
        "changes": public_changes,
    }
    public["approval_hash"] = hashlib.sha256(
        json.dumps(public, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {"public": public, "changes": changes}


def apply(root: Path, approval: str, *, validate: bool = True) -> dict[str, Any]:
    plan = build_plan(root)
    if approval != plan["public"]["approval_hash"]:
        raise RepairError("approval hash does not match current repository state; generate a fresh plan")
    backups: dict[Path, bytes] = {}
    try:
        for item in plan["changes"]:
            path = root / item["path"]
            if path.is_symlink() or path.parent.is_symlink():
                raise RepairError(f"refusing write through symlink: {item['path']}")
            backups[path] = path.read_bytes()
            path.write_text(item["content"], encoding="utf-8")
        if validate:
            commands = [
                [sys.executable, "scripts/validate-metadata-lifecycle.py"],
                [sys.executable, "scripts/validate-skills.py"],
                [sys.executable, "scripts/generate-distribution.py", "--check"],
            ]
            for command in commands:
                completed = subprocess.run(command, cwd=root, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
                if completed.returncode:
                    raise RepairError(f"validation failed: {' '.join(command)}\n{completed.stdout}")
    except Exception:
        for path, content in backups.items():
            path.write_bytes(content)
        raise
    return {
        "status": "applied",
        "approval_hash": approval,
        "changed": [item["path"] for item in plan["changes"]],
    }


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("--repo-root", type=Path, default=Path.cwd())
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("plan", help="Print a zero-write normalization plan")
    apply_cmd = sub.add_parser("apply", help="Apply an unchanged approved plan")
    apply_cmd.add_argument("--approve", required=True)
    sub.add_parser("check", help="Fail when metadata normalization drift exists")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.repo_root.resolve()
    try:
        plan = build_plan(root)
        if args.command == "plan":
            print(json.dumps(plan["public"], indent=2))
            return 0
        if args.command == "check":
            if plan["changes"]:
                raise RepairError(f"metadata lifecycle drift detected in {len(plan['changes'])} file(s); run plan/apply")
            print("OK: metadata lifecycle has no repair drift")
            return 0
        print(json.dumps(apply(root, args.approve), indent=2))
        return 0
    except (OSError, yaml.YAMLError, RepairError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
