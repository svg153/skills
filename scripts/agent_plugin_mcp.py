#!/usr/bin/env python3
"""Validate and render Agent Plugins 1.0 MCP composition from distribution config."""

from __future__ import annotations

from datetime import date
import ipaddress
import re
from pathlib import PurePosixPath
from typing import Any
from urllib.parse import urlsplit

SPEC_VERSION = "1.0.0"
PLUGIN_SCHEMA = f"https://agent-plugins.org/schemas/{SPEC_VERSION}/plugin.schema.json"
MCP_SCHEMA = f"https://agent-plugins.org/schemas/{SPEC_VERSION}/mcp.schema.json"
SERVER_NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEADER_NAME_RE = re.compile(r"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+$")
SECRET_NAME_RE = re.compile(r"(?:authorization|api[-_]?key|token|secret|password|cookie|credential)", re.IGNORECASE)


class MCPConfigError(ValueError):
    """Invalid or unsafe Agent Plugins MCP composition."""


def fail(message: str) -> "NoReturn":
    raise MCPConfigError(message)


def _nonempty(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        fail(f"{field} must be a non-empty string")
    return value.strip()


def _https_source(value: Any, field: str) -> str:
    text = _nonempty(value, field)
    parsed = urlsplit(text)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password or parsed.fragment:
        fail(f"{field} must be an absolute HTTPS URL without credentials or fragment")
    return text


def _is_loopback(host: str) -> bool:
    if host.casefold() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def _remote_url(value: Any, field: str) -> str:
    text = _nonempty(value, field)
    parsed = urlsplit(text)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        fail(f"{field} must be an absolute HTTP(S) URL")
    if parsed.username or parsed.password or parsed.fragment:
        fail(f"{field} must not contain user information or a fragment")
    if parsed.scheme == "http" and not _is_loopback(parsed.hostname):
        fail(f"{field} must use HTTPS for non-loopback endpoints")
    return text


def _safe_relative_parts(value: str, field: str) -> None:
    if "\\" in value:
        fail(f"{field} must use POSIX separators")
    parts = PurePosixPath(value).parts
    if ".." in parts:
        fail(f"{field} must not escape its Agent Plugin root")


def _normalize_headers(value: Any, field: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        fail(f"{field} must be an object of literal strings")
    result: dict[str, str] = {}
    seen: set[str] = set()
    for raw_name, raw_value in value.items():
        if not isinstance(raw_name, str) or not HEADER_NAME_RE.fullmatch(raw_name):
            fail(f"{field} contains an invalid HTTP header name")
        if not isinstance(raw_value, str) or "\r" in raw_value or "\n" in raw_value:
            fail(f"{field}.{raw_name} must be a single-line literal string")
        identity = raw_name.casefold()
        if identity in seen:
            fail(f"{field} contains duplicate header {raw_name!r} with different casing")
        if SECRET_NAME_RE.search(raw_name):
            fail(f"{field}.{raw_name} looks credential-bearing; authentication must remain client-managed")
        seen.add(identity)
        result[raw_name] = raw_value
    return result


def _normalize_env(value: Any, field: str) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        fail(f"{field} must be an object of strings")
    result: dict[str, str] = {}
    for raw_name, raw_value in value.items():
        if not isinstance(raw_name, str) or not raw_name:
            fail(f"{field} contains an invalid environment variable name")
        if raw_name.casefold() in {"plugin_root", "plugin_data"}:
            fail(f"{field} must not override PLUGIN_ROOT or PLUGIN_DATA")
        if SECRET_NAME_RE.search(raw_name):
            fail(f"{field}.{raw_name} looks credential-bearing; portable config must not embed secrets")
        if not isinstance(raw_value, str):
            fail(f"{field}.{raw_name} must be a string")
        result[raw_name] = raw_value
    return result


def _normalize_cwd(value: Any, field: str) -> str | None:
    if value is None:
        return None
    cwd = _nonempty(value, field)
    if cwd.startswith("./"):
        _safe_relative_parts(cwd[2:], field)
        return cwd
    for prefix in ("${PLUGIN_ROOT}", "${PLUGIN_DATA}"):
        if cwd == prefix:
            return cwd
        marker = prefix + "/"
        if cwd.startswith(marker):
            _safe_relative_parts(cwd[len(marker):], field)
            return cwd
    fail(f"{field} must be ./relative, ${{PLUGIN_ROOT}}[/...], or ${{PLUGIN_DATA}}[/...]")


def _normalize_provenance(server: str, value: Any, *, transport: str) -> dict[str, str]:
    field = f"mcpServers.{server}.provenance"
    if not isinstance(value, dict):
        fail(f"{field} must be an object")
    allowed = {"kind", "owner", "source", "purpose", "reviewed", "legacyReason"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        fail(f"{field} has unknown fields: {', '.join(unknown)}")
    kind = _nonempty(value.get("kind"), f"{field}.kind")
    if kind not in {"official", "community", "local"}:
        fail(f"{field}.kind must be official, community, or local")
    reviewed = _nonempty(value.get("reviewed"), f"{field}.reviewed")
    try:
        date.fromisoformat(reviewed)
    except ValueError:
        fail(f"{field}.reviewed must be YYYY-MM-DD")
    result = {
        "kind": kind,
        "owner": _nonempty(value.get("owner"), f"{field}.owner"),
        "source": _https_source(value.get("source"), f"{field}.source"),
        "purpose": _nonempty(value.get("purpose"), f"{field}.purpose"),
        "reviewed": reviewed,
    }
    legacy_reason = value.get("legacyReason")
    if transport == "sse":
        result["legacyReason"] = _nonempty(legacy_reason, f"{field}.legacyReason")
    elif legacy_reason is not None:
        fail(f"{field}.legacyReason is only valid for legacy sse transport")
    return result


def _normalize_stdio(server: str, value: dict[str, Any]) -> dict[str, Any]:
    field = f"mcpServers.{server}.config"
    allowed = {"type", "command", "args", "env", "cwd"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        fail(f"{field} has fields invalid for stdio: {', '.join(unknown)}")
    command = _nonempty(value.get("command"), f"{field}.command")
    if any(character.isspace() for character in command):
        fail(f"{field}.command must be one executable token, not a shell command")
    if command.startswith("./"):
        if command == "./":
            fail(f"{field}.command must name an executable")
        _safe_relative_parts(command[2:], f"{field}.command")
    elif "/" in command or "\\" in command:
        fail(f"{field}.command must be a bare executable or begin with ./")

    result: dict[str, Any] = {"type": "stdio", "command": command}
    args = value.get("args")
    if args is not None:
        if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
            fail(f"{field}.args must be a string array")
        result["args"] = args
    env = _normalize_env(value.get("env"), f"{field}.env")
    if env:
        result["env"] = env
    cwd = _normalize_cwd(value.get("cwd"), f"{field}.cwd")
    if cwd is not None:
        result["cwd"] = cwd
    return result


def _normalize_remote(server: str, value: dict[str, Any], transport: str) -> dict[str, Any]:
    field = f"mcpServers.{server}.config"
    allowed = {"type", "url", "headers"}
    unknown = sorted(set(value) - allowed)
    if unknown:
        fail(f"{field} has fields invalid for {transport}: {', '.join(unknown)}")
    result: dict[str, Any] = {
        "type": transport,
        "url": _remote_url(value.get("url"), f"{field}.url"),
    }
    headers = _normalize_headers(value.get("headers"), f"{field}.headers")
    if headers:
        result["headers"] = headers
    return result


def normalize_mcp_servers(value: Any) -> dict[str, dict[str, Any]]:
    """Normalize governed plugin-level MCP composition.

    Input entries carry both portable `config` and catalog-only `provenance`.
    Only `config` is emitted to Agent Plugins `mcp.json`.
    """
    if value is None:
        return {}
    if not isinstance(value, dict):
        fail("distribution.config.json mcpServers must be an object")

    normalized: dict[str, dict[str, Any]] = {}
    for server in sorted(value):
        if not isinstance(server, str) or not SERVER_NAME_RE.fullmatch(server):
            fail("mcpServers names must be lowercase kebab-case")
        entry = value[server]
        if not isinstance(entry, dict):
            fail(f"mcpServers.{server} must be an object")
        unknown = sorted(set(entry) - {"config", "provenance"})
        if unknown:
            fail(f"mcpServers.{server} has unknown fields: {', '.join(unknown)}")
        config = entry.get("config")
        if not isinstance(config, dict):
            fail(f"mcpServers.{server}.config must be an object")
        transport = config.get("type")
        if transport == "stdio":
            portable = _normalize_stdio(server, config)
        elif transport in {"streamable-http", "sse"}:
            portable = _normalize_remote(server, config, transport)
        else:
            fail(f"mcpServers.{server}.config.type must be stdio, streamable-http, or sse")
        provenance = _normalize_provenance(server, entry.get("provenance"), transport=transport)
        normalized[server] = {"config": portable, "provenance": provenance}
    return normalized


def mcp_manifest_from_distribution_config(config: dict[str, Any]) -> dict[str, Any] | None:
    servers = normalize_mcp_servers(config.get("mcpServers"))
    if not servers:
        return None
    return {
        "$schema": MCP_SCHEMA,
        "mcpServers": {name: entry["config"] for name, entry in servers.items()},
    }
