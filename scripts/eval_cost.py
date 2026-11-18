#!/usr/bin/env python3
"""Cost controls for the trusted, model-backed Waza evaluations.

Subcommands (all stdlib only, so they run on a bare GitHub-hosted runner):

  select   decide which suites a run must evaluate (see docs/evals.md)
  summary  render per-suite premium requests as Markdown for $GITHUB_STEP_SUMMARY

The decision logic lives in pure functions (`pick_baseline`, `suite_inputs`,
`select_suites`, `premium_requests`) so it is unit-tested without git or gh.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Models a dispatcher may select. Keep in sync with ALLOWED_MODELS in
# scripts/run-behavioral-suites.sh and the `model` choices in the workflow
# (tests/test_eval_cost.py enforces this). "default" means: no override, use each
# suite's config.model (or the Copilot default when the suite sets none).
ALLOWED_MODELS = ("claude-haiku-4.5", "claude-sonnet-4.6")

# Changing any of these invalidates every suite's last result. scripts/eval_cost.py
# is intentionally absent: it only decides what to run and is unit-tested, so editing
# it must not trigger a full paid run.
SHARED_PATHS = (
    "scripts/run-behavioral-suites.sh",
    "scripts/install-waza-ci.sh",
    ".github/workflows/eval-behavioral.yml",
)

BASELINE_ARTIFACT = "waza-eval-baseline"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
SUITE_RE = re.compile(r"^[a-z0-9-]+$")


@dataclass(frozen=True)
class Selection:
    run: bool  # False: execute nothing
    suites: tuple[str, ...]  # empty with run=True means "every suite"
    reason: str


def pick_baseline(artifacts_response: dict, default_branch: str) -> str | None:
    """Head SHA of the newest unexpired baseline marker from the default branch.

    `artifacts_response` is the JSON of `GET /repos/{r}/actions/artifacts?name=...`
    (newest first). A marker is only uploaded by a run that executed suites and
    finished successfully, so its existence is the "last successful model-backed run".
    """
    artifacts = artifacts_response.get("artifacts") if isinstance(artifacts_response, dict) else None
    for art in artifacts or []:
        if not isinstance(art, dict) or art.get("name") != BASELINE_ARTIFACT or art.get("expired"):
            continue
        run = art.get("workflow_run") or {}
        sha = run.get("head_sha")
        if run.get("head_branch") == default_branch and isinstance(sha, str) and SHA_RE.match(sha):
            return sha
    return None


def skill_name_from_spec(text: str) -> str | None:
    match = re.search(r"^skill:\s*['\"]?([A-Za-z0-9._-]+)['\"]?\s*(?:#.*)?$", text, re.MULTILINE)
    return match.group(1) if match else None


def skill_dirs(root: Path, skill: str) -> list[str]:
    """skills/<skill>/ and plugins/*/skills/<skill>/ (repo-relative, trailing slash)."""
    found = []
    if (root / "skills" / skill / "SKILL.md").is_file():
        found.append(f"skills/{skill}/")
    plugins = root / "plugins"
    if plugins.is_dir():
        for cand in sorted(plugins.glob(f"*/skills/{skill}/SKILL.md")):
            found.append(cand.parent.relative_to(root).as_posix() + "/")
    return found


def suite_inputs(root: Path) -> dict[str, tuple[str, ...]]:
    """suite name -> repo-relative path prefixes that are inputs of that suite."""
    inputs: dict[str, tuple[str, ...]] = {}
    for spec in sorted((root / "evals").glob("*/eval.yaml")):
        suite = spec.parent.name
        prefixes = [f"evals/{suite}/"]
        skill = skill_name_from_spec(spec.read_text(encoding="utf-8"))
        # A missing/unparseable skill field cannot hide changes: the suite then
        # depends on evals/<suite>/ only, and validate-evals.py rejects it anyway.
        if skill:
            prefixes += skill_dirs(root, skill)
        inputs[suite] = tuple(prefixes)
    return inputs


def select_suites(
    event: str,
    changed: list[str] | None,
    inputs: dict[str, tuple[str, ...]],
    requested_suite: str = "",
    force_all: bool = False,
) -> Selection:
    """Pure selection policy.

    `changed` is the file list between baseline and HEAD, or None when there is no
    usable baseline.
    """
    if event != "schedule":
        if force_all or not requested_suite:
            return Selection(True, (), "manual dispatch: every suite" + (" (force_all)" if force_all else ""))
        if requested_suite not in inputs:
            raise ValueError(f"unknown suite {requested_suite!r}")
        return Selection(True, (requested_suite,), f"manual dispatch: suite {requested_suite}")

    if changed is None:
        return Selection(
            False,
            (),
            "no baseline (no unexpired successful model-backed run found): nothing evaluated; "
            "dispatch one full run to create it",
        )
    shared = sorted(p for p in changed if p in SHARED_PATHS)
    if shared:
        return Selection(True, (), "shared eval machinery changed (" + ", ".join(shared) + "): every suite")
    hit = tuple(
        suite
        for suite, prefixes in sorted(inputs.items())
        if any(p.startswith(prefix) for p in changed for prefix in prefixes)
    )
    if not hit:
        return Selection(False, (), "no suite inputs changed since the last model-backed run")
    return Selection(True, hit, f"{len(hit)} changed suite(s)")


