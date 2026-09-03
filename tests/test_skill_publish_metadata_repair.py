from __future__ import annotations

import importlib.util
from pathlib import Path
import tempfile
import unittest

import yaml

MODULE_PATH = Path(__file__).resolve().parents[1] / "skills" / "skill-publish" / "scripts" / "metadata_repair.py"
spec = importlib.util.spec_from_file_location("metadata_repair", MODULE_PATH)
module = importlib.util.module_from_spec(spec)
assert spec and spec.loader
spec.loader.exec_module(module)


class MetadataRepairTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "skills").mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def write_meta(self, name: str, origin: str, sync: dict):
        path = self.root / "skills" / name
        path.mkdir()
        data = {
            "name": name,
            "origin": origin,
            "origin_path": f"/{name}",
            "category": "github",
            "status": "active",
            "sync": sync,
            "tags": ["test"],
        }
        (path / "metadata.yaml").write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")
        return path / "metadata.yaml"

    def test_local_legacy_metadata_becomes_local_v2(self):
        path = self.write_meta("local-one", module.CATALOG_ORIGIN, {"enabled": False, "interval": "weekly", "strategy": "manual"})
        plan = module.build_plan(self.root)
        self.assertEqual(1, len(plan["changes"]))
        changed = yaml.safe_load(plan["changes"][0]["content"])
        self.assertEqual("LOCAL", plan["changes"][0]["ownership"])
        self.assertEqual("local", changed["sync"]["strategy"])
        self.assertEqual("local", changed["sync"]["authoritative"])
        self.assertFalse(changed["sync"]["enabled"])
        self.assertEqual("manual", changed["sync"]["interval"])
        self.assertEqual("skills/local-one", changed["origin_path"])
        self.assertNotIn("authoritative", yaml.safe_load(path.read_text())["sync"])

    def test_external_manual_metadata_becomes_curated_v2(self):
        self.write_meta("curated", "https://github.com/example/upstream", {"enabled": True, "interval": "weekly", "strategy": "manual"})
        plan = module.build_plan(self.root)
        changed = yaml.safe_load(plan["changes"][0]["content"])
        self.assertEqual("CURATED_UPSTREAM", plan["changes"][0]["ownership"])
        self.assertEqual({"enabled": False, "interval": "manual", "strategy": "manual", "authoritative": "local"}, changed["sync"])

    def test_valid_mirror_is_not_rewritten(self):
        self.write_meta("mirror", "https://github.com/example/upstream", {"enabled": True, "interval": "weekly", "strategy": "download", "authoritative": "upstream", "channel": "stable"})
        plan = module.build_plan(self.root)
        self.assertEqual([], plan["changes"])

    def test_plan_is_zero_write_and_stable(self):
        path = self.write_meta("local-one", module.CATALOG_ORIGIN, {"enabled": False, "interval": "weekly", "strategy": "manual"})
        before = path.read_bytes()
        first = module.build_plan(self.root)["public"]
        second = module.build_plan(self.root)["public"]
        self.assertEqual(first["approval_hash"], second["approval_hash"])
        self.assertEqual(before, path.read_bytes())

    def test_stale_approval_fails_closed(self):
        path = self.write_meta("curated", "https://github.com/example/upstream", {"enabled": True, "interval": "weekly", "strategy": "manual"})
        approval = module.build_plan(self.root)["public"]["approval_hash"]
        path.write_text(path.read_text() + "note: changed\n", encoding="utf-8")
        with self.assertRaises(module.RepairError):
            module.apply(self.root, approval, validate=False)


if __name__ == "__main__":
    unittest.main()
