from __future__ import annotations

import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import eval_cost as ec  # noqa: E402

SHA = "a" * 40
INPUTS = {
    "alpha": ("evals/alpha/", "skills/alpha/"),
    "beta": ("evals/beta/", "plugins/p/skills/beta/"),
}


def artifact(sha=SHA, branch="main", expired=False, name=ec.BASELINE_ARTIFACT):
    return {"name": name, "expired": expired, "workflow_run": {"head_sha": sha, "head_branch": branch}}


class SelectSuitesTests(unittest.TestCase):
    def sched(self, changed):
        return ec.select_suites("schedule", changed, INPUTS)

    def test_no_baseline_runs_nothing(self):
        sel = self.sched(None)
        self.assertFalse(sel.run)
        self.assertIn("no baseline", sel.reason)

    def test_nothing_changed_runs_nothing(self):
        sel = self.sched(["docs/evals.md", "README.md"])
        self.assertFalse(sel.run)

    def test_eval_dir_change_selects_only_that_suite(self):
        sel = self.sched(["evals/alpha/tasks/x.yaml"])
        self.assertEqual((sel.run, sel.suites), (True, ("alpha",)))

    def test_skill_dir_change_selects_suite(self):
        self.assertEqual(self.sched(["skills/alpha/SKILL.md"]).suites, ("alpha",))
        self.assertEqual(self.sched(["plugins/p/skills/beta/references/a.md"]).suites, ("beta",))

    def test_prefix_is_directory_bounded(self):
        self.assertFalse(self.sched(["skills/alpha-extra/SKILL.md", "evals/alphabet/eval.yaml"]).run)

    def test_multiple_suites_sorted(self):
        sel = self.sched(["skills/alpha/a", "evals/beta/eval.yaml"])
        self.assertEqual(sel.suites, ("alpha", "beta"))

    def test_each_shared_path_selects_all(self):
        for path in ec.SHARED_PATHS:
            sel = self.sched([path])
            self.assertEqual((sel.run, sel.suites), (True, ()), path)

    def test_eval_cost_script_is_not_shared_machinery(self):
        self.assertFalse(self.sched(["scripts/eval_cost.py", "tests/test_eval_cost.py"]).run)

    def test_manual_dispatch_runs_all_or_selected(self):
        self.assertEqual(ec.select_suites("workflow_dispatch", None, INPUTS).suites, ())
        self.assertEqual(ec.select_suites("workflow_dispatch", None, INPUTS, "beta").suites, ("beta",))
        forced = ec.select_suites("workflow_dispatch", None, INPUTS, "beta", force_all=True)
        self.assertEqual((forced.run, forced.suites), (True, ()))

    def test_manual_unknown_suite_rejected(self):
        with self.assertRaises(ValueError):
            ec.select_suites("workflow_dispatch", None, INPUTS, "nope")


class BaselineTests(unittest.TestCase):
    def test_picks_newest_valid(self):
        resp = {"artifacts": [artifact("b" * 40), artifact(SHA)]}
        self.assertEqual(ec.pick_baseline(resp, "main"), "b" * 40)

    def test_skips_expired_other_branch_other_name_and_bad_sha(self):
        resp = {
            "artifacts": [
                artifact(expired=True),
                artifact(branch="feature"),
                artifact(name="waza-behavioral-results-1"),
                artifact(sha="not-a-sha"),
                artifact("c" * 40),
            ]
        }
        self.assertEqual(ec.pick_baseline(resp, "main"), "c" * 40)

    def test_garbage_means_no_baseline(self):
        for resp in ({}, {"artifacts": None}, {"artifacts": ["x"]}, [], None):
            self.assertIsNone(ec.pick_baseline(resp, "main"))


