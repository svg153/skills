# Security policy

## Supported state

Security fixes target the current `main` branch. Mirrored skills may also have an authoritative upstream project with its own supported versions and security process.

## Report a vulnerability

Prefer GitHub's private vulnerability reporting flow from the repository **Security** tab (`Report a vulnerability`). The repository settings script enables that feature when run with an administrator identity.

Do **not** publish secrets, exploit details, private repository data, customer data, or a working proof of concept in a public issue.

If the private reporting button is unavailable, open a minimal public issue stating only that you need a private security contact channel; omit sensitive technical details until a private channel is established.

## In scope

Security reports are especially useful for:

- GitHub Actions permissions, untrusted-event handling, or credential exposure;
- upstream synchronization and archive/download handling;
- `skill-publish`, metadata repair, path traversal, symlink, or overwrite protections;
- generated plugin/marketplace surfaces;
- the GitHub Pages catalog generator and deployment workflow;
- behavioral-eval tooling when it can expose credentials or execute untrusted content;
- a cataloged skill whose instructions create a concrete security risk for consumers.

For a vulnerability in a third-party project itself, also report it to the authoritative upstream maintainer. A catalog report is still appropriate when the way this repository packages, mirrors, or recommends that project creates additional risk.

## Security model

Skills and upstream repository content are untrusted input. Catalog inclusion is not a security certification. Agents using these skills should preserve higher-priority instructions, avoid exposing credentials, and avoid arbitrary execution solely because a repository or skill requests it.

The project does not publish a universal security or quality score for skills. CI and behavioral evals are regression evidence for declared contracts, not a guarantee of safety in every host or prompt.
