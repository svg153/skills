from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import shutil
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
PACKAGE = ROOT / "plugins" / "planning"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

helper_spec = importlib.util.spec_from_file_location("agent_plugin_mcp", SCRIPTS / "agent_plugin_mcp.py")
agent_plugin_mcp = importlib.util.module_from_spec(helper_spec)
sys.modules["agent_plugin_mcp"] = agent_plugin_mcp
assert helper_spec.loader is not None
helper_spec.loader.exec_module(agent_plugin_mcp)

generator_spec = importlib.util.spec_from_file_location("generate_capability_plugin", SCRIPTS / "generate-capability-plugin.py")
generator = importlib.util.module_from_spec(generator_spec)
sys.modules["generate_capability_plugin"] = generator
assert generator_spec.loader is not None
generator_spec.loader.exec_module(generator)

import apm_external_components as external_components


class PlanningCapabilityPluginTests(unittest.TestCase):
    def config(self) -> dict:
        return json.loads((PACKAGE / "distribution.config.json").read_text(encoding="utf-8"))

    def test_tracked_manifests_match_canonical_config_and_skills(self) -> None:
        config = generator.normalize_config(self.config(), PACKAGE / "distribution.config.json")
        skills = generator.discover_skills(PACKAGE)
        self.assertEqual(skills, ["backlog-management", "planning"])
        outputs = generator.render(config, skills)
        self.assertEqual((PACKAGE / "plugin.json").read_text(encoding="utf-8"), outputs[Path("plugin.json")])
        self.assertEqual((PACKAGE / "mcp.json").read_text(encoding="utf-8"), outputs[Path("mcp.json")])

    def test_planning_plugin_composes_only_reused_remote_mcps(self) -> None:
        manifest = json.loads((PACKAGE / "mcp.json").read_text(encoding="utf-8"))
        self.assertEqual(set(manifest["mcpServers"]), {"github", "atlassian"})
        self.assertEqual(manifest["mcpServers"]["github"]["type"], "streamable-http")
        self.assertEqual(manifest["mcpServers"]["github"]["url"], "https://api.githubcopilot.com/mcp/")
        self.assertEqual(manifest["mcpServers"]["atlassian"]["type"], "streamable-http")
        self.assertEqual(manifest["mcpServers"]["atlassian"]["url"], "https://mcp.atlassian.com/v1/mcp/authv2")
        for server in manifest["mcpServers"].values():
            self.assertNotIn("headers", server)
            self.assertNotIn("command", server)
            self.assertNotIn("env", server)

    def test_both_mcp_dependencies_have_official_provenance(self) -> None:
        servers = self.config()["mcpServers"]
        for name in ("github", "atlassian"):
            provenance = servers[name]["provenance"]
            self.assertEqual(provenance["kind"], "official")
            self.assertTrue(provenance["source"].startswith("https://"))
            self.assertEqual(provenance["reviewed"], "2026-09-05")
            self.assertTrue(provenance["purpose"])

    def test_skills_keep_single_system_of_record_rule(self) -> None:
        planning = (PACKAGE / "skills" / "planning" / "SKILL.md").read_text(encoding="utf-8").casefold()
        backlog = (PACKAGE / "skills" / "backlog-management" / "SKILL.md").read_text(encoding="utf-8").casefold()
        self.assertIn("one authoritative system of record per work item", planning)
        self.assertIn("one source of truth per work item", backlog)
        self.assertIn("cross-link", planning)
        self.assertIn("duplicated mutable tickets", backlog)

    def test_mutations_require_user_intent_without_redundant_reconfirmation(self) -> None:
        planning = (PACKAGE / "skills" / "planning" / "SKILL.md").read_text(encoding="utf-8").casefold()
        backlog = (PACKAGE / "skills" / "backlog-management" / "SKILL.md").read_text(encoding="utf-8").casefold()
        self.assertIn("explicitly asked to create/update planning records", planning)
        self.assertIn("do not ask again", planning)
        self.assertIn("mutations require explicit user intent", backlog)
        self.assertIn("do not re-ask", backlog)

    def test_provider_failure_is_degradable(self) -> None:
        planning = (PACKAGE / "skills" / "planning" / "SKILL.md").read_text(encoding="utf-8").casefold()
        backlog = (PACKAGE / "skills" / "backlog-management" / "SKILL.md").read_text(encoding="utf-8").casefold()
        self.assertIn("provider failure is degradable", planning)
        self.assertIn("if neither is available, produce a plan-only result", planning)
        self.assertIn("do not mirror the blocked change into another provider", backlog)

    def test_planning_does_not_absorb_repository_delivery(self) -> None:
        planning = (PACKAGE / "skills" / "planning" / "SKILL.md").read_text(encoding="utf-8").casefold()
        backlog = (PACKAGE / "skills" / "backlog-management" / "SKILL.md").read_text(encoding="utf-8").casefold()
        self.assertIn("do not take over implementation", planning)
        self.assertIn("github-repo-autopilot", planning)
        self.assertIn("use repository delivery/implementation skills instead", backlog)

class ExternalSkillComponentTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "dependencies" / "external-skills").mkdir(parents=True)
        (self.root / "skills").mkdir()
        self.package = self.root / "plugins" / "demo"
        (self.package / "skills" / "local").mkdir(parents=True)
        (self.package / "skills" / "local" / "SKILL.md").write_text(
            "---\nname: local\ndescription: local\n---\n# Local\n",
            encoding="utf-8",
        )
        self.source = Path(tempfile.mkdtemp()) / "foo"
        self.source.mkdir(parents=True)
        (self.source / "SKILL.md").write_text(
            "---\nname: foo\ndescription: external\n---\n# Foo\n",
            encoding="utf-8",
        )
        (self.source / "references").mkdir()
        (self.source / "references" / "guide.md").write_text("guide\n", encoding="utf-8")
        self.write_lock("sha256:" + "a" * 64)
        (self.root / "dependencies" / "external-skills" / "apm-policy.yml").write_text(
            "dependencies:\n  allow:\n    - acme/repo/skills/foo\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.source.parent, ignore_errors=True)

    def write_lock(self, content_hash: str) -> None:
        (self.root / "dependencies" / "external-skills" / "apm.lock.yaml").write_text(
            "dependencies:\n"
            "- repo_url: acme/repo\n"
            "  virtual_path: skills/foo\n"
            "  resolved_ref: v1.0.0\n"
            "  resolved_commit: 0123456789012345678901234567890123456789\n"
            f"  content_hash: {content_hash}\n",
            encoding="utf-8",
        )

    def declarations(self):
        return external_components.normalize_external_components(
            [
                {
                    "dependency": "acme/repo/skills/foo",
                    "target": "foo",
                    "license": "MIT",
                    "attribution": "Acme upstream skill",
                }
            ]
        )

    def test_resolve_requires_exact_allowlisted_lock_entry(self) -> None:
        resolved = external_components.resolve_external_components(
            self.root, self.declarations()
        )
        self.assertEqual(resolved[0]["resolved_commit"], "0123456789012345678901234567890123456789")
        policy = self.root / "dependencies" / "external-skills" / "apm-policy.yml"
        policy.write_text("dependencies:\n  allow: []\n", encoding="utf-8")
        with self.assertRaisesRegex(external_components.ExternalComponentError, "not allowlisted"):
            external_components.resolve_external_components(self.root, self.declarations())

    def test_target_path_and_duplicates_fail_closed(self) -> None:
        with self.assertRaises(external_components.ExternalComponentError):
            external_components.normalize_external_components(
                [{
                    "dependency": "acme/repo/skills/foo",
                    "target": "../foo",
                    "license": "MIT",
                    "attribution": "Acme",
                }]
            )
        with self.assertRaisesRegex(
            external_components.ExternalComponentError, "duplicate external component target"
        ):
            external_components.normalize_external_components(
                [
                    {
                        "dependency": "acme/repo/skills/foo",
                        "target": "foo",
                        "license": "MIT",
                        "attribution": "Acme",
                    },
                    {
                        "dependency": "other/repo/skills/bar",
                        "target": "foo",
                        "license": "MIT",
                        "attribution": "Other",
                    },
                ]
            )

    def test_materialization_converges_and_detects_payload_drift(self) -> None:
        resolved = external_components.resolve_external_components(self.root, self.declarations())
        with mock.patch.object(
            external_components, "_checkout_locked_source",
            side_effect=lambda _item, _temp: self.source,
        ):
            self.assertEqual(
                external_components.sync_external_components(
                    self.root, self.package, resolved, check_only=False
                ),
                [],
            )
            self.assertEqual(
                external_components.sync_external_components(
                    self.root, self.package, resolved, check_only=True
                ),
                [],
            )
            target = self.package / "skills" / "foo" / "SKILL.md"
            target.write_text(target.read_text(encoding="utf-8") + "\nDRIFT\n", encoding="utf-8")
            drift = external_components.sync_external_components(
                self.root, self.package, resolved, check_only=True
            )
            self.assertTrue(any("content differs" in item for item in drift))

    def test_lock_hash_change_is_visible_as_manifest_drift(self) -> None:
        resolved = external_components.resolve_external_components(self.root, self.declarations())
        with mock.patch.object(
            external_components, "_checkout_locked_source",
            side_effect=lambda _item, _temp: self.source,
        ):
            external_components.sync_external_components(
                self.root, self.package, resolved, check_only=False
            )
            self.write_lock("sha256:" + "b" * 64)
            changed = external_components.resolve_external_components(self.root, self.declarations())
            drift = external_components.sync_external_components(
                self.root, self.package, changed, check_only=True
            )
            self.assertIn("external-components.json: stale", drift)

    def test_symlink_payload_and_runtime_collision_fail_closed(self) -> None:
        link = self.source / "unsafe"
        try:
            link.symlink_to("SKILL.md")
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        resolved = external_components.resolve_external_components(self.root, self.declarations())
        with mock.patch.object(
            external_components, "_checkout_locked_source",
            side_effect=lambda _item, _temp: self.source,
        ):
            with self.assertRaisesRegex(external_components.ExternalComponentError, "symlink"):
                external_components.sync_external_components(
                    self.root, self.package, resolved, check_only=False
                )
        link.unlink()
        (self.root / "skills" / "foo").mkdir()
        (self.root / "skills" / "foo" / "SKILL.md").write_text(
            "---\nname: foo\ndescription: collision\n---\n# Foo\n",
            encoding="utf-8",
        )
        with mock.patch.object(
            external_components, "_checkout_locked_source",
            side_effect=lambda _item, _temp: self.source,
        ):
            with self.assertRaisesRegex(external_components.ExternalComponentError, "collides"):
                external_components.sync_external_components(
                    self.root, self.package, resolved, check_only=False
                )




if __name__ == "__main__":
    unittest.main()
