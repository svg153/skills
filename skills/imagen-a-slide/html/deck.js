/* imagen-a-slide: renders the SAME JSON spec as build_from_spec.ps1 (PowerPoint) as HTML slides.
   No dependencies. build_html.ps1 embeds it in a single .html together with the spec and the resources (data URIs).
   Canvas: 960 x 540 (1 CSS unit = 1 PowerPoint pt), spec coordinates in source px (sourceWidth).
   Keys: arrows / space / PgUp-PgDn = navigate, F = fullscreen, N = notes, E = edit texts,
           P = print / PDF (one slide per page). Hash #3 = go to slide 3.
   Capture mode: #export=1&slide=N shows only that slide, no UI, scaled to the window width. */
(function () {
  'use strict';
  var W = 960, H = 540;
  var DECK = JSON.parse(document.getElementById('deck-data').textContent);
  var params = {};
  location.hash.replace(/^#/, '').split('&').forEach(function (kv) { var p = kv.split('='); if (p[0]) params[p[0]] = decodeURIComponent(p[1] || ''); });
  var EXPORT = params['export'] === '1';

  function el(tag, cls, parent) { var e = document.createElement(tag); if (cls) e.className = cls; if (parent) parent.appendChild(e); return e; }
  function svgEl(tag, attrs, parent) {
    var e = document.createElementNS('http://www.w3.org/2000/svg', tag);
    for (var a in attrs) if (attrs[a] !== undefined && attrs[a] !== null) e.setAttribute(a, attrs[a]);
    if (parent) parent.appendChild(e); return e;
  }
  function hex(c, alpha) {
    c = String(c || '000000').replace('#', '');
    var r = parseInt(c.substr(0, 2), 16), g = parseInt(c.substr(2, 2), 16), b = parseInt(c.substr(4, 2), 16);
    return alpha === undefined || alpha >= 1 ? '#' + c : 'rgba(' + r + ',' + g + ',' + b + ',' + alpha + ')';
  }
  function get(o, k, d) { return o && o[k] !== undefined && o[k] !== null ? o[k] : d; }
  var DASH = { solid: null, dot: '1 2', squareDot: '1 1', dash: '4 3', dashDot: '4 2 1 2', longDash: '8 3' };

  /* ---------- text ---------- */
  function fontStack(f) { return "'" + f + "', 'Segoe UI', -apple-system, 'Helvetica Neue', Arial, sans-serif"; }
  function renderText(box, e, ctx) {
    var role = get(e, 'role');
    var font = get(e, 'font', (role === 'title' || role === 'subtitle') ? ctx.headFont : ctx.font);
    var size = get(e, 'size', 12), align = get(e, 'align', 'left');
    var wrap = get(e, 'wrap', false) || align !== 'left';
    var m = get(e, 'margin', 0);
    box.style.padding = m + 'px';
    box.style.display = 'flex'; box.style.flexDirection = 'column';
    box.style.justifyContent = { top: 'flex-start', middle: 'center', bottom: 'flex-end' }[get(e, 'anchor', get(e, 'valign', 'top'))] || 'flex-start';
    var inner = el('div', 'txt', box);
    inner.style.fontFamily = fontStack(font);
    inner.style.fontSize = size + 'px';
    inner.style.color = hex(get(e, 'color', ctx.text));
    inner.style.fontWeight = get(e, 'bold', false) ? '700' : '400';
    inner.style.fontStyle = get(e, 'italic', false) ? 'italic' : 'normal';
    inner.style.textAlign = align;
    inner.style.whiteSpace = wrap ? 'pre-wrap' : 'pre';
    inner.style.lineHeight = e.lineSpacing ? e.lineSpacing + 'px' : '1.2';
    if (e.charSpacing) inner.style.letterSpacing = e.charSpacing + 'px';

    var paras = e.paragraphs || [{ text: e.text || '' }];
    // Full text as in PowerPoint (paragraphs joined by \r) to apply the runs by position.
    var full = paras.map(function (p) { return String(p.text || ''); }).join('\r');
    var styles = new Array(full.length);
    (e.runs || []).forEach(function (run) {
      var txt = String(run.match || ''); if (!txt) return;
      var start = 0, found = false;
      while (true) {
        var i = full.indexOf(txt, start); if (i < 0) break;
        found = true;
        for (var j = i; j < i + txt.length; j++) styles[j] = Object.assign({}, styles[j] || {}, run);
        if (!run.all) break; start = i + txt.length;
      }
      if (!found) console.warn('run no encontrado:', txt, 'en', e.name);
    });
    var pos = 0, num = 0;
    paras.forEach(function (p) {
      var pd = el('div', 'para', inner), t = String(p.text || '');
      if (p.size) pd.style.fontSize = p.size + 'px';
      if (p.bold !== undefined) pd.style.fontWeight = p.bold ? '700' : '400';
      if (p.italic !== undefined) pd.style.fontStyle = p.italic ? 'italic' : 'normal';
      if (p.color) pd.style.color = hex(p.color);
      if (p.align) pd.style.textAlign = p.align;
      if (e.spaceAfter) pd.style.marginBottom = e.spaceAfter + 'px';
      if (p.bullet) {
        num++;
        var lvl = get(p, 'level', 0);
        pd.style.paddingLeft = (18 + lvl * 18) + 'px'; pd.style.textIndent = '-14px';
        var b = el('span', 'bullet', pd); b.textContent = p.bullet === 'number' ? num + '. ' : '• ';
        b.style.display = 'inline-block'; b.style.width = '14px'; b.style.textIndent = '0';
      } else num = 0;
      // groups consecutive characters with the same style into spans
      var cur = null, buf = '', curKey = null;
      function flush() {
        if (!buf) return;
        var s = el('span', null, pd); s.textContent = buf;
        if (cur) {
          if (cur.bold !== undefined) s.style.fontWeight = cur.bold ? '700' : '400';
          if (cur.italic !== undefined) s.style.fontStyle = cur.italic ? 'italic' : 'normal';
          if (cur.underline) s.style.textDecoration = 'underline';
          if (cur.color) s.style.color = hex(cur.color);
          if (cur.size) s.style.fontSize = cur.size + 'px';
          if (cur.gradient) {
            s.style.backgroundImage = 'linear-gradient(90deg,' + hex(cur.gradient[0]) + ',' + hex(cur.gradient[1]) + ')';
            s.style.webkitBackgroundClip = 'text'; s.style.backgroundClip = 'text'; s.style.color = 'transparent';
          }
        }
        buf = '';
      }
      for (var c = 0; c < t.length; c++) {
        var st = styles[pos + c] || null, key = st ? JSON.stringify(st) : '';
        if (key !== curKey) { flush(); cur = st; curKey = key; }
        buf += t[c];
      }
      flush();
      if (!t.length) pd.innerHTML = '&#8203;';
      pos += t.length + 1;
    });
    return inner;
  }

  /* ---------- shapes ---------- */
  // Non-rectangular shapes: polygons in a 0..100 box (stretched to the bounding box).
  var POLY = {
    triangle: '50,0 100,100 0,100', rtTriangle: '0,0 100,100 0,100', diamond: '50,0 100,50 50,100 0,50',
    parallelogram: '25,0 100,0 75,100 0,100', trapezoid: '25,0 75,0 100,100 0,100',
    hexagon: '25,0 75,0 100,50 75,100 25,100 0,50', octagon: '29,0 71,0 100,29 100,71 71,100 29,100 0,71 0,29',
    regularPentagon: '50,0 100,38 81,100 19,100 0,38', pentagon: '0,0 80,0 100,50 80,100 0,100', homePlate: '0,0 80,0 100,50 80,100 0,100',
    chevron: '0,0 80,0 100,50 80,100 0,100 20,50', plus: '35,0 65,0 65,35 100,35 100,65 65,65 65,100 35,100 35,65 0,65 0,35 35,35',
    rightArrow: '0,25 65,25 65,0 100,50 65,100 65,75 0,75', leftArrow: '100,25 35,25 35,0 0,50 35,100 35,75 100,75',
    upArrow: '25,100 25,35 0,35 50,0 100,35 75,35 75,100', downArrow: '25,0 75,0 75,65 100,65 50,100 0,65 25,65',
    leftRightArrow: '0,50 20,0 20,25 80,25 80,0 100,50 80,100 80,75 20,75 20,100',
    star5: '50,0 61,35 98,35 68,57 79,91 50,70 21,91 32,57 2,35 39,35',
    flowChartDecision: '50,0 100,50 50,100 0,50'
  };
  function lineStyle(e) {
    var ln = e.line;
    if (!ln) return null;
    if (typeof ln === 'string') return { color: ln, width: get(e, 'lineWidth', 1), dash: 'solid' };
    return { color: get(ln, 'color', '000000'), width: get(ln, 'width', 1), dash: get(ln, 'dash', 'solid') };
  }
  function renderShape(box, e, ctx, k) {
    var kind = e.shape || (get(e, 'radius', 0) > 0 ? 'roundRect' : 'rect');
    var fill = e.fill ? hex(e.fill, 1 - get(e, 'fillTransparency', 0)) : 'transparent';
    var ls = lineStyle(e);
    var w = e.w * k, h = e.h * k;
    if (kind === 'rect' || kind === 'roundRect' || kind === 'ellipse' || kind === 'flowChartProcess' || kind === 'flowChartTerminator') {
      box.style.background = fill;
      if (ls) box.style.border = ls.width + 'px ' + (ls.dash === 'solid' ? 'solid' : 'dashed') + ' ' + hex(ls.color);
      box.style.boxSizing = 'border-box';
      if (kind === 'roundRect') box.style.borderRadius = (get(e, 'radius', 0.16667) * Math.min(w, h)) + 'px';
      if (kind === 'ellipse') box.style.borderRadius = '50%';
      if (kind === 'flowChartTerminator') box.style.borderRadius = (Math.min(w, h) / 2) + 'px';
      if (e.shadow) box.style.boxShadow = '0 2px 10px rgba(30,58,138,0.10)';
    } else {
      var pts = POLY[kind];
      if (!pts) { console.warn('forma no soportada en HTML:', kind, '-> rect'); box.style.background = fill; }
      else {
        var s = svgEl('svg', { viewBox: '0 0 100 100', preserveAspectRatio: 'none', width: '100%', height: '100%', 'class': 'shape-svg' }, box);
        svgEl('polygon', { points: pts, fill: fill, stroke: ls ? hex(ls.color) : 'none', 'stroke-width': ls ? ls.width : 0,
          'vector-effect': 'non-scaling-stroke', 'stroke-dasharray': ls ? DASH[ls.dash] : null }, s);
        if (e.shadow) s.style.filter = 'drop-shadow(0 2px 5px rgba(30,58,138,0.12))';
      }
    }
    if (e.textBox || e.text || e.paragraphs) {
      var t = el('div', 'shape-text', box);
      t.style.position = 'absolute'; t.style.inset = '0';
      renderText(t, e.textBox || e, ctx);
    }
  }

  /* ---------- lines ---------- */
  var mid = 0;
  function renderLine(slide, e, ctx, k) {
    var x1 = e.x1 * k, y1 = e.y1 * k, x2 = e.x2 * k, y2 = e.y2 * k, pad = 12;
    var x0 = Math.min(x1, x2) - pad, y0 = Math.min(y1, y2) - pad;
    var s = svgEl('svg', { width: Math.abs(x2 - x1) + 2 * pad, height: Math.abs(y2 - y1) + 2 * pad, 'class': 'el line' }, slide);
    s.style.left = x0 + 'px'; s.style.top = y0 + 'px';
    var color = hex(get(e, 'color', ctx.text)), width = get(e, 'width', 1.25);
    function marker(type, start) {
      if (!type || type === 'none') return null;
      var id = 'm' + (++mid);
      var m = svgEl('marker', { id: id, viewBox: '0 0 10 10', refX: start ? 1 : 9, refY: 5, markerWidth: 5, markerHeight: 5, orient: 'auto-start-reverse', markerUnits: 'strokeWidth' }, s);
      if (type === 'oval') svgEl('circle', { cx: 5, cy: 5, r: 4, fill: color }, m);
      else if (type === 'diamond') svgEl('polygon', { points: '5,0 10,5 5,10 0,5', fill: color }, m);
      else if (type === 'arrow' || type === 'open') svgEl('polyline', { points: '0,0 10,5 0,10', fill: 'none', stroke: color, 'stroke-width': 1.5 }, m);
      else if (type === 'stealth') svgEl('polygon', { points: '0,0 10,5 0,10 3,5', fill: color }, m);
      else svgEl('polygon', { points: '0,0 10,5 0,10', fill: color }, m);
      return 'url(#' + id + ')';
    }
    svgEl('line', { x1: x1 - x0, y1: y1 - y0, x2: x2 - x0, y2: y2 - y0, stroke: color, 'stroke-width': width,
      'stroke-dasharray': DASH[get(e, 'dash', 'solid')], 'marker-start': marker(e.beginArrow, true), 'marker-end': marker(e.endArrow, false) }, s);
    return s;
  }

  /* ---------- tables ---------- */
  function renderTable(box, e, ctx, k) {
    var t = el('table', 'tbl', box), rows = e.rows, nr = rows.length, hdr = e.header, bd = e.border;
    t.style.width = '100%'; t.style.height = '100%';
    if (e.colW) { var cg = el('colgroup', null, t); e.colW.forEach(function (cw) { var c = el('col', null, cg); c.style.width = (cw * k) + 'px'; }); }
    rows.forEach(function (row, r) {
      var tr = el('tr', null, t); tr.style.height = (e.h * k / nr) + 'px';
      row.forEach(function (v) {
        var cs = (typeof v === 'object' && v !== null) ? v : { text: String(v) };
        var td = el(r === 0 && hdr ? 'th' : 'td', null, tr), isH = r === 0 && !!hdr;
        td.textContent = get(cs, 'text', '');
        td.style.fontFamily = fontStack(ctx.font);
        td.style.fontSize = get(cs, 'size', get(e, 'size', 12)) + 'px';
        td.style.color = hex(get(cs, 'color', isH ? get(hdr, 'color', 'FFFFFF') : get(e, 'color', ctx.text)));
        td.style.fontWeight = get(cs, 'bold', isH ? get(hdr, 'bold', true) : false) ? '700' : '400';
        td.style.textAlign = get(cs, 'align', get(e, 'align', 'left'));
        var f = get(cs, 'fill', isH ? get(hdr, 'fill') : get(e, 'fill'));
        if (f) td.style.background = hex(f);
        if (bd) td.style.border = get(bd, 'width', 1) + 'px solid ' + hex(get(bd, 'color', 'CBD5E1'));
      });
    });
  }

  /* ---------- charts (custom SVG, no libraries) ---------- */
  var PALETTE = ['2563EB', '60A5FA', '1F2937', 'F59E0B', '10B981', 'EF4444', '8B5CF6', '64748B'];
  function fmt(v, f) {
    if (!f) return String(Math.round(v * 100) / 100);
    if (/%$/.test(f)) { var d = (f.split('.')[1] || '').replace('%', '').length; return (v * 100).toFixed(d) + '%'; }
    var dd = (f.split('.')[1] || '').length; return v.toFixed(dd);
  }
  function renderChart(box, e, ctx, k) {
    var w = e.w * k, h = e.h * k, s = svgEl('svg', { width: w, height: h, viewBox: '0 0 ' + w + ' ' + h }, box);
    s.style.fontFamily = fontStack(ctx.font); s.style.fontSize = '10px';
    var series = e.series || [], labels = (series[0] || {}).labels || [], cols = (e.colors || PALETTE);
    var type = e.chartType || 'bar', top = 8, legendH = 0, txt = hex(ctx.text);
    if (e.title) { svgEl('text', { x: w / 2, y: 16, 'text-anchor': 'middle', 'font-size': 13, 'font-weight': 700, fill: txt }, s).textContent = e.title; top = 28; }
    var showLegend = get(e, 'showLegend', series.length > 1);
    if (showLegend) legendH = 20;
    if (type === 'pie' || type === 'doughnut') {
      var vals = series[0].values, tot = vals.reduce(function (a, b) { return a + b; }, 0);
      var cx = w / 2, cy = top + (h - top - legendH) / 2, R = Math.min(w, h - top - legendH) / 2 - 6, r0 = type === 'doughnut' ? R * 0.55 : 0, a = -Math.PI / 2;
      vals.forEach(function (v, i) {
        var a2 = a + 2 * Math.PI * v / tot, large = a2 - a > Math.PI ? 1 : 0;
        var p = ['M', cx + R * Math.cos(a), cy + R * Math.sin(a), 'A', R, R, 0, large, 1, cx + R * Math.cos(a2), cy + R * Math.sin(a2)];
        if (r0) p = p.concat(['L', cx + r0 * Math.cos(a2), cy + r0 * Math.sin(a2), 'A', r0, r0, 0, large, 0, cx + r0 * Math.cos(a), cy + r0 * Math.sin(a), 'Z']);
        else p = p.concat(['L', cx, cy, 'Z']);
        svgEl('path', { d: p.join(' '), fill: hex(cols[i % cols.length]), stroke: '#fff', 'stroke-width': 1 }, s);
        if (e.showValue) { var am = (a + a2) / 2, rr = r0 ? (R + r0) / 2 : R * 0.65;
          svgEl('text', { x: cx + rr * Math.cos(am), y: cy + rr * Math.sin(am) + 3, 'text-anchor': 'middle', fill: '#fff', 'font-weight': 700 }, s).textContent = fmt(v, e.valueFormat); }
        a = a2;
      });
      if (showLegend) legend(labels.map(function (l, i) { return [l, cols[i % cols.length]]; }));
      return;
    }
    var horiz = type === 'bar' && e.dir === 'bar', stacked = !!e.stacked;
    var pl = horiz ? 70 : 34, pr = 8, pb = 22 + legendH, x0 = pl, y0 = top, pw = w - pl - pr, ph = h - top - pb;
    var max = 0;
    labels.forEach(function (_, i) {
      if (stacked) max = Math.max(max, series.reduce(function (a, se) { return a + (se.values[i] || 0); }, 0));
      else series.forEach(function (se) { max = Math.max(max, se.values[i] || 0); });
    });
    max = max || 1; var step = Math.pow(10, Math.floor(Math.log10(max))); max = Math.ceil(max / step) * step;
    for (var g = 0; g <= 4; g++) {
      var gv = max * g / 4;
      if (horiz) { var gx = x0 + pw * g / 4; svgEl('line', { x1: gx, y1: y0, x2: gx, y2: y0 + ph, stroke: '#E5E7EB' }, s); svgEl('text', { x: gx, y: y0 + ph + 12, 'text-anchor': 'middle', fill: txt }, s).textContent = fmt(gv, e.valueFormat); }
      else { var gy = y0 + ph - ph * g / 4; svgEl('line', { x1: x0, y1: gy, x2: x0 + pw, y2: gy, stroke: '#E5E7EB' }, s); svgEl('text', { x: x0 - 4, y: gy + 3, 'text-anchor': 'end', fill: txt }, s).textContent = fmt(gv, e.valueFormat); }
    }
    var n = labels.length, band = (horiz ? ph : pw) / n;
    labels.forEach(function (lab, i) {
      if (horiz) svgEl('text', { x: x0 - 4, y: y0 + band * (i + 0.5) + 3, 'text-anchor': 'end', fill: txt }, s).textContent = lab;
      else svgEl('text', { x: x0 + band * (i + 0.5), y: y0 + ph + 13, 'text-anchor': 'middle', fill: txt }, s).textContent = lab;
    });
    if (type === 'line' || type === 'area') {
      series.forEach(function (se, si) {
        var pts = se.values.map(function (v, i) { return [x0 + band * (i + 0.5), y0 + ph - ph * v / max]; });
        var c = hex(cols[si % cols.length]);
        if (type === 'area') svgEl('polygon', { points: [[pts[0][0], y0 + ph]].concat(pts).concat([[pts[pts.length - 1][0], y0 + ph]]).map(function (p) { return p.join(','); }).join(' '), fill: hex(cols[si % cols.length], 0.35) }, s);
        svgEl('polyline', { points: pts.map(function (p) { return p.join(','); }).join(' '), fill: 'none', stroke: c, 'stroke-width': 2 }, s);
        pts.forEach(function (p, i) {
          if (e.markers) svgEl('circle', { cx: p[0], cy: p[1], r: 3, fill: c }, s);
          if (e.showValue) svgEl('text', { x: p[0], y: p[1] - 6, 'text-anchor': 'middle', fill: txt }, s).textContent = fmt(se.values[i], e.valueFormat);
        });
      });
    } else {
      var inner = band * 0.7, bw = stacked ? inner : inner / series.length;
      labels.forEach(function (_, i) {
        var acc = 0;
        series.forEach(function (se, si) {
          var v = se.values[i] || 0, len = (horiz ? pw : ph) * v / max, off = (horiz ? pw : ph) * acc / max;
          var pos = band * i + (band - inner) / 2 + (stacked ? 0 : bw * si), c = hex(cols[si % cols.length]), r;
          if (horiz) r = svgEl('rect', { x: x0 + off, y: y0 + pos, width: len, height: bw, fill: c }, s);
          else r = svgEl('rect', { x: x0 + pos, y: y0 + ph - off - len, width: bw, height: len, fill: c }, s);
          if (e.showValue && v) {
            var tx = horiz ? x0 + off + len + (stacked ? -len / 2 : 4) : x0 + pos + bw / 2;
            var ty = horiz ? y0 + pos + bw / 2 + 3 : y0 + ph - off - len + (stacked ? len / 2 + 3 : -4);
            svgEl('text', { x: tx, y: ty, 'text-anchor': horiz && !stacked ? 'start' : 'middle', fill: stacked ? '#fff' : txt }, s).textContent = fmt(v, e.valueFormat);
          }
          if (stacked) acc += v;
        });
      });
    }
    if (showLegend) legend(series.map(function (se, i) { return [se.name, cols[i % cols.length]]; }));
    function legend(items) {
      var lx = 10, ly = h - 8;
      items.forEach(function (it) {
        svgEl('rect', { x: lx, y: ly - 8, width: 9, height: 9, fill: hex(it[1]) }, s);
        var t = svgEl('text', { x: lx + 13, y: ly, fill: txt }, s); t.textContent = it[0];
        lx += 22 + String(it[0]).length * 5.5;
      });
    }
  }

  /* ---------- slide ---------- */
  function buildSlide(spec, idx) {
    var k = W / get(spec, 'sourceWidth', 2000), th = spec.theme || {};
    var ctx = { font: get(spec, 'font', get(th, 'font', 'Segoe UI')), headFont: get(th, 'headFont', get(spec, 'font', get(th, 'font', 'Segoe UI'))), text: get(th, 'text', '374151') };
    var slide = el('section', 'slide');
    slide.setAttribute('data-index', idx + 1);
    var bg = spec.background || {};
    if (bg.image) { slide.style.backgroundImage = 'url(' + bg.image + ')'; slide.style.backgroundSize = '100% 100%'; }
    else slide.style.background = hex(get(bg, 'color', get(th, 'bg', 'FFFFFF')));
    (spec.elements || []).forEach(function (e, i) {
      var t = e.type || e.kind, name = e.name || e.id || (t + ' ' + (i + 1)), node;
      if (t === 'line') { node = renderLine(slide, e, ctx, k); }
      else {
        node = el('div', 'el ' + t, slide);
        node.style.left = (e.x * k) + 'px'; node.style.top = (e.y * k) + 'px'; node.style.width = (e.w * k) + 'px';
        if (e.h !== undefined) node.style.height = (e.h * k) + 'px';
        if (t === 'text') { renderText(node, e, ctx); if (e.fill) node.style.background = hex(e.fill); }
        else if (t === 'rect' || t === 'shape') renderShape(node, e, ctx, k);
        else if (t === 'picture' || t === 'image') {
          var img = el('img', null, node); img.src = e.path || e.src; img.alt = e.alt || '';
          img.style.width = '100%'; img.style.height = e.h !== undefined ? '100%' : 'auto'; img.style.display = 'block';
        } else if (t === 'svg') {
          node.innerHTML = e.svg; var sv = node.querySelector('svg');
          if (sv) { sv.style.width = '100%'; sv.style.height = e.h !== undefined ? '100%' : 'auto'; sv.style.display = 'block'; if (e.alt) { sv.setAttribute('role', 'img'); sv.setAttribute('aria-label', e.alt); } }
        } else if (t === 'table') renderTable(node, e, ctx, k);
        else if (t === 'chart') renderChart(node, e, ctx, k);
        else console.warn('tipo no soportado:', t);
      }
      node.setAttribute('data-name', name);
      if (e.group) node.setAttribute('data-group', e.group);
      if (e.rotate) node.style.transform = 'rotate(' + e.rotate + 'deg)';
    });
    var notes = el('aside', 'notes', slide); notes.textContent = spec.notes || '';
    return slide;
  }

  /* ---------- presentation ---------- */
  var stage = el('div', 'stage', document.body);
  var slides = DECK.slides.map(function (s, i) { var n = buildSlide(s, i); stage.appendChild(n); return n; });
  var cur = Math.max(0, Math.min(slides.length - 1, (parseInt(params.slide || location.hash.replace(/^#/, ''), 10) || 1) - 1));
  var counter = EXPORT ? null : el('div', 'counter', document.body);
  if (EXPORT) document.body.classList.add('export');
  if (DECK.title) document.title = DECK.title;

  function fit() {
    var s = EXPORT ? innerWidth / W : Math.min(innerWidth / W, innerHeight / H);
    stage.style.transform = 'translate(' + ((innerWidth - W * s) / 2) + 'px,' + (EXPORT ? 0 : (innerHeight - H * s) / 2) + 'px) scale(' + s + ')';
  }
  function show(i) {
    cur = Math.max(0, Math.min(slides.length - 1, i));
    slides.forEach(function (s, j) { s.classList.toggle('active', j === cur); });
    if (counter) counter.textContent = (cur + 1) + ' / ' + slides.length;
    if (!EXPORT) history.replaceState(null, '', '#' + (cur + 1));
  }
  addEventListener('resize', fit);
  addEventListener('keydown', function (ev) {
    if (document.body.classList.contains('editing') && ev.key !== 'Escape' && !(ev.key === 'e' && ev.ctrlKey)) return;
    var k = ev.key;
    if (k === 'ArrowRight' || k === 'PageDown' || k === ' ') show(cur + 1);
    else if (k === 'ArrowLeft' || k === 'PageUp') show(cur - 1);
    else if (k === 'Home') show(0); else if (k === 'End') show(slides.length - 1);
    else if (k === 'f' || k === 'F') { if (document.fullscreenElement) document.exitFullscreen(); else document.documentElement.requestFullscreen(); }
    else if (k === 'n' || k === 'N') document.body.classList.toggle('show-notes');
    else if (k === 'p' || k === 'P') print();
    else if (k === 'e' || k === 'E' || k === 'Escape') {
      var on = k !== 'Escape' && !document.body.classList.contains('editing');
      document.body.classList.toggle('editing', on);
      document.querySelectorAll('.txt, td, th').forEach(function (t) { t.contentEditable = on ? 'true' : 'false'; });
    } else return;
    ev.preventDefault();
  });
  stage.addEventListener('click', function (ev) { if (!document.body.classList.contains('editing')) show(cur + (ev.clientX < innerWidth / 3 ? -1 : 1)); });
  fit(); show(cur);
  document.body.setAttribute('data-ready', '1');
})();
