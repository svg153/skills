#!/usr/bin/env python3
"""Complete a trusted Renovate APM dependency update in the current worktree.

This script intentionally does not inspect or mutate GitHub PR metadata and does not
push. The trusted workflow validates the PR author/head/change allowlist first, then
checks out that exact head and invokes this repository-owned orchestrator.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
APM_PROJECT = ROOT / "dependencies" / "external-skills"

DISTRIBUTION_EXACT = {
    "plugin.json",
    "marketplace.json",
    "gemini-extension.json",
}
DISTRIBUTION_PREFIXES = (
    ".agents/",
    ".codex-plugin/",
    ".claude-plugin/",
    ".cursor-plugin/",
)


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"ERROR: {message}")


def run(command: list[str], *, cwd: Path = ROOT, env: dict[str, str] | None = None) -> None:
    print(f"+ {' '.join(command)}")
    subprocess.run(command, cwd=cwd, env=env, check=True)


def changed_worktree_paths() -> set[str]:
    changed: set[str] = set()
    for command in (
        ["git", "diff", "--name-only"],
        ["git", "diff", "--cached", "--name-only"],
        ["git", "ls-files", "--others", "--exclude-standard"],
    ):
        completed = subprocess.run(
            command,
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
        changed.update(line.strip() for line in completed.stdout.splitlines() if line.strip())
    return changed


def allowed_generated_path(path: str, skill: str) -> bool:
    if path == "dependencies/external-skills/apm.lock.yaml":
        return True
    if path in DISTRIBUTION_EXACT:
        return True
    if any(path.startswith(prefix) for prefix in DISTRIBUTION_PREFIXES):
        return True
    skill_prefix = f"skills/{skill}/"
    if path.startswith(skill_prefix):
        # metadata.yaml is catalog-owned governance. A mirrored upstream update
        # must never rewrite it as an incidental dependency artifact.
        return path != f"{skill_prefix}metadata.yaml"
    return False


def validate_generated_scope(skill: str) -> list[str]:
    changed = sorted(changed_worktree_paths())
    unexpected = [path for path in changed if not allowed_generated_path(path, skill)]
    if unexpected:
        fail("completion produced unexpected paths: " + ", ".join(unexpected))
    if f"skills/{skill}/metadata.yaml" in changed:
        fail(f"completion modified catalog-owned skills/{skill}/metadata.yaml")
    return changed


def complete(skill: str) -> list[str]:
    if shutil.which("apm") is None:
        fail("APM CLI is not installed; run scripts/install-apm-ci.sh in CI first")

    metadata = ROOT / "skills" / skill / "metadata.yaml"
    if not metadata.is_file():
        fail(f"unknown catalog skill or missing metadata: {skill}")

    # Dependency resolution is owned by APM. Never independently resolve
    # latest-release here; the materializer consumes only the resulting lock.
    run(["apm", "lock"], cwd=APM_PROJECT)
    run([sys.executable, "scripts/materialize-apm-mirror.py", skill, "--apply"])
    run([sys.executable, "scripts/generate-distribution.py"])

    # Validate before any caller is allowed to commit/push the generated state.
    run(["git", "diff", "--check"])
    run([sys.executable, "scripts/validate-workflow-security.py"])
    run([sys.executable, "scripts/validate-skills.py"])
    run([sys.executable, "scripts/validate-metadata-lifecycle.py"])
    run([sys.executable, "skills/skill-publish/scripts/metadata_repair.py", "check"])
    run([sys.executable, "scripts/generate-distribution.py", "--check"])
    run([sys.executable, "scripts/generate-catalog.py", "--check"])
    run([sys.executable, "scripts/validate-evals.py"])
    run([sys.executable, "scripts/materialize-apm-mirror.py", skill, "--check"])

    env = os.environ.copy()
    env["DISABLE_TELEMETRY"] = "1"
    run(["npx", "-y", "skills@latest", "add", ".", "--list"], env=env)

    changed = validate_generated_scope(skill)
    if changed:
        print("Completion output:")
        for path in changed:
            print(f"  {path}")
    else:
        print("Completion is already converged; no generated changes remain.")
    return changed


def parser() -> argparse.ArgumentParser:
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument("skill", help="MIRRORED_UPSTREAM catalog skill to materialize")
    return result


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    complete(args.skill)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
