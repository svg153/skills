"""Numeric comparison of source image vs. build_from_spec.ps1 render.

For each spec element (coordinates in source px):
  ssim    structural similarity of its box (1 = identical)
  dx, dy  render offset relative to the source, in source px
          (template search within a margin of +-MAX_SHIFT px)
  wratio  text only: ink width in the render / in the source.
          > 1 = text comes out wider (lower the size), < 1 = narrower.
          suggested size = size / wratio

Outputs (next to the render):
  <render>.compare.json   all the data
  <render>.compare.md     summary sorted by severity, ready to fix the spec
  <render>.compare.png    source | render | difference map, worst ones marked

Usage:
  python compare.py --src fuente.png --render render.png [--spec spec.json] [--slide 1]
                    [--threshold 0.80] [--shift 15]
"""
import argparse
import json
import os

import cv2
import numpy as np
from skimage.metrics import structural_similarity as ssim

MAX_SHIFT = 40  # source px


def load_elements(spec_path, slide):
    if not spec_path:
        return [], 2000
    with open(spec_path, encoding="utf-8-sig") as fh:
        spec = json.load(fh)
    sw = float(spec.get("sourceWidth", 2000))
    if spec.get("slides"):
        els = spec["slides"][slide - 1].get("elements", [])
    else:
        els = spec.get("elements", [])
    return els, sw


def el_box(e):
    k = e.get("type") or e.get("kind")
    if k == "line" or ("x1" in e and "x2" in e):
        x0, x1 = sorted((e["x1"], e["x2"]))
        y0, y1 = sorted((e["y1"], e["y2"]))
        return x0 - 6, y0 - 6, x1 - x0 + 12, y1 - y0 + 12
    if not all(c in e for c in ("x", "y", "w")):
        return None
    if "h" not in e:
        return e["x"], e["y"], e["w"], None  # picture/svg without h: estimated from the source
    return e["x"], e["y"], e["w"], e["h"]


def estimate_h(src, x, y, w, k):
    """Height of a picture/svg without h: ink box in the source below (x, y)."""
    H, W = src.shape[:2]
    x0, y0, x1, y1 = clip(x * k, y * k, w * k, min(w, 600) * k, W, H)
    bb = ink_bbox(src, max(0, x0 - 4), max(0, y0 - 4), min(W, x1 + 4), y1)
    if not bb:
        return w
    return max(8.0, (bb[3] - y0) / k + 2)


def clip(x, y, w, h, W, H):
    x0, y0 = max(0, int(round(x))), max(0, int(round(y)))
    x1, y1 = min(W, int(round(x + w))), min(H, int(round(y + h)))
    return x0, y0, x1, y1


def ink_bbox(img, x0, y0, x1, y1, exclude=(), core=None):
    """Box of the 'ink' (pixels different from the background) within a region.
    `exclude`: boxes (px) of other elements that do not count as ink.
    `core`: the element's own box; only strokes (connected components)
    whose center falls inside it count, to avoid catching neighboring text."""
    reg = img[y0:y1, x0:x1].astype(np.int16)
    if reg.size == 0:
        return None
    border = np.concatenate([reg[0], reg[-1], reg[:, 0], reg[:, -1]])
    bg = np.median(border, axis=0)
    mask = np.sqrt(((reg - bg) ** 2).sum(axis=2)) > 60
    for ex0, ey0, ex1, ey1 in exclude:
        mask[max(0, ey0 - y0):max(0, ey1 - y0), max(0, ex0 - x0):max(0, ex1 - x0)] = False
    if core is not None:
        cx0, cy0, cx1, cy1 = core[0] - x0 - 2, core[1] - y0 - 2, core[2] - x0 + 2, core[3] - y0 + 2
        n, lab, stats, cents = cv2.connectedComponentsWithStats(mask.astype(np.uint8), connectivity=8)
        keep = np.zeros(n, bool)
        for c in range(1, n):
            mx, my = cents[c]
            keep[c] = cx0 <= mx <= cx1 and cy0 <= my <= cy1
        mask = keep[lab]
    ys, xs = np.nonzero(mask)
    if len(xs) < 20:
        return None
    return xs.min() + x0, ys.min() + y0, xs.max() + x0, ys.max() + y0


