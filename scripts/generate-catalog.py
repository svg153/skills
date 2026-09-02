#!/usr/bin/env python3
"""Build the public skills catalog from canonical repository metadata."""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / "skills"
GROUPS_PATH = ROOT / "skills.sh.json"
DEFAULT_OUTPUT = ROOT / "_site"
HREF_RE = re.compile(r"href=[\"']([^\"']+)[\"']")


def fail(message: str) -> "NoReturn":
    raise SystemExit(f"ERROR: {message}")


def load_yaml(path: Path) -> dict:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError) as exc:
        fail(f"{path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)}: expected a YAML mapping")
    return value


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{path.relative_to(ROOT)}: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)}: expected a JSON object")
    return value


def frontmatter(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        fail(f"{path.relative_to(ROOT)}: missing YAML frontmatter")
    parts = text.split("---\n", 2)
    if len(parts) < 3:
        fail(f"{path.relative_to(ROOT)}: missing closing YAML frontmatter delimiter")
    try:
        value = yaml.safe_load(parts[1])
    except yaml.YAMLError as exc:
        fail(f"{path.relative_to(ROOT)}: invalid YAML frontmatter: {exc}")
    if not isinstance(value, dict):
        fail(f"{path.relative_to(ROOT)}: frontmatter must be a mapping")
    return value


def normalized_origin(origin: str) -> str:
    return origin[:-1] if origin.endswith("/") else origin


def ownership(metadata: dict) -> str:
    sync = metadata.get("sync") if isinstance(metadata.get("sync"), dict) else {}
    strategy = str(sync.get("strategy", "manual"))
    authority = str(sync.get("authoritative", ""))
    origin = str(metadata.get("origin", ""))
    if strategy == "local":
        return "Local"
    if strategy == "download" and authority == "upstream":
        return "Mirrored upstream"
    if origin and normalized_origin(origin) != "https://github.com/svg153/skills":
        return "Curated upstream"
    return "Local catalog"


def load_groups() -> tuple[dict[str, dict], list[dict]]:
    config = load_json(GROUPS_PATH)
    membership: dict[str, dict] = {}
    groups = config.get("groupings", [])
    if not isinstance(groups, list):
        fail("skills.sh.json: groupings must be an array")
    normalized: list[dict] = []
    for index, group in enumerate(groups):
        if not isinstance(group, dict):
            fail(f"skills.sh.json: grouping {index} must be an object")
        title = str(group.get("title", "")).strip()
        description = str(group.get("description", "")).strip()
        names = group.get("skills", [])
        if not title or not isinstance(names, list):
            fail(f"skills.sh.json: grouping {index} requires title and skills")
        item = {"title": title, "description": description, "skills": [str(name) for name in names]}
        normalized.append(item)
        for name in item["skills"]:
            if name in membership:
                fail(f"skills.sh.json: {name!r} appears in more than one grouping")
            membership[name] = item
    return membership, normalized


def discover() -> tuple[list[dict], list[dict]]:
    membership, groups = load_groups()
    entries: list[dict] = []
    seen_runtime: set[str] = set()
    for directory in sorted(SKILLS.iterdir(), key=lambda p: p.name.casefold()):
        if not directory.is_dir():
            continue
        metadata_path = directory / "metadata.yaml"
        skill_path = directory / "SKILL.md"
        if not metadata_path.is_file() or not skill_path.is_file():
            fail(f"{directory.relative_to(ROOT)}: SKILL.md and metadata.yaml are required")
        meta = load_yaml(metadata_path)
        fm = frontmatter(skill_path)
        catalog_name = directory.name
        if meta.get("name") != catalog_name:
            fail(f"{metadata_path.relative_to(ROOT)}: name must equal {catalog_name!r}")
        runtime_name = str(fm.get("name", "")).strip()
        description = str(fm.get("description", "")).strip()
        if not runtime_name or not description:
            fail(f"{skill_path.relative_to(ROOT)}: name and description are required")
        runtime_key = runtime_name.casefold()
        if runtime_key in seen_runtime:
            fail(f"{skill_path.relative_to(ROOT)}: duplicate runtime skill name {runtime_name!r}")
        seen_runtime.add(runtime_key)
        category = str(meta.get("category", "other")).strip() or "other"
        group = membership.get(catalog_name)
        group_title = group["title"] if group else category.replace("-", " ").title()
        sync = meta.get("sync") if isinstance(meta.get("sync"), dict) else {}
        origin = str(meta.get("origin", "")).strip()
        tags = meta.get("tags", [])
        if not isinstance(tags, list):
            fail(f"{metadata_path.relative_to(ROOT)}: tags must be a list")
        entries.append({
            "catalogName": catalog_name,
            "runtimeName": runtime_name,
            "description": description,
            "category": category,
            "group": group_title,
            "status": str(meta.get("status", "unknown")),
            "origin": origin,
            "originPath": str(meta.get("origin_path", "")),
            "originRef": str(meta.get("origin_ref", "")),
            "ownership": ownership(meta),
            "sync": {
                "enabled": bool(sync.get("enabled", False)),
                "interval": str(sync.get("interval", "manual")),
                "strategy": str(sync.get("strategy", "manual")),
                "authoritative": str(sync.get("authoritative", "")),
                "channel": str(sync.get("channel", "")),
            },
            "tags": [str(tag) for tag in tags],
            "apm": (directory / "apm.yml").is_file(),
            "source": f"https://github.com/svg153/skills/tree/main/skills/{catalog_name}",
        })
    names = {entry["catalogName"] for entry in entries}
    unknown_grouped = sorted(set(membership) - names)
    if unknown_grouped:
        fail(f"skills.sh.json references missing catalog entries: {', '.join(unknown_grouped)}")
    return entries, groups


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)


