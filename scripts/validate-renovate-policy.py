#!/usr/bin/env python3
"""Validate the repository's intentionally narrow hosted Renovate policy."""

from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "renovate.json"


def validate_config(config: Any) -> list[str]:
    errors: list[str] = []
    if not isinstance(config, dict):
        return ["renovate.json must contain a JSON object"]

    extends = config.get("extends")
    if not isinstance(extends, list) or "config:recommended" not in extends:
        errors.append("extends must include 'config:recommended'")

    managers = config.get("enabledManagers")
    if managers != ["apm"]:
        errors.append("enabledManagers must be exactly ['apm']")

    if config.get("dependencyDashboard") is not True:
        errors.append("dependencyDashboard must be true")

    if config.get("pinDigests") is not True:
        errors.append("pinDigests must be true")

    lock_maintenance = config.get("lockFileMaintenance")
    if not isinstance(lock_maintenance, dict) or lock_maintenance.get("enabled") is not False:
        errors.append("lockFileMaintenance.enabled must be false")

    if config.get("automerge") is True:
        errors.append("top-level automerge must not be true")

    package_rules = config.get("packageRules")
    if not isinstance(package_rules, list):
        errors.append("packageRules must be a list")
        package_rules = []

    guarded_apm_rule = False
    for index, rule in enumerate(package_rules):
        if not isinstance(rule, dict):
            errors.append(f"packageRules[{index}] must be an object")
            continue

        match_managers = rule.get("matchManagers")
        if not isinstance(match_managers, list) or "apm" not in match_managers:
            continue

        if rule.get("automerge") is True:
            errors.append(f"packageRules[{index}] enables automerge for APM dependencies")
        if rule.get("automerge") is False:
            guarded_apm_rule = True

    if not guarded_apm_rule:
        errors.append("at least one APM package rule must explicitly set automerge to false")

    return errors


def load_config(path: Path = CONFIG_PATH) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing {path.relative_to(ROOT)}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON in {path.relative_to(ROOT)}: {exc}") from exc


def main() -> None:
    try:
        config = load_config()
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc

    errors = validate_config(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        raise SystemExit(1)

    print("OK: Renovate policy is APM-only, review-gated, digest-pinned, and dashboard-enabled")


if __name__ == "__main__":
    main()
