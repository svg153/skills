#!/usr/bin/env python3
"""Validate parity between the Waza and Vally evaluation research prototypes."""

from __future__ import annotations

from pathlib import Path
import sys

import yaml

ROOT = Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research" / "evals"
SCENARIOS_PATH = RESEARCH / "scenarios.yaml"
WAZA_ROOT = RESEARCH / "waza" / "github-build-or-reuse"
VALLY_PATH = RESEARCH / "vally" / "github-build-or-reuse" / "eval.yaml"


def fail(message: str) -> "NoReturn":
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    if not path.is_file():
        fail(f"missing {path.relative_to(ROOT)}")
    if path.is_symlink():
        fail(f"symlink not allowed: {path.relative_to(ROOT)}")
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        fail(f"{path.relative_to(ROOT)}: invalid YAML: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)}: expected mapping")
    return value


def main() -> None:
    contract = load(SCENARIOS_PATH)
    if contract.get("skill") != "github-build-or-reuse":
        fail("scenarios.yaml must target github-build-or-reuse")
    scenarios = contract.get("scenarios")
    if not isinstance(scenarios, list) or not scenarios:
        fail("scenarios.yaml requires a non-empty scenarios list")

    expected: dict[str, dict] = {}
    for scenario in scenarios:
        if not isinstance(scenario, dict):
            fail("each scenario must be a mapping")
        scenario_id = scenario.get("id")
        prompt = scenario.get("prompt")
        trigger = scenario.get("expected_trigger")
        expectation = scenario.get("expectation")
        if not isinstance(scenario_id, str) or not scenario_id:
            fail("every scenario requires a non-empty id")
        if scenario_id in expected:
            fail(f"duplicate scenario id: {scenario_id}")
        if not isinstance(prompt, str) or not prompt.strip():
            fail(f"{scenario_id}: prompt is required")
        if not isinstance(trigger, bool):
            fail(f"{scenario_id}: expected_trigger must be boolean")
        if not isinstance(expectation, str) or not expectation.strip():
            fail(f"{scenario_id}: expectation is required")
        expected[scenario_id] = scenario

    waza_eval = load(WAZA_ROOT / "eval.yaml")
    if waza_eval.get("skill") != contract["skill"]:
        fail("Waza prototype targets a different skill")
    tasks_declared = waza_eval.get("tasks")
    if tasks_declared != ["tasks/*.yaml"]:
        fail("Waza prototype must use tasks/*.yaml")

    waza: dict[str, dict] = {}
    for task_path in sorted((WAZA_ROOT / "tasks").glob("*.yaml")):
        task = load(task_path)
        task_id = task.get("id")
        if not isinstance(task_id, str) or not task_id:
            fail(f"{task_path.relative_to(ROOT)}: id is required")
        if task_id in waza:
            fail(f"duplicate Waza task id: {task_id}")
        inputs = task.get("inputs")
        expected_block = task.get("expected")
        if not isinstance(inputs, dict) or not isinstance(expected_block, dict):
            fail(f"{task_id}: Waza task requires inputs and expected mappings")
        if not isinstance(expected_block.get("graders"), list) or not expected_block["graders"]:
            fail(f"{task_id}: Waza task needs at least one grader")
        waza[task_id] = {
            "prompt": str(inputs.get("prompt", "")).strip(),
            "trigger": expected_block.get("should_trigger"),
        }

    vally_eval = load(VALLY_PATH)
    stimuli = vally_eval.get("stimuli")
    if not isinstance(stimuli, list) or not stimuli:
        fail("Vally prototype requires stimuli")
    vally: dict[str, dict] = {}
    for stimulus in stimuli:
        if not isinstance(stimulus, dict):
            fail("Vally stimuli must be mappings")
        name = stimulus.get("name")
        if not isinstance(name, str) or not name:
            fail("Vally stimulus name is required")
        if name in vally:
            fail(f"duplicate Vally stimulus name: {name}")
        if not isinstance(stimulus.get("graders"), list) or not stimulus["graders"]:
            fail(f"{name}: Vally stimulus needs at least one grader")
        if not isinstance(stimulus.get("rubric"), list) or not stimulus["rubric"]:
            fail(f"{name}: Vally stimulus needs a rubric")
        vally[name] = {"prompt": str(stimulus.get("prompt", "")).strip()}

    expected_ids = set(expected)
    if set(waza) != expected_ids:
        fail(f"Waza scenario IDs differ: expected {sorted(expected_ids)}, got {sorted(waza)}")
    if set(vally) != expected_ids:
        fail(f"Vally scenario IDs differ: expected {sorted(expected_ids)}, got {sorted(vally)}")

    for scenario_id, scenario in expected.items():
        prompt = str(scenario["prompt"]).strip()
        if waza[scenario_id]["prompt"] != prompt:
            fail(f"{scenario_id}: Waza prompt differs from common contract")
        if vally[scenario_id]["prompt"] != prompt:
            fail(f"{scenario_id}: Vally prompt differs from common contract")
        if waza[scenario_id]["trigger"] is not scenario["expected_trigger"]:
            fail(f"{scenario_id}: Waza should_trigger differs from common contract")

    print(f"OK: {len(expected)} equivalent scenarios represented in Waza and Vally prototypes")


if __name__ == "__main__":
    main()
