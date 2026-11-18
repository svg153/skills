"""Every generated host marketplace must list the same plugins.

Regression for #120: capability plugins reached the Copilot and Codex marketplaces
but not the Claude Code and Cursor ones, because those two were hard-coded.
"""

from __future__ import annotations

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

# marketplace file -> how to read each entry's source path
MARKETPLACES = {
    "marketplace.json": lambda entry: entry["source"],
    ".agents/plugins/marketplace.json": lambda entry: entry["source"]["path"],
    ".claude-plugin/marketplace.json": lambda entry: entry["source"],
    ".cursor-plugin/marketplace.json": lambda entry: entry["source"],
}


def normalize(source: str) -> str:
    return source.rstrip("/") or "."


def listed(relative: str) -> set[tuple[str, str]]:
    data = json.loads((ROOT / relative).read_text(encoding="utf-8"))
    source_of = MARKETPLACES[relative]
    return {(entry["name"], normalize(source_of(entry))) for entry in data["plugins"]}


def capability_plugins() -> set[tuple[str, str]]:
    plugins = ROOT / "plugins"
    if not plugins.is_dir():
        return set()
    return {
        (directory.name, f"./plugins/{directory.name}")
        for directory in plugins.iterdir()
        if (directory / "distribution.config.json").is_file()
    }


class MarketplaceParityTests(unittest.TestCase):
    def test_every_marketplace_lists_the_same_plugins(self) -> None:
        reference = listed("marketplace.json")
        for relative in MARKETPLACES:
            with self.subTest(marketplace=relative):
                self.assertEqual(
                    listed(relative),
                    reference,
                    f"{relative} lists different plugins than marketplace.json; "
                    "run scripts/generate-distribution.py",
                )

    def test_every_capability_plugin_is_in_every_marketplace(self) -> None:
        expected = capability_plugins()
        self.assertTrue(expected, "no capability plugins found under plugins/")
        for relative in MARKETPLACES:
            with self.subTest(marketplace=relative):
                missing = expected - listed(relative)
                self.assertFalse(missing, f"{relative} is missing {sorted(missing)}")


if __name__ == "__main__":
    unittest.main()
