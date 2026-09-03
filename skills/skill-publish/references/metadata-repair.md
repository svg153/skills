# Metadata lifecycle repair

`skill-publish` owns lifecycle registration and can also normalize legacy catalog metadata without inventing a second source of truth.

The repair command classifies existing entries from canonical state:

- catalog origin (`https://github.com/svg153/skills`) -> `LOCAL`;
- external origin + manual/local legacy strategy -> `CURATED_UPSTREAM`;
- valid `download + authoritative: upstream` -> `MIRRORED_UPSTREAM` and is left unchanged.

Preview without writes:

```bash
python skills/skill-publish/scripts/metadata_repair.py plan
```

Apply only the exact approved plan:

```bash
python skills/skill-publish/scripts/metadata_repair.py apply --approve <approval_hash>
```

Check for drift in CI:

```bash
python skills/skill-publish/scripts/metadata_repair.py check
python scripts/validate-metadata-lifecycle.py
```

Legacy `enabled: true + strategy: manual` is intentionally rejected after migration. Manual means curated local authority and therefore has no automatic sync cadence or channel.
