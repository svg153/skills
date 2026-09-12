#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def replace_once(path: str, old: str, new: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one patch anchor in {path}, found {count}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")

def append_before(path: str, marker: str, content: str) -> None:
    target = ROOT / path
    text = target.read_text(encoding="utf-8")
    if content.strip() in text:
        return
    if marker not in text:
        raise SystemExit(f"missing append marker in {path}")
    target.write_text(text.replace(marker, content + "\n\n" + marker, 1), encoding="utf-8")

HELPER = '#!/usr/bin/env python3\n"""Resolve and materialize capability-scoped external Agent Skills from APM lock state."""\n\nfrom __future__ import annotations\n\nimport filecmp\nimport json\nfrom pathlib import Path\nimport re\nimport shutil\nimport subprocess\nimport tempfile\nfrom typing import Any\n\nimport yaml\n\nNAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")\nCOMMIT_RE = re.compile(r"^[0-9a-f]{40}$")\nCONTENT_HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")\nMANIFEST_NAME = "external-components.json"\n\n\nclass ExternalComponentError(RuntimeError):\n    """Fail-closed external component declaration or materialization error."""\n\n\ndef fail(message: str) -> "NoReturn":\n    raise ExternalComponentError(message)\n\n\ndef _load_yaml(path: Path) -> dict[str, Any]:\n    try:\n        value = yaml.safe_load(path.read_text(encoding="utf-8"))\n    except (OSError, yaml.YAMLError) as exc:\n        fail(f"cannot read {path}: {exc}")\n    if not isinstance(value, dict):\n        fail(f"{path}: expected a YAML mapping")\n    return value\n\n\ndef _load_json(path: Path) -> dict[str, Any]:\n    try:\n        value = json.loads(path.read_text(encoding="utf-8"))\n    except (OSError, json.JSONDecodeError) as exc:\n        fail(f"cannot read {path}: {exc}")\n    if not isinstance(value, dict):\n        fail(f"{path}: expected a JSON object")\n    return value\n\n\ndef parse_locator(locator: str) -> tuple[str, str]:\n    parts = [part for part in locator.strip("/").split("/") if part]\n    if len(parts) < 3 or any(part in {".", ".."} for part in parts):\n        fail(\n            "external dependency locator must be owner/repo/path with no path traversal: "\n            f"{locator!r}"\n        )\n    return "/".join(parts[:2]), "/".join(parts[2:])\n\n\ndef normalize_external_components(value: Any) -> list[dict[str, str]]:\n    if value in (None, []):\n        return []\n    if not isinstance(value, list):\n        fail("externalSkillComponents must be an array")\n\n    result: list[dict[str, str]] = []\n    seen_targets: set[str] = set()\n    seen_dependencies: set[str] = set()\n    allowed = {"dependency", "target", "license", "attribution"}\n    for index, raw in enumerate(value):\n        if not isinstance(raw, dict):\n            fail(f"externalSkillComponents[{index}] must be an object")\n        unknown = set(raw) - allowed\n        if unknown:\n            fail(\n                f"externalSkillComponents[{index}] has unsupported fields: "\n                + ", ".join(sorted(unknown))\n            )\n        normalized: dict[str, str] = {}\n        for field in ("dependency", "target", "license", "attribution"):\n            item = raw.get(field)\n            if not isinstance(item, str) or not item.strip():\n                fail(f"externalSkillComponents[{index}].{field} must be a non-empty string")\n            normalized[field] = item.strip()\n\n        parse_locator(normalized["dependency"])\n        if not NAME_RE.fullmatch(normalized["target"]):\n            fail(\n                f"externalSkillComponents[{index}].target must be lowercase kebab-case"\n            )\n        target_id = normalized["target"].casefold()\n        if target_id in seen_targets:\n            fail(f"duplicate external component target: {normalized[\'target\']!r}")\n        if normalized["dependency"] in seen_dependencies:\n            fail(f"duplicate external dependency: {normalized[\'dependency\']!r}")\n        seen_targets.add(target_id)\n        seen_dependencies.add(normalized["dependency"])\n        result.append(normalized)\n    return result\n\n\ndef _normalize_repo_slug(value: str) -> str:\n    result = value.strip()\n    if result.startswith("https://github.com/"):\n        result = result[len("https://github.com/") :]\n    if result.endswith(".git"):\n        result = result[:-4]\n    return result.strip("/")\n\n\ndef resolve_external_components(\n    repo_root: Path, declarations: list[dict[str, str]]\n) -> list[dict[str, str]]:\n    if not declarations:\n        return []\n\n    lock_path = repo_root / "dependencies" / "external-skills" / "apm.lock.yaml"\n    policy_path = repo_root / "dependencies" / "external-skills" / "apm-policy.yml"\n    lock = _load_yaml(lock_path)\n    policy = _load_yaml(policy_path)\n\n    allow = policy.get("dependencies", {}).get("allow", [])\n    if not isinstance(allow, list) or not all(isinstance(item, str) for item in allow):\n        fail(f"{policy_path}: dependencies.allow must be a string array")\n    allowed = set(allow)\n\n    dependencies = lock.get("dependencies", [])\n    if not isinstance(dependencies, list):\n        fail(f"{lock_path}: dependencies must be an array")\n\n    resolved: list[dict[str, str]] = []\n    for declaration in declarations:\n        locator = declaration["dependency"]\n        if locator not in allowed:\n            fail(f"external dependency is not allowlisted by APM policy: {locator}")\n        repo_slug, virtual_path = parse_locator(locator)\n        matches = [\n            item\n            for item in dependencies\n            if isinstance(item, dict)\n            and _normalize_repo_slug(str(item.get("repo_url", ""))) == repo_slug\n            and str(item.get("virtual_path", "")).strip("/") == virtual_path\n        ]\n        if len(matches) != 1:\n            fail(\n                f"expected exactly one APM lock entry for {locator}; found {len(matches)}"\n            )\n        dependency = matches[0]\n        commit = str(dependency.get("resolved_commit", ""))\n        ref = str(dependency.get("resolved_ref", ""))\n        content_hash = str(dependency.get("content_hash", ""))\n        if not COMMIT_RE.fullmatch(commit):\n            fail(f"APM lock entry for {locator} has invalid resolved_commit")\n        if not ref:\n            fail(f"APM lock entry for {locator} is missing resolved_ref")\n        if not CONTENT_HASH_RE.fullmatch(content_hash):\n            fail(f"APM lock entry for {locator} has invalid content_hash")\n\n        resolved.append(\n            {\n                **declaration,\n                "repo_url": repo_slug,\n                "virtual_path": virtual_path,\n                "resolved_ref": ref,\n                "resolved_commit": commit,\n                "content_hash": content_hash,\n            }\n        )\n    return resolved\n\n\ndef manifest_data(resolved: list[dict[str, str]]) -> dict[str, Any]:\n    return {\n        "schemaVersion": 1,\n        "authority": "dependencies/external-skills/apm.lock.yaml",\n        "components": [\n            {\n                "dependency": item["dependency"],\n                "target": item["target"],\n                "license": item["license"],\n                "attribution": item["attribution"],\n                "repo_url": item["repo_url"],\n                "virtual_path": item["virtual_path"],\n                "resolved_ref": item["resolved_ref"],\n                "resolved_commit": item["resolved_commit"],\n                "content_hash": item["content_hash"],\n            }\n            for item in resolved\n        ],\n    }\n\n\ndef render_manifest(resolved: list[dict[str, str]]) -> str:\n    return json.dumps(manifest_data(resolved), indent=2, ensure_ascii=False) + "\\n"\n\n\ndef _frontmatter_name(path: Path) -> str:\n    text = path.read_text(encoding="utf-8")\n    if not text.startswith("---\\n"):\n        fail(f"{path}: missing YAML frontmatter")\n    parts = text.split("---\\n", 2)\n    if len(parts) < 3:\n        fail(f"{path}: missing closing YAML frontmatter")\n    try:\n        value = yaml.safe_load(parts[1])\n    except yaml.YAMLError as exc:\n        fail(f"{path}: invalid frontmatter: {exc}")\n    if not isinstance(value, dict) or not isinstance(value.get("name"), str):\n        fail(f"{path}: frontmatter name is required")\n    return value["name"]\n\n\ndef _payload_files(root: Path) -> dict[str, Path]:\n    result: dict[str, Path] = {}\n    for path in sorted(root.rglob("*")):\n        relative = path.relative_to(root)\n        if any(part in {".git", "node_modules"} for part in relative.parts):\n            continue\n        if path.is_symlink():\n            fail(f"external component payload contains a symlink: {relative.as_posix()}")\n        if path.is_dir():\n            continue\n        result[relative.as_posix()] = path\n    return result\n\n\ndef _compare_payload(source: Path, target: Path) -> list[str]:\n    if not target.is_dir() or target.is_symlink():\n        return ["missing materialized target"]\n    source_files = _payload_files(source)\n    target_files = _payload_files(target)\n    messages: list[str] = []\n    for name in sorted(source_files.keys() - target_files.keys()):\n        messages.append(f"missing locally: {name}")\n    for name in sorted(target_files.keys() - source_files.keys()):\n        messages.append(f"extra locally: {name}")\n    for name in sorted(source_files.keys() & target_files.keys()):\n        if not filecmp.cmp(source_files[name], target_files[name], shallow=False):\n            messages.append(f"content differs: {name}")\n    return messages\n\n\ndef _checkout_locked_source(resolved: dict[str, str], temp: Path) -> Path:\n    checkout = temp / "upstream"\n    origin = f"https://github.com/{resolved[\'repo_url\']}.git"\n    subprocess.run(["git", "init", str(checkout)], check=True, capture_output=True, text=True)\n    subprocess.run(\n        ["git", "-C", str(checkout), "remote", "add", "origin", origin],\n        check=True,\n        capture_output=True,\n        text=True,\n    )\n    subprocess.run(\n        [\n            "git",\n            "-C",\n            str(checkout),\n            "fetch",\n            "--depth",\n            "1",\n            "origin",\n            resolved["resolved_commit"],\n        ],\n        check=True,\n        capture_output=True,\n        text=True,\n    )\n    subprocess.run(\n        ["git", "-C", str(checkout), "checkout", "--detach", "FETCH_HEAD"],\n        check=True,\n        capture_output=True,\n        text=True,\n    )\n    actual = subprocess.run(\n        ["git", "-C", str(checkout), "rev-parse", "HEAD"],\n        check=True,\n        capture_output=True,\n        text=True,\n    ).stdout.strip()\n    if actual != resolved["resolved_commit"]:\n        fail(\n            f"locked external component resolved to {actual}, expected "\n            f"{resolved[\'resolved_commit\']}"\n        )\n    source = checkout / resolved["virtual_path"]\n    skill_file = source / "SKILL.md"\n    if not skill_file.is_file() or skill_file.is_symlink():\n        fail(f"locked external component has no regular SKILL.md: {resolved[\'dependency\']}")\n    return source\n\n\ndef _existing_runtime_identities(repo_root: Path, package_root: Path) -> dict[str, str]:\n    identities: dict[str, str] = {}\n    for skill_file in sorted((repo_root / "skills").glob("*/SKILL.md")):\n        if skill_file.is_symlink():\n            fail(f"root runtime skill is symlinked: {skill_file.relative_to(repo_root)}")\n        name = _frontmatter_name(skill_file)\n        identities[name.casefold()] = str(skill_file.parent.relative_to(repo_root))\n    plugins = repo_root / "plugins"\n    if plugins.is_dir():\n        for skill_file in sorted(plugins.glob("*/skills/*/SKILL.md")):\n            if package_root in skill_file.parents:\n                continue\n            if skill_file.is_symlink():\n                fail(f"capability runtime skill is symlinked: {skill_file.relative_to(repo_root)}")\n            name = _frontmatter_name(skill_file)\n            identity = name.casefold()\n            if identity in identities:\n                fail(f"repository already has duplicate runtime identity {name!r}")\n            identities[identity] = str(skill_file.parent.relative_to(repo_root))\n    return identities\n\n\ndef _previous_components(package_root: Path) -> dict[str, dict[str, Any]]:\n    manifest = package_root / MANIFEST_NAME\n    if not manifest.is_file():\n        return {}\n    value = _load_json(manifest)\n    components = value.get("components", [])\n    if not isinstance(components, list):\n        fail(f"{manifest}: components must be an array")\n    result: dict[str, dict[str, Any]] = {}\n    for item in components:\n        if isinstance(item, dict) and isinstance(item.get("target"), str):\n            result[item["target"].casefold()] = item\n    return result\n\n\ndef sync_external_components(\n    repo_root: Path,\n    package_root: Path,\n    resolved: list[dict[str, str]],\n    *,\n    check_only: bool,\n) -> list[str]:\n    manifest_path = package_root / MANIFEST_NAME\n    previous = _previous_components(package_root)\n    external_targets = {item["target"].casefold(): item for item in resolved}\n    identities = _existing_runtime_identities(repo_root, package_root)\n    drift: list[str] = []\n\n    for identity, item in external_targets.items():\n        if identity in identities:\n            fail(\n                f"external component target {item[\'target\']!r} collides with "\n                f"{identities[identity]}"\n            )\n\n    skills_root = package_root / "skills"\n    skills_root.mkdir(parents=True, exist_ok=True)\n\n    for identity, item in external_targets.items():\n        target = skills_root / item["target"]\n        prior = previous.get(identity)\n        if target.exists() and prior is None:\n            fail(\n                f"external component target {item[\'target\']!r} already exists but is not "\n                "recorded as a previously materialized external component"\n            )\n        if prior is not None and prior.get("dependency") != item["dependency"]:\n            fail(\n                f"external component target {item[\'target\']!r} changed dependency from "\n                f"{prior.get(\'dependency\')!r} to {item[\'dependency\']!r}"\n            )\n\n        with tempfile.TemporaryDirectory(prefix="capability-external-") as temporary:\n            source = _checkout_locked_source(item, Path(temporary))\n            source_name = _frontmatter_name(source / "SKILL.md")\n            if source_name != item["target"]:\n                fail(\n                    f"locked skill name {source_name!r} does not match declared target "\n                    f"{item[\'target\']!r}"\n                )\n            _payload_files(source)\n            differences = _compare_payload(source, target)\n            if differences:\n                if check_only:\n                    drift.extend(f"{item[\'target\']}: {message}" for message in differences)\n                else:\n                    if target.exists():\n                        if target.is_symlink():\n                            fail(f"refuse to replace symlinked target: {target}")\n                        shutil.rmtree(target)\n                    shutil.copytree(source, target)\n\n    stale_targets = set(previous) - set(external_targets)\n    for identity in sorted(stale_targets):\n        prior = previous[identity]\n        target_name = str(prior.get("target", identity))\n        target = skills_root / target_name\n        if check_only:\n            if target.exists():\n                drift.append(f"{target_name}: stale materialized external component")\n        elif target.exists():\n            if target.is_symlink():\n                fail(f"refuse to remove symlinked stale target: {target}")\n            shutil.rmtree(target)\n\n    expected_manifest = render_manifest(resolved) if resolved else None\n    if expected_manifest is None:\n        if check_only and manifest_path.exists():\n            drift.append(f"{MANIFEST_NAME}: stale; no external components are declared")\n        elif not check_only and manifest_path.exists():\n            manifest_path.unlink()\n    elif check_only:\n        if not manifest_path.is_file():\n            drift.append(f"{MANIFEST_NAME}: missing")\n        elif manifest_path.read_text(encoding="utf-8") != expected_manifest:\n            drift.append(f"{MANIFEST_NAME}: stale")\n    else:\n        manifest_path.write_text(expected_manifest, encoding="utf-8")\n\n    return drift\n'
(ROOT / "scripts" / "apm_external_components.py").write_text(HELPER, encoding="utf-8")