def shift_of(gs, gr, x0, y0, x1, y1, pad):
    """Offset (dx, dy) of the source box's content within the render."""
    tpl = gs[y0:y1, x0:x1]
    if tpl.shape[0] < 6 or tpl.shape[1] < 6 or float(tpl.std()) < 4:
        return None, None, 0.0
    H, W = gr.shape
    sx0, sy0 = max(0, x0 - pad), max(0, y0 - pad)
    sx1, sy1 = min(W, x1 + pad), min(H, y1 + pad)
    area = gr[sy0:sy1, sx0:sx1]
    if area.shape[0] < tpl.shape[0] or area.shape[1] < tpl.shape[1]:
        return None, None, 0.0
    res = cv2.matchTemplate(area, tpl, cv2.TM_CCOEFF_NORMED)
    _, score, _, loc = cv2.minMaxLoc(res)
    return loc[0] + sx0 - x0, loc[1] + sy0 - y0, float(score)


def detect_zones(smap, k, max_zones=15):
    """Without a spec: zones where source and render differ (blobs of the SSIM map),
    returned as pseudo-elements in source px."""
    d = np.clip(1 - smap, 0, 1).astype(np.float32)
    d = cv2.GaussianBlur(d, (0, 0), 3)
    mask = (d > 0.35).astype(np.uint8) * 255
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_RECT, (31, 17)))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(mask)
    zones = []
    for i in range(1, n):
        x, y, w, h, area = stats[i]
        if area < 900:
            continue
        weight = float(d[y:y + h, x:x + w].sum())
        zones.append((weight, x, y, w, h))
    zones.sort(reverse=True)
    out = []
    for j, (_, x, y, w, h) in enumerate(sorted(zones[:max_zones], key=lambda z: (z[2], z[1])), 1):
        out.append({"type": "zona", "name": f"zona {j}", "x": x / k, "y": y / k, "w": w / k, "h": h / k})
    return out