class SuiteInputsTests(unittest.TestCase):
    def test_resolves_skill_and_plugin_dirs_without_git(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "evals/alpha").mkdir(parents=True)
            (root / "evals/alpha/eval.yaml").write_text("name: x\nskill: alpha\n", encoding="utf-8")
            (root / "skills/alpha").mkdir(parents=True)
            (root / "skills/alpha/SKILL.md").write_text("x", encoding="utf-8")
            (root / "evals/beta").mkdir(parents=True)
            (root / "evals/beta/eval.yaml").write_text("skill: 'beta'  # c\n", encoding="utf-8")
            (root / "plugins/p/skills/beta").mkdir(parents=True)
            (root / "plugins/p/skills/beta/SKILL.md").write_text("x", encoding="utf-8")
            got = ec.suite_inputs(root)
        self.assertEqual(got["alpha"], ("evals/alpha/", "skills/alpha/"))
        self.assertEqual(got["beta"], ("evals/beta/", "plugins/p/skills/beta/"))

    def test_every_real_suite_resolves_its_skill(self):
        inputs = ec.suite_inputs(ROOT)
        self.assertTrue(inputs)
        for suite, prefixes in inputs.items():
            self.assertEqual(prefixes[0], f"evals/{suite}/")
            self.assertGreaterEqual(len(prefixes), 2, f"{suite} has no resolvable skill dir")


class UsageTests(unittest.TestCase):
    def test_ai_credits_summary(self):
        self.assertEqual(ec.ai_credits({"summary": {"usage": {"ai_credits": 1.25}}}), 1.25)

    def test_ai_credits_zero_is_a_real_value(self):
        self.assertEqual(ec.ai_credits({"summary": {"usage": {"ai_credits": 0}}}), 0.0)

    def test_ai_credits_sums_complete_model_metrics(self):
        usage = {"model_metrics": {"a": {"ai_credits": 1.5}, "b": {"ai_credits": 0.5}}}
        self.assertEqual(ec.ai_credits({"summary": {"usage": usage}}), 2.0)

    def test_ai_credits_partial_model_metrics_is_unavailable(self):
        usage = {"model_metrics": {"a": {"ai_credits": 1.5}, "b": {"input_tokens": 3}}}
        self.assertIsNone(ec.ai_credits({"summary": {"usage": usage}}))

    def test_ai_credits_missing_or_malformed_is_none(self):
        for data in (None, [], {}, {"summary": {}}, {"summary": {"usage": {"ai_credits": "x"}}},
                     {"summary": {"usage": {"ai_credits": True}}}, {"summary": {"usage": {"premium_requests": 4}}}):
            self.assertIsNone(ec.ai_credits(data))

    def test_summary_usage(self):
        self.assertEqual(ec.premium_requests({"summary": {"usage": {"premium_requests": 4}}}), 4.0)

    def test_falls_back_to_run_usage(self):
        data = {"tasks": [{"runs": [{"usage": {"premium_requests": 1}}, {"usage": {"premium_requests": 2.5}}]}]}
        self.assertEqual(ec.premium_requests(data), 3.5)

    def test_missing_or_malformed_is_none(self):
        for data in (None, [], {}, {"summary": {}}, {"summary": {"usage": {"premium_requests": "x"}}},
                     {"summary": {"usage": {"premium_requests": True}}}, {"tasks": [None, {"runs": None}]}):
            self.assertIsNone(ec.premium_requests(data))

    def test_render_summary(self):
        def write(root, name, payload):
            (root / name).mkdir()
            (root / name / "results.json").write_text(payload if isinstance(payload, str) else json.dumps(payload), encoding="utf-8")

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write(root, "a", {"config": {"model_id": "claude-haiku-4.5"}, "tasks": [{}, {}],
                              "summary": {"usage": {"ai_credits": 3.5, "premium_requests": 9}}})
            write(root, "b", "{not json")
            write(root, "c", {"tasks": [{}], "summary": {"usage": {"premium_requests": 2}}})
            out = ec.render_summary(root)
            empty = ec.render_summary(root / "none")
        self.assertIn("## AI Credits per suite", out)
        self.assertIn("| a | claude-haiku-4.5 | 3.5 | 2 |", out)
        self.assertIn("| b | default | not reported | 0 |", out)
        self.assertIn("| c | default | 2 premium requests (legacy) | 1 |", out)
        self.assertIn("| **Total** | | **3.5** (partial) | |", out)
        self.assertIn("legacy premium requests (2 in total", out)
        self.assertIn("No results.json", empty)