replace_once(
    "scripts/generate-capability-plugin.py",
    "from agent_plugin_mcp import MCPConfigError, PLUGIN_SCHEMA, mcp_manifest_from_distribution_config\n",
    "from agent_plugin_mcp import MCPConfigError, PLUGIN_SCHEMA, mcp_manifest_from_distribution_config\n"
    "from apm_external_components import (\n"
    "    ExternalComponentError,\n"
    "    normalize_external_components,\n"
    "    resolve_external_components,\n"
    "    sync_external_components,\n"
    ")\n",
)
replace_once(
    "scripts/generate-capability-plugin.py",
    "    return config\n\n\ndef discover_skills",
    "    try:\n"
    "        config[\"externalSkillComponents\"] = normalize_external_components(\n"
    "            config.get(\"externalSkillComponents\", [])\n"
    "        )\n"
    "    except ExternalComponentError as exc:\n"
    "        fail(f\"{config_path}: externalSkillComponents: {exc}\")\n"
    "    return config\n\n\ndef discover_skills",
)
replace_once(
    "scripts/generate-capability-plugin.py",
    '''    config = normalize_config(load_json(config_path), config_path)
    skill_names = discover_skills(package_root)
    outputs = render(config, skill_names)
    return check(package_root, outputs) if check_only else write(package_root, outputs)
''',
    '''    config = normalize_config(load_json(config_path), config_path)
    repo_root = package_root.parent.parent
    try:
        resolved = resolve_external_components(
            repo_root, config.get("externalSkillComponents", [])
        )
        component_drift = sync_external_components(
            repo_root, package_root, resolved, check_only=check_only
        )
    except ExternalComponentError as exc:
        fail(f"external skill components: {exc}")

    if check_only and component_drift:
        for item in component_drift:
            print(f"DRIFT: {package_root.name}/{item}", file=sys.stderr)
        return 1

    skill_names = discover_skills(package_root)
    outputs = render(config, skill_names)
    return check(package_root, outputs) if check_only else write(package_root, outputs)
''',
)

