#!/usr/bin/env python3
"""
Domain Manager — Automatiza compra, DNS y configuración de dominios
para proyectos de svg153.

Soporta: Porkbun (compra + DNS) y Cloudflare (DNS + registrar).

Uso:
    python domain_manager.py check reclaimit.dev
    python domain_manager.py purchase reclaimit.dev --registrar porkbun
    python domain_manager.py dns add reclaimit.dev --type CNAME --name www --value svg153.github.io
    python domain_manager.py monitor --check-expiry
    python domain_manager.py github-config reclaimit --homepage https://reclaimit.dev

Requisitos:
    export PORKBUN_API_KEY=xxx
    export PORKBUN_SECRET_KEY=xxx
    export CLOUDFLARE_EMAIL=xxx
    export CLOUDFLARE_API_KEY=xxx
"""

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from typing import Optional

# GitHub Pages IPs
GITHUB_PAGES_IPS = [
    "185.199.108.153",
    "185.199.109.153",
    "185.199.110.153",
    "185.199.111.153",
]


# ─── Porkbun API ────────────────────────────────────────────────────────────

def porkbun_request(endpoint: str, payload: dict) -> dict:
    """Make a request to Porkbun API."""
    import requests

    api_key = os.environ.get("PORKBUN_API_KEY", "")
    secret_key = os.environ.get("PORKBUN_SECRET_KEY", "")

    if not api_key or not secret_key:
        return {"error": "PORKBUN_API_KEY and PORKBUN_SECRET_KEY env vars required"}

    payload["apikey"] = api_key
    payload["secretapikey"] = secret_key

    resp = requests.post(
        f"https://api.porkbun.com/api/json{endpoint}",
        json=payload,
        timeout=30,
    )
    return resp.json()


def check_domain_porkbun(domain: str) -> dict:
    """Check if a domain is available via Porkbun."""
    result = porkbun_request("/v3/domain/check", {"domain": domain})
    return result


def purchase_domain_porkbun(domain: str, years: int = 1) -> dict:
    """Purchase a domain via Porkbun."""
    price_result = porkbun_request(
        "/v3/domain/register",
        {
            "domain": domain,
            "renewals": "false",
            "period": years,
            "privacy": "false",  # Cloudflare handles SSL
        },
    )
    return price_result


def get_domains_porkbun() -> dict:
    """List all domains registered via Porkbun."""
    return porkbun_request("/v3/domain", {})


def set_nameservers_porkbun(domain: str, nameservers: list) -> dict:
    """Set nameservers for a domain."""
    return porkbun_request(
        "/v3/domain/editnameservers",
        {"domain": domain, "nameservers": nameservers},
    )


# ─── Cloudflare DNS ─────────────────────────────────────────────────────────

def cloudflare_request(method: str, endpoint: str, json_data: Optional[dict] = None) -> dict:
    """Make a request to Cloudflare API."""
    import requests

    email = os.environ.get("CLOUDFLARE_EMAIL", "")
    api_key = os.environ.get("CLOUDFLARE_API_KEY", "")

    if not email or not api_key:
        return {"error": "CLOUDFLARE_EMAIL and CLOUDFLARE_API_KEY env vars required"}

    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": api_key,
        "Content-Type": "application/json",
    }

    url = f"https://api.cloudflare.com/client/v4/zones{endpoint}"

    resp = requests.request(method, url, json=json_data, headers=headers, timeout=30)
    return resp.json()


def get_cloudflare_zone(domain: str) -> Optional[dict]:
    """Find the Cloudflare zone for a domain."""
    import requests

    email = os.environ.get("CLOUDFLARE_EMAIL", "")
    api_key = os.environ.get("CLOUDFLARE_API_KEY", "")

    headers = {
        "X-Auth-Email": email,
        "X-Auth-Key": api_key,
    }

    resp = requests.get(
        "https://api.cloudflare.com/client/v4/zones",
        params={"name": domain},
        headers=headers,
        timeout=30,
    )
    data = resp.json()
    if data.get("success") and data.get("result"):
        return data["result"][0]
    return None


