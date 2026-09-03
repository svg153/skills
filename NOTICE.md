# Notices and licensing

`svg153/skills` is both an open-source project and an aggregation of independently authored Agent Skills. Inclusion in this catalog does **not** transfer copyright or replace an upstream license.

## License precedence

- The root [MIT license](LICENSE) covers repository-authored infrastructure, automation, documentation, and locally authored material unless a more specific license applies.
- Every skill's `SKILL.md` frontmatter is expected to declare its runtime license.
- Every skill's `metadata.yaml` records provenance and lifecycle ownership.
- `MIRRORED_UPSTREAM` and `CURATED_UPSTREAM` entries retain the licensing and attribution obligations of their source material. The root MIT license does not override them.
- A nested `LICENSE`, `COPYING`, `NOTICE`, or equivalent upstream file takes precedence for the content it covers.
- Generated distribution manifests describe the catalog; they do not claim ownership of third-party skill content.

## Provenance model

The catalog distinguishes three ownership modes:

| Mode | Meaning for authorship and licensing |
| --- | --- |
| `LOCAL` | Authored and maintained here. The skill's own license declaration controls. |
| `CURATED_UPSTREAM` | Adapted locally from an identified upstream. Upstream provenance and license obligations remain relevant. |
| `MIRRORED_UPSTREAM` | Payload is replaceable from an authoritative upstream release. Upstream authorship and license remain authoritative. |

For a specific skill, consult:

```text
skills/<name>/SKILL.md       runtime license and behavior
skills/<name>/metadata.yaml  origin, origin path/ref, and lifecycle authority
```

The public catalog at https://svg153.github.io/skills/ also exposes provenance information derived from those canonical files.

If licensing metadata appears incomplete or inconsistent, treat that as a catalog defect and report it before redistributing the affected skill.