def make_demo(d):
    """Generates fuente.png, render.png and spec.json with two known faults:
    title shifted +20 px and body 10 % larger."""
    os.makedirs(d, exist_ok=True)
    W, H = 2000, 1125

    def draw(title_dx=0, body_scale=1.0):
        img = np.full((H, W, 3), 255, np.uint8)
        cv2.putText(img, "Resultados del trimestre", (100 + title_dx, 140), cv2.FONT_HERSHEY_DUPLEX, 2.4, (89, 37, 27), 4, cv2.LINE_AA)
        cv2.rectangle(img, (100, 300), (900, 800), (252, 246, 242), -1)
        cv2.circle(img, (220, 420), 60, (224, 79, 42), -1)
        for i, t in enumerate(("Crecimiento sostenido", "en todas las regiones")):
            cv2.putText(img, t, (320, 440 + 60 * i), cv2.FONT_HERSHEY_SIMPLEX, 1.2 * body_scale, (40, 40, 40), 2, cv2.LINE_AA)
        cv2.rectangle(img, (1100, 300), (1900, 800), (230, 230, 230), 3)
        return img

    cv2.imwrite(os.path.join(d, "fuente.png"), draw())
    cv2.imwrite(os.path.join(d, "render.png"), draw(title_dx=20, body_scale=1.1))
    spec = {"sourceWidth": 2000, "elements": [
        {"type": "text", "name": "titulo", "x": 95, "y": 80, "w": 1000, "h": 80, "size": 36, "text": "Resultados del trimestre"},
        {"type": "shape", "name": "tarjeta", "x": 100, "y": 300, "w": 800, "h": 500, "fill": "F3F4F6"},
        {"type": "shape", "name": "icono", "shape": "ellipse", "x": 160, "y": 360, "w": 120, "h": 120, "fill": "2563EB"},
        {"type": "text", "name": "cuerpo", "x": 315, "y": 400, "w": 560, "h": 120, "size": 16, "text": "Crecimiento sostenido\nen todas las regiones"},
        {"type": "shape", "name": "marco", "x": 1100, "y": 300, "w": 800, "h": 500, "fill": None, "line": "E6E6E6"}]}
    with open(os.path.join(d, "spec.json"), "w", encoding="utf-8") as fh:
        json.dump(spec, fh, indent=1)
    print(f"demo={d}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--make-demo", default="", help="only generates the demo files in this folder")
    ap.add_argument("--src")
    ap.add_argument("--render")
    ap.add_argument("--spec", default="")
    ap.add_argument("--slide", type=int, default=1)
    ap.add_argument("--threshold", type=float, default=0.80)
    ap.add_argument("--shift", type=float, default=15, help="source px from which to warn")
    a = ap.parse_args()
    if a.make_demo:
        make_demo(a.make_demo)
        return
    if not a.src or not a.render:
        ap.error("--src and --render are required")

    elements, sw = load_elements(a.spec, a.slide)
    rend = cv2.imread(a.render)
    src = cv2.imread(a.src)
    if rend is None or src is None:
        raise SystemExit(f"Could not read {'the render' if rend is None else 'the source'}")
    H, W = rend.shape[:2]
    src = cv2.resize(src, (W, H), interpolation=cv2.INTER_AREA)
    k = W / sw  # source px -> render px
    gs = cv2.cvtColor(src, cv2.COLOR_BGR2GRAY)
    gr = cv2.cvtColor(rend, cv2.COLOR_BGR2GRAY)
    g_score, smap = ssim(gs, gr, full=True, data_range=255)

    auto = not elements
    if auto:
        elements = detect_zones(smap, k)

    rows = []
    for i, e in enumerate(elements):
        b = el_box(e)
        if b is None:
            continue
        if b[3] is None:
            b = (b[0], b[1], b[2], estimate_h(src, b[0], b[1], b[2], k))
        x0, y0, x1, y1 = clip(b[0] * k, b[1] * k, b[2] * k, b[3] * k, W, H)
        if x1 - x0 < 6 or y1 - y0 < 6:
            continue
        kind = e.get("type") or e.get("kind") or "?"
        name = e.get("name") or f"{kind}#{i + 1}"
        is_text = kind == "text" or ("text" in e and kind in ("shape", "rect"))
        container = kind in ("shape", "rect") and not is_text and (x1 - x0) > 100 and (y1 - y0) > 50
        if container:
            # Cards and boxes: their outline is measured (border, shadow, corners), not
            # what they contain, which is already measured in their own elements.
            t = max(4, int(10 * k))
            ring = np.ones((y1 - y0, x1 - x0), bool)
            ring[t:-t, t:-t] = False
            sval = float(smap[y0:y1, x0:x1][ring].mean())
        else:
            sval = float(smap[y0:y1, x0:x1].mean())
        r = {"name": name, "kind": kind, "box_src": [round(v) for v in b], "ssim": round(sval, 3)}
        dx, dy, mscore = shift_of(gs, gr, x0, y0, x1, y1, int(MAX_SHIFT * k))
        if dx is not None and mscore > 0.5:
            r["dx"], r["dy"] = round(dx / k, 1), round(dy / k, 1)
            r["match"] = round(mscore, 2)
        if is_text or kind == "zona":
            # Ink box: robust to different fonts and anti-aliasing (rasterized source).
            # Wide horizontal margin (text may overflow sideways) and
            # small vertical margin, to avoid catching the neighboring line or text.
            pxp = 0 if kind == "zona" else int(30 * k)
            pyp = 0 if kind == "zona" else int(6 * k)
            px0, py0, px1, py1 = clip(x0 - pxp, y0 - pyp, (x1 - x0) + 2 * pxp, (y1 - y0) + 2 * pyp, W, H)
            # Excluded from the measurement: shapes, lines and images that cross the region
            # (an underline inside the title box), except those that contain it
            # (the card the text sits on).
            excl = []
            if kind != "zona":
                for j, o in enumerate(elements):
                    ok_ = (o.get("type") or o.get("kind")) in ("rect", "shape", "line", "picture", "svg") and "text" not in o
                    ob = el_box(o) if ok_ and j != i else None
                    if not ob or ob[3] is None:
                        continue
                    ox0, oy0, ox1, oy1 = clip(ob[0] * k, ob[1] * k, ob[2] * k, ob[3] * k, W, H)
                    contains = ox0 <= x0 + 2 and oy0 <= y0 + 2 and ox1 >= x1 - 2 and oy1 >= y1 - 2
                    if not contains and ox0 < px1 and ox1 > px0 and oy0 < py1 and oy1 > py0:
                        m = max(3, int(4 * k))  # anti-aliased edge and shadow
                        excl.append((ox0 - m, oy0 - m, ox1 + m, oy1 + m))
            # Center filter only vertically (neighbors above/below); horizontally
            # the whole region is kept, which is where text overflows.
            core = None if kind == "zona" else (px0, y0, px1, y1)
            # In the source, the box is looked at where the content was (undoing
            # the measured offset); otherwise the original's letters fall outside.
            # Only if the template is reliable (>= 0.8); a weak match gives false dx.
            score_core, sdx, sdy = core, 0, 0
            if core is not None and dx is not None and mscore >= 0.8:
                sdx, sdy = dx, dy
                score_core = (px0 - dx, y0 - dy, px1 - dx, y1 - dy)
            bs = ink_bbox(src, max(0, px0 - abs(sdx)), max(0, py0 - abs(sdy)),
                          min(W, px1 + abs(sdx)), min(H, py1 + abs(sdy)), excl, score_core)
            br = ink_bbox(rend, px0, py0, px1, py1, excl, core)
            if bs and br and bs[2] - bs[0] > 10:
                wr = (br[2] - br[0]) / (bs[2] - bs[0])
                hr = (br[3] - br[1]) / max(1, bs[3] - bs[1])
                r["wratio"], r["hratio"] = round(wr, 3), round(hr, 3)
                r["ink_h_render"] = int(br[3] - br[1])
                r["ink_dx"], r["ink_dy"] = round((br[0] - bs[0]) / k, 1), round((br[1] - bs[1]) / k, 1)
                if kind != "zona":
                    # Overflow: the render's ink goes outside the text box.
                    over = max(br[2] - x1, x0 - br[0], 0) / k
                    if over > 4:
                        r["desborda_px"] = round(over)
                size = e.get("size")
                if isinstance(size, (int, float)) and abs(wr - 1) > 0.03:
                    r["size_sugerido"] = round(size / wr * 2) / 2
                # With text, the ink edge is more reliable than the template
                # (the template fails if the font or line breaks change).
                if "dx" not in r or r.get("match", 0) < 0.8:
                    r["dx"], r["dy"] = r["ink_dx"], r["ink_dy"]
        issues = []
        # Text and zones: SSIM drops just from different font/anti-aliasing; warn
        # on SSIM only if it is very low. The rest is covered by dx/dy and the width.
        # Redrawn icons and images: same lenient criterion. Thin lines: the SSIM
        # of a 1-2 px box means nothing; only the offset counts.
        if is_text or kind in ("zona", "svg", "picture"):
            ssim_min = min(a.threshold, 0.45)
        elif kind == "line" or min(x1 - x0, y1 - y0) < 20 * k:
            ssim_min = -1  # lines and very thin shapes (underlines): only dx/dy counts
        else:
            ssim_min = a.threshold
        if r["ssim"] < ssim_min:
            issues.append(f"ssim {r['ssim']:.2f}")
        if "dx" in r and max(abs(r["dx"]), abs(r["dy"])) > a.shift:
            issues.append(f"shifted dx={r['dx']:+.0f} dy={r['dy']:+.0f} px")
        if "wratio" in r and abs(r["wratio"] - 1) > 0.05:
            issues.append(f"width x{r['wratio']:.2f}" + (f" -> size {r['size_sugerido']}" if "size_sugerido" in r else ""))
        if "desborda_px" in r:
            issues.append(f"OVERFLOWS its box by {r['desborda_px']} px" +
                          (f" -> size {r['size_sugerido']}" if "size_sugerido" in r else " (reduce size or widen)"))
        # Extra line: only if the render's ink also does not fit the height of its box.
        if "hratio" in r and r["hratio"] > 1.2 and r.get("ink_h_render", 0) > (y1 - y0) + 4:
            issues.append(f"height x{r['hratio']:.2f} (one line too many?)")
        if kind == "zona" and issues:
            bx = r["box_src"]
            issues.insert(0, f"at x={bx[0]} y={bx[1]} ({bx[2]}x{bx[3]})")
        r["issues"] = issues
        r["_px"] = (x0, y0, x1, y1)
        rows.append(r)

    def severity(r):
        s = (1 - r["ssim"]) * 2 + (5 if "desborda_px" in r else 0)
        if "dx" in r:
            s += max(abs(r["dx"]), abs(r["dy"])) / 20
        if "wratio" in r:
            s += abs(r["wratio"] - 1) * 5
        return s

    # A container (card, box) with low SSIM but no offset of its own
    # is usually "contaminated" by a faulty child: reported separately, without a warning.
    def inside(c, p):
        return c[0] >= p[0] - 2 and c[1] >= p[1] - 2 and c[2] <= p[2] + 2 and c[3] <= p[3] + 2

    real = [r for r in rows if any(not i.startswith("ssim") for i in r["issues"])]
    affected = []
    for r in rows:
        if r["issues"] and all(i.startswith("ssim") for i in r["issues"]):
            culprits = [c["name"] for c in real if c is not r and inside(c["_px"], r["_px"])]
            if culprits:
                r["afectado_por"] = culprits
                r["issues"] = []
                affected.append(r)

    bad = sorted([r for r in rows if r["issues"]], key=severity, reverse=True)

    diff = np.clip((1 - smap) * 255, 0, 255).astype(np.uint8)
    heat = cv2.cvtColor(gs, cv2.COLOR_GRAY2BGR) // 3
    heat[:, :, 2] = np.maximum(heat[:, :, 2], diff)
    marked = rend.copy()
    for n, r in enumerate(bad[:12], 1):
        x0, y0, x1, y1 = r["_px"]
        for img in (marked, heat):
            cv2.rectangle(img, (x0, y0), (x1, y1), (0, 165, 255), 3)
            cv2.putText(img, str(n), (x0 + 4, y0 + 26), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 165, 255), 2)
    sheet = np.hstack([src, marked, heat])
    sheet = cv2.resize(sheet, None, fx=2400 / sheet.shape[1], fy=2400 / sheet.shape[1], interpolation=cv2.INTER_AREA)

    base = os.path.splitext(a.render)[0]
    cv2.imwrite(base + ".compare.png", sheet)
    for r in rows:
        r.pop("_px", None)
    with open(base + ".compare.json", "w", encoding="utf-8") as fh:
        json.dump({"ssim_global": round(float(g_score), 3), "elements": rows}, fh, ensure_ascii=False, indent=2)

    md = [f"# Comparison: {os.path.basename(a.render)}", "",
          f"Global SSIM: **{g_score:.3f}** · {'zones detected (no spec)' if auto else 'elements measured'}: {len(rows)} · with warnings: {len(bad)}", ""]
    if auto:
        md += ["No-spec mode: zones are difference blobs, not elements. The coordinates "
               "(`box_src` in the .json) are in source px; find them on the sheet by their number.", ""]
    if bad:
        md += ["| # | Element | Type | Warnings |", "|---|---|---|---|"]
        md += [f"| {n} | `{r['name']}` | {r['kind']} | {'; '.join(r['issues'])} |" for n, r in enumerate(bad, 1)]
    else:
        md.append("No warnings.")
    if affected:
        md += ["", "No warning of its own (low SSIM due to an inner element): " +
               ", ".join(f"`{r['name']}` ← {', '.join(r['afectado_por'])}" for r in affected)]
    md += ["", "The numbers match the boxes on the .compare.png sheet. "
           "SSIM is a guide, not the final word: check the sheet before fixing."]
    with open(base + ".compare.md", "w", encoding="utf-8") as fh:
        fh.write("\n".join(md) + "\n")

    print(f"ssim_global={g_score:.3f} medidos={len(rows)} avisos={len(bad)}")
    for n, r in enumerate(bad[:12], 1):
        print(f"  {n}. {r['name']}: {'; '.join(r['issues'])}")
    print(f"report={base}.compare.md")


if __name__ == "__main__":
    main()