def shell(title: str, body: str, prefix: str = ".") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="dark light">
  <title>{esc(title)} · SVG153 Skills</title>
  <meta name="description" content="Provenance-aware cross-agent Agent Skills catalog.">
  <link rel="stylesheet" href="{prefix}/assets/catalog.css">
</head>
<body>
  <header class="topbar">
    <a class="brand" href="{prefix}/">SVG153 Skills</a>
    <nav>
      <a href="{prefix}/">Catalog</a>
      <a href="{prefix}/catalog.json">JSON</a>
      <a href="https://github.com/svg153/skills">GitHub</a>
    </nav>
  </header>
  <main>{body}</main>
  <footer>Generated from <code>skills/</code>, <code>metadata.yaml</code> and <code>skills.sh.json</code>. Provenance is part of the product, not an afterthought.</footer>
</body>
</html>
"""


def badge(text: str, kind: str = "") -> str:
    suffix = f" {esc(kind)}" if kind else ""
    return f'<span class="badge{suffix}">{esc(text)}</span>'


def render_index(entries: list[dict]) -> str:
    local_count = sum(1 for item in entries if item["ownership"].startswith("Local"))
    mirrored_count = sum(1 for item in entries if item["ownership"] == "Mirrored upstream")
    apm_count = sum(1 for item in entries if item["apm"])
    options = ['<option value="">All groups</option>']
    options.extend(f'<option value="{esc(group)}">{esc(group)}</option>' for group in sorted({item["group"] for item in entries}))
    cards: list[str] = []
    for item in entries:
        search = " ".join([item["catalogName"], item["runtimeName"], item["description"], item["category"], item["group"], item["ownership"], " ".join(item["tags"])]).casefold()
        runtime = f'<div class="runtime">runtime: <code>{esc(item["runtimeName"])}</code></div>' if item["runtimeName"] != item["catalogName"] else ""
        apm = badge("APM", "accent") if item["apm"] else ""
        cards.append(f"""
<article class="card" data-search="{esc(search)}" data-group="{esc(item['group'])}">
  <div class="card-meta">{badge(item['group'])}{badge(item['ownership'], 'ownership')}{apm}</div>
  <h2><a href="./skills/{esc(item['catalogName'])}/">{esc(item['catalogName'])}</a></h2>
  {runtime}
  <p>{esc(item['description'])}</p>
  <div class="card-footer"><span>{esc(item['status'])}</span><span>{esc(item['sync']['strategy'])}</span></div>
