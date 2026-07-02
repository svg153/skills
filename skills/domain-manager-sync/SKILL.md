---
name: repo-skills-sync
description: 'Auto-sync all skills from svg153/skills GitHub repo to Hermes. Before any task, pulls latest changes and verifies symlinks. Trigger: any task that might benefit from updated skills from the centralized repo.'
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# Repository Skills Sync

Synchronizes ALL skills from the `svg153/skills` GitHub repository to Hermes.

## How It Works

The repo at `github.com/svg153/skills` is the **single source of truth** for project skills.

Hermes skills directory (`/hermes-home/skills/`) uses **symlinks** to point to the repo.

Every skill in the repo is automatically symlinked to Hermes — no manual step needed.

```
svg153/skills/                          /hermes-home/skills/
├── .gitignore                          ├── branch-pr → ../../workspace/svg153-skills/skills/branch-pr
├── skills/                             ├── chained-pr → ...
│   ├── branch-pr/                      ├── cognitive-doc-design → ...
│   │   ├── SKILL.md                    ├── comment-writer → ...
│   │   └── metadata.yaml               ├── domain-manager → ...
│   ├── sdd-init/                       ├── gentle-ai-ecosystem → ...
│   │   ├── SKILL.md                    ├── go-testing → ...
│   │   └── metadata.yaml               ├── issue-creation → ...
│   ├── ... (24 skills total)           ├── judgment-day → ...
└── scripts/                            ├── sdd-apply → ...
    ├── sync-all.sh ← MAIN SYNC SCRIPT   ├── sdd-archive → ...
    ├── check-updates.sh                 ├── sdd-design → ...
    └── migrate-skills.sh                ├── sdd-explore → ...
                                         ├── sdd-init → ...
                                         ├── sdd-onboard → ...
                                         ├── sdd-propose → ...
                                         ├── sdd-spec → ...
                                         ├── sdd-tasks → ...
                                         ├── sdd-verify → ...
                                         ├── skill-creator → ...
                                         ├── skill-improver → ...
                                         ├── skill-registry → ...
                                         └── work-unit-commits → ...
```

## Quick Sync (Recommended)

Run the automated sync script before any task:

```bash
./scripts/sync-all.sh full
```

This does:
1. `git pull origin main` — fetch latest from remote
2. Create/update symlinks for ALL skills
3. Verify all SKILL.md files are accessible
4. List all skills with status

## Sync Modes

```bash
./scripts/sync-all.sh pull    # Only git pull
./scripts/sync-all.sh symlink # Only create/update symlinks
./scripts/sync-all.sh verify  # Verify all skills accessible
./scripts/sync-all.sh list    # List all skills with status
./scripts/sync-all.sh full    # All of the above (default)
```

## Adding New Skills to Sync

When adding a new skill to the repo:

1. Create skill folder in `skills/<name>/` with `SKILL.md`
2. Add `metadata.yaml` with origin info
3. Commit and push to `svg153/skills`
4. Run `./scripts/sync-all.sh full` — symlinks created automatically
5. Done — Hermes reads it automatically

## Removing Skills from Sync

To stop syncing a skill:

```bash
rm /hermes-home/skills/<name>
```

The skill stays in the repo (git history preserved), just no longer symlinked to Hermes.

## Handling Duplicate Removal

If a skill exists both as a symlink and as a local directory in a category
(e.g., `software-development/gentleman-ai/branch-pr`), the duplicate must be
removed to avoid ambiguous skill name errors:

```bash
# Find duplicates
find /hermes-home/skills -name "<skill-name>" -type d

# Remove the duplicate (keep the symlink)
rm -rf /hermes-home/skills/software-development/gentleman-ai/<skill-name>
```

This happened with: branch-pr, gentle-ai-ecosystem, issue-creation, skill-creator.

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