def add_cloudflare_record(zone_id: str, record: dict) -> dict:
    """Add a DNS record in Cloudflare."""
    return cloudflare_request(
        "POST",
        f"/zones/{zone_id}/dns_records",
        record,
    )


def list_cloudflare_records(zone_id: str) -> dict:
    """List DNS records for a zone."""
    return cloudflare_request(
        "GET",
        f"/zones/{zone_id}/dns_records",
    )


def delete_cloudflare_record(zone_id: str, record_id: str) -> dict:
    """Delete a DNS record in Cloudflare."""
    return cloudflare_request(
        "DELETE",
        f"/zones/{zone_id}/dns_records/{record_id}",
    )


# ─── GitHub API ──────────────────────────────────────────────────────────────

def github_request(method: str, endpoint: str, json_data: Optional[dict] = None) -> dict:
    """Make a request to GitHub API."""
    import requests

    token = os.environ.get("GITHUB_TOKEN", "")
    if not token:
        token = os.environ.get("GH_TOKEN", "")

    if not token:
        return {"error": "GITHUB_TOKEN env var required"}

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
    }

    url = f"https://api.github.com{endpoint}"

    resp = requests.request(method, url, json=json_data, headers=headers, timeout=30)
    return resp.json()


def update_github_repo(repo: str, data: dict) -> dict:
    """Update a GitHub repository's settings."""
    return github_request("PATCH", f"/repos/svg153/{repo}", data)


def get_github_repo(repo: str) -> dict:
    """Get GitHub repository info."""
    return github_request("GET", f"/repos/svg153/{repo}")


# ─── Actions ─────────────────────────────────────────────────────────────────

def action_check(args):
    """Check domain availability."""
    print(f"🔍 Checking availability of '{args.domain}'...")

    # Try Porkbun first
    result = check_domain_porkbun(args.domain)

    if "error" in result:
        print(f"  ⚠️  Porkbun check failed: {result['error']}")
        return

    if result.get("status") == "AVAILABLE":
        print(f"  ✅ '{args.domain}' is AVAILABLE!")

        # Show price
        price = purchase_domain_porkbun(args.domain)
        if "results" in price and "prices" in price["results"]:
            for p in price["results"]["prices"]:
                if p.get("tld") == args.domain.split(".")[-1]:
                    print(f"  💰 Price: ${p.get('price', 'N/A')}/year")
    elif result.get("status") == "REGISTERED":
        print(f"  ❌ '{args.domain}' is already registered.")
    else:
        print(f"  ⚠️  Status: {result.get('status', 'unknown')}")
        print(f"  Response: {json.dumps(result, indent=2)}")


def action_purchase(args):
    """Purchase a domain."""
    print(f"🛒 Purchasing '{args.domain}' via {args.registrar}...")

    if args.registrar == "porkbun":
        result = purchase_domain_porkbun(args.domain, args.years)

        if result.get("success"):
            print(f"  ✅ Domain '{args.domain}' purchased successfully!")
            print(f"  📋 Transaction ID: {result.get('transaction', {}).get('id', 'N/A')}")
        else:
            print(f"  ❌ Purchase failed: {result.get('message', 'Unknown error')}")
            print(f"  Response: {json.dumps(result, indent=2)}")
    else:
        print(f"  ⚠️  Registrar '{args.registrar}' not yet implemented.")