class GuardBudgetTests(unittest.TestCase):
    def write(self, root, suite, payload):
        (root / suite).mkdir()
        text = payload if isinstance(payload, str) else json.dumps(payload)
        (root / suite / "results.json").write_text(text, encoding="utf-8")

    def guard(self, root, cap):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return ec.main(["guard", str(root), "--cap", cap])

    def test_within_cap_exits_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "a", {"summary": {"usage": {"ai_credits": 20}}})
            self.write(root, "b", {"summary": {"usage": {"ai_credits": 5.5}}})
            self.assertEqual(ec.guard_budget(root, 50), (25.5, []))
            self.assertEqual(self.guard(root, "50"), 0)

    def test_exceeding_cap_exits_one(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "a", {"summary": {"usage": {"ai_credits": 40}}})
            self.write(root, "b", {"summary": {"usage": {"ai_credits": 11}}})
            self.assertEqual(self.guard(root, "50"), 1)

    def test_unreported_credits_fail_closed_even_when_under_cap(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "a", {"summary": {"usage": {"ai_credits": 1}}})
            self.write(root, "b", {})
            self.write(root, "c", "{not json")
            total, problems = ec.guard_budget(root, 50)
            self.assertEqual(total, 1.0)
            self.assertEqual(problems, ["b: AI Credits not reported", "c: AI Credits not reported"])
            self.assertEqual(self.guard(root, "50"), 1)

    def test_zero_cap_disables_the_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.write(root, "a", {"summary": {"usage": {"ai_credits": 1000}}})
            self.assertEqual(self.guard(root, "0"), 0)

    def test_empty_results_dir_sums_to_zero(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self.assertEqual(ec.guard_budget(root, 50), (0.0, []))
            self.assertEqual(self.guard(root, "50"), 0)


class ConsistencyTests(unittest.TestCase):
    def test_allowlist_matches_script_workflow_and_suites(self):
        script = (ROOT / "scripts/run-behavioral-suites.sh").read_text(encoding="utf-8")
        match = re.search(r"^ALLOWED_MODELS=\(([^)]*)\)", script, re.MULTILINE)
        self.assertIsNotNone(match)
        self.assertEqual(tuple(match.group(1).split()), ec.ALLOWED_MODELS)

        workflow = (ROOT / ".github/workflows/eval-behavioral.yml").read_text(encoding="utf-8")
        options = re.search(r"type: choice\n\s+options:\n((?:\s+- .+\n)+)", workflow)
        self.assertIsNotNone(options)
        listed = tuple(line.strip()[2:] for line in options.group(1).splitlines())
        self.assertEqual(listed, ("default",) + ec.ALLOWED_MODELS)

        for spec in (ROOT / "evals").glob("*/eval.yaml"):
            m = re.search(r"^  model:\s*(\S+)", spec.read_text(encoding="utf-8"), re.MULTILINE)
            if m:
                self.assertIn(m.group(1), ec.ALLOWED_MODELS, spec.parent.name)

    def test_workflow_never_interpolates_inputs_inside_run(self):
        workflow = (ROOT / ".github/workflows/eval-behavioral.yml").read_text(encoding="utf-8")
        for block in re.findall(r"^\s+run: \|\n((?:\s{10,}.*\n|\n)+)", workflow, re.MULTILINE):
            self.assertNotIn("${{", block)


if __name__ == "__main__":
    unittest.main()
