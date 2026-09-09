from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "skill-publish"
    / "scripts"
    / "catalog_capability.py"
)
spec = importlib.util.spec_from_file_location("catalog_capability", SCRIPT)
catalog_capability = importlib.util.module_from_spec(spec)
sys.modules["catalog_capability"] = catalog_capability
assert spec.loader is not None
spec.loader.exec_module(catalog_capability)


class CapabilityPublishTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "skills" / "existing").mkdir(parents=True)
        (self.root / "skills" / "existing" / "SKILL.md").write_text(
            """---
name: existing
description: "Existing root skill."
license: MIT
---
# Existing
""",
            encoding="utf-8",
        )
        (self.root / "plugins" / "planning" / "skills" / "planning").mkdir(
            parents=True
        )
        (self.root / "plugins" / "planning" / "skills" / "planning" / "SKILL.md").write_text(
            """---
name: planning
description: "Existing plugin skill."
license: MIT
---
# Planning
""",
            encoding="utf-8",
        )
        (self.root / "plugins" / "planning" / "distribution.config.json").write_text(
            json.dumps(
                {
                    "schemaVersion": 1,
                    "name": "planning",
                    "version": "0.1.0",
                    "description": "Planning",
                    "author": {"name": "svg153"},
                    "repository": "https://github.com/svg153/skills",
                    "homepage": "https://github.com/svg153/skills/tree/main/plugins/planning",
                    "license": "MIT",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        (self.root / "distribution.config.json").write_text("{}\n", encoding="utf-8")
        (self.root / "scripts").mkdir()
        for filename in (
            "generate-distribution.py",
            "generate-capability-plugin.py",
            "agent_plugin_mcp.py",
        ):
            (self.root / "scripts" / filename).write_text("# fixture\n", encoding="utf-8")
        self.spec_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.spec_dir, ignore_errors=True)

    def skill_source(self, name: str) -> Path:
        source = self.spec_dir / name
        source.mkdir(parents=True, exist_ok=True)
        (source / "SKILL.md").write_text(
            f"""---
name: {name}
description: "Capability skill {name}."
license: MIT
---
# {name}
""",
            encoding="utf-8",
        )
        (source / "references").mkdir(exist_ok=True)
        (source / "references" / "guide.md").write_text("guide\n", encoding="utf-8")
        return source

    def write_spec(self, value: dict) -> Path:
        path = self.spec_dir / "capability.json"
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        return path

    def capability_spec(self) -> dict:
        return {
            "schemaVersion": 1,
            "name": "delivery-triage",
            "version": "0.1.0",
            "description": "Triage delivery work with reusable provider tools.",
            "author": {"name": "svg153", "url": "https://github.com/svg153"},
            "license": "MIT",
            "keywords": ["delivery", "triage"],
            "skill_sources": [
                str(self.skill_source("delivery-triage")),
                str(self.skill_source("delivery-status")),
            ],
            "mcpServers": {
                "github": {
                    "config": {
                        "type": "streamable-http",
                        "url": "https://api.githubcopilot.com/mcp/",
                    },
                    "provenance": {
                        "kind": "official",
                        "owner": "GitHub",
                        "source": "https://github.com/github/github-mcp-server",
                        "purpose": "Read delivery state from GitHub.",
                        "reviewed": "2026-09-09",
                    },
                }
            },
        }

    def test_plan_is_zero_write_and_contains_package_sources(self) -> None:
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        plan = catalog_capability.plan_from_spec(
            self.write_spec(self.capability_spec()), repo_root=self.root
        )
        after = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        self.assertEqual(before, after)
        paths = {item.path for item in plan.files}
        self.assertIn("plugins/delivery-triage/distribution.config.json", paths)
        self.assertIn("plugins/delivery-triage/skills/delivery-triage/SKILL.md", paths)
        self.assertIn("plugins/delivery-triage/skills/delivery-status/references/guide.md", paths)
        self.assertEqual(plan.public["mcp_servers"], ["github"])
        self.assertRegex(plan.approval_hash, r"^[0-9a-f]{64}$")

    def test_apply_moves_package_without_touching_root_skill(self) -> None:
        original = (self.root / "skills" / "existing" / "SKILL.md").read_bytes()
        plan = catalog_capability.plan_from_spec(
            self.write_spec(self.capability_spec()), repo_root=self.root
        )
        report = catalog_capability.apply_plan(plan, run_validations=False)
        self.assertEqual(report["status"], "applied")
        self.assertTrue((self.root / "plugins/delivery-triage/skills/delivery-status/SKILL.md").is_file())
        self.assertEqual((self.root / "skills/existing/SKILL.md").read_bytes(), original)

    def test_root_runtime_collision_fails_closed(self) -> None:
        value = self.capability_spec()
        value["skill_sources"] = [str(self.skill_source("existing"))]
        with self.assertRaisesRegex(catalog_capability.CapabilityPlanError, "already exists"):
            catalog_capability.plan_from_spec(self.write_spec(value), repo_root=self.root)

    def test_existing_canonical_source_cannot_be_repacked_by_copy(self) -> None:
        value = self.capability_spec()
        value["skill_sources"] = [str(self.root / "skills" / "existing")]
        with self.assertRaisesRegex(
            catalog_capability.CapabilityPlanError, "unregistered staging directories"
        ):
            catalog_capability.plan_from_spec(self.write_spec(value), repo_root=self.root)

    def test_credential_bearing_mcp_header_fails_during_plan(self) -> None:
        value = self.capability_spec()
        value["mcpServers"]["github"]["config"]["headers"] = {
            "Authorization": "Bearer nope"
        }
        with self.assertRaisesRegex(catalog_capability.CapabilityPlanError, "credential"):
            catalog_capability.plan_from_spec(self.write_spec(value), repo_root=self.root)
        self.assertFalse((self.root / "plugins/delivery-triage").exists())

    def test_valid_mcp_composition_is_preserved_in_distribution_config(self) -> None:
        plan = catalog_capability.plan_from_spec(
            self.write_spec(self.capability_spec()), repo_root=self.root
        )
        item = next(
            value for value in plan.files if value.path.endswith("/distribution.config.json")
        )
        config = json.loads(item.content)
        self.assertEqual(config["mcpServers"]["github"]["config"]["type"], "streamable-http")
        self.assertEqual(config["mcpServers"]["github"]["provenance"]["kind"], "official")

    def test_repository_runtime_change_invalidates_approval_hash(self) -> None:
        spec_path = self.write_spec(self.capability_spec())
        before = catalog_capability.plan_from_spec(spec_path, repo_root=self.root)
        (self.root / "skills" / "another").mkdir()
        (self.root / "skills" / "another" / "SKILL.md").write_text(
            """---
name: another
description: "Another."
license: MIT
---
# Another
""",
            encoding="utf-8",
        )
        after = catalog_capability.plan_from_spec(spec_path, repo_root=self.root)
        self.assertNotEqual(before.approval_hash, after.approval_hash)

    def test_validation_failure_rolls_back_capability_and_generated_state(self) -> None:
        marketplace = self.root / "marketplace.json"
        marketplace.write_text('{"before": true}\n', encoding="utf-8")
        original = marketplace.read_bytes()
        plan = catalog_capability.plan_from_spec(
            self.write_spec(self.capability_spec()), repo_root=self.root
        )
        previous = catalog_capability.run_command
        try:
            def explode(root, command):
                marketplace.write_text('{"changed": true}\n', encoding="utf-8")
                raise catalog_capability.CapabilityPlanError("forced validation failure")

            catalog_capability.run_command = explode
            with self.assertRaisesRegex(catalog_capability.CapabilityPlanError, "forced"):
                catalog_capability.apply_plan(plan, run_validations=True)
        finally:
            catalog_capability.run_command = previous
        self.assertFalse((self.root / "plugins/delivery-triage").exists())
        self.assertEqual(marketplace.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
