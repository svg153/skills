## Summary

Describe the user-visible or repository-level change and why it is needed.

## Ownership and provenance

- [ ] I identified affected skills as `LOCAL`, `CURATED_UPSTREAM`, or `MIRRORED_UPSTREAM`.
- [ ] Imported or derived content keeps accurate origin and license information.
- [ ] I did not edit generated distribution manifests as an independent source of truth.
- [ ] No secrets, customer data, private repository details, or sensitive exploit information are included.

## Validation

Run the checks relevant to the change:

```bash
python scripts/validate-workflow-security.py
python scripts/validate-skills.py
python scripts/validate-metadata-lifecycle.py
python skills/skill-publish/scripts/metadata_repair.py check
python scripts/generate-distribution.py --check
python scripts/validate-evals.py
DISABLE_TELEMETRY=1 npx -y skills@latest add . --list
```

- [ ] Canonical metadata/frontmatter validation passes.
- [ ] Generated surfaces are current.
- [ ] Client/discovery checks relevant to this change pass.
- [ ] High-impact behavior has appropriate deterministic or Waza coverage.

## Notes for reviewers

Call out compatibility risks, upstream assumptions, intentionally deferred work, or follow-up decisions.
