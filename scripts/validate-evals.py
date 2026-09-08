#!/usr/bin/env python3
"""Validate catalog-owned Waza behavioral evaluation suites without model credentials."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
SKILLS = ROOT / "skills"
PLUGINS = ROOT / "plugins"
EXPECTED_SCHEMA = "1.2"


def load_yaml(path: Path) -> dict:
    if not path.is_file():
        raise ValueError(f"missing {path.relative_to(ROOT)}")
    if path.is_symlink():
        raise ValueError(f"symlink not allowed: {path.relative_to(ROOT)}")
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ValueError(f"{path.relative_to(ROOT)}: invalid YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path.relative_to(ROOT)}: expected a YAML mapping")
    return data


def sync_strategy(metadata: dict) -> tuple[str, str]:
    sync = metadata.get("sync")
    if not isinstance(sync, dict):
        return "manual", ""
    return str(sync.get("strategy", "manual")), str(sync.get("authoritative", ""))


def resolve_skill_dir(skill_name: str) -> Path:
    """Resolve one canonical skill source without creating an eval-only copy.

    A behavioral suite may target either a root catalog skill or a skill embedded
    in a capability Agent Plugin. The name must resolve uniquely across both
    namespaces so a new duplicate cannot silently redirect behavioral evidence.
    """

    candidates: list[Path] = []
    catalog = SKILLS / skill_name
    if (catalog / "SKILL.md").is_file():
        candidates.append(catalog)

    if PLUGINS.is_dir():
        for candidate in sorted(PLUGINS.glob(f"*/skills/{skill_name}")):
            if (candidate / "SKILL.md").is_file():
                candidates.append(candidate)

    if not candidates:
        raise ValueError(f"no canonical SKILL.md found for eval skill {skill_name!r}")
    if len(candidates) != 1:
        paths = ", ".join(path.relative_to(ROOT).as_posix() for path in candidates)
        raise ValueError(
            f"eval skill {skill_name!r} is ambiguous across canonical sources: {paths}"
        )
    return candidates[0]


def validate_plugin_skill(skill_dir: Path) -> None:
    """Require embedded eval targets to belong to a real capability package."""

    try:
        relative = skill_dir.relative_to(PLUGINS)
    except ValueError as exc:
        raise ValueError(f"{skill_dir.relative_to(ROOT)}: invalid capability skill path") from exc
    if len(relative.parts) != 3 or relative.parts[1] != "skills":
        raise ValueError(
            f"{skill_dir.relative_to(ROOT)}: capability skill must live at "
            "plugins/<plugin>/skills/<skill>"
        )
    plugin_root = PLUGINS / relative.parts[0]
    for required in ("plugin.json", "distribution.config.json"):
        if not (plugin_root / required).is_file():
            raise ValueError(
                f"{skill_dir.relative_to(ROOT)}: owning capability plugin is missing {required}"
            )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--resolve-skill-dir",
        metavar="NAME",
        help="Print the unique canonical skill directory for a suite name and exit.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    if args.resolve_skill_dir:
        try:
            resolved = resolve_skill_dir(args.resolve_skill_dir)
        except ValueError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            raise SystemExit(1)
        print(resolved.relative_to(ROOT).as_posix())
        return

    errors: list[str] = []
    if not EVALS.is_dir():
        errors.append("evals/: directory is missing")
    else:
        for path in EVALS.rglob("*"):
            if path.is_symlink():
                errors.append(f"{path.relative_to(ROOT)}: symlinks are forbidden in eval suites")

    suites = sorted(path for path in EVALS.glob("*/eval.yaml") if path.is_file())
    if len(suites) < 4:
        errors.append(f"evals/: expected at least 4 representative suites, found {len(suites)}")

    covered: list[str] = []
    for eval_path in suites:
        suite_dir = eval_path.parent
        skill_name = suite_dir.name

        try:
            spec = load_yaml(eval_path)
            skill_dir = resolve_skill_dir(skill_name)
        except ValueError as exc:
            errors.append(str(exc))
            continue

        skill_path = skill_dir / "SKILL.md"
        metadata: dict | None = None
        metadata_path = skill_dir / "metadata.yaml"
        if skill_dir.parent == SKILLS:
            try:
                metadata = load_yaml(metadata_path)
            except ValueError as exc:
                errors.append(str(exc))
                continue
        else:
            try:
                validate_plugin_skill(skill_dir)
            except ValueError as exc:
                errors.append(str(exc))
                continue

        if spec.get("skill") != skill_name:
            errors.append(f"{eval_path.relative_to(ROOT)}: skill must equal {skill_name!r}")
        if spec.get("schemaVersion") != EXPECTED_SCHEMA:
            errors.append(f"{eval_path.relative_to(ROOT)}: schemaVersion must be {EXPECTED_SCHEMA!r}")
        if not isinstance(spec.get("name"), str) or not spec["name"].strip():
            errors.append(f"{eval_path.relative_to(ROOT)}: name is required")
        if not isinstance(spec.get("version"), str) or not spec["version"].strip():
            errors.append(f"{eval_path.relative_to(ROOT)}: version is required")
        if spec.get("tasks") != ["tasks/*.yaml"]:
            errors.append(f"{eval_path.relative_to(ROOT)}: tasks must be exactly ['tasks/*.yaml']")
        config = spec.get("config")
        if not isinstance(config, dict) or config.get("executor") != "copilot-sdk":
            errors.append(f"{eval_path.relative_to(ROOT)}: config.executor must be 'copilot-sdk'")
        if not skill_path.is_file():
            errors.append(f"{skill_path.relative_to(ROOT)}: covered skill is missing")

        if metadata is not None:
            if metadata.get("name") != skill_name:
                errors.append(
                    f"{metadata_path.relative_to(ROOT)}: metadata name must match {skill_name!r}"
                )
            strategy, authority = sync_strategy(metadata)
            if strategy == "download" and authority == "upstream":
                try:
                    suite_dir.relative_to(skill_dir)
                except ValueError:
                    pass
                else:
                    errors.append(
                        f"{suite_dir.relative_to(ROOT)}: upstream-authoritative evals must live "
                        "outside the mirrored skill payload"
                    )

        task_paths = sorted((suite_dir / "tasks").glob("*.yaml"))
        if len(task_paths) < 2:
            errors.append(f"{suite_dir.relative_to(ROOT)}: expected at least two task files")
            continue

        ids: set[str] = set()
        positives = 0
        negatives = 0
        behavior_graders = 0
        expected_skill_path = skill_path.relative_to(ROOT).as_posix()

        for task_path in task_paths:
            try:
                task = load_yaml(task_path)
            except ValueError as exc:
                errors.append(str(exc))
                continue

            task_id = task.get("id")
            if not isinstance(task_id, str) or not task_id.strip():
                errors.append(f"{task_path.relative_to(ROOT)}: id is required")
                continue
            if task_id in ids:
                errors.append(f"{suite_dir.relative_to(ROOT)}: duplicate task id {task_id!r}")
            ids.add(task_id)

            inputs = task.get("inputs")
            prompt = inputs.get("prompt") if isinstance(inputs, dict) else None
            if not isinstance(prompt, str) or not prompt.strip():
                errors.append(f"{task_path.relative_to(ROOT)}: inputs.prompt is required")

            expected = task.get("expected")
            if not isinstance(expected, dict):
                errors.append(f"{task_path.relative_to(ROOT)}: expected mapping is required")
                continue
            should_trigger = expected.get("should_trigger")
            if not isinstance(should_trigger, bool):
                errors.append(f"{task_path.relative_to(ROOT)}: expected.should_trigger must be boolean")
                continue
            positives += int(should_trigger)
            negatives += int(not should_trigger)

            graders = expected.get("graders")
            if not isinstance(graders, list) or not graders:
                errors.append(f"{task_path.relative_to(ROOT)}: at least one grader is required")
                continue

            trigger_graders = [
                grader for grader in graders
                if isinstance(grader, dict) and grader.get("type") == "trigger"
            ]
            if len(trigger_graders) != 1:
                errors.append(f"{task_path.relative_to(ROOT)}: exactly one trigger grader is required")
            else:
                trigger_config = trigger_graders[0].get("config")
                if not isinstance(trigger_config, dict):
                    errors.append(f"{task_path.relative_to(ROOT)}: trigger grader config is required")
                else:
                    expected_mode = "positive" if should_trigger else "negative"
                    if trigger_config.get("mode") != expected_mode:
                        errors.append(
                            f"{task_path.relative_to(ROOT)}: trigger mode must be {expected_mode!r}"
                        )
                    if trigger_config.get("skill_path") != expected_skill_path:
                        errors.append(
                            f"{task_path.relative_to(ROOT)}: trigger skill_path must be "
                            f"{expected_skill_path!r}"
                        )

            non_trigger = [
                grader for grader in graders
                if isinstance(grader, dict) and grader.get("type") != "trigger"
            ]
            behavior_graders += len(non_trigger)
            if should_trigger and not non_trigger:
                errors.append(
                    f"{task_path.relative_to(ROOT)}: positive tasks need a behavioral grader "
                    "in addition to trigger accuracy"
                )

        if positives == 0:
            errors.append(f"{suite_dir.relative_to(ROOT)}: needs at least one positive case")
        if negatives == 0:
            errors.append(f"{suite_dir.relative_to(ROOT)}: needs at least one negative/boundary case")
        if behavior_graders == 0:
            errors.append(f"{suite_dir.relative_to(ROOT)}: needs at least one behavioral grader")
        covered.append(skill_name)

    if errors:
        for message in errors:
            print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(1)

    print(f"OK: {len(covered)} catalog-owned Waza suites validated: " + ", ".join(covered))


if __name__ == "__main__":
    main()
