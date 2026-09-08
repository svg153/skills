#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "complete-apm-renovate-update.py"

spec = importlib.util.spec_from_file_location("apm_completion", MODULE_PATH)
assert spec and spec.loader
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class CompletionScopeTests(unittest.TestCase):
    def test_allows_only_lock_mirror_and_derived_distribution(self) -> None:
        skill = "github-build-or-reuse"
        allowed = [
            "dependencies/external-skills/apm.lock.yaml",
            "skills/github-build-or-reuse/SKILL.md",
            "skills/github-build-or-reuse/references/example.md",
            "plugin.json",
            "marketplace.json",
            "gemini-extension.json",
            ".agents/plugins/marketplace.json",
            ".codex-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            ".cursor-plugin/marketplace.json",
        ]
        for path in allowed:
            with self.subTest(path=path):
                self.assertTrue(module.allowed_generated_path(path, skill))

    def test_refuses_catalog_metadata_and_unrelated_repository_files(self) -> None:
        skill = "github-build-or-reuse"
        denied = [
            "skills/github-build-or-reuse/metadata.yaml",
            "skills/another-skill/SKILL.md",
            "dependencies/external-skills/apm.yml",
            ".github/workflows/validate.yml",
            "scripts/materialize-apm-mirror.py",
            "README.md",
        ]
        for path in denied:
            with self.subTest(path=path):
                self.assertFalse(module.allowed_generated_path(path, skill))


class ResolverOnlyLockTests(unittest.TestCase):
    def write_lock(self, text: str) -> Path:
        temporary = tempfile.NamedTemporaryFile("w", suffix=".yaml", delete=False)
        with temporary:
            temporary.write(text)
        self.addCleanup(Path(temporary.name).unlink, missing_ok=True)
        return Path(temporary.name)

    def test_accepts_dependency_lock_without_runtime_deployments(self) -> None:
        path = self.write_lock(
            """lockfile_version: '1'\ndependencies:\n  - repo_url: example/repo\n    resolved_commit: 0123456789012345678901234567890123456789\ndeployments: []\n"""
        )
        module.validate_resolver_only_lock(path)

    def test_rejects_runtime_deployment_ownership(self) -> None:
        path = self.write_lock(
            """lockfile_version: '1'\ndependencies:\n  - repo_url: example/repo\ndeployments:\n  - kind: project-relative\n    target: claude\n    value: .claude/skills/example\n"""
        )
        with self.assertRaises(SystemExit) as raised:
            module.validate_resolver_only_lock(path)
        self.assertIn("second runtime source of truth", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
