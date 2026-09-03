# Hermes integration

This directory contains the optional local-runtime integration for Hermes. It is deliberately outside `scripts/` because it does **not** participate in catalog provenance or upstream synchronization.

Direction:

```text
svg153/skills -> local Hermes runtime (/hermes-home/skills)
```

Use:

```bash
./integrations/hermes/sync-all.sh full
```

Override the runtime directory when needed:

```bash
HERMES_SKILLS=/custom/hermes/skills ./integrations/hermes/sync-all.sh symlink
```

The helper never overwrites a real directory at the target path and uses `git pull --ff-only`; it does not perform destructive resets.
