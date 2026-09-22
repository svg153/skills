#!/usr/bin/env python3
"""Phase 4: quantitative design analysis of extracted PPTX internals.

Usage: analyze_design.py <base-dir> [out.json]

<base-dir> holds one subdirectory per deck, each containing an extracted
ppt/ tree (from extract_assets.sh). For slide size the script also looks
for the original <deck-name>.pptx next to or inside the deck directory;
without it slide_size is omitted.

Writes a JSON array of deck objects: slide size, theme palette/fonts,
actual per-slide color/font/size usage, layout names, media inventory.

Trust actual run usage over theme XML: decks routinely override theme
colors with literal srgbClr values and theme fonts with explicit typefaces.

Deps: Pillow  (pip install Pillow)
"""
import json
import re
import sys
import zipfile
from collections import Counter
from pathlib import Path

from PIL import Image

EMU_PER_INCH = 914400


def read_xml(path):
    return Path(path).read_text(encoding="utf-8", errors="ignore")


def slide_size(pptx):
    if pptx is None:
        return {}
    with zipfile.ZipFile(pptx) as z:
        xml = z.read("ppt/presentation.xml").decode("utf-8", "ignore")
    m = re.search(r'<p:sldSz cx="(\d+)" cy="(\d+)"', xml)
    if not m:
        return {}
    cx, cy = int(m.group(1)), int(m.group(2))
    return {
        "emu": [cx, cy],
        "inches": [round(cx / EMU_PER_INCH, 2), round(cy / EMU_PER_INCH, 2)],
        "ratio": round(cx / cy, 3),
    }


def theme_info(deck_dir):
    info = {"palette": {}, "fonts": {}}
    theme = deck_dir / "ppt" / "theme" / "theme1.xml"
    if not theme.exists():
        return info
    xml = read_xml(theme)
    for tag in ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2", "accent3",
                "accent4", "accent5", "accent6", "hlink", "folHlink"):
        m = re.search(
            r'<a:%s>.*?(?:srgbClr val="([0-9A-Fa-f]{6})"|lastClr="([0-9A-Fa-f]{6})")' % tag,
            xml, re.S)
        if m:
            info["palette"][tag] = (m.group(1) or m.group(2)).upper()
    for scheme in ("majorFont", "minorFont"):
        m = re.search(r'<a:%s>.*?<a:latin typeface="([^"]*)"' % scheme, xml, re.S)
        if m:
            info["fonts"][scheme] = m.group(1)
    return info


def layout_names(deck_dir):
    names = {}
    layouts = deck_dir / "ppt" / "slideLayouts"
    if not layouts.exists():
        return names
    for f in sorted(layouts.glob("slideLayout*.xml")):
        m = re.search(r'<p:cSld name="([^"]*)"', read_xml(f))
        names[f.stem] = m.group(1) if m else f.stem
    return names


def analyze_deck(deck_dir, pptx):
    names = layout_names(deck_dir)
    slides_dir = deck_dir / "ppt" / "slides"
    slides = sorted(slides_dir.glob("slide*.xml"),
                    key=lambda p: int(re.search(r"(\d+)", p.stem).group(1)))
    colors, fonts, sizes, layouts = Counter(), Counter(), Counter(), Counter()
    for slide in slides:
        xml = read_xml(slide)
        colors.update(c.upper() for c in re.findall(r'srgbClr val="([0-9A-Fa-f]{6})"', xml))
        fonts.update(re.findall(r'<a:latin typeface="([^"]*)"', xml))
        sizes.update(int(s) for s in re.findall(r'<a:rPr[^>]*\bsz="(\d+)"', xml))
        rels = slides_dir / "_rels" / f"{slide.stem}.xml.rels"
        if rels.exists():
            m = re.search(r'slideLayout(\d+)\.xml', read_xml(rels))
            if m:
                layouts[names.get(f"slideLayout{m.group(1)}", m.group(0))] += 1

    media_dir = deck_dir / "ppt" / "media"
    media = sorted(media_dir.glob("*")) if media_dir.exists() else []
    by_type = Counter(m.suffix.lstrip(".").lower() for m in media)
    total_mb = round(sum(m.stat().st_size for m in media) / 1024 / 1024, 2)
    notable = []
    for m in sorted(media, key=lambda x: -x.stat().st_size)[:5]:
        entry = {"file": m.name, "mb": round(m.stat().st_size / 1024 / 1024, 2)}
        if m.suffix.lower() in (".png", ".jpg", ".jpeg", ".gif"):
            try:
                with Image.open(m) as im:
                    entry["dims"] = list(im.size)
            except Exception:
                pass
        notable.append(entry)

    return {
        "deck": deck_dir.name,
        "dir": str(deck_dir),
        "slide_size": slide_size(pptx),
        "theme": theme_info(deck_dir),
        "slide_count": len(slides),
        "color_usage_top": colors.most_common(30),
        "distinct_colors": len(colors),
        "font_usage": fonts.most_common(),
        "font_size_pt_top": [{"pt": pt / 100, "count": n} for pt, n in sizes.most_common(15)],
        "layout_usage": layouts.most_common(),
        "media_by_type": dict(by_type),
        "media_total_mb": total_mb,
        "notable_media": notable,
    }


def main():
    base = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else base / "analysis.json"
    decks = []
    for d in sorted(p for p in base.iterdir() if p.is_dir() and (p / "ppt").exists()):
        pptx = None
        for candidate in (d.with_name(f"{d.name}.pptx"), d / f"{d.name}.pptx"):
            if candidate.exists():
                pptx = candidate
                break
        decks.append(analyze_deck(d, pptx))
        r = decks[-1]
        print(f"{r['deck']}: {r['slide_count']} slides, {r['distinct_colors']} colors, "
              f"{r['media_total_mb']} MB media")
    out.write_text(json.dumps(decks, indent=2), encoding="utf-8")
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