def action_dns_add(args):
    """Add a DNS record via Cloudflare."""
    zone = get_cloudflare_zone(args.domain)

    if not zone:
        print(f"  ❌ Zone not found for '{args.domain}' in Cloudflare.")
        print(f"  💡 First add the domain to Cloudflare dashboard, then retry.")
        return

    record = {
        "type": args.type,
        "name": args.name,
        "content": args.value,
        "ttl": args.ttl,
        "proxied": args.proxied,
    }

    result = add_cloudflare_record(zone["id"], record)

    if result.get("success"):
        print(f"  ✅ DNS record added:")
        print(f"     Type: {args.type}")
        print(f"     Name: {args.name}.{args.domain}")
        print(f"     Value: {args.value}")
        print(f"     TTL: {args.ttl}")
        print(f"     Proxied: {args.proxied}")
    else:
        print(f"  ❌ Failed: {result.get('errors', [{}])[0].get('message', 'Unknown error')}")


def action_dns_setup_github_pages(args):
    """Set up DNS records for GitHub Pages (CNAME + A records)."""
    zone = get_cloudflare_zone(args.domain)

    if not zone:
        print(f"  ❌ Zone not found for '{args.domain}' in Cloudflare.")
        return

    # Delete existing records to avoid duplicates
    existing = list_cloudflare_records(zone["id"])
    if existing.get("success"):
        for rec in existing["result"]:
            if rec["name"] in (args.name, "www", "@"):
                if rec["type"] in ("CNAME", "A"):
                    delete_cloudflare_record(zone["id"], rec["id"])
                    print(f"  🗑️  Deleted existing record: {rec['name']} {rec['type']}")

    # Add CNAME for www
    cname_result = add_cloudflare_record(zone["id"], {
        "type": "CNAME",
        "name": "www",
        "content": f"{args.name}.github.io",
        "ttl": 1,
        "proxied": True,
    })

    if cname_result.get("success"):
        print(f"  ✅ CNAME www → {args.name}.github.io")
    else:
        print(f"  ⚠️  CNAME failed: {cname_result.get('errors', [{}])[0].get('message', '')}")

    # Add A records for root
    for ip in GITHUB_PAGES_IPS:
        a_result = add_cloudflare_record(zone["id"], {
            "type": "A",
            "name": "@",
            "content": ip,
            "ttl": 1,
            "proxied": True,
        })
        if a_result.get("success"):
            print(f"  ✅ A record @{ip}")

    print(f"\n  📌 DNS propagation may take up to 48 hours.")
    print(f"  📌 Cloudflare proxy is enabled (SSL auto-provisioned).")


def action_dns_list(args):
    """List DNS records."""
    zone = get_cloudflare_zone(args.domain)

    if not zone:
        print(f"  ❌ Zone not found for '{args.domain}' in Cloudflare.")
        return

    result = list_cloudflare_records(zone["id"])

    if result.get("success"):
        print(f"  📋 DNS records for {args.domain}:\n")
        for rec in result["result"]:
            proxied = " 🔒" if rec.get("proxied") else ""
            print(f"    {rec['type']:5s}  {rec['name']:5s}  →  {rec['content']:20s}{proxied}")
    else:
        print(f"  ❌ Failed: {result.get('errors', [{}])[0].get('message', '')}")


def action_monitor(args):
    """Monitor domain expiry dates."""
    if args.registrar == "porkbun":
        result = get_domains_porkbun()

        if result.get("success"):
            print(f"  📋 Domains registered via Porkbun:\n")
            for domain in result.get("results", []):
                expiry = domain.get("expirationDate", "N/A")
                # Convert to readable format
                try:
                    expiry_dt = datetime.strptime(expiry, "%Y-%m-%d %H:%M:%S")
                    days_left = (expiry_dt - datetime.now(timezone.utc)).days
                    status = "✅" if days_left > 30 else "⚠️" if days_left > 7 else "🔴"
                    print(f"    {status}  {domain.get('domain', 'N/A'):30s}  Expires: {expiry}  ({days_left} days)")
                except (ValueError, TypeError):
                    print(f"    ⚠️  {domain.get('domain', 'N/A'):30s}  Expires: {expiry}")
        else:
            print(f"  ❌ Failed: {result.get('message', 'Unknown error')}")
    else:
        print(f"  ⚠️  Monitor not yet implemented for '{args.registrar}'.")


