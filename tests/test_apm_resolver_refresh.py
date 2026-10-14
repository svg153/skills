#!/usr/bin/env python3
"""Real APM CLI regression for the resolver-only catalog (requires APM + network)."""

from pathlib import Path
import shutil
import subprocess
import tempfile

import yaml

ROOT = Path(__file__).resolve().parents[1]
PROJECT = ROOT / "dependencies" / "external-skills"
PREVIOUS_SHA = "74f8cfeca5c0ed5799a0ab71be88d06fc9e2afb1"
CURRENT_SHA = "24af1931681bb03b0282472c4d4b6900359418c7"


def run(project: Path, *args: str) -> subprocess.CompletedProcess:
    result = subprocess.run(
        ["apm", *args], cwd=project, capture_output=True, text=True, timeout=180
    )
    print(result.stdout, end="")
    print(result.stderr, end="")
    return result


def check_lock(project: Path, expected_sha: str) -> None:
    lock = yaml.safe_load((project / "apm.lock.yaml").read_text())
    assert lock["deployments"] == [], "resolver refresh deployed runtime files"
    dependency = lock["dependencies"][0]
    assert dependency["resolved_commit"] == expected_sha
    assert dependency["resolved_ref"] == expected_sha
    assert dependency["content_hash"].startswith("sha256:")
    assert not dependency.get("deployed_files")
    for path in (".agents", ".claude", ".github", ".cursor", ".codex"):
        assert not (project / path).exists(), f"unexpected harness tree: {path}"


def main() -> None:
    assert shutil.which("apm"), "install scripts/install-apm-ci.sh first"
    with tempfile.TemporaryDirectory(prefix="apm-resolver-refresh-") as temporary:
        project = Path(temporary)
        for name in ("apm.yml", "apm.lock.yaml", "apm-policy.yml"):
            shutil.copy2(PROJECT / name, project / name)
        manifest = (project / "apm.yml").read_bytes()
        locked = (project / "apm.lock.yaml").read_bytes()

        assert run(project, "lock", "--update").returncode == 0
        assert (project / "apm.yml").read_bytes() == manifest
        assert (project / "apm.lock.yaml").read_bytes() == locked
        check_lock(project, CURRENT_SHA)

        # This simulates a reviewed Renovate manifest change using real releases,
        # rather than allowing maintenance to independently advance a SHA pin.
        previous_manifest = manifest.decode().replace(CURRENT_SHA, PREVIOUS_SHA)
        previous_manifest = previous_manifest.replace("# v1.2.3", "# v1.2.2")
        (project / "apm.yml").write_text(previous_manifest)
        assert run(project, "lock").returncode == 0
        assert (project / "apm.yml").read_text() == previous_manifest
        check_lock(project, PREVIOUS_SHA)
        previous_lock = (project / "apm.lock.yaml").read_bytes()
        assert run(project, "lock", "--update").returncode == 0
        assert (project / "apm.lock.yaml").read_bytes() == previous_lock
        check_lock(project, PREVIOUS_SHA)

        (project / "apm.yml").write_bytes(manifest)
        assert run(project, "lock").returncode == 0
        assert (project / "apm.yml").read_bytes() == manifest
        assert (project / "apm.lock.yaml").read_bytes() == locked
        check_lock(project, CURRENT_SHA)
        assert run(project, "deps", "clean", "--yes").returncode == 0
        assert not (project / "apm_modules").exists()
    print("OK: immutable maintenance and real-release round trip preserve resolver-only state")


if __name__ == "__main__":
    main()