replace_once(
    "skills/skill-publish/scripts/catalog_capability.py",
    "from agent_plugin_mcp import MCPConfigError, normalize_mcp_servers  # noqa: E402\n",
    "from agent_plugin_mcp import MCPConfigError, normalize_mcp_servers  # noqa: E402\n"
    "from apm_external_components import (  # noqa: E402\n"
    "    ExternalComponentError,\n"
    "    normalize_external_components,\n"
    "    resolve_external_components,\n"
    ")\n",
)
replace_once(
    "skills/skill-publish/scripts/catalog_capability.py",
    '''    repository = raw.get("repository", "https://github.com/svg153/skills")
''',
    '''    try:
        spec["externalSkillComponents"] = normalize_external_components(
            raw.get("externalSkillComponents", [])
        )
    except ExternalComponentError as exc:
        fail(f"spec.externalSkillComponents: {exc}")

    repository = raw.get("repository", "https://github.com/svg153/skills")
''',
)
replace_once(
    "skills/skill-publish/scripts/catalog_capability.py",
    '''    if spec["mcpServers"]:
        config["mcpServers"] = spec["mcpServers"]
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
''',
    '''    if spec["mcpServers"]:
        config["mcpServers"] = spec["mcpServers"]
    if spec["externalSkillComponents"]:
        config["externalSkillComponents"] = spec["externalSkillComponents"]
    return (json.dumps(config, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
''',
)
replace_once(
    "skills/skill-publish/scripts/catalog_capability.py",
    '''    for base in (root / "skills", root / "plugins"):
''',
    '''    for optional in (
        root / "scripts" / "apm_external_components.py",
        root / "dependencies" / "external-skills" / "apm.lock.yaml",
        root / "dependencies" / "external-skills" / "apm-policy.yml",
    ):
        if optional.is_file():
            paths.append(optional)
    for base in (root / "skills", root / "plugins"):
''',
)
replace_once(
    "skills/skill-publish/scripts/catalog_capability.py",
    '''    files = [
        PlannedFile(
            f"plugins/{spec['name']}/distribution.config.json",
            render_distribution_config(spec),
        ),
        *source_files,
    ]

    for item in files:
''',
    '''    files = [
        PlannedFile(
            f"plugins/{spec['name']}/distribution.config.json",
            render_distribution_config(spec),
        ),
        *source_files,
    ]

    try:
        resolved_components = resolve_external_components(
            root, spec["externalSkillComponents"]
        )
    except ExternalComponentError as exc:
        fail(f"spec.externalSkillComponents: {exc}")

    staged_identities = {name.casefold() for name in runtime_names}
    for component in resolved_components:
        identity = component["target"].casefold()
        if identity in existing:
            fail(
                f"external runtime skill {component['target']!r} already exists at "
                f"{existing[identity]}"
            )
        if identity in staged_identities:
            fail(
                f"external runtime skill {component['target']!r} collides with a local "
                "capability skill"
            )
        staged_identities.add(identity)

    for item in files:
''',
)
replace_once(
    "skills/skill-publish/scripts/catalog_capability.py",
    '''        "mcp_servers": sorted(spec["mcpServers"]),
        "repo_fingerprint": repo_fingerprint(root),
''',
    '''        "mcp_servers": sorted(spec["mcpServers"]),
        "external_skill_components": [
            {
                "dependency": item["dependency"],
                "target": item["target"],
                "resolved_commit": item["resolved_commit"],
                "content_hash": item["content_hash"],
            }
            for item in resolved_components
        ],
        "repo_fingerprint": repo_fingerprint(root),
''',
)
replace_once(
    "skills/skill-publish/scripts/catalog_capability.py",
    '''            f"plugins/{spec['name']}/plugin.json",
            *([f"plugins/{spec['name']}/mcp.json"] if spec["mcpServers"] else []),
''',
    '''            f"plugins/{spec['name']}/plugin.json",
            *([f"plugins/{spec['name']}/mcp.json"] if spec["mcpServers"] else []),
            *(
                [f"plugins/{spec['name']}/external-components.json"]
                if spec["externalSkillComponents"]
                else []
            ),
''',
)
replace_once(
    "skills/skill-publish/scripts/catalog_capability.py",
    '''        "mcp_servers": plan.public["mcp_servers"],
        "approval_hash": plan.approval_hash,
''',
    '''        "mcp_servers": plan.public["mcp_servers"],
        "external_skill_components": plan.public["external_skill_components"],
        "approval_hash": plan.approval_hash,
''',
)