def action_github_config(args):
    """Update GitHub repository configuration."""
    repo_info = get_github_repo(args.repo)

    if "error" in repo_info:
        print(f"  ❌ Repo not found: {args.repo}")
        return

    update_data = {}
    if args.homepage:
        update_data["homepage"] = args.homepage
    if args.description:
        update_data["description"] = args.description
    if args.default_branch:
        update_data["default_branch"] = args.default_branch

    if not update_data:
        print(f"  ⚠️  No configuration options specified.")
        return

    result = update_github_repo(args.repo, update_data)

    if "full_name" in result:
        print(f"  ✅ Repository '{result['full_name']}' updated:")
        for key, value in update_data.items():
            print(f"     {key}: {value}")
    else:
        print(f"  ❌ Failed: {result.get('message', 'Unknown error')}")


def action_github_pages_setup(args):
    """Set up GitHub Pages for a repository."""
    # Get repo info
    repo_info = get_github_repo(args.repo)

    if "error" in repo_info:
        print(f"  ❌ Repo not found: {args.repo}")
        return

    # Enable GitHub Pages
    pages_data = {
        "source": {
            "branch": args.branch,
            "path": args.path,
        }
    }

    result = github_request(
        "PATCH",
        f"/repos/svg153/{args.repo}/pages",
        pages_data,
    )

    if result.get("status") in ("200", "201") or "html_url" in result:
        print(f"  ✅ GitHub Pages enabled for '{args.repo}'")
        if "html_url" in result:
            print(f"     URL: {result['html_url']}")
    else:
        print(f"  ⚠️  Pages status: {result.get('message', 'Check manually')}")
        print(f"  Response: {json.dumps(result, indent=2)}")


def action_full_setup(args):
    """Full setup: purchase domain + configure DNS + update GitHub."""
    print(f"🚀 Full setup for '{args.domain}' → '{args.repo}'")
    print(f"{'='*60}\n")

    # Step 1: Check availability
    print("1️⃣  Checking domain availability...")
    check_result = check_domain_porkbun(args.domain)
    if check_result.get("status") != "AVAILABLE":
        print(f"  ❌ Domain '{args.domain}' is not available!")
        if check_result.get("status") == "REGISTERED":
            print(f"  💡 Domain is already registered. Use 'dns-setup' instead.")
        return
    print(f"  ✅ Available!")

    # Step 2: Purchase
    print(f"\n2️⃣  Purchasing domain...")
    purchase_result = purchase_domain_porkbun(args.domain)
    if purchase_result.get("success"):
        print(f"  ✅ Purchased!")
    else:
        print(f"  ❌ Purchase failed: {purchase_result.get('message', '')}")
        return

    # Step 3: Wait for DNS propagation (simulated)
    print(f"\n3️⃣  Waiting for domain registration to propagate...")
    print(f"  ⏳ This may take a few minutes.")

    # Step 4: Setup DNS
    print(f"\n4️⃣  Setting up DNS records...")
    action_dns_setup_github_pages(args)

    # Step 5: Update GitHub
    print(f"\n5️⃣  Updating GitHub repository...")
    action_github_config(args)

    print(f"\n{'='*60}")
    print(f"✅ Full setup complete for '{args.domain}'!")
    print(f"  📌 DNS may take up to 48h to fully propagate.")
    print(f"  📌 Check https://{args.domain} after propagation.")


# ─── CLI ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Domain Manager — Automatiza compra y gestión de dominios",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s check reclaimit.dev
  %(prog)s purchase reclaimit.dev --registrar porkbun
  %(prog)s dns add reclaimit.dev --type CNAME --name www --value svg153.github.io
  %(prog)s dns-setup reclaimit.dev --name svg153
  %(prog)s dns-list reclaimit.dev
  %(prog)s monitor --registrar porkbun
  %(prog)s github-config reclaimit --homepage https://reclaimit.dev
  %(prog)s github-pages reclaimit --branch main --path /
  %(prog)s full-setup reclaimit.dev --repo reclaimit

