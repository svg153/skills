#!/usr/bin/env python3
"""Regression tests for the repository Renovate policy contract."""

from __future__ import annotations

import copy
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "scripts" / "validate-renovate-policy.py"
SPEC = importlib.util.spec_from_file_location("validate_renovate_policy", MODULE_PATH)
assert SPEC is not None and SPEC.loader is not None
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RenovatePolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = MODULE.load_config()

    def assert_invalid(self, mutate, expected_fragment: str) -> None:
        candidate = copy.deepcopy(self.config)
        mutate(candidate)
        errors = MODULE.validate_config(candidate)
        self.assertTrue(
            any(expected_fragment in error for error in errors),
            msg=f"expected {expected_fragment!r} in {errors!r}",
        )

    def test_repository_config_is_valid(self) -> None:
        self.assertEqual([], MODULE.validate_config(self.config))

    def test_rejects_extra_manager(self) -> None:
        self.assert_invalid(
            lambda config: config.__setitem__("enabledManagers", ["apm", "github-actions"]),
            "enabledManagers must be exactly",
        )

    def test_rejects_disabled_dashboard(self) -> None:
        self.assert_invalid(
            lambda config: config.__setitem__("dependencyDashboard", False),
            "dependencyDashboard must be true",
        )

    def test_rejects_unpinned_dependency_updates(self) -> None:
        self.assert_invalid(
            lambda config: config.__setitem__("pinDigests", False),
            "pinDigests must be true",
        )

    def test_rejects_native_lock_file_maintenance(self) -> None:
        self.assert_invalid(
            lambda config: config.__setitem__("lockFileMaintenance", {"enabled": True}),
            "lockFileMaintenance.enabled must be false",
        )

    def test_rejects_top_level_automerge(self) -> None:
        self.assert_invalid(
            lambda config: config.__setitem__("automerge", True),
            "top-level automerge",
        )

    def test_rejects_apm_automerge_rule(self) -> None:
        def mutate(config):
            config["packageRules"][0]["automerge"] = True

        candidate = copy.deepcopy(self.config)
        mutate(candidate)
        errors = MODULE.validate_config(candidate)
        self.assertIn("packageRules[0] enables automerge for APM dependencies", errors)
        self.assertIn("at least one APM package rule must explicitly set automerge to false", errors)

    def test_requires_explicit_apm_no_automerge_rule(self) -> None:
        def mutate(config):
            config["packageRules"] = []

        self.assert_invalid(mutate, "explicitly set automerge to false")


if __name__ == "__main__":
    unittest.main()
