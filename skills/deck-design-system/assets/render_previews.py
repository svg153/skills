#!/usr/bin/env python3
"""Phase 3: render per-slide PNG previews from the converted PDFs.

Usage: render_previews.py <pdf-dir> <out-dir> [width]

Renders every page of every <pdf-dir>/*.pdf to <out-dir>/<name>/slide-NN.png
at the given pixel width (default 1500).

Deps: pypdfium2  (pip install pypdfium2)
"""
import sys
from pathlib import Path

import pypdfium2 as pdfium


def main():
    pdf_dir, out_dir = Path(sys.argv[1]), Path(sys.argv[2])
    width = int(sys.argv[3]) if len(sys.argv) > 3 else 1500
    for pdf in sorted(pdf_dir.glob("*.pdf")):
        dest = out_dir / pdf.stem
        dest.mkdir(parents=True, exist_ok=True)
        doc = pdfium.PdfDocument(pdf)
        for i, page in enumerate(doc):
            img = page.render(scale=width / page.get_width()).to_pil()
            img.save(dest / f"slide-{i + 1:02d}.png")
        print(f"{pdf.stem}: {len(doc)} slides -> {dest}")
        doc.close()


if __name__ == "__main__":
    main()
