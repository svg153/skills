#!/usr/bin/env python3
"""Cost controls for the model-backed Waza evals (stdlib only, no PyYAML).

Subcommands:
  select        decide which suites a run evaluates (changed-suite policy)
  check-model   exit 0 when a model id is in the pricing allowlist
  credits-total print estimated AI credits spent so far under a results root
  summary       print a Markdown cost table for $GITHUB_STEP_SUMMARY

Selection policy (see docs/evals.md):
  * workflow_dispatch runs every suite, or the single `--suite`;
  * `--force-all` always runs every suite;
  * schedule runs only suites whose inputs changed since the baseline (head SHA of
    the last successful run that evaluated full coverage). Inputs are
    evals/<suite>/**, the targeted skill directory and the shared eval machinery;
    a shared-machinery change runs every suite. Without a baseline nothing runs.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRICING = Path(__file__).resolve().with_name("eval-model-pricing.json")
SUITE_RE = re.compile(r"^[a-z0-9-]+$")
MODEL_RE = re.compile(r"^[a-z0-9][a-z0-9.-]*$")
SKILL_FIELD_RE = re.compile(r"^skill:\s*['\"]?([a-z0-9-]+)['\"]?\s*$", re.MULTILINE)

# Changing any of these can change every suite's result, so every suite runs.
SHARED_PATHS = (
    ".github/workflows/eval-behavioral.yml",
    "scripts/run-behavioral-suites.sh",
    "scripts/install-waza-ci.sh",
    "scripts/eval-suite-policy.py",
)


@dataclass
class Selection:
    suites: list[str]
    reason: str
    full_coverage: bool
    details: list[str] = field(default_factory=list)


def select_suites(
    event: str,
    suites: dict[str, str],
    changed: list[str] | None,
    suite_filter: str = "",
    force_all: bool = False,
    shared_paths: tuple[str, ...] = SHARED_PATHS,
) -> Selection:
    """Pure selection logic.

    suites maps suite name -> repository-relative skill directory (posix, no
    trailing slash, '' when unresolved). changed is the list of files changed
    since the baseline, or None when no baseline exists.
    """
    every = sorted(suites)
    if force_all:
        return Selection(every, "force_all requested: every suite runs", True)
    if event != "schedule":
        if suite_filter:
            if suite_filter not in suites:
                raise ValueError(f"unknown suite {suite_filter!r}")
            return Selection([suite_filter], f"manual run of suite {suite_filter}", False)
        return Selection(every, "manual run: every suite runs", True)

    if changed is None:
        return Selection(
            [],
            "no baseline (no successful full-coverage eval run recorded): scheduled run evaluates nothing. "
            "Dispatch the workflow manually (no suite, or force_all) to establish one.",
            False,
        )
    changed = [path.strip().replace("\\", "/") for path in changed if path.strip()]
    shared = sorted({path for path in changed if path in shared_paths})
    if shared:
        return Selection(every, "shared eval machinery changed: every suite runs", True, shared)

    selected: list[str] = []
    details: list[str] = []
    for name in every:
        prefixes = [f"evals/{name}/"]
        if suites[name]:
            prefixes.append(suites[name].rstrip("/") + "/")
        hits = [path for path in changed if any(path.startswith(prefix) for prefix in prefixes)]
        if hits:
            selected.append(name)
            details.append(f"{name}: {', '.join(hits[:3])}{' ...' if len(hits) > 3 else ''}")
    if not selected:
        return Selection([], "no suite inputs changed since the baseline: nothing to evaluate", True)
    return Selection(selected, f"{len(selected)} suite(s) with changed inputs", True, details)


def resolve_skill_dir(root: Path, skill: str) -> str:
    direct = root / "skills" / skill
    if (direct / "SKILL.md").is_file():
        return f"skills/{skill}"
    matches = sorted(p.parent for p in root.glob(f"plugins/*/skills/{skill}/SKILL.md"))
    if len(matches) == 1:
        return matches[0].relative_to(root).as_posix()
    return ""


def discover_suites(root: Path) -> dict[str, str]:
    suites: dict[str, str] = {}
    for spec in sorted(root.glob("evals/*/eval.yaml")):
        name = spec.parent.name
        match = SKILL_FIELD_RE.search(spec.read_text(encoding="utf-8"))
        suites[name] = resolve_skill_dir(root, match.group(1)) if match else ""
    return suites


# ---------------------------------------------------------------- cost estimate

TOKEN_KEYS = ("input_tokens", "cache_read_tokens", "cache_write_tokens", "output_tokens")
NANO_KEYS = ("total_nano_aiu", "totalNanoAiu")


def load_pricing(path: Path = PRICING) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _num(value) -> float:
    return float(value) if isinstance(value, (int, float)) and not isinstance(value, bool) else 0.0


def _nano(usage: dict) -> float | None:
    for key in NANO_KEYS:
        if isinstance(usage.get(key), (int, float)):
            return float(usage[key])
    return None


def extract_usage(results: dict) -> dict | None:
    """Return summary-level usage from a Waza results.json, or None when absent.

    Waza 0.38.6 writes summary.usage; older/partial outputs may only carry
    per-run usage, which is summed as a fallback.
    """
    summary = results.get("summary")
    usage = summary.get("usage") if isinstance(summary, dict) else None
    if isinstance(usage, dict) and usage:
        return usage
    total: dict = {key: 0.0 for key in TOKEN_KEYS}
    total["premium_requests"] = 0.0
    found = False
    for task in results.get("tasks") or []:
        for run in (task.get("runs") or []) if isinstance(task, dict) else []:
            if not isinstance(run, dict):
                continue
            run_usage = run.get("usage")
            if not isinstance(run_usage, dict):
                digest = run.get("session_digest")
                run_usage = digest.get("usage") if isinstance(digest, dict) else None
            if isinstance(run_usage, dict):
                found = True
                for key in (*TOKEN_KEYS, "premium_requests"):
                    total[key] += _num(run_usage.get(key))
    return total if found else None


def _token_cost_usd(tokens: dict, price: dict) -> float:
    cache_write = price.get("cache_write")
    if cache_write is None:
        cache_write = price["input"]
    return (
        _num(tokens.get("input_tokens")) * price["input"]
        + _num(tokens.get("cache_read_tokens")) * price["cached_input"]
        + _num(tokens.get("cache_write_tokens")) * cache_write
        + _num(tokens.get("output_tokens")) * price["output"]
    ) / 1_000_000


def estimate_credits(usage: dict, model: str, pricing: dict) -> tuple[float, str]:
    """Estimate AI credits for one suite. Returns (credits, source).

    SDK cost metrics (nano-AI units) are preferred when present. Otherwise
    tokens are priced per model_metrics entry (falling back to the requested
    model's price). input_tokens is billed in full at the input price; if the SDK
    already includes cache reads in input_tokens this overestimates, which is the
    safe direction for a budget guard.
    """
    nano = _nano(usage)
    if nano is not None:
        return nano / 1e9, "sdk-cost"
    credit_usd = float(pricing.get("credit_usd", 0.01))
    models = pricing["models"]
    fallback = models.get(model)
    metrics = usage.get("model_metrics")
    if isinstance(metrics, dict) and metrics:
        nanos = [_nano(m) for m in metrics.values() if isinstance(m, dict)]
        if nanos and all(n is not None for n in nanos):
            return sum(nanos) / 1e9, "sdk-cost"
        usd = 0.0
        unpriced = []
        for name, entry in metrics.items():
            if not isinstance(entry, dict):
                continue
            price = models.get(name) or fallback
            if price is None:
                unpriced.append(name)
                continue
            usd += _token_cost_usd(entry, price)
        if unpriced:
            return math.nan, f"no price for {', '.join(sorted(unpriced))}"
        return usd / credit_usd, "tokens x price table"
    if fallback is None:
        return math.nan, f"no price for {model or 'default model'}"
    return _token_cost_usd(usage, fallback) / credit_usd, "tokens x price table"


@dataclass
class SuiteCost:
    suite: str
    usage: dict | None
    credits: float
    source: str


def collect_costs(results_root: Path, model: str, pricing: dict) -> list[SuiteCost]:
    costs: list[SuiteCost] = []
    if not results_root.is_dir():
        return costs
    for suite_dir in sorted(p for p in results_root.iterdir() if p.is_dir()):
        results_path = suite_dir / "results.json"
        if not results_path.is_file():
            costs.append(SuiteCost(suite_dir.name, None, math.nan, "results.json missing"))
            continue
        try:
            results = json.loads(results_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            costs.append(SuiteCost(suite_dir.name, None, math.nan, f"unreadable results.json ({exc.__class__.__name__})"))
            continue
        usage = extract_usage(results) if isinstance(results, dict) else None
        if usage is None:
            costs.append(SuiteCost(suite_dir.name, None, math.nan, "usage missing in results.json"))
            continue
        credits, source = estimate_credits(usage, model, pricing)
        costs.append(SuiteCost(suite_dir.name, usage, credits, source))
    return costs


def total_credits(costs: list[SuiteCost]) -> float:
    return sum(c.credits for c in costs if not math.isnan(c.credits))


def _fmt_int(value) -> str:
    return f"{int(_num(value)):,}"


def render_summary(costs: list[SuiteCost], model: str, max_credits: float | None, pricing: dict,
                   budget_note: str = "") -> str:
    lines = ["## Eval cost (estimated AI credits)", ""]
    price = pricing["models"].get(model)
    lines.append(
        f"Model: `{model or 'spec default'}`"
        + (f" ({price['label']}: ${price['input']}/${price['cached_input']}/${price['output']} per 1M input/cached/output)" if price else "")
        + f". Prices: {pricing['source']} (retrieved {pricing['retrieved']}). 1 credit = ${pricing.get('credit_usd', 0.01)}."
    )
    lines.append("")
    if not costs:
        lines.append("No suite results were found, so no usage could be reported.")
        return "\n".join(lines) + "\n"
    lines.append("| Suite | Input | Cached input | Cache write | Output | Est. credits | Source | Legacy premium req. |")
    lines.append("|---|---:|---:|---:|---:|---:|---|---:|")
    for cost in costs:
        usage = cost.usage or {}
        credits = "n/a" if math.isnan(cost.credits) else f"{cost.credits:.1f}"
        if cost.usage is None:
            lines.append(f"| {cost.suite} | - | - | - | - | {credits} | {cost.source} | - |")
            continue
        lines.append(
            f"| {cost.suite} | {_fmt_int(usage.get('input_tokens'))} | {_fmt_int(usage.get('cache_read_tokens'))} | "
            f"{_fmt_int(usage.get('cache_write_tokens'))} | {_fmt_int(usage.get('output_tokens'))} | {credits} | "
            f"{cost.source} | {_num(usage.get('premium_requests')):.0f} |"
        )
    total = total_credits(costs)
    missing = [c.suite for c in costs if math.isnan(c.credits)]
    lines.append("")
    lines.append(f"**Estimated total: {total:.1f} credits (~${total * pricing.get('credit_usd', 0.01):.2f})**"
                 + (f" of a {max_credits:g}-credit budget." if max_credits is not None else "."))
    if missing:
        lines.append("")
        lines.append(f"Usage could not be estimated for: {', '.join(missing)} (the total excludes them).")
    lines.append("")
    lines.append("The legacy premium-request count printed by Waza is not a cost measure under token-based billing. "
                 "Estimates price `input_tokens` in full at the input rate and use the short-context tier.")
    if budget_note:
        lines.append("")
        lines.append(f"**Budget guard:** {budget_note}")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- CLI

def _cmd_select(args: argparse.Namespace) -> int:
    if args.suite and not SUITE_RE.fullmatch(args.suite):
        print("::error::invalid suite name (allowed: [a-z0-9-]+)", file=sys.stderr)
        return 2
    changed = None
    if args.changed_files:
        changed = Path(args.changed_files).read_text(encoding="utf-8").splitlines()
    suites = discover_suites(Path(args.root))
    try:
        selection = select_suites(args.event, suites, changed, args.suite, args.force_all)
    except ValueError as exc:
        print(f"::error::{exc}", file=sys.stderr)
        return 2
    Path(args.output).write_text("".join(f"{s}\n" for s in selection.suites), encoding="utf-8")
    summary = ["## Eval suite selection", "", f"Event: `{args.event}`. {selection.reason}."]
    if args.baseline:
        summary.append(f"Baseline: `{args.baseline}`.")
    if selection.details:
        summary += ["", *[f"- {d}" for d in selection.details]]
    summary += ["", f"Selected ({len(selection.suites)}): {', '.join(selection.suites) or 'none'}", ""]
    text = "\n".join(summary) + "\n"
    if args.summary:
        Path(args.summary).write_text(text, encoding="utf-8")
    print(text)
    if args.github_output:
        with open(args.github_output, "a", encoding="utf-8") as handle:
            handle.write(f"count={len(selection.suites)}\n")
            handle.write(f"full_coverage={'true' if selection.full_coverage else 'false'}\n")
    return 0


def _cmd_check_model(args: argparse.Namespace) -> int:
    models = load_pricing(Path(args.pricing))["models"]
    if MODEL_RE.fullmatch(args.model) and args.model in models:
        return 0
    print(f"::error::model {args.model!r} is not allowed; choose one of: {', '.join(sorted(models))}", file=sys.stderr)
    return 2


def _cmd_credits_total(args: argparse.Namespace) -> int:
    pricing = load_pricing(Path(args.pricing))
    print(f"{total_credits(collect_costs(Path(args.results_root), args.model, pricing)):.3f}")
    return 0


def _cmd_summary(args: argparse.Namespace) -> int:
    pricing = load_pricing(Path(args.pricing))
    results_root = Path(args.results_root)
    note_path = results_root / "budget-stop.txt"
    note = note_path.read_text(encoding="utf-8").strip() if note_path.is_file() else ""
    max_credits = float(args.max_credits) if args.max_credits else None
    print(render_summary(collect_costs(results_root, args.model, pricing), args.model, max_credits, pricing, note), end="")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pricing", default=str(PRICING))
    sub = parser.add_subparsers(dest="command", required=True)

    select = sub.add_parser("select")
    select.add_argument("--root", default=str(ROOT))
    select.add_argument("--event", required=True)
    select.add_argument("--suite", default="")
    select.add_argument("--force-all", action="store_true")
    select.add_argument("--changed-files", help="file listing paths changed since the baseline; omit when there is no baseline")
    select.add_argument("--baseline", default="")
    select.add_argument("--output", required=True)
    select.add_argument("--summary")
    select.add_argument("--github-output")

    check = sub.add_parser("check-model")
    check.add_argument("model")

    for name in ("credits-total", "summary"):
        cmd = sub.add_parser(name)
        cmd.add_argument("--results-root", required=True)
        cmd.add_argument("--model", default="")
        if name == "summary":
            cmd.add_argument("--max-credits", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    return {
        "select": _cmd_select,
        "check-model": _cmd_check_model,
        "credits-total": _cmd_credits_total,
        "summary": _cmd_summary,
    }[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
