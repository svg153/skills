---
name: domain-manager-sync
description: 'Auto-update domain-manager skill from svg153/skills repo. Loads the latest SKILL.md and scripts from the repo before each run. Trigger: any domain management task — always sync first to get latest version.'
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# Domain Manager Sync

Auto-syncs the domain-manager skill from the svg153/skills GitHub repo before each run.

## How It Works

Before executing any domain management task:

1. **Sync the repo**: Pull latest changes from `svg153/skills`
2. **Verify symlink**: Ensure `/hermes-home/skills/domain-manager` points to the repo
3. **Proceed**: Execute the domain management task with latest code

## Sync Procedure

```bash
cd /root/workspace/svg153-skills && git pull origin main
```

The symlink at `/hermes-home/skills/domain-manager` → `/root/workspace/svg153-skills/skills/domain-manager` ensures Hermes always reads the latest version.

## When to Push Updates

After modifying the domain-manager skill:

1. Edit `SKILL.md` and/or `scripts/domain_manager.py`
2. Commit changes in the repo
3. Push to `svg153/skills`
4. The symlink picks up changes automatically

## Security Notes

- **Never commit API keys** — the `.gitignore` excludes secrets
- **Never expose credentials** in the SKILL.md or scripts output
- **Use environment variables** for all sensitive data
- **SKILL.md is public** — only include non-sensitive instructions

## Repo Structure

```
svg153-skills/
├── .gitignore          # Excludes secrets (*.env, *.key, hosts.yml)
├── skills/
│   └── domain-manager/
│       ├── SKILL.md    # Public instructions (no secrets)
│       └── scripts/
│           └── domain_manager.py  # Automation script
└── scripts/
    ├── check-updates.sh
    └── migrate-skills.sh
```

## Updating the Script

When `domain_manager.py` changes:

1. Edit `scripts/domain_manager.py` in the repo
2. Commit and push
3. The symlink is automatic — no restart needed

## Updating the SKILL.md

When instructions change:

1. Edit `SKILL.md` in the repo
2. Commit and push
3. Hermes reloads on next `skill_view` call