</article>""")
    body = f"""
<section class="hero">
  <p class="eyebrow">Cross-agent · provenance-aware · reproducible</p>
  <h1>Skills you can install <em>and trace.</em></h1>
  <p class="lede">A public catalog of {len(entries)} Agent Skills. Every entry keeps its origin, ownership and synchronization policy visible so mirrored work is never confused with local authorship.</p>
  <div class="stats">
    <div><strong>{len(entries)}</strong><span>skills</span></div>
    <div><strong>{local_count}</strong><span>local</span></div>
    <div><strong>{mirrored_count}</strong><span>mirrored</span></div>
    <div><strong>{apm_count}</strong><span>APM packages</span></div>
  </div>
</section>
<section class="controls" aria-label="Catalog filters">
  <label><span>Search</span><input id="search" type="search" placeholder="GitHub, testing, publishing…" autocomplete="off"></label>
  <label><span>Group</span><select id="group">{''.join(options)}</select></label>
  <span id="count" class="result-count">{len(entries)} results</span>
</section>
<section id="catalog" class="grid">{''.join(cards)}</section>
<p id="empty" class="empty" hidden>No skills match those filters.</p>
<script>
const search = document.querySelector('#search');
const group = document.querySelector('#group');
const cards = [...document.querySelectorAll('.card')];
const count = document.querySelector('#count');
const empty = document.querySelector('#empty');
function filterCatalog() {{
  const q = search.value.trim().toLowerCase();
  const g = group.value;
  let visible = 0;
  for (const card of cards) {{
    const matches = (!q || card.dataset.search.includes(q)) && (!g || card.dataset.group === g);
    card.hidden = !matches;
    if (matches) visible++;
  }}
  count.textContent = `${{visible}} result${{visible === 1 ? '' : 's'}}`;
  empty.hidden = visible !== 0;
}}
search.addEventListener('input', filterCatalog);
group.addEventListener('change', filterCatalog);
</script>
"""
    return shell("Catalog", body)


def definition(label: str, value: str, raw: bool = False) -> str:
    if not value:
        return ""
    rendered = value if raw else esc(value)
    return f"<div><dt>{esc(label)}</dt><dd>{rendered}</dd></div>"


def render_detail(item: dict) -> str:
    sync = item["sync"]
    runtime = definition("Runtime name", f"<code>{esc(item['runtimeName'])}</code>", raw=True) if item["runtimeName"] != item["catalogName"] else ""
    origin_link = f'<a href="{esc(normalized_origin(item["origin"]))}">{esc(item["origin"])}</a>' if item["origin"] else ""
    source_link = f'<a href="{esc(item["source"])}">View catalog source</a>'
    install = f"npx skills@latest add svg153/skills --skill {item['catalogName']}"
    apm = f"""<section class="panel"><h2>Microsoft APM</h2><pre><code>apm install svg153/skills/skills/{esc(item['catalogName'])} --target agent-skills</code></pre></section>""" if item["apm"] else ""
    tags = "".join(badge(tag) for tag in item["tags"])
    body = f"""
<a class="back" href="../../">← Back to catalog</a>
<section class="detail-hero">
  <div class="card-meta">{badge(item['group'])}{badge(item['ownership'], 'ownership')}</div>
  <h1>{esc(item['catalogName'])}</h1>
  <p class="lede">{esc(item['description'])}</p>
  <div class="tag-row">{tags}</div>
</section>
<div class="detail-grid">
<section class="panel"><h2>Provenance</h2><dl>
  {definition("Ownership", item["ownership"])}
  {definition("Origin", origin_link, raw=True)}
  {definition("Origin path", item["originPath"])}
  {definition("Origin ref", item["originRef"])}
  {definition("Catalog source", source_link, raw=True)}
  {runtime}
</dl></section>
<section class="panel"><h2>Lifecycle</h2><dl>
  {definition("Status", item["status"])}
  {definition("Category", item["category"])}
  {definition("Strategy", sync["strategy"])}
  {definition("Authority", sync["authoritative"])}
  {definition("Interval", sync["interval"])}
  {definition("Channel", sync["channel"])}