Environment variables:
  PORKBUN_API_KEY, PORKBUN_SECRET_KEY  — Porkbun API credentials
  CLOUDFLARE_EMAIL, CLOUDFLARE_API_KEY  — Cloudflare API credentials
  GITHUB_TOKEN                          — GitHub API token
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # check
    check_parser = subparsers.add_parser("check", help="Check domain availability")
    check_parser.add_argument("domain", help="Domain to check (e.g., reclaimit.dev)")

    # purchase
    purchase_parser = subparsers.add_parser("purchase", help="Purchase a domain")
    purchase_parser.add_argument("domain", help="Domain to purchase")
    purchase_parser.add_argument(
        "--registrar", choices=["porkbun", "cloudflare"], default="porkbun"
    )
    purchase_parser.add_argument("--years", type=int, default=1, help="Years to register")

    # dns add
    dns_add_parser = subparsers.add_parser("dns", help="Manage DNS records")
    dns_add_parser.add_argument("domain", help="Domain name")
    dns_add_parser.add_argument("--type", required=True, help="DNS record type (A, CNAME, etc.)")
    dns_add_parser.add_argument("--name", required=True, help="Record name (@ or subdomain)")
    dns_add_parser.add_argument("--value", required=True, help="Record value")
    dns_add_parser.add_argument("--ttl", type=int, default=1, help="TTL in seconds (1=auto)")
    dns_add_parser.add_argument(
        "--proxied", action="store_true", default=True, help="Enable Cloudflare proxy"
    )

    # dns-setup
    dns_setup_parser = subparsers.add_parser(
        "dns-setup", help="Setup DNS for GitHub Pages (CNAME + A records)"
    )
    dns_setup_parser.add_argument("domain", help="Domain name")
    dns_setup_parser.add_argument(
        "--name", default="svg153", help="GitHub username (for CNAME target)"
    )

    # dns-list
    dns_list_parser = subparsers.add_parser("dns-list", help="List DNS records")
    dns_list_parser.add_argument("domain", help="Domain name")

    # monitor
    monitor_parser = subparsers.add_parser("monitor", help="Monitor domain expiry")
    monitor_parser.add_argument(
        "--registrar", choices=["porkbun", "cloudflare"], default="porkbun"
    )
    monitor_parser.add_argument(
        "--check-expiry", action="store_true", help="Check expiry dates"
    )

    # github-config
    gh_config_parser = subparsers.add_parser(
        "github-config", help="Update GitHub repository settings"
    )
    gh_config_parser.add_argument("repo", help="Repository name")
    gh_config_parser.add_argument("--homepage", help="Repository homepage URL")
    gh_config_parser.add_argument("--description", help="Repository description")
    gh_config_parser.add_argument("--default-branch", help="Default branch name")

    # github-pages
    gh_pages_parser = subparsers.add_parser(
        "github-pages", help="Enable/configure GitHub Pages"
    )
    gh_pages_parser.add_argument("repo", help="Repository name")
    gh_pages_parser.add_argument("--branch", default="main", help="Branch for Pages")
    gh_pages_parser.add_argument("--path", default="/", help="Path for Pages")

    # full-setup
    full_parser = subparsers.add_parser(
        "full-setup", help="Full setup: purchase + DNS + GitHub config"
    )
    full_parser.add_argument("domain", help="Domain to set up")
    full_parser.add_argument("--repo", required=True, help="GitHub repository name")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Dispatch
    commands = {
        "check": action_check,
        "purchase": action_purchase,
        "dns": action_dns_add,
        "dns-setup": action_dns_setup_github_pages,
        "dns-list": action_dns_list,
        "monitor": action_monitor,
        "github-config": action_github_config,
        "github-pages": action_github_pages_setup,
        "full-setup": action_full_setup,
    }

    handler = commands.get(args.command)
    if handler:
        handler(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
