---
name: repo-skills-sync
description: 'Auto-sync all skills from svg153/skills GitHub repo to Hermes. Before any task, pulls latest changes and verifies symlinks. Trigger: any task that might benefit from updated skills from the centralized repo.'
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# Repository Skills Sync

Synchronizes all skills from the `svg153/skills` GitHub repository to Hermes.

## How It Works

The repo at `github.com/svg153/skills` is the **single source of truth** for project skills.

Hermes skills directory (`/hermes-home/skills/`) uses **symlinks** to point to the repo.

```
svg153/skills/                          /hermes-home/skills/
├── .gitignore                          ├── domain-manager → ../../workspace/svg153-skills/skills/domain-manager
├── skills/                             ├── domain-manager-sync → ...
│   ├── domain-manager/                 └── (any other synced skill)
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── domain_manager.py
│   ├── branch-pr/
│   │   ├── SKILL.md
│   │   └── metadata.yaml
│   └── ... (22+ skills)
└── scripts/
    ├── check-updates.sh
    └── migrate-skills.sh
```

## Sync Procedure

Before any task that could benefit from updated skills:

```bash
cd /root/workspace/svg153-skills && git pull origin main
```

## Adding New Skills to Sync

When adding a new skill to the repo:

1. Create skill folder in `skills/<name>/` with `SKILL.md`
2. Commit and push to `svg153/skills`
3. Create symlink: `ln -sf /root/workspace/svg153-skills/skills/<name> /hermes-home/skills/<name>`
4. Done — Hermes reads it automatically

## Removing Skills from Sync

To stop syncing a skill:

```bash
rm /hermes-home/skills/<name>
```

The skill stays in the repo (git history preserved), just no longer symlinked to Hermes.

## Security Rules

1. **NEVER commit API keys** — `.gitignore` excludes `*.env`, `*.key`, `hosts.yml`
2. **NEVER expose credentials** in SKILL.md or scripts output
3. **SKILL.md is public** — only non-sensitive instructions
4. **Use environment variables** for all sensitive data
5. **Scripts are public** — no hardcoded secrets, only env var references

## Repo Structure

```
svg153-skills/
├── .gitignore          # Excludes secrets (*.env, *.key, hosts.yml)
├── CONTRIBUTING.md
├── README.md
├── skills/
│   ├── domain-manager/
│   │   ├── SKILL.md
│   │   └── scripts/
│   │       └── domain_manager.py
│   ├── branch-pr/
│   │   ├── SKILL.md
│   │   └── metadata.yaml
│   ├── sdd-init/
│   │   ├── SKILL.md
│   │   └── metadata.yaml
│   └── ... (22+ skills total)
└── scripts/
    ├── check-updates.sh
    └── migrate-skills.sh
```

## Current Synced Skills

Run this to see which skills are currently symlinked:

```bash
ls -la /hermes-home/skills/ | grep "^l"
```

Each `l` (symlink) entry points to a skill in the repo that's active in Hermes.

## Updating Any Skill

To update any skill in the repo:

1. Edit the file in `/root/workspace/svg153-skills/skills/<name>/`
2. Commit and push: `git commit -m "fix: update <name> skill" && git push`
3. Symlink picks up changes automatically — no restart needed

## Pitfalls

1. **Symlink must be absolute** — relative symlinks break when Hermes changes working directory
2. **Git pull first** — always pull before assuming you have the latest skill version
3. **SKILL.md frontmatter** — name must match folder name, description 10-1024 chars
4. **Asset file sizes** — keep bundled assets under 5MB per file
5. **Script permissions** — ensure scripts are executable (`chmod +x`)

