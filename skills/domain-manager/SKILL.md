---
name: domain-manager
description: 'Automate domain purchase, DNS configuration, and GitHub Pages setup for projects. Supports Porkbun and Cloudflare registrars. Trigger: managing domains, buying domains, configuring DNS, setting up custom domains for GitHub Pages.'
license: MIT
metadata:
  author: svg153
  version: "1.0"
---

# Domain Manager

Automates domain purchase, DNS configuration, and GitHub Pages setup for projects.

## When to Use

Use this skill when:
- Buying a new domain for a project (e.g., `projectname.dev`)
- Configuring DNS records for GitHub Pages
- Setting up a custom domain with GitHub Pages
- Monitoring domain expiry dates
- Managing multiple project domains

## Critical Security Rules

1. **NEVER hardcode API keys** — always use environment variables
2. **NEVER commit secrets** — the `.gitignore` in this repo excludes `*.env` files
3. **NEVER expose credentials** in logs, error messages, or shared output
4. **Store API keys in GitHub Secrets** for CI/CD usage
5. **Use read-only checks** when possible (RDAP WHOIS) before API calls

## Prerequisites

### Environment Variables (local use)

```bash
# Porkbun (for purchasing domains)
export PORKBUN_API_KEY="your-api-key"
export PORKBUN_SECRET_KEY="your-secret-key"

# Cloudflare (for DNS management)
export CLOUDFLARE_EMAIL="your@email.com"
export CLOUDFLARE_API_KEY="your-api-key"

# GitHub (for repo configuration)
export GITHUB_TOKEN="your-github-token"
```

### Python Dependencies

```bash
pip install requests
```

## Usage

### Check Domain Availability

```bash
python3 scripts/domain_manager.py check reclaimit.dev
```

Uses RDAP WHOIS (free, no API key needed) to check if a domain is registered.

### Purchase a Domain

```bash
# Via Porkbun
python3 scripts/domain_manager.py purchase reclaimit.dev --registrar porkbun

# Via Cloudflare Registrar
python3 scripts/domain_manager.py purchase reclaimit.dev --registrar cloudflare
```

### Setup DNS for GitHub Pages

```bash
python3 scripts/domain_manager.py dns-setup reclaimit.dev --name svg153
```

Creates these DNS records:
- `CNAME www → svg153.github.io`
- `A @ → 185.199.108.153` (GitHub Pages IPs)
- `A @ → 185.199.109.153`
- `A @ → 185.199.110.153`
- `A @ → 185.199.111.153`

### Update GitHub Repository Settings

```bash
python3 scripts/domain_manager.py github-config reclaimit --homepage "https://reclaimit.dev"
```

### Full Setup (Purchase + DNS + GitHub)

```bash
python3 scripts/domain_manager.py full-setup reclaimit.dev --repo reclaimit
```

## Available Commands

| Command | Description |
|---------|-------------|
| `check <domain>` | Check if domain is available (RDAP WHOIS) |
| `purchase <domain> --registrar porkbun\|cloudflare` | Purchase a domain |
| `dns add <domain> --type <type> --name <name> --value <value>` | Add DNS record |
| `dns-setup <domain> --name <username>` | Setup DNS for GitHub Pages |
| `dns-list <domain>` | List DNS records (Cloudflare) |
| `monitor --registrar porkbun\|cloudflare` | Monitor domain expiry |
| `github-config <repo> --homepage <url>` | Update GitHub repo settings |
| `github-pages <repo> --branch <branch>` | Enable GitHub Pages |
| `full-setup <domain> --repo <name>` | Full pipeline: purchase + DNS + GitHub |

## Registrar Comparison

| Feature | Porkbun | Cloudflare |
|---------|---------|------------|
| .dev price | $10.49/yr | $9.15/yr |
| .io price | $40.99/yr | $40.00/yr |
| .com price | $9.19/yr | $9.15/yr |
| DNS included | Basic | Full (Cloudflare DNS) |
| SSL included | No | Yes (free) |
| CDN included | No | Yes (free) |
| API quality | Excellent | Excellent |
| Best for | Simple purchases | Full stack (DNS+SSL+CDN) |

**Recommendation**: Cloudflare Registrar for best value (cheapest + DNS + SSL + CDN all included).

## GitHub Pages DNS Records

For any custom domain pointing to GitHub Pages:

```
Type    Name    Value
─────   ────    ─────
CNAME   www     <username>.github.io
A       @       185.199.108.153
A       @       185.199.109.153
A       @       185.199.110.153
A       @       185.199.111.153
```

## CI/CD Integration

For automated domain management in GitHub Actions:

```yaml
env:
  PORKBUN_API_KEY: ${{ secrets.PORKBUN_API_KEY }}
  PORKBUN_SECRET_KEY: ${{ secrets.PORKBUN_SECRET_KEY }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Files

- `scripts/domain_manager.py` — Main automation script (595 lines)
- `SKILL.md` — This file

## Pitfalls

1. **RDAP rate limits**: Public WHOIS has rate limits. Use Porkbun/Cloudflare API for bulk checks.
2. **DNS propagation**: Can take up to 48 hours. Check with `dig` or online tools.
3. **GitHub Pages CNAME**: Must add a `CNAME` file in the repo root for GitHub to recognize the custom domain.
4. **SSL certificates**: Cloudflare provides free SSL. Porkbun does not — need Let's Encrypt or similar.
5. **Token from gh CLI**: The GitHub token lives in `/root/.config/gh/hosts.yml`. The script reads it from the `GITHUB_TOKEN` env var.
