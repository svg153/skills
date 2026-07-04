---
name: community-pr-audit
description: "Trigger: community PR review, collaborador, external PR, outsider PR, comunidad. Evaluate external contributor PRs for security, injection, profile legitimacy, and code quality before merge."
license: MIT
metadata:
  author: svg153
  version: "1.2"
---

# Community PR Audit

Evaluate PRs from external collaborators or community contributors. Detect security issues, injection attempts, profile red flags, and code quality concerns.

## When to Use

- User says "revisar PR de comunidad", "review collaborator PR", "external PR", "analiza contribución"
- PR comes from a user who is NOT a regular maintainer (not svg153)
- You need a structured security + quality assessment before recommending merge

## Phase 1 — Contributor Profile Assessment

Before looking at code, assess the contributor:

| Signal | Safe | Suspicious |
|--------|------|------------|
| **GitHub stars** | >10k or established | <100, brand new |
| **Account age** | >6 months | <30 days |
| **Followers following ratio** | Balanced | 0 following / 5k+ followers (bot) |
| **Public repos** | Relevant to project | Empty, or spam/fork-only |
| **Commit history** | Consistent, meaningful messages | One massive commit, AI-generated messages |
| **Profile bio** | Describes relevant expertise | Generic, templated, or empty |
| **Email pattern** | `login@users.noreply.github.com` + real email | Disposable domains |
| **First contribution ever** | Could be legitimate beginner | First commit ever in a complex Go/Rust/TS project |

**Red flags requiring escalation:**
- Account created <30 days ago AND first PR in a non-trivial project
- Contributor forked and pushed directly without forking
- Contributor name differs from login (impersonation risk)
- Multiple PRs targeting different unrelated repos in short timeframe

## Phase 2 — Security Scan (Static Analysis)

For EVERY file changed in the PR, scan added/modified lines:

### Critical (block merge)
- **Eval/exec injection**: `eval()`, `exec()`, `new Function()`, `os.system()`, `subprocess(...shell=True)`, `template literals with user input`
- **Secret handling**: Hardcoded API keys, tokens, passwords, private keys
- **Path traversal**: `../` patterns that could escape intended directories without validation
- **SQL injection**: String concatenation in queries
- **Prototype pollution**: `obj[key] = value` with user-controlled key without sanitization
- **Remote code fetch**: Dynamic imports from URLs or domain-dependent module loading
- **Dependency poisoning**: New dependencies from non-npm/PyPI/rust crates registries
- **Shell metacharacters**: User input passed to `sh -c` or backticks without sanitization

### Warning (flag for review)
- **`chmod 0o000` or `rm -rf`** in cleanup tools — verify user confirmation flows
- **Symlink handling** — could cause symlink following attacks in traversal
- **Large diffs** (>15k chars) — harder to review, split recommendation
- **Changes to CI/CD files** — always suspicious from external contributors
- **Changes to authentication/authorization logic**

### Method
1. Read the diff (`gh pr diff <number>`)
2. For each changed file, read ONLY the added lines (lines starting with `+`)
3. Run the security checklist above against added lines
4. Read `matchFile`/`matchDirectory` or equivalent scanning logic to verify new categories actually work (not just registered)

## Phase 3 — Logic & Correctness Review

### Pattern Matching (from code-review skill)
- **Correctness**: Do the new categories actually match? Verify against the scanner logic — but DO NOT trust AI-generated claims about language behavior. Always verify with a real program. Load `language-quirks` skill for the Go `filepath.Ext()` case study.
- **Alternative paths**: What if the directory has nested items? What about symlinks? Permission errors?
- **Incoherences**: Does the display name match the key? Are there naming inconsistencies?
- **Boundary & safety**: Does size calculation handle nested directories correctly?

### Test Review
- **Are tests real?** Not just asserting "category exists" — they should verify the scanner actually finds the paths
- **Table-driven tests**: Preferred over single-test functions (per Go convention in most repos)
- **`t.TempDir()` used**: Filesystem tests must not operate on real home directories
- **Edge cases covered**: Empty directories, permission denied, symlinks, cycles

### Documentation
- README updated to match new functionality
- CONTRIBUTING.md changes don't contradict AGENTS.md

## Phase 4 — Report Output

Produce a structured report:

```markdown
## 📋 Report de PR — [Contributor] in [repo]

[PR #[N]] — [Title]
| **Branch** | `branch-name` |
| **Files** | `file1`, `file2` |
| **Impacto** | +X / -Y |

### ✅ Lo bueno
- [bullet points of what's correct]

### ⚠️ Para cambiar
- [bullet points of issues, missing tests]

### ❌ [CRITICAL/BLOCKER]
- [security issues or broken features that must be fixed]

**Veredicto:** ✅ Aprobable / ⚠️ Requiere cambios / 🔴 NO merger

---
```

### Overall Summary Table
| PR | Title | Risk | Action |
|---|---|---|---|
| #N | Title | 🟢/🟡/🔴 | Action |

**Seguridad:** Summary of any security findings.

## Phase 5 — Profile Summary Block

At the end of the full report, add:

```markdown
## 👤 Resumen del Colaborador

**Perfil:** [username] | [stars] | [account_age] | [public_repos]
**Contribuciones al repo:** [N] PRs abiertas, [M] merged
**Historial:** [brief assessment of quality, consistency, engagement]
**Recomendación:** [welcome continuation / monitor / caution]
```

## Execution Steps

1. `gh pr list` to get all open PRs
2. For each PR from non-maintainer: `gh pr view <number> --json title,body,files,commits,reviews`
3. `gh pr diff <number>` to get the actual code changes
4. Read the relevant source files (scanner logic, test helpers, category definitions)
5. Apply security scan (Phase 2) against added lines
6. Apply correctness review (Phase 3) against the project's scanning/matching logic
7. Assess contributor profile (Phase 1)
8. Produce report (Phase 4) with profile summary (Phase 5)

## Pitfalls

- **Don't trust AI claims about language behavior**: Copilot (and other LLMs) frequently confuse behavior between languages. The #1 case: Go's `filepath.Ext(".DS_Store")` returns `".DS_Store"`, NOT `""` (Python's `os.path.splitext` returns `""`). Always verify with a real program before flagging "broken" functionality. Load `language-quirks` skill for the full case study.
- **Tests only check registration**: A test that verifies "category appears in report" doesn't prove the scanner actually finds the files. Tests must verify `matchFile()`/`matchDirectory()` logic.
- **Copilot-reviewed doesn't mean correct**: Auto-reviews from Copilot are common — they often miss the actual scanning logic. They also hallucinate about language-specific behavior (see pitfall above).
- **`node_modules/.cache/bun` in body but not in code**: Contributors often describe files they plan to add but forgot in the diff.
- **Don't assume malicious intent**: Most external PRs are genuine contributions. Flag issues, don't assume sabotage. Escalate only when red flags cluster.

## Golden Rule — NEVER close PRs without merging

- **Always merge** (squash or normal) external PRs — never close them without merging first.
- If there are merge conflicts, resolve them locally then merge.
- Closing a PR without merging erases the contributor's credit from GitHub's contribution graph and commit history.
- Exception: only close without merge if explicitly told to do so, or if there's a real security risk (malware, injection).
