# Skills Library

Centralized library of agent skills with origin tracking and upstream sync.

## Structure

Each skill directory contains:

```
skills/
├── SKILL.md          # Skill definition (prompt, instructions, workflow)
├── metadata.yaml     # Origin, category, status, sync config
├── templates/        # Reusable templates
├── scripts/          # Helper scripts
├── references/       # API docs, specs, examples
└── assets/           # Diagrams, images, configs
```

## Origin Tracking

Every skill MUST have a `metadata.yaml` with:

```yaml
name: skill-name
origin: https://github.com/original/repo
origin_path: path/to/skill
category: devops|github|software-development|mlops|...
status: active|deprecated|experimental
sync:
  enabled: true
  interval: weekly
  strategy: git-submodule|download|manual
```

## Adding a Skill

1. Create directory: `skills/<name>/`
2. Add `SKILL.md` with the skill definition
3. Add `metadata.yaml` with origin info
4. Add any supporting files
5. Submit PR

## Syncing with Upstream

When `sync.enabled: true`, the skill should be kept in sync with its origin:

```bash
# Pull latest from origin
./scripts/sync <skill-name>

# Check for updates
./scripts/check-updates
```

## Categories

| Category | Description |
|----------|-------------|
| `software-development` | Coding patterns, frameworks, workflows |
| `devops` | Docker, CI/CD, infrastructure |
| `github` | GitHub workflows, PRs, reviews |
| `mlops` | ML operations, model serving, training |
| `creative` | Design, art, content generation |
| `data-science` | Data analysis, notebooks, visualization |
| `research` | Academic research, paper discovery |
| `productivity` | Docs, presentations, spreadsheets |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
