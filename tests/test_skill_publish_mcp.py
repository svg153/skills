from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

helper_spec = importlib.util.spec_from_file_location("agent_plugin_mcp", SCRIPTS / "agent_plugin_mcp.py")
agent_plugin_mcp = importlib.util.module_from_spec(helper_spec)
sys.modules["agent_plugin_mcp"] = agent_plugin_mcp
assert helper_spec.loader is not None
helper_spec.loader.exec_module(agent_plugin_mcp)

generator_spec = importlib.util.spec_from_file_location("generate_distribution", SCRIPTS / "generate-distribution.py")
generate_distribution = importlib.util.module_from_spec(generator_spec)
sys.modules["generate_distribution"] = generate_distribution
assert generator_spec.loader is not None
generator_spec.loader.exec_module(generate_distribution)


class AgentPluginMCPTests(unittest.TestCase):
    def base_config(self) -> dict:
        return {
            "schemaVersion": 1,
            "name": "example-plugin",
            "displayName": "Example Plugin",
            "version": "1.0.0",
            "description": "Example capability package.",
            "author": {"name": "Example", "url": "https://example.com"},
            "repository": "https://github.com/example/plugin",
            "homepage": "https://example.com/plugin",
            "category": "Developer Tools",
        }

    def provenance(self, **overrides) -> dict:
        value = {
            "kind": "official",
            "owner": "Example",
            "source": "https://github.com/example/mcp-server",
            "purpose": "Provide the tools required by the example capability.",
            "reviewed": "2026-09-05",
        }
        value.update(overrides)
        return value

    def test_no_mcp_servers_omits_optional_manifest(self) -> None:
        outputs = generate_distribution.render(self.base_config(), ["one-skill"], ["one-skill"])
        self.assertNotIn(Path("mcp.json"), outputs)

    def test_multiple_existing_servers_render_portable_mcp_json(self) -> None:
        config = self.base_config()
        config["mcpServers"] = {
            "github": {
                "config": {
                    "type": "streamable-http",
                    "url": "https://api.githubcopilot.com/mcp/",
                },
                "provenance": self.provenance(owner="GitHub", source="https://github.com/github/github-mcp-server"),
            },
            "local-validator": {
                "config": {
                    "type": "stdio",
                    "command": "npx",
                    "args": ["validator", "--data", "${PLUGIN_DATA}/validator"],
                    "env": {"CONFIG": "${PLUGIN_ROOT}/config.json"},
                    "cwd": "${PLUGIN_ROOT}",
                },
                "provenance": self.provenance(kind="community"),
            },
        }
        outputs = generate_distribution.render(config, ["one-skill"], ["one-skill"])
        manifest = json.loads(outputs[Path("mcp.json")])
        self.assertEqual(manifest["$schema"], agent_plugin_mcp.MCP_SCHEMA)
        self.assertEqual(set(manifest["mcpServers"]), {"github", "local-validator"})
        self.assertNotIn("provenance", manifest["mcpServers"]["github"])
        self.assertEqual(manifest["mcpServers"]["github"]["type"], "streamable-http")

    def test_remote_non_loopback_http_is_rejected(self) -> None:
        config = self.base_config()
        config["mcpServers"] = {
            "unsafe": {
                "config": {"type": "streamable-http", "url": "http://example.com/mcp"},
                "provenance": self.provenance(),
            }
        }
        with self.assertRaisesRegex(agent_plugin_mcp.MCPConfigError, "HTTPS"):
            agent_plugin_mcp.mcp_manifest_from_distribution_config(config)

    def test_loopback_http_is_allowed(self) -> None:
        config = self.base_config()
        config["mcpServers"] = {
            "local": {
                "config": {"type": "streamable-http", "url": "http://localhost:9000/mcp"},
                "provenance": self.provenance(kind="local"),
            }
        }
        manifest = agent_plugin_mcp.mcp_manifest_from_distribution_config(config)
        self.assertEqual(manifest["mcpServers"]["local"]["url"], "http://localhost:9000/mcp")

    def test_credential_header_is_rejected(self) -> None:
        config = self.base_config()
        config["mcpServers"] = {
            "github": {
                "config": {
                    "type": "streamable-http",
                    "url": "https://api.githubcopilot.com/mcp/",
                    "headers": {"Authorization": "Bearer do-not-store-this"},
                },
                "provenance": self.provenance(),
            }
        }
        with self.assertRaisesRegex(agent_plugin_mcp.MCPConfigError, "client-managed"):
            agent_plugin_mcp.mcp_manifest_from_distribution_config(config)

    def test_secret_like_stdio_env_is_rejected(self) -> None:
        config = self.base_config()
        config["mcpServers"] = {
            "local": {
                "config": {
                    "type": "stdio",
                    "command": "npx",
                    "env": {"API_TOKEN": "literal-secret"},
                },
                "provenance": self.provenance(kind="local"),
            }
        }
        with self.assertRaisesRegex(agent_plugin_mcp.MCPConfigError, "must not embed secrets"):
            agent_plugin_mcp.mcp_manifest_from_distribution_config(config)

    def test_stdio_command_cannot_be_shell_string_or_absolute_path(self) -> None:
        for command in ("npx server", "/usr/bin/server"):
            with self.subTest(command=command):
                config = self.base_config()
                config["mcpServers"] = {
                    "local": {
                        "config": {"type": "stdio", "command": command},
                        "provenance": self.provenance(kind="local"),
                    }
                }
                with self.assertRaises(agent_plugin_mcp.MCPConfigError):
                    agent_plugin_mcp.mcp_manifest_from_distribution_config(config)

    def test_sse_requires_explicit_legacy_reason(self) -> None:
        config = self.base_config()
        config["mcpServers"] = {
            "legacy": {
                "config": {"type": "sse", "url": "https://legacy.example.com/sse"},
                "provenance": self.provenance(),
            }
        }
        with self.assertRaisesRegex(agent_plugin_mcp.MCPConfigError, "legacyReason"):
            agent_plugin_mcp.mcp_manifest_from_distribution_config(config)

    def test_provenance_is_required_and_review_date_is_validated(self) -> None:
        config = self.base_config()
        config["mcpServers"] = {
            "github": {
                "config": {"type": "streamable-http", "url": "https://api.githubcopilot.com/mcp/"},
                "provenance": self.provenance(reviewed="not-a-date"),
            }
        }
        with self.assertRaisesRegex(agent_plugin_mcp.MCPConfigError, "YYYY-MM-DD"):
            agent_plugin_mcp.mcp_manifest_from_distribution_config(config)


if __name__ == "__main__":
    unittest.main()