def _num(value) -> float | None:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def premium_requests(results: object) -> float | None:
    """Premium requests of one Waza results.json, or None when not reported.

    Waza 0.38.6 writes summary.usage.premium_requests; fall back to summing
    per-run usage if only that is present. Zero is treated as "not reported"
    because Waza omits the field when the SDK sent no count.
    """
    if not isinstance(results, dict):
        return None
    summary = results.get("summary")
    usage = summary.get("usage") if isinstance(summary, dict) else None
    total = _num(usage.get("premium_requests")) if isinstance(usage, dict) else None
    if total:
        return total
    total = 0.0
    for task in results.get("tasks") or []:
        for run in (task.get("runs") or []) if isinstance(task, dict) else []:
            run_usage = run.get("usage") if isinstance(run, dict) else None
            total += (_num(run_usage.get("premium_requests")) or 0.0) if isinstance(run_usage, dict) else 0.0
    return total or None


def render_summary(results_root: Path, model_override: str = "") -> str:
    lines = ["## Premium requests per suite", "", "| Suite | Model | Premium requests | Tasks |", "| --- | --- | ---: | ---: |"]
    grand, missing, rows = 0.0, 0, 0
    for path in sorted(results_root.glob("*/results.json")):
        rows += 1
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            data = None
        cfg = data.get("config") if isinstance(data, dict) else None
        model = (cfg.get("model_id") if isinstance(cfg, dict) else "") or model_override or "default"
        tasks = len(data.get("tasks") or []) if isinstance(data, dict) else 0
        prem = premium_requests(data)
        if prem is None:
            missing += 1
            cell = "not reported"
        else:
            grand += prem
            cell = f"{prem:g}"
        lines.append(f"| {path.parent.name} | {model} | {cell} | {tasks} |")
    if not rows:
        return "## Premium requests per suite\n\nNo results.json was produced, so no usage is available.\n"
    lines.append(f"| **Total** | | **{grand:g}**{' (partial)' if missing else ''} | |")
    if missing:
        lines += ["", f"{missing} suite(s) reported no premium-request usage (missing or unparsable results.json); the total is a lower bound."]
    return "\n".join(lines) + "\n"


def _changed_files(base: str, root: Path) -> list[str] | None:
    if not SHA_RE.match(base):
        return None
    proc = subprocess.run(
        ["git", "-C", str(root), "diff", "--name-only", "-z", f"{base}..HEAD"],
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:  # baseline commit unreachable (history rewritten)
        return None
    return [p for p in proc.stdout.decode("utf-8", "replace").split("\0") if p]


def _cmd_select(args: argparse.Namespace) -> int:
    if args.suite and not SUITE_RE.match(args.suite):
        print("::error::invalid suite name (allowed: [a-z0-9-]+)", file=sys.stderr)
        return 2
    root = Path(args.root).resolve()
    inputs = suite_inputs(root)
    changed = None
    baseline = ""
    if args.event == "schedule":
        artifacts = {}
        if args.artifacts_json and Path(args.artifacts_json).is_file():
            try:
                artifacts = json.loads(Path(args.artifacts_json).read_text(encoding="utf-8"))
            except ValueError:
                artifacts = {}
        baseline = pick_baseline(artifacts, args.default_branch) or ""
        changed = _changed_files(baseline, root) if baseline else None
    try:
        sel = select_suites(args.event, changed, inputs, args.suite, args.force_all == "true")
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2
    print(f"run={'true' if sel.run else 'false'}")
    print(f"suites={','.join(sel.suites)}")
    print(f"baseline={baseline}")
    print(f"reason={sel.reason}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sel = sub.add_parser("select")
    sel.add_argument("--event", required=True)
    sel.add_argument("--suite", default="")
    sel.add_argument("--force-all", default="false")
    sel.add_argument("--default-branch", default="main")
    sel.add_argument("--artifacts-json", default="")
    sel.add_argument("--root", default=str(ROOT))
    summ = sub.add_parser("summary")
    summ.add_argument("results_root")
    summ.add_argument("--model", default="")
    args = parser.parse_args(argv)
    if args.cmd == "select":
        return _cmd_select(args)
    sys.stdout.write(render_summary(Path(args.results_root), args.model))
    return 0


if __name__ == "__main__":
    sys.exit(main())