</dl></section>
</div>
<section class="panel install"><h2>Install with skills CLI</h2><pre><code>{esc(install)}</code></pre><p>The repository also exposes generated cross-agent bundle manifests for compatible plugin hosts.</p></section>
{apm}
"""
    return shell(item["catalogName"], body, "../..")


CSS = """
:root{--bg:#0b0f14;--surface:#111820;--surface-2:#17212b;--text:#edf3f8;--muted:#9fb0bf;--line:#263542;--accent:#7dd3fc;--accent-2:#c4b5fd;--max:1180px}*{box-sizing:border-box}html{font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;background:var(--bg);color:var(--text)}body{margin:0;min-height:100vh;background:radial-gradient(circle at 75% -10%,#172a3d 0,transparent 34rem),var(--bg)}a{color:inherit;text-decoration-color:#557086;text-underline-offset:.2em}a:hover{color:var(--accent)}.topbar{max-width:var(--max);margin:auto;padding:1.2rem 1.5rem;display:flex;justify-content:space-between;gap:1rem;align-items:center;border-bottom:1px solid var(--line)}.brand{font-weight:800;text-decoration:none;letter-spacing:-.02em}nav{display:flex;gap:1rem;font-size:.92rem}main{max-width:var(--max);margin:auto;padding:3.5rem 1.5rem 5rem}.hero{max-width:850px}.eyebrow{color:var(--accent);text-transform:uppercase;letter-spacing:.12em;font-size:.75rem;font-weight:800}h1{font-size:clamp(2.4rem,7vw,5.6rem);line-height:.96;letter-spacing:-.055em;margin:.6rem 0 1.3rem}h1 em{color:var(--accent);font-style:normal}.lede{color:var(--muted);font-size:clamp(1.05rem,2vw,1.35rem);line-height:1.6}.stats{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:1px;background:var(--line);border:1px solid var(--line);border-radius:1rem;overflow:hidden;margin-top:2.2rem}.stats div{background:var(--surface);padding:1.1rem 1.25rem;display:flex;flex-direction:column}.stats strong{font-size:1.55rem}.stats span{color:var(--muted);font-size:.8rem}.controls{display:grid;grid-template-columns:minmax(0,2fr) minmax(12rem,1fr) auto;gap:1rem;align-items:end;margin:3.5rem 0 1.25rem}.controls label{display:flex;flex-direction:column;gap:.45rem;color:var(--muted);font-size:.78rem;font-weight:700}input,select{width:100%;border:1px solid var(--line);background:var(--surface);color:var(--text);border-radius:.7rem;padding:.8rem .9rem;font:inherit}input:focus,select:focus{outline:2px solid var(--accent);outline-offset:1px}.result-count{color:var(--muted);padding:.82rem 0;white-space:nowrap;font-size:.85rem}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:1rem}.card{border:1px solid var(--line);background:linear-gradient(180deg,var(--surface),#0f151c);border-radius:1rem;padding:1.25rem;min-height:15rem;display:flex;flex-direction:column}.card[hidden]{display:none}.card h2{margin:1rem 0 .5rem;font-size:1.2rem;word-break:break-word}.card h2 a{text-decoration:none}.card p{color:var(--muted);line-height:1.5;font-size:.9rem;flex:1}.card-meta,.tag-row{display:flex;gap:.4rem;flex-wrap:wrap}.badge{display:inline-flex;border:1px solid var(--line);border-radius:999px;padding:.28rem .55rem;color:var(--muted);background:var(--surface-2);font-size:.68rem;line-height:1}.badge.ownership{color:var(--accent)}.badge.accent{color:var(--accent-2)}.runtime{color:var(--muted);font-size:.75rem}.card-footer{display:flex;justify-content:space-between;color:#7890a3;font-size:.72rem;padding-top:.9rem;border-top:1px solid var(--line)}.empty{color:var(--muted);padding:3rem;text-align:center;border:1px dashed var(--line);border-radius:1rem}.back{color:var(--muted);text-decoration:none}.detail-hero{max-width:850px;margin:2.5rem 0}.detail-hero h1{font-size:clamp(2.3rem,6vw,4.6rem)}.detail-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:1rem}.panel{border:1px solid var(--line);background:var(--surface);border-radius:1rem;padding:1.35rem;margin:1rem 0;overflow:hidden}.panel h2{margin:0 0 1rem;font-size:1rem}.panel p{color:var(--muted);line-height:1.55}dl{margin:0}dl div{display:grid;grid-template-columns:8rem 1fr;gap:1rem;padding:.7rem 0;border-top:1px solid var(--line)}dl div:first-child{border-top:0}dt{color:var(--muted);font-size:.78rem}dd{margin:0;font-size:.88rem;overflow-wrap:anywhere}pre{margin:0;padding:1rem;border-radius:.7rem;overflow-x:auto;background:#080c10;border:1px solid var(--line);color:#d8e8f4}code{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace}footer{max-width:var(--max);margin:auto;border-top:1px solid var(--line);padding:1.8rem 1.5rem 3rem;color:#718697;font-size:.8rem}@media(max-width:850px){.grid{grid-template-columns:repeat(2,minmax(0,1fr))}.stats{grid-template-columns:repeat(2,1fr)}}@media(max-width:620px){main{padding-top:2.2rem}.topbar{align-items:flex-start}nav{flex-wrap:wrap;justify-content:flex-end}.grid,.detail-grid,.controls{grid-template-columns:1fr}.result-count{padding:0}dl div{grid-template-columns:1fr;gap:.25rem}}
"""


def write_site(output: Path, entries: list[dict], groups: list[dict]) -> None:
    if output.exists():
        shutil.rmtree(output)
    (output / "assets").mkdir(parents=True)
    (output / "skills").mkdir()
    (output / "index.html").write_text(render_index(entries), encoding="utf-8")
    (output / "assets" / "catalog.css").write_text(CSS.strip() + "\n", encoding="utf-8")
    (output / "catalog.json").write_text(json.dumps({"skills": entries, "groups": groups}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (output / ".nojekyll").write_text("", encoding="utf-8")
    for item in entries:
        directory = output / "skills" / item["catalogName"]
        directory.mkdir(parents=True)
        (directory / "index.html").write_text(render_detail(item), encoding="utf-8")


def validate_links(output: Path, expected_count: int) -> None:
    pages = sorted(output.rglob("*.html"))
    if len(pages) != expected_count + 1:
        fail(f"catalog generated {len(pages) - 1} skill pages, expected {expected_count}")
    errors: list[str] = []
    for page in pages:
        text = page.read_text(encoding="utf-8")
        for href in HREF_RE.findall(text):
            parsed = urlparse(href)
            if parsed.scheme or href.startswith(("#", "mailto:", "javascript:")):
                continue
            clean = parsed.path
            if not clean:
                continue
            target = (page.parent / clean).resolve()
            try:
                target.relative_to(output.resolve())
            except ValueError:
                errors.append(f"{page.relative_to(output)}: link escapes output: {href}")
                continue
            if target.is_dir():
                target = target / "index.html"
            if not target.exists():
                errors.append(f"{page.relative_to(output)}: broken internal link: {href}")
    if errors:
        fail("\n".join(errors))


def build(output: Path) -> tuple[int, Path]:
    entries, groups = discover()
    write_site(output, entries, groups)
    validate_links(output, len(entries))
    return len(entries), output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--check", action="store_true", help="build in a temporary directory and validate without writing _site")
    args = parser.parse_args()
    if args.check:
        with tempfile.TemporaryDirectory(prefix="skills-catalog-") as temporary:
            count, _ = build(Path(temporary))
        print(f"OK: catalog inputs render {count} skill pages with valid internal links")
        return
    output = args.output if args.output.is_absolute() else (ROOT / args.output)
    count, output = build(output)
    try:
        display = output.relative_to(ROOT)
    except ValueError:
        display = output
    print(f"OK: generated {count} skill pages in {display}")


if __name__ == "__main__":
    main()
