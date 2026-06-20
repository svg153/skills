# Contributing to Skills Library

## Adding a New Skill

1. **Create directory**: `skills/<skill-name>/`
2. **SKILL.md**: Write the skill definition following the template
3. **metadata.yaml**: Fill in origin, category, status, sync config
4. **Supporting files**: Add templates, scripts, references as needed
5. **Submit PR**

## SKILL.md Format

```markdown
---
title: Skill Title
description: One-line description
---

# Skill Title

## When to Use

Trigger conditions for this skill.

## Prerequisites

Tools or setup required.

## Steps

1. First step
2. Second step
3. ...

## Pitfalls

Common issues and workarounds.

## Verification

How to confirm the skill worked.
```

## metadata.yaml Format

```yaml
name: skill-name
origin: https://github.com/author/repo
origin_path: path/to/skill
category: software-development
status: active
sync:
  enabled: true
  interval: weekly
  strategy: manual
tags:
  - go
  - testing
```

## Sync Strategies

- **`manual`**: Review and update manually when needed
- **`download`**: Script downloads from origin URL
- **`git-submodule`**: Git submodule pointing to origin

## Category Guidelines

- Pick the **most specific** category
- A skill can only belong to **one** category
- If unsure, use `software-development`

## Review Criteria

- [ ] SKILL.md follows the template format
- [ ] metadata.yaml is complete and accurate
- [ ] Origin URL is correct and accessible
- [ ] No duplicate skills exist
- [ ] Supporting files are relevant and useful