config_path = ROOT / "plugins" / "design-engineering" / "distribution.config.json"
config = json.loads(config_path.read_text(encoding="utf-8"))
config["externalSkillComponents"] = []
config_path.write_text(json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

replace_once(
    "tests/test_capability_plugins.py",
    "import sys\nimport unittest\n",
    "import sys\nimport tempfile\nimport shutil\nimport unittest\nfrom unittest import mock\n",
)
replace_once(
    "tests/test_capability_plugins.py",
    "generator_spec.loader.exec_module(generator)\n",
    "generator_spec.loader.exec_module(generator)\n\nimport apm_external_components as external_components\n",
)
external_tests = r'''
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
'''
append_before("tests/test_capability_plugins.py", '\n\nif __name__ == "__main__":', external_tests)

publisher_test = r'''
    def test_external_components_are_resolved_into_approved_plan(self) -> None:
        dependencies = self.root / "dependencies" / "external-skills"
        dependencies.mkdir(parents=True)
        (dependencies / "apm-policy.yml").write_text(
            "dependencies:\n  allow:\n    - acme/repo/skills/external-status\n",
            encoding="utf-8",
        )
        (dependencies / "apm.lock.yaml").write_text(
            "dependencies:\n"
            "- repo_url: acme/repo\n"
            "  virtual_path: skills/external-status\n"
            "  resolved_ref: v1.0.0\n"
            "  resolved_commit: 0123456789012345678901234567890123456789\n"
            "  content_hash: sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa\n",
            encoding="utf-8",
        )
        value = self.capability_spec()
        value["externalSkillComponents"] = [
            {
                "dependency": "acme/repo/skills/external-status",
                "target": "external-status",
                "license": "MIT",
                "attribution": "Acme external status skill",
            }
        ]
        plan = catalog_capability.plan_from_spec(self.write_spec(value), repo_root=self.root)
        item = next(
            entry for entry in plan.files if entry.path.endswith("/distribution.config.json")
        )
        config = json.loads(item.content)
        self.assertEqual(
            config["externalSkillComponents"][0]["dependency"],
            "acme/repo/skills/external-status",
        )
        self.assertEqual(
            plan.public["external_skill_components"][0]["resolved_commit"],
            "0123456789012345678901234567890123456789",
        )
        self.assertIn(
            "plugins/delivery-triage/external-components.json",
            plan.public["generated_package_files"],
        )
'''
append_before("tests/test_skill_publish_capability.py", '\n\nif __name__ == "__main__":', publisher_test)

capability_doc = r'''
## APM-locked external skill components

A capability may declare reviewed external skill payloads with `externalSkillComponents`.
The declaration contains **no version, ref, commit, or digest**: those values come only
from `dependencies/external-skills/apm.lock.yaml`.

```json
{
  "externalSkillComponents": [
    {
      "dependency": "owner/repo/skills/example",
      "target": "example",
      "license": "MIT",
      "attribution": "Upstream project / author"
    }
  ]
}
```

Rules:

- `dependency` must be exactly allowlisted by `apm-policy.yml` and resolve to exactly
  one committed APM lock entry.
- `target` is a runtime skill identity, not an arbitrary filesystem path.
- materialized `plugins/<capability>/skills/<target>/` payloads are derived artifacts;
  the declaration plus APM policy/lock remain the authority.
- `external-components.json` is generated provenance evidence recording the exact
  lock commit/content hash, license and attribution; it is not another lock.
- path traversal, symlink payloads, local/root/plugin identity collisions, missing
  locks, malformed hashes and unallowlisted dependencies fail closed.
- `--check` compares the materialized payload against the exact locked commit and
  detects manifest drift. Removing a declaration removes only a target previously
  recorded as externally managed.
- capability planning resolves lock evidence into the approval hash before mutation;
  lock or policy drift therefore invalidates the reviewed plan.
'''
append_before(
    "skills/skill-publish/references/capability-contract.md",
    "\n## Planning and approval",
    capability_doc,
)

external_doc = r'''
## Capability-scoped external components

Agent Plugin capabilities may also **embed** a selected APM dependency as a portable
skill while keeping APM as the only resolution/integrity authority. This is distinct
from a root-catalog `MIRRORED_UPSTREAM` entry.

The package declaration uses `externalSkillComponents` with an APM locator, runtime
target, license and attribution. It deliberately carries no independent version/ref/
digest. `scripts/apm_external_components.py` resolves the locator only through the
committed resolver policy + lock, checks the exact immutable commit, and materializes
the upstream skill subtree into the capability package.

Generated `external-components.json` records the resolved commit/content hash and
attribution for review/distribution, but is derived evidence rather than a lock.
`generate-capability-plugin.py --check` also compares the packaged payload to the
locked source so local edits cannot silently fork upstream instructions.

The generic mechanism is landed before enrolling design dependencies. In particular,
Phase 3 does **not** add Emil Kowalski or web-quality skills to the allowlist while
the first genuine hosted Renovate update proof in #46 is still pending.
'''
append_before(
    "docs/external-skill-dependencies.md",
    "\n## Migration from scheduled direct sync",
    external_doc,
)

(ROOT / ".github" / "workflows" / "phase-03-apply.yml").unlink(missing_ok=True)
Path(__file__).unlink(missing_ok=True)
