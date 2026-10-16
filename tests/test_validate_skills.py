from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "validate-skills.py"
SPEC = importlib.util.spec_from_file_location("validate_skills", SCRIPT)
assert SPEC is not None and SPEC.loader is not None
validate_skills = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate_skills)


class ValidateSkillsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "skills").mkdir()

    def tearDown(self) -> None:
        self.tempdir.cleanup()

    def write_skill(
        self,
        relative_dir: str,
        *,
        name: str,
        description: str = "Does useful work. Use when testing Agent Skills.",
        extra_frontmatter: str = "",
    ) -> None:
        skill_dir = self.root / relative_dir
        skill_dir.mkdir(parents=True, exist_ok=True)
        frontmatter = (
            "---\n"
            f"name: {name}\n"
            f"description: {description!r}\n"
            f"{extra_frontmatter}"
            "---\n\n"
            "# Test skill\n"
        )
        (skill_dir / "SKILL.md").write_text(frontmatter, encoding="utf-8")

    def errors(self) -> list[str]:
        _, errors = validate_skills.validate_repository(self.root)
        return errors

    def test_accepts_catalog_and_capability_plugin_skills(self) -> None:
        self.write_skill("skills/example-skill", name="example-skill")
        self.write_skill(
            "plugins/example/skills/plugin-skill",
            name="plugin-skill",
            extra_frontmatter=(
                "license: MIT\n"
                "compatibility: Requires network access\n"
                "metadata:\n"
                "  author: example\n"
                '  version: "1.0"\n'
                "allowed-tools: Read Bash(git:*)\n"
            ),
        )

        count, errors = validate_skills.validate_repository(self.root)

        self.assertEqual(2, count)
        self.assertEqual([], errors)

    def test_rejects_name_that_does_not_match_parent_directory(self) -> None:
        self.write_skill("skills/domain-manager-sync", name="skill-sync")

        self.assertTrue(
            any("must match parent directory" in error for error in self.errors())
        )

    def test_rejects_invalid_name_and_length(self) -> None:
        invalid_name = "A" * 65
        self.write_skill("skills/example-skill", name=invalid_name)

        errors = self.errors()
        self.assertTrue(any("exceeds 64 characters" in error for error in errors))
        self.assertTrue(any("lowercase ASCII letters" in error for error in errors))

    def test_rejects_unknown_frontmatter_and_non_string_metadata_values(self) -> None:
        self.write_skill(
            "skills/example-skill",
            name="example-skill",
            extra_frontmatter=(
                "unexpected: true\n"
                "metadata:\n"
                "  author: example\n"
                "  version: 1\n"
            ),
        )

        errors = self.errors()
        self.assertTrue(any("unexpected frontmatter fields" in error for error in errors))
        self.assertTrue(any("metadata entries must use string keys" in error for error in errors))

    def test_rejects_description_and_compatibility_limits(self) -> None:
        self.write_skill(
            "skills/example-skill",
            name="example-skill",
            description="x" * 1025,
            extra_frontmatter=f"compatibility: {'y' * 501!r}\n",
        )

        errors = self.errors()
        self.assertTrue(any("description exceeds 1024" in error for error in errors))
        self.assertTrue(any("compatibility exceeds 500" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
