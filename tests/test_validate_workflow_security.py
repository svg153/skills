from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "validate-workflow-security.py"
SPEC = importlib.util.spec_from_file_location("validate_workflow_security", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
validate_workflow_security = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_workflow_security)


def inside_git_work_tree(path: Path) -> bool:
    if shutil.which("git") is None:
        return False
    result = subprocess.run(
        ["git", "-C", str(path), "rev-parse", "--is-inside-work-tree"],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.returncode == 0 and result.stdout.strip() == "true"


def completed(stdout: str, returncode: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=["git"], returncode=returncode, stdout=stdout, stderr="")


class ExecutableBitTests(unittest.TestCase):
    """The committed Git mode is authoritative; NTFS cannot represent POSIX exec bits."""

    def test_index_mode_100755_wins_over_filesystem_bits(self) -> None:
        target = ROOT / "README.md"
        with mock.patch.object(
            validate_workflow_security.subprocess,
            "run",
            return_value=completed(f"100755 {'0' * 40} 0\tREADME.md\n"),
        ):
            self.assertEqual(validate_workflow_security.git_index_mode(target), "100755")
            self.assertTrue(validate_workflow_security.is_executable(target))

    def test_index_mode_100644_wins_over_filesystem_bits(self) -> None:
        target = ROOT / "scripts" / "sync-upstreams.sh"
        with mock.patch.object(
            validate_workflow_security.subprocess,
            "run",
            return_value=completed(f"100644 {'0' * 40} 0\tscripts/sync-upstreams.sh\n"),
        ):
            self.assertFalse(validate_workflow_security.is_executable(target))

    def test_falls_back_to_filesystem_mode_when_git_is_unavailable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            script = root / "run.sh"
            script.write_text("#!/usr/bin/env bash\n", encoding="utf-8", newline="\n")
            for side_effect in (OSError("git not found"), None):
                kwargs = {"side_effect": side_effect} if side_effect else {"return_value": completed("", 128)}
                with mock.patch.object(validate_workflow_security.subprocess, "run", **kwargs):
                    self.assertIsNone(validate_workflow_security.git_index_mode(script, root))
                    if os.name == "nt":
                        continue
                    os.chmod(script, 0o755)
                    self.assertTrue(validate_workflow_security.is_executable(script, root))
                    os.chmod(script, 0o644)
                    self.assertFalse(validate_workflow_security.is_executable(script, root))

    @unittest.skipUnless(inside_git_work_tree(ROOT), "requires a Git checkout")
    def test_real_index_modes_of_tracked_files(self) -> None:
        executable = ROOT / "scripts" / "sync-upstreams.sh"
        regular = ROOT / "README.md"
        self.assertEqual(validate_workflow_security.git_index_mode(executable), "100755")
        self.assertTrue(validate_workflow_security.is_executable(executable))
        self.assertEqual(validate_workflow_security.git_index_mode(regular), "100644")
        self.assertFalse(validate_workflow_security.is_executable(regular))

    @unittest.skipUnless(inside_git_work_tree(ROOT), "requires a Git checkout")
    def test_repository_workflows_pass_baseline(self) -> None:
        errors: list[str] = []
        for path in sorted(validate_workflow_security.WORKFLOWS.glob("*.yml")):
            errors.extend(validate_workflow_security.validate(path))
        self.assertEqual(errors, [])


if __name__ == "__main__":
    unittest.main()
