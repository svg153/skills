from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

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


if __name__ == "__main__":
    unittest.main()
