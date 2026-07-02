---
name: domain-manager
description: 'Automate domain purchase, DNS configuration, and GitHub Pages setup for projects. Uses Cloudflare Registrar (cheapest + DNS + SSL + CDN included). Trigger: managing domains, buying domains, configuring DNS, setting up custom domains for GitHub Pages.'
license: MIT
metadata:
  author: svg153
  version: "1.1"
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

## Registrar: Cloudflare Only

**Cloudflare Registrar** is the only registrar we use. Reasons:

- **Precio de coste** (sin markup): .dev $9.15/yr, .io $40/yr, .com $9.15/yr
- **Todo incluido**: registrar + DNS + SSL + CDN en un solo sitio
- **Totalmente automatizable** vía API REST
- **Interfaz web** para compra manual si se prefiere
- **Renovación automática** incluida

No se usa Porkbun ni ningún otro registrar. Cloudflare es más barato y más completo.

## Prerequisites

### Environment Variables (local use)

```bash
# Cloudflare (for DNS management + registrar)
export CLOUDFLARE_EMAIL="your@email.com"
export CLOUDFLARE_API_KEY="your-api-key"

# GitHub (for repo configuration)
export GITHUB_TOKEN="your-github-token"
```

### Python Dependencies

```bash
pip install requests
```

### Cloudflare Setup

1. Crear cuenta en cloudflare.com (gratis)
2. My Profile → API Tokens → Create Token
3. Usar el token predefinido "Edit Cloudflare DNS" (o crear uno personalizado con permisos: Zone DNS Edit + Zone Zone Read)
4. Guardar el token en `CLOUDFLARE_API_KEY`

## Usage

### Check Domain Availability

```bash
python3 scripts/domain_manager.py check reclaimit.dev
```

Uses RDAP WHOIS (free, no API key needed) to check if a domain is registered.

### Purchase a Domain

```bash
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
| `purchase <domain> --registrar cloudflare` | Purchase a domain via Cloudflare |
| `dns add <domain> --type <type> --name <name> --value <value>` | Add DNS record |
| `dns-setup <domain> --name <username>` | Setup DNS for GitHub Pages |
| `dns-list <domain>` | List DNS records (Cloudflare) |
| `monitor --registrar cloudflare` | Monitor domain expiry |
| `github-config <repo> --homepage <url>` | Update GitHub repo settings |
| `github-pages <repo> --branch <branch>` | Enable GitHub Pages |
| `full-setup <domain> --repo <name>` | Full pipeline: purchase + DNS + GitHub |

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
  CLOUDFLARE_EMAIL: ${{ secrets.CLOUDFLARE_EMAIL }}
  CLOUDFLARE_API_KEY: ${{ secrets.CLOUDFLARE_API_KEY }}
  GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

## Files

- `scripts/domain_manager.py` — Main automation script (595 lines)
- `SKILL.md` — This file

## Pitfalls

1. **RDAP rate limits**: Public WHOIS has rate limits. Use Cloudflare API for bulk checks.
2. **DNS propagation**: Can take up to 48 hours. Check with `dig` or online tools.
3. **GitHub Pages CNAME**: Must add a `CNAME` file in the repo root for GitHub to recognize the custom domain.
4. **SSL certificates**: Cloudflare provides free SSL automatically. No manual setup needed.
5. **Token from gh CLI**: The GitHub token lives in `/root/.config/gh/hosts.yml`. The script reads it from the `GITHUB_TOKEN` env var.
