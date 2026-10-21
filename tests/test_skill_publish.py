from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
import yaml

SCRIPT = Path(__file__).resolve().parents[1] / "skills" / "skill-publish" / "scripts" / "catalog_skill.py"
spec = importlib.util.spec_from_file_location("catalog_skill", SCRIPT)
catalog_skill = importlib.util.module_from_spec(spec)
sys.modules["catalog_skill"] = catalog_skill
assert spec.loader is not None
spec.loader.exec_module(catalog_skill)

VALIDATOR_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-skills.py"
validator_spec = importlib.util.spec_from_file_location("validate_skills", VALIDATOR_SCRIPT)
validate_skills = importlib.util.module_from_spec(validator_spec)
assert validator_spec.loader is not None
validator_spec.loader.exec_module(validate_skills)


class CatalogSkillTests(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())
        (self.root / "skills" / "existing").mkdir(parents=True)
        (self.root / "skills" / "existing" / "SKILL.md").write_text(
            '''---
name: existing
description: "Trigger: existing workflow. Do existing things."
license: MIT
---
# Existing
''', encoding="utf-8")
        (self.root / "skills" / "existing" / "metadata.yaml").write_text(
            '''name: existing
origin: https://github.com/svg153/skills
origin_path: skills/existing
category: devops
status: active
sync:
  enabled: false
  interval: manual
  strategy: local
  authoritative: local
tags:
  - existing
''', encoding="utf-8")
        (self.root / "skills.sh.json").write_text(json.dumps({"$schema": "test", "notGrouped": "bottom", "groupings": [{"title": "Software Development", "description": "test", "skills": ["existing"]}]}, indent=2) + "\n", encoding="utf-8")
        (self.root / "distribution.config.json").write_text("{}\n", encoding="utf-8")
        (self.root / "scripts").mkdir()
        for filename in ("generate-distribution.py", "validate-skills.py", "validate-evals.py"):
            (self.root / "scripts" / filename).write_text("# fixture\n", encoding="utf-8")
        (self.root / "scripts" / "sync-upstreams.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
        self.spec_dir = Path(tempfile.mkdtemp())

    def tearDown(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        shutil.rmtree(self.spec_dir, ignore_errors=True)

    def write_spec(self, value: dict) -> Path:
        path = self.spec_dir / "spec.json"
        path.write_text(json.dumps(value, indent=2), encoding="utf-8")
        return path

    def local_spec(self) -> dict:
        return {"schemaVersion": 1, "name": "new-skill", "ownership": "LOCAL", "summary": "Do a distinct new workflow", "use_for": ["brand-new operation"], "do_not_use_for": ["existing workflow"], "category": "devops", "status": "active", "tags": ["agent-skills", "new-skill"], "apm": True, "evals": True, "skills_sh_group": "Software Development", "allow_overlap_with": [], "license": "MIT", "author": "svg153", "body": "# New Skill\n\n## Activation Contract\n\nUse for the new operation.\n", "eval_positive_prompt": "Run the brand-new operation for me.", "eval_negative_prompt": "Explain the weather forecast.", "eval_behavior": "Pass only if the response follows the new operation contract."}

    def source_dir(self, runtime_name: str = "upstream-runtime") -> Path:
        source = self.spec_dir / "source"
        source.mkdir(exist_ok=True)
        (source / "SKILL.md").write_text(f'''---
name: {runtime_name}
description: "Trigger: imported upstream operation. Use the upstream workflow."
license: MIT
---
# Upstream
''', encoding="utf-8")
        (source / "references").mkdir(exist_ok=True)
        (source / "references" / "guide.md").write_text("upstream guide\n", encoding="utf-8")
        return source

    def upstream_spec(self, ownership: str) -> dict:
        source = self.source_dir()
        value = {"schemaVersion": 1, "name": "imported-skill", "ownership": ownership, "summary": "Use a distinct imported upstream workflow", "use_for": ["imported upstream operation"], "do_not_use_for": ["existing workflow"], "category": "devops", "status": "active", "tags": ["agent-skills", "upstream"], "apm": False, "evals": False, "skills_sh_group": None, "allow_overlap_with": [], "source_dir": str(source), "origin": "https://github.com/example/upstream", "origin_path": "skills/imported-skill"}
        if ownership == "MIRRORED_UPSTREAM":
            value.update({"origin_ref": "latest-release", "sync_interval": "weekly", "channel": "stable"})
        else:
            value["origin_ref"] = "v1.2.3"
        return value

    def metadata_from_plan(self, plan) -> dict:
        item = next(file for file in plan.files if file.path.endswith("/metadata.yaml"))
        return yaml.safe_load(item.content.decode("utf-8"))

    def plan_with_description_length(self, length: int, *, unicode_summary: bool = False):
        value = self.local_spec()
        value["use_for"] = ["first unique trigger", "second unique trigger"]
        prefix = f"Trigger: {'; '.join(value['use_for'])}. "
        fill = "é" if unicode_summary else "x"
        value["summary"] = fill * (length - len(prefix))
        return value, catalog_skill.plan_from_spec(self.write_spec(value), repo_root=self.root)

    def description_from_plan(self, plan) -> str:
        item = next(file for file in plan.files if file.path.endswith("/SKILL.md"))
        frontmatter = yaml.safe_load(item.content.decode("utf-8").split("---\n", 2)[1])
        return frontmatter["description"]

    def assert_validator_accepts_rendered_skill(self, plan) -> None:
        skill_root = Path(tempfile.mkdtemp())
        try:
            skill_dir = skill_root / "skills" / "new-skill"
            skill_dir.mkdir(parents=True)
            item = next(file for file in plan.files if file.path == "skills/new-skill/SKILL.md")
            (skill_dir / "SKILL.md").write_bytes(item.content)
            runtime_name, errors = validate_skills.validate_skill_dir(skill_dir, root=skill_root)
            self.assertEqual(runtime_name, "new-skill")
            self.assertEqual(errors, [])
        finally:
            shutil.rmtree(skill_root, ignore_errors=True)

    def test_local_plan_is_zero_write_and_complete(self) -> None:
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        plan = catalog_skill.plan_from_spec(self.write_spec(self.local_spec()), repo_root=self.root)
        after = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        self.assertEqual(before, after)
        paths = {item.path for item in plan.files}
        self.assertIn("skills/new-skill/SKILL.md", paths)
        self.assertIn("skills/new-skill/metadata.yaml", paths)
        self.assertIn("skills/new-skill/apm.yml", paths)
        self.assertIn("evals/new-skill/eval.yaml", paths)
        self.assertIn("skills.sh.json", paths)
        self.assertRegex(plan.approval_hash, r"^[0-9a-f]{64}$")

    def test_description_longer_than_legacy_cap_is_accepted(self) -> None:
        value, plan = self.plan_with_description_length(251)
        description = self.description_from_plan(plan)
        self.assertEqual(description, f"Trigger: {'; '.join(value['use_for'])}. {value['summary']}")
        self.assertEqual(len(description), 251)

    def test_description_at_spec_limit_counts_unicode_characters_and_validates(self) -> None:
        value, plan = self.plan_with_description_length(1024, unicode_summary=True)
        description = self.description_from_plan(plan)
        self.assertEqual(description, f"Trigger: {'; '.join(value['use_for'])}. {value['summary']}")
        self.assertEqual(len(description), 1024)
        self.assertGreater(len(description.encode("utf-8")), len(description))
        self.assert_validator_accepts_rendered_skill(plan)

    def test_description_over_spec_limit_fails_before_any_write(self) -> None:
        value = self.local_spec()
        value["use_for"] = ["first unique trigger", "second unique trigger"]
        prefix = f"Trigger: {'; '.join(value['use_for'])}. "
        value["summary"] = "x" * (1025 - len(prefix))
        before = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        with self.assertRaisesRegex(catalog_skill.SkillPlanError, "exceeds 1024"):
            catalog_skill.plan_from_spec(self.write_spec(value), repo_root=self.root)
        after = sorted(path.relative_to(self.root).as_posix() for path in self.root.rglob("*"))
        self.assertEqual(before, after)

    def test_local_apply_writes_approved_plan(self) -> None:
        plan = catalog_skill.plan_from_spec(self.write_spec(self.local_spec()), repo_root=self.root)
        report = catalog_skill.apply_plan(plan, run_validations=False)
        self.assertEqual(report["status"], "applied")
        self.assertTrue((self.root / "skills/new-skill/SKILL.md").is_file())
        self.assertTrue((self.root / "evals/new-skill/eval.yaml").is_file())
        grouping = json.loads((self.root / "skills.sh.json").read_text(encoding="utf-8"))["groupings"][0]
        self.assertEqual(grouping["skills"], ["existing", "new-skill"])
        metadata = yaml.safe_load((self.root / "skills/new-skill/metadata.yaml").read_text(encoding="utf-8"))
        self.assertEqual(metadata["sync"]["strategy"], "local")
        self.assertEqual(metadata["sync"]["authoritative"], "local")

    def test_mirrored_upstream_records_download_authority(self) -> None:
        plan = catalog_skill.plan_from_spec(self.write_spec(self.upstream_spec("MIRRORED_UPSTREAM")), repo_root=self.root)
        metadata = self.metadata_from_plan(plan)
        self.assertEqual(metadata["sync"]["strategy"], "download")
        self.assertEqual(metadata["sync"]["authoritative"], "upstream")
        self.assertEqual(metadata["sync"]["channel"], "stable")
        self.assertEqual(metadata["origin_ref"], "latest-release")
        self.assertIn("skills/imported-skill/references/guide.md", {item.path for item in plan.files})

    def test_curated_upstream_is_local_authority_and_manual(self) -> None:
        plan = catalog_skill.plan_from_spec(self.write_spec(self.upstream_spec("CURATED_UPSTREAM")), repo_root=self.root)
        metadata = self.metadata_from_plan(plan)
        self.assertFalse(metadata["sync"]["enabled"])
        self.assertEqual(metadata["sync"]["strategy"], "manual")
        self.assertEqual(metadata["sync"]["authoritative"], "local")
        self.assertEqual(metadata["origin_ref"], "v1.2.3")

    def test_duplicate_catalog_name_fails_before_write(self) -> None:
        value = self.local_spec(); value["name"] = "existing"
        with self.assertRaisesRegex(catalog_skill.SkillPlanError, "already exists"):
            catalog_skill.plan_from_spec(self.write_spec(value), repo_root=self.root)

    def test_substantial_overlap_fails_closed(self) -> None:
        value = self.local_spec(); value["use_for"] = ["existing workflow"]
        with self.assertRaisesRegex(catalog_skill.SkillPlanError, "overlap"):
            catalog_skill.plan_from_spec(self.write_spec(value), repo_root=self.root)
        self.assertFalse((self.root / "skills/new-skill").exists())

    def test_runtime_collision_from_upstream_fails(self) -> None:
        value = self.upstream_spec("CURATED_UPSTREAM")
        shutil.rmtree(Path(value["source_dir"]))
        value["source_dir"] = str(self.source_dir(runtime_name="existing"))
        with self.assertRaisesRegex(catalog_skill.SkillPlanError, "runtime name collision"):
            catalog_skill.plan_from_spec(self.write_spec(value), repo_root=self.root)

    def test_repository_change_invalidates_approval_hash(self) -> None:
        spec_path = self.write_spec(self.local_spec())
        before = catalog_skill.plan_from_spec(spec_path, repo_root=self.root)
        data = json.loads((self.root / "skills.sh.json").read_text(encoding="utf-8")); data["notGrouped"] = "top"
        (self.root / "skills.sh.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        after = catalog_skill.plan_from_spec(spec_path, repo_root=self.root)
        self.assertNotEqual(before.approval_hash, after.approval_hash)

    def test_validation_failure_rolls_back_registration(self) -> None:
        plan = catalog_skill.plan_from_spec(self.write_spec(self.local_spec()), repo_root=self.root)
        original = (self.root / "skills.sh.json").read_bytes(); previous = catalog_skill.run_command
        try:
            def explode(root, command):
                raise catalog_skill.SkillPlanError("forced validation failure")
            catalog_skill.run_command = explode
            with self.assertRaisesRegex(catalog_skill.SkillPlanError, "forced"):
                catalog_skill.apply_plan(plan, run_validations=True)
        finally:
            catalog_skill.run_command = previous
        self.assertFalse((self.root / "skills/new-skill").exists())
        self.assertFalse((self.root / "evals/new-skill").exists())
        self.assertEqual((self.root / "skills.sh.json").read_bytes(), original)

    def test_symlinked_source_fails_closed(self) -> None:
        value = self.upstream_spec("CURATED_UPSTREAM")
        source = Path(value["source_dir"]); target = source / "real.txt"; target.write_text("real\n", encoding="utf-8")
        linked = source / "linked.txt"
        try:
            linked.symlink_to(target)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        with self.assertRaisesRegex(catalog_skill.SkillPlanError, "symlink"):
            catalog_skill.plan_from_spec(self.write_spec(value), repo_root=self.root)


if __name__ == "__main__":
    unittest.main()
