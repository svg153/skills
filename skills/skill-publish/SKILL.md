---
name: skill-publish
description: "Trigger: new skill, create skill, add skill, publish skill. Create a skill in svg153/skills repo and sync to Hermes automatically. Trigger: creating a new skill that should be available in Hermes."
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# Skill Publish — Create, Commit, and Sync

Creates a new skill in the `svg153/skills` repo and automatically syncs it to Hermes via symlink.

## When to Use

When you create a new skill and want it available in Hermes immediately:
- User asks you to create a skill
- You identify a reusable pattern worth saving
- You're documenting a new workflow

## How It Works

The skill is created in the repo at `/root/workspace/svg153-skills/skills/<name>/` and symlinked to `/hermes-home/skills/<name>/`.

```
svg153/skills/                          /hermes-home/skills/
├── skills/                             ├── skill-name → ../../workspace/svg153-skills/skills/skill-name
│   └── skill-name/                     └── (symlink, no copy)
│       ├── SKILL.md                    (reads from repo)
│       └── metadata.yaml
└── scripts/
    └── sync-all.sh
```

## Execution Steps

### 1. Validate the skill name

```bash
name="<skill-name>"
repo_dir="/root/workspace/svg153-skills/skills/$name"
hermes_link="/hermes-home/skills/$name"

# Check if skill already exists
if [ -d "$repo_dir" ]; then
    echo "ERROR: skill '$name' already exists in repo"
    exit 1
fi
if [ -e "$hermes_link" ]; then
    echo "ERROR: skill '$name' already exists in Hermes"
    exit 1
fi
```

### 2. Create the skill in the repo

```bash
mkdir -p "$repo_dir"

# Create SKILL.md with frontmatter
cat > "$repo_dir/SKILL.md" << 'SKILL_EOF'
---
name: {skill-name}
description: "Trigger: {trigger words}. {What this skill does}."
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# {Skill Title}

{Skill content here — see skill-creator for formatting rules.}
SKILL_EOF

# Create metadata.yaml
cat > "$repo_dir/metadata.yaml" << EOF
name: $name
origin: https://github.com/svg153/skills
origin_path: /skills/$name
category: {category}
status: active
sync:
  enabled: true
  interval: weekly
  strategy: manual
tags:
  - {tag1}
  - {tag2}
EOF
```

### 3. Add supporting directories (if needed)

```bash
# Optional directories — create only if needed:
mkdir -p "$repo_dir/assets"      # templates, schemas, examples
mkdir -p "$repo_dir/references"  # links to local docs
mkdir -p "$repo_dir/scripts"     # helper scripts
```

### 4. Commit and push

```bash
cd /root/workspace/svg153-skills
git add -A
git commit -m "feat: add $name skill"
git push origin main
```

### 5. Sync to Hermes

```bash
cd /root/workspace/svg153-skills
./scripts/sync-all.sh full
```

This creates the symlink and verifies everything works.

### 6. Verify

```bash
# Check symlink exists
ls -la /hermes-home/skills/$name

# Check SKILL.md is readable
cat /hermes-home/skills/$name/SKILL.md | head -10

# Test loading with skill_view
# (call skill_view(name=$name) to verify)
```

## One-Liner (when you know the name and content)

```bash
name="my-skill"
repo_dir="/root/workspace/svg153-skills/skills/$name"
hermes_link="/hermes-home/skills/$name"

# Create
mkdir -p "$repo_dir"
cat > "$repo_dir/SKILL.md" << 'EOF'
---
name: my-skill
description: "Trigger: my-skill. Does something useful."
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# My Skill

Content here.
EOF
cat > "$repo_dir/metadata.yaml" << EOF
name: $name
origin: https://github.com/svg153/skills
origin_path: /skills/$name
category: software-development
status: active
sync:
  enabled: true
  interval: weekly
  strategy: manual
tags:
  - my-skill
EOF

# Commit + push + sync
cd /root/workspace/svg153-skills
git add -A && git commit -m "feat: add $name skill" && git push origin main
./scripts/sync-all.sh full
```

## Pitfalls

1. **Skill name must be lowercase with hyphens** — no spaces, no underscores preferred
2. **Description must be one line** — 10-250 chars, include trigger words
3. **Always commit to svg153/skills** — not to any other repo
4. **Sync after push** — the symlink points to the local clone, but the remote is the source of truth
5. **Don't create duplicate skills** — check both repo and Hermes before creating
6. **If skill already exists as local dir** — remove the local dir first, then create symlink

## Updating an Existing Skill

If the skill already exists in the repo:

```bash
# 1. Edit the skill in the repo
# /root/workspace/svg153-skills/skills/<name>/SKILL.md

# 2. Commit + push
cd /root/workspace/svg153-skills
git add -A && git commit -m "fix: update <name> skill" && git push origin main

# 3. No need to sync — symlink already exists and points to the repo
```

The symlink picks up changes automatically.
