---
title: Gentle-AI Ecosystem
description: Complete Gentle-AI setup: persona, Engram MCP, GGA pre-commit, SDD skills
---

# Gentle-AI Ecosystem

## When to Use

When setting up or configuring Gentle-AI ecosystem in a new project: persona installation, Engram MCP, GGA hooks, SDD skills.

## Prerequisites

- Hermes Agent installed
- GitHub CLI (`gh`) available
- Git configured

## Steps

1. **Install persona**: Copy SOUL.md to project root
2. **Configure Engram MCP**: Add engram server to config.yaml
3. **Install GGA**: Add .gga config and pre-commit hook
4. **Install SDD skills**: Copy SDD skill directories to .agents/skills/

## Pitfalls

- Engram MCP requires the engram binary to be installed and on PATH
- GGA pre-commit hook needs to be configured with the right AI provider
- SDD skills should be kept in sync with upstream gentle-ai repo

## Verification

```bash
# Check persona is loaded
cat SOUL.md | head -5

# Check Engram MCP is configured
cat .hermes/config.yaml | grep engram

# Check GGA is configured
cat .gga | head -5
```
