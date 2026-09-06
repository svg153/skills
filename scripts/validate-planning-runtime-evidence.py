#!/usr/bin/env python3
"""Validate sanitized authenticated-runtime evidence for the planning Agent Plugin."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import sys
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_EVIDENCE_DIR = ROOT / "plugins" / "planning" / "evidence"
ALLOWED_STATUS = {"pending", "verified", "blocked", "not-applicable"}
ALLOWED_CLIENTS = {"codex-cli", "copilot-cli", "vscode-copilot", "chatgpt-codex", "other"}
SECRET_KEY_RE = re.compile(
    r"(?:^|[_-])(token|secret|password|passwd|authorization|cookie|credential|api[_-]?key)(?:$|[_-])",
    re.IGNORECASE,
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/-]+=*", re.IGNORECASE),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bATATT[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\beyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
)


class EvidenceError(ValueError):
    pass


def require(condition: bool, message: str) -> None:
    if not condition:
        raise EvidenceError(message)


def require_non_empty_string(value: Any, path: str) -> str:
    require(isinstance(value, str) and value.strip(), f"{path} must be a non-empty string")
    return value.strip()


def validate_no_secrets(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            require(isinstance(key, str), f"{path}: object keys must be strings")
            require(not SECRET_KEY_RE.search(key), f"{path}.{key}: secret-like key is forbidden in committed evidence")
            validate_no_secrets(child, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, child in enumerate(value):
            validate_no_secrets(child, f"{path}[{index}]")
        return
    if isinstance(value, str):
        for pattern in SECRET_VALUE_PATTERNS:
            require(not pattern.search(value), f"{path}: secret-like value is forbidden in committed evidence")


def validate_status_record(record: Any, path: str) -> str:
    require(isinstance(record, dict), f"{path} must be an object")
    status = record.get("status")
    require(status in ALLOWED_STATUS, f"{path}.status must be one of {sorted(ALLOWED_STATUS)}")
    if status in {"blocked", "verified"}:
        require_non_empty_string(record.get("evidence"), f"{path}.evidence")
    return status


def validate_provider(name: str, provider: Any, mode: str) -> None:
    path = f"$.providers.{name}"
    require(isinstance(provider, dict), f"{path} must be an object")

    auth = provider.get("authentication")
    auth_status = validate_status_record(auth, f"{path}.authentication")
    if auth_status == "verified":
        require_non_empty_string(auth.get("method"), f"{path}.authentication.method")
        require(auth.get("credentialStoredInPlugin") is False, f"{path}.authentication.credentialStoredInPlugin must be false")

    read = provider.get("readToolCall")
    read_status = validate_status_record(read, f"{path}.readToolCall")
    if read_status == "verified":
        require(auth_status == "verified", f"{path}.readToolCall cannot be verified before authentication")
        for field in ("operation", "resourceType", "resourceRef", "resultSummary"):
            require_non_empty_string(read.get(field), f"{path}.readToolCall.{field}")

    mutation = provider.get("mutation")
    mutation_status = validate_status_record(mutation, f"{path}.mutation")
    if mutation_status == "verified":
        require(auth_status == "verified", f"{path}.mutation cannot be verified before authentication")
        require(mutation.get("explicitUserIntent") is True, f"{path}.mutation.explicitUserIntent must be true")
        for field in ("operation", "returnedId", "resultSummary"):
            require_non_empty_string(mutation.get(field), f"{path}.mutation.{field}")

    if mode == "evidence":
        require(
            auth_status != "pending" or read_status != "pending" or mutation_status != "pending",
            f"{path}: evidence files must record progress or an explicit blocker",
        )


def validate_document(document: Any, source: str = "<memory>") -> None:
    require(isinstance(document, dict), f"{source}: root must be an object")
    validate_no_secrets(document)

    require(document.get("schemaVersion") == 1, f"{source}: schemaVersion must be 1")
    require(document.get("plugin") == "planning", f"{source}: plugin must be 'planning'")
    require_non_empty_string(document.get("pluginVersion"), f"{source}: pluginVersion")

    mode = document.get("mode")
    require(mode in {"template", "evidence"}, f"{source}: mode must be template or evidence")

    client = document.get("client")
    require(isinstance(client, dict), f"{source}: client must be an object")
    client_name = client.get("name")
    require(client_name in ALLOWED_CLIENTS, f"{source}: client.name must be one of {sorted(ALLOWED_CLIENTS)}")
    require_non_empty_string(client.get("version"), f"{source}: client.version")

    captured_at = require_non_empty_string(document.get("capturedAt"), f"{source}: capturedAt")
    try:
        datetime.fromisoformat(captured_at.replace("Z", "+00:00"))
    except ValueError as exc:
        raise EvidenceError(f"{source}: capturedAt must be ISO-8601") from exc

    environment = document.get("environment")
    require(isinstance(environment, dict), f"{source}: environment must be an object")
    require_non_empty_string(environment.get("platform"), f"{source}: environment.platform")
    require(environment.get("containsSensitiveData") is False, f"{source}: environment.containsSensitiveData must be false")

    providers = document.get("providers")
    require(isinstance(providers, dict), f"{source}: providers must be an object")
    require(set(providers) == {"github", "atlassian"}, f"{source}: providers must contain exactly github and atlassian")
    validate_provider("github", providers["github"], mode)
    validate_provider("atlassian", providers["atlassian"], mode)

    end_to_end = document.get("endToEnd")
    end_status = validate_status_record(end_to_end, f"{source}: endToEnd")
    if end_status == "verified":
        github = providers["github"]
        atlassian = providers["atlassian"]
        require(github["readToolCall"]["status"] == "verified", f"{source}: endToEnd requires verified GitHub read")
        require(atlassian["readToolCall"]["status"] == "verified", f"{source}: endToEnd requires verified Atlassian read")
        require(
            github["mutation"]["status"] == "verified" or atlassian["mutation"]["status"] == "verified",
            f"{source}: endToEnd requires at least one verified mutation",
        )
        require(end_to_end.get("singleSourceOfTruthVerified") is True, f"{source}: endToEnd.singleSourceOfTruthVerified must be true")
        require(end_to_end.get("crossProviderLinkVerified") is True, f"{source}: endToEnd.crossProviderLinkVerified must be true")
        require_non_empty_string(end_to_end.get("resultSummary"), f"{source}: endToEnd.resultSummary")


def evidence_files(directory: Path) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(path for path in directory.glob("*.json") if path.is_file())


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="*", type=Path, help="Evidence JSON files; defaults to plugins/planning/evidence/*.json")
    args = parser.parse_args()

    paths = args.paths or evidence_files(DEFAULT_EVIDENCE_DIR)
    if not paths:
        print("OK: no planning runtime evidence files to validate")
        return 0

    failures = 0
    for path in paths:
        try:
            document = json.loads(path.read_text(encoding="utf-8"))
            validate_document(document, str(path))
        except (OSError, json.JSONDecodeError, EvidenceError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            failures += 1
        else:
            print(f"OK: {path}")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
