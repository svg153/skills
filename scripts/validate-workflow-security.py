#!/usr/bin/env python3
"""Enforce the repository GitHub Actions security baseline."""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / ".github" / "workflows"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
WRITE_PERMISSION_RE = re.compile(r"(?:^|-)(?:write|admin)$")


def fail(errors: list[str]) -> None:
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    raise SystemExit(1)


def load_workflow(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail([f"{path.relative_to(ROOT)}: invalid YAML: {exc}"])
    if not isinstance(data, dict):
        fail([f"{path.relative_to(ROOT)}: workflow must be a YAML mapping"])
    return data


def top_level_permissions(data: dict) -> dict:
    permissions = data.get("permissions")
    return permissions if isinstance(permissions, dict) else {}


def has_write_permission(permissions: dict) -> bool:
    for value in permissions.values():
        if isinstance(value, str) and WRITE_PERMISSION_RE.search(value):
            return True
    return False


def iter_steps(data: dict):
    jobs = data.get("jobs")
    if not isinstance(jobs, dict):
        return
    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            continue
        for index, step in enumerate(job.get("steps", []) or [], start=1):
            if isinstance(step, dict):
                yield str(job_name), index, step


def validate_direct_local_command(location: str, stripped: str, errors: list[str]) -> None:
    """Require workflow-local commands invoked as ./path to be executable in Git."""
    if not stripped.startswith("./"):
        return

    command = stripped.split(maxsplit=1)[0]
    relative = Path(command[2:])
    if not relative.parts or ".." in relative.parts:
        errors.append(f"{location}: unsafe direct local command {command!r}")
        return

    target = ROOT / relative
    if not target.is_file():
        errors.append(f"{location}: direct local command {command!r} does not exist")
        return
    if target.stat().st_mode & 0o111 == 0:
        errors.append(
            f"{location}: direct local command {command!r} is not executable; "
            "commit the executable bit or invoke it explicitly through its interpreter"
        )


def validate(path: Path) -> list[str]:
    data = load_workflow(path)
    rel = path.relative_to(ROOT)
    errors: list[str] = []

    # PyYAML 1.1 may parse the key `on` as boolean True, so support both forms.
    triggers = data.get("on", data.get(True))
    if isinstance(triggers, dict) and "pull_request_target" in triggers:
        errors.append(f"{rel}: pull_request_target is forbidden for repository workflows")

    permissions = top_level_permissions(data)
    if not permissions:
        errors.append(f"{rel}: declare explicit top-level permissions")
    if path.name == "validate.yml" and has_write_permission(permissions):
        errors.append(f"{rel}: validation workflow must remain read-only")

    jobs = data.get("jobs")
    if not isinstance(jobs, dict) or not jobs:
        errors.append(f"{rel}: jobs mapping is missing or empty")
        return errors

    for job_name, job in jobs.items():
        if not isinstance(job, dict):
            errors.append(f"{rel}: job {job_name!r} must be a mapping")
            continue
        timeout = job.get("timeout-minutes")
        if not isinstance(timeout, int) or timeout <= 0:
            errors.append(f"{rel}: job {job_name!r} requires a positive timeout-minutes")

    for job_name, index, step in iter_steps(data):
        location = f"{rel}: job {job_name!r} step {index}"
        uses = step.get("uses")
        if isinstance(uses, str) and not uses.startswith("./"):
            if "@" not in uses:
                errors.append(f"{location}: external action {uses!r} is missing an immutable ref")
            else:
                action, ref = uses.rsplit("@", 1)
                if not SHA_RE.fullmatch(ref):
                    errors.append(
                        f"{location}: {action} must be pinned to a full 40-character commit SHA"
                    )
                if action == "actions/checkout":
                    with_block = step.get("with")
                    persist = with_block.get("persist-credentials") if isinstance(with_block, dict) else None
                    if persist is not False:
                        errors.append(f"{location}: actions/checkout must set persist-credentials: false")

        run = step.get("run")
        if isinstance(run, str):
            for line in run.splitlines():
                stripped = line.strip()
                if stripped.startswith("npm ci") and "--ignore-scripts" not in stripped:
                    errors.append(f"{location}: npm ci must use --ignore-scripts")
                validate_direct_local_command(location, stripped, errors)

    return errors


def main() -> None:
    paths = sorted([*WORKFLOWS.glob("*.yml"), *WORKFLOWS.glob("*.yaml")])
    if not paths:
        fail([".github/workflows: no workflows found"])

    errors: list[str] = []
    for path in paths:
        errors.extend(validate(path))

    if errors:
        fail(errors)
    print(f"OK: {len(paths)} workflow(s) satisfy the repository security baseline")


if __name__ == "__main__":
    main()
