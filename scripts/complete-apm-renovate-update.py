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
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
APM_PROJECT = ROOT / "dependencies" / "external-skills"
APM_LOCK = APM_PROJECT / "apm.lock.yaml"
APM_POLICY = APM_PROJECT / "apm-policy.yml"

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


def validate_resolver_only_lock(lock_path: Path = APM_LOCK) -> None:
    try:
        data = yaml.safe_load(lock_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"invalid APM lock: {exc}")
    if not isinstance(data, dict):
        fail("APM lock must be a YAML mapping")
    dependencies = data.get("dependencies")
    if not isinstance(dependencies, list) or not dependencies:
        fail("APM resolver lock must contain at least one dependency")
    if data.get("deployments") != []:
        fail(
            "resolver-only APM project must keep deployments: []; refusing to let "
            "dependency completion introduce a second runtime source of truth"
        )


def collect_apm_supply_chain_evidence() -> None:
    """Run the same lock/policy/integrity evidence used by APM CI.

    A GITHUB_TOKEN-authored completion push may not trigger a fresh pull_request
    workflow run, so the trusted completion gate must carry the full evidence itself
    before it records success on the new commit.
    """

    validate_resolver_only_lock()
    with tempfile.TemporaryDirectory(prefix="apm-completion-evidence-") as temporary:
        evidence = Path(temporary)
        sbom = evidence / "external-skills.cdx.json"
        audit = evidence / "apm-audit.json"

        run(
            ["apm", "lock", "export", "--format", "cyclonedx", "--output", str(sbom)],
            cwd=APM_PROJECT,
        )
        if not sbom.is_file() or sbom.stat().st_size == 0:
            fail("APM CycloneDX export did not produce evidence")

        run(
            [
                "apm",
                "policy",
                "status",
                "--policy-source",
                str(APM_POLICY),
                "--check",
                "--json",
            ],
            cwd=APM_PROJECT,
        )
        run(
            [
                "apm",
                "audit",
                "--ci",
                "--no-drift",
                "--policy",
                str(APM_POLICY),
                "--no-fail-fast",
                "--format",
                "json",
                "--output",
                str(audit),
            ],
            cwd=APM_PROJECT,
        )
        if not audit.is_file() or audit.stat().st_size == 0:
            fail("APM audit did not produce evidence")


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
    collect_apm_supply_chain_evidence()
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
