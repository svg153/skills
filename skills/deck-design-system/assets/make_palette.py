#!/usr/bin/env python3
"""Phase 3: render a palette swatch grid from analysis.json.

Usage: make_palette.py <analysis.json> <out.png> [top_n]

Aggregates color_usage_top across all decks in the analysis array (it is a
JSON array of deck objects) and renders the top N colors as labeled swatches.

Deps: Pillow  (pip install Pillow)
"""
import json
import sys
from collections import Counter
from pathlib import Path

from PIL import Image, ImageDraw

SW, SH, PAD = 130, 90, 12
BG = (17, 17, 20)


def luminance(rgb):
    r, g, b = rgb
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def main():
    analysis = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out = Path(sys.argv[2])
    top_n = int(sys.argv[3]) if len(sys.argv) > 3 else 20

    total = Counter()
    for deck in analysis:
        for hex_color, count in deck.get("color_usage_top", []):
            total[hex_color.upper()] += count
    colors = total.most_common(top_n)

    cols = min(5, len(colors))
    rows = (len(colors) + cols - 1) // cols
    w = cols * SW + (cols + 1) * PAD
    h = rows * SH + (rows + 1) * PAD
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    for i, (hex_color, count) in enumerate(colors):
        r, c = divmod(i, cols)
        x = PAD + c * (SW + PAD)
        y = PAD + r * (SH + PAD)
        rgb = tuple(int(hex_color[j:j + 2], 16) for j in (0, 2, 4))
        draw.rectangle([x, y, x + SW, y + SH - 24], fill=rgb)
        label_color = (0, 0, 0) if luminance(rgb) > 140 else (255, 255, 255)
        draw.text((x + 6, y + SH - 20), f"#{hex_color}", fill=label_color)
        draw.text((x + 6, y + SH - 34), f"{count:,}", fill=(160, 160, 170))
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print(f"wrote {out} ({len(colors)} colors)")


if __name__ == "__main__":
    main()
