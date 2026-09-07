#!/usr/bin/env python3
"""Check or materialize an upstream-authoritative skill from APM lock state.

APM resolves and pins the dependency. This script owns the catalog-specific
projection into skills/<name>/ while preserving catalog-only metadata.yaml.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOCK = ROOT / "dependencies" / "external-skills" / "apm.lock.yaml"


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"ERROR: {message}")


def load_yaml(path: Path) -> dict:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"{path.relative_to(ROOT)}: invalid YAML: {exc}")
    if not isinstance(data, dict):
        fail(f"{path.relative_to(ROOT)}: expected a mapping")
    return data


def github_repo_slug(origin: str) -> str:
    parsed = urlparse(origin)
    if parsed.scheme != "https" or parsed.netloc != "github.com":
        fail(f"only github.com HTTPS origins are supported by this pilot: {origin}")
    slug = parsed.path.strip("/")
    if slug.endswith(".git"):
        slug = slug[:-4]
    if slug.count("/") != 1:
        fail(f"expected GitHub owner/repo origin, got: {origin}")
    return slug


def is_commit_sha(value: str) -> bool:
    return len(value) == 40 and all(c in "0123456789abcdef" for c in value)


def resolve_dependency(skill: str, metadata: dict, lock: dict) -> dict:
    origin = str(metadata.get("origin", ""))
    origin_path = str(metadata.get("origin_path", "")).strip("/")
    repo_slug = github_repo_slug(origin)

    sync = metadata.get("sync")
    if not isinstance(sync, dict):
        fail(f"skills/{skill}/metadata.yaml: missing sync mapping")
    expected_sync = {
        "enabled": True,
        "strategy": "download",
        "authoritative": "upstream",
    }
    for field, expected in expected_sync.items():
        if sync.get(field) != expected:
            fail(
                f"skills/{skill}/metadata.yaml: APM materialization requires "
                f"sync.{field}={expected!r}"
            )

    matches: list[dict] = []
    for dependency in lock.get("dependencies", []) or []:
        if not isinstance(dependency, dict):
            continue
        if (
            str(dependency.get("repo_url", "")).removesuffix(".git") == repo_slug
            and str(dependency.get("virtual_path", "")).strip("/") == origin_path
        ):
            matches.append(dependency)

    if len(matches) != 1:
        fail(
            f"expected exactly one APM lock dependency for {repo_slug}/{origin_path}; "
            f"found {len(matches)}"
        )

    dependency = matches[0]
    resolved_commit = str(dependency.get("resolved_commit", ""))
    resolved_ref = str(dependency.get("resolved_ref", ""))
    content_hash = str(dependency.get("content_hash", ""))
    if not is_commit_sha(resolved_commit):
        fail(f"APM lock dependency has invalid resolved_commit: {resolved_commit!r}")
    if not resolved_ref:
        fail("APM lock dependency is missing resolved_ref")
    if not content_hash.startswith("sha256:"):
        fail("APM lock dependency is missing a sha256 content_hash")

    return dependency


def payload_paths(root: Path) -> dict[str, Path]:
    result: dict[str, Path] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root)
        if relative.parts and relative.parts[0] == ".git":
            continue
        if relative == Path("metadata.yaml"):
            continue
        if path.is_dir():
            continue
        result[relative.as_posix()] = path
    return result


def compare_payloads(upstream: Path, target: Path) -> list[str]:
    upstream_files = payload_paths(upstream)
    target_files = payload_paths(target)
    messages: list[str] = []

    for path in sorted(upstream_files.keys() - target_files.keys()):
        messages.append(f"missing locally: {path}")
    for path in sorted(target_files.keys() - upstream_files.keys()):
        messages.append(f"extra locally: {path}")
    for path in sorted(upstream_files.keys() & target_files.keys()):
        if upstream_files[path].is_symlink() != target_files[path].is_symlink():
            messages.append(f"file type differs: {path}")
            continue
        if upstream_files[path].is_symlink():
            if upstream_files[path].readlink() != target_files[path].readlink():
                messages.append(f"symlink target differs: {path}")
            continue
        if not filecmp.cmp(upstream_files[path], target_files[path], shallow=False):
            messages.append(f"content differs: {path}")
    return messages


def clone_locked_source(
    origin: str,
    origin_path: str,
    resolved_ref: str,
    resolved_commit: str,
    temp: Path,
) -> Path:
    checkout = temp / "upstream"

    if resolved_ref == resolved_commit and is_commit_sha(resolved_ref):
        # Digest-pinned APM dependencies intentionally use an immutable commit as
        # resolved_ref. `git clone --branch <sha>` is invalid because a commit is
        # not a branch/tag name, so fetch exactly that object and detach at it.
        subprocess.run(["git", "init", str(checkout)], check=True)
        subprocess.run(
            ["git", "-C", str(checkout), "remote", "add", "origin", origin],
            check=True,
        )
        subprocess.run(
            [
                "git",
                "-C",
                str(checkout),
                "fetch",
                "--depth",
                "1",
                "origin",
                resolved_commit,
            ],
            check=True,
        )
        subprocess.run(
            ["git", "-C", str(checkout), "checkout", "--detach", "FETCH_HEAD"],
            check=True,
        )
    else:
        # Human-readable refs remain useful during migration. Clone the ref and
        # verify it still points at the exact commit pinned by APM, failing closed
        # if a release tag was moved after lock generation.
        subprocess.run(
            ["git", "clone", "--depth", "1", "--branch", resolved_ref, origin, str(checkout)],
            check=True,
        )

    actual_commit = subprocess.run(
        ["git", "-C", str(checkout), "rev-parse", "HEAD"],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    if actual_commit != resolved_commit:
        fail(
            f"upstream ref {resolved_ref} now resolves to {actual_commit}, but APM lock pins "
            f"{resolved_commit}; refuse materialization"
        )

    source = checkout / origin_path.strip("/") if origin_path.strip("/") else checkout
    if not (source / "SKILL.md").is_file():
        fail(f"locked upstream source has no SKILL.md: {origin_path}")
    return source


def materialize(source: Path, target: Path) -> None:
    metadata_path = target / "metadata.yaml"
    metadata_bytes = metadata_path.read_bytes()

    for child in target.iterdir():
        if child.name == "metadata.yaml":
            continue
        if child.is_dir() and not child.is_symlink():
            shutil.rmtree(child)
        else:
            child.unlink()

    for child in source.iterdir():
        if child.name in {".git", "metadata.yaml"}:
            continue
        destination = target / child.name
        if child.is_dir() and not child.is_symlink():
            shutil.copytree(child, destination, symlinks=True)
        elif child.is_symlink():
            destination.symlink_to(child.readlink())
        else:
            shutil.copy2(child, destination)

    metadata_path.write_bytes(metadata_bytes)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("skill", help="catalog skill name under skills/<name>")
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    target = ROOT / "skills" / args.skill
    metadata_path = target / "metadata.yaml"
    if not metadata_path.is_file():
        fail(f"unknown catalog skill or missing metadata: {args.skill}")

    lock_path = args.lock if args.lock.is_absolute() else ROOT / args.lock
    metadata = load_yaml(metadata_path)
    lock = load_yaml(lock_path)
    dependency = resolve_dependency(args.skill, metadata, lock)

    origin = str(metadata["origin"])
    origin_path = str(metadata.get("origin_path", ""))
    resolved_ref = str(dependency["resolved_ref"])
    resolved_commit = str(dependency["resolved_commit"])
    content_hash = str(dependency["content_hash"])

    with tempfile.TemporaryDirectory(prefix="apm-mirror-") as temporary:
        source = clone_locked_source(
            origin,
            origin_path,
            resolved_ref,
            resolved_commit,
            Path(temporary),
        )

        differences = compare_payloads(source, target)
        if args.check:
            if differences:
                for difference in differences:
                    print(f"DRIFT: {difference}")
                print(
                    f"Run: python scripts/materialize-apm-mirror.py {args.skill} --apply",
                )
                return 1
            print(
                f"OK: {args.skill} matches APM lock {resolved_ref}@{resolved_commit[:12]} "
                f"({content_hash})"
            )
            return 0

        materialize(source, target)
        remaining = compare_payloads(source, target)
        if remaining:
            fail("materialized payload still differs from locked upstream source")
        print(
            f"MATERIALIZED: {args.skill} from APM lock {resolved_ref}@{resolved_commit[:12]} "
            f"({content_hash})"
        )
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
