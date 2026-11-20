// Records a product-demo video of a web page that already exists, driving a real browser with
// Playwright from a JSON storyboard. Nothing is rebuilt: the video is the real page plus overlays
// (caption band, fake cursor, camera zoom) and optional offline voice-over (Piper).
//
// usage: node record.mjs <storyboard.json> <outDir> [--tools <dir>] [--no-voice] [--browser <chrome.exe>]
//
// <tools dir> (optional) may hold: node_modules/playwright-core, piper/piper(.exe), voices/<model>.onnx.
// Writes to <outDir>: <name>.webm, vo.json (voice lines + timing), timeline.json, shots/*.png, vo-cache/*.wav.
import { pathToFileURL, fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import { join, dirname, resolve, isAbsolute } from 'node:path';
import { renameSync, mkdirSync, writeFileSync, existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const argv = process.argv.slice(2);
const flag = (n) => { const i = argv.indexOf(n); if (i < 0) return undefined; const [, v] = argv.splice(i, 2); return v; };
const toolsDir = flag('--tools');
const browserFlag = flag('--browser') ?? process.env.WEB_DEMO_VIDEO_BROWSER;
const previewDiv = Math.max(1, Number(flag('--preview-div') ?? 4));
const preview = argv.includes('--preview'); // no video, no voice, holds divided by previewDiv
const noLint = argv.includes('--no-lint');
const noVoiceFlag = argv.includes('--no-voice') || preview;
const [storyPath, outArg] = argv.filter((a) => !a.startsWith('--'));
if (!storyPath || !outArg) {
  console.error('usage: node record.mjs <storyboard.json> <outDir> [--tools <dir>] [--no-voice] [--browser <chrome.exe>] [--preview [--preview-div 4]] [--no-lint]');
  process.exit(2);
}
if (!noLint) { // fail fast on a broken storyboard, before launching a browser
  const lintArgs = [join(dirname(fileURLToPath(import.meta.url)), 'lint.mjs'), storyPath, ...(toolsDir ? ['--tools', toolsDir] : [])];
  const r = spawnSync(process.execPath, lintArgs, { encoding: 'utf8' });
  process.stdout.write(r.stdout ?? '');
  if (r.status) { console.error('Storyboard lint failed: fix the errors above (or pass --no-lint).'); process.exit(1); }
}
const story = JSON.parse(readFileSync(storyPath, 'utf8').replace(/^﻿/, ''));
const cfg = story.config ?? {};
const outDir = resolve(outArg);
const baseDir = resolve(dirname(resolve(storyPath)), cfg.baseDir ?? '.');
const name = cfg.name ?? 'demo';
mkdirSync(outDir, { recursive: true });

// playwright-core: normal resolution, then <tools>/node_modules, then cwd / NODE_PATH.
async function loadPlaywright() {
  try { return await import('playwright-core'); } catch { /* try the next place */ }
  for (const from of [toolsDir && join(resolve(toolsDir), 'x.js'), join(process.cwd(), 'x.js')].filter(Boolean)) {
    try { return createRequire(from)('playwright-core'); } catch { /* next */ }
  }
  throw new Error('playwright-core not found. Run `npm i playwright-core` next to the scripts or in the tools dir (--tools).');
}
const { chromium } = await loadPlaywright();

// ── Style tokens (all optional) ──────────────────────────────────────────────────────────────
const W = cfg.viewport?.width ?? 1280, H = cfg.viewport?.height ?? 720;
const k = W / 1440; // the default sizes were tuned at 1440 px wide
const px = (n) => Math.round(n * k);
const st = {
  background: '#04122e', accent: '#7fd6ff', text: '#ffffff', bandRgb: '4,18,46',
  font: 'Segoe UI,Helvetica,Arial,sans-serif', captionPx: px(34), labelPx: px(15), titlePx: px(64), subtitlePx: px(28),
  ...(cfg.style ?? {}),
};
const maxZoom = cfg.maxZoom ?? 1.1;

// ── Voice-over: one WAV per line with Piper (offline), cached by text ────────────────────────
const voiceCfg = cfg.voice;
const voiceOn = !!voiceCfg?.model && !noVoiceFlag;
const VO_DIR = join(outDir, 'vo-cache');
const pron = (cfg.pronunciation ?? []).map(([re, to, fl]) => [new RegExp(re, fl ?? 'g'), to]);
const spoken = (t) => pron.reduce((s, [re, to]) => s.replace(re, to), t);
function resolveTool(rel, extra = []) {
  for (const c of [rel, ...extra]) if (c && isAbsolute(c) && existsSync(c)) return c;
  for (const dir of [toolsDir && resolve(toolsDir), baseDir].filter(Boolean)) {
    for (const c of [rel, ...extra]) { const p = join(dir, c); if (existsSync(p)) return p; }
  }
  return undefined;
}
let piperExe, voiceModel;
if (voiceOn) {
  piperExe = resolveTool(voiceCfg.piper ?? 'piper/piper.exe', ['piper/piper']);
  voiceModel = resolveTool(voiceCfg.model, ['voices/' + voiceCfg.model]);
  if (!piperExe) throw new Error('Piper not found (config.voice.piper, or <tools>/piper/piper.exe). Use --no-voice for captions only.');
  if (!voiceModel) throw new Error(`Voice model not found: ${voiceCfg.model} (try <tools>/voices/...).`);
  mkdirSync(VO_DIR, { recursive: true });
}
function wavDuration(file) { // walk the RIFF chunks to the data chunk
  const b = readFileSync(file);
  const byteRate = b.readUInt32LE(28);
  let o = 12;
  while (o + 8 <= b.length) {
    const id = b.toString('ascii', o, o + 4), size = b.readUInt32LE(o + 4);
    if (id === 'data') return Math.min(size, b.length - o - 8) / byteRate;
    o += 8 + size;
  }
  return (b.length - 44) / byteRate;
}
const tts = (text) => {
  const file = join(VO_DIR, createHash('sha1').update(`${voiceModel}|${voiceCfg.lengthScale ?? 1}|${text}`).digest('hex').slice(0, 12) + '.wav');
  if (!existsSync(file)) {
    const r = spawnSync(piperExe, ['-m', voiceModel, '--length_scale', String(voiceCfg.lengthScale ?? 1.0),
      '--sentence_silence', String(voiceCfg.sentenceSilence ?? 0.25), '--output_file', file], { input: text, encoding: 'utf8' });
    if (!existsSync(file)) throw new Error('piper failed: ' + (r.stderr || r.error));
  }
  return { file, dur: wavDuration(file) };
};

// ── Browser, context, overlays ───────────────────────────────────────────────────────────────
const launchOpts = { headless: cfg.headless ?? true };
const exe = browserFlag ?? cfg.executablePath;
if (exe) launchOpts.executablePath = exe;
else if (cfg.channel) launchOpts.channel = cfg.channel;
const browser = await chromium.launch(launchOpts);
const ctx = await browser.newContext({ viewport: { width: W, height: H }, ...(preview ? {} : { recordVideo: { dir: outDir, size: { width: W, height: H } } }) });
if (preview) { // instant transitions and scrolls, so shots taken after shortened holds still show the final state
  await ctx.addInitScript(() => {
    const s = document.createElement('style'); s.textContent = '*{transition:none!important}';
    (document.head ?? document.documentElement).appendChild(s);
    for (const [o, n] of [[window, 'scrollTo'], [Element.prototype, 'scrollTo'], [Element.prototype, 'scrollIntoView']]) {
      const f = o[n]; o[n] = function (a, ...r) { return f.call(this, a && typeof a === 'object' ? { ...a, behavior: 'instant' } : a, ...r); };
    }
  });
}

// Overlays are installed on every page (they are recreated after each navigation).
await ctx.addInitScript(({ st, maxZoom, ripple }) => {
  // Spring-like easing as a CSS linear() list: slightly under-damped, so the camera settles with a tiny overshoot.
  const spring = (() => {
    const z = 0.7, w = 9, wd = w * Math.sqrt(1 - z * z), pts = [];
    for (let i = 0; i <= 30; i++) {
      const t = i / 30 * 1.1; // 1.1 s of motion is shown over the .9 s transition: the tail is cut when it is within 0.5 %
      pts.push((1 - Math.exp(-z * w * t) * (Math.cos(wd * t) + z * w / wd * Math.sin(wd * t))).toFixed(4));
    }
    pts[pts.length - 1] = '1';
    return `linear(${pts.join(',')})`;
  })();
  const css = `
  #__cap{position:fixed;left:0;right:0;bottom:0;height:24%;z-index:2147483600;pointer-events:none;display:flex;
    flex-direction:column;justify-content:flex-end;align-items:center;padding:0 5% 2.2%;opacity:0;transition:opacity .45s;box-sizing:border-box;
    background:linear-gradient(to top,rgba(${st.bandRgb},.92) 0%,rgba(${st.bandRgb},.75) 45%,rgba(${st.bandRgb},0) 100%);font-family:${st.font}}
  #__cap.on{opacity:1}
  #__cap .k{font-size:${st.labelPx}px;letter-spacing:.14em;text-transform:uppercase;color:${st.accent};font-weight:600;margin-bottom:.4em}
  #__cap .t{font-size:${st.captionPx}px;line-height:1.25;color:${st.text};font-weight:500;text-align:center;max-width:85%}
  #__cur{position:fixed;z-index:2147483602;width:22px;height:22px;margin:-3px 0 0 -3px;pointer-events:none;left:-50px;top:-50px;
    transform-origin:3px 3px;transition:transform .14s cubic-bezier(.3,1.6,.5,1)}
  #__cur.down{transform:scale(.78);transition-duration:.07s}
  .__rip{position:fixed;z-index:2147483601;pointer-events:none;width:64px;height:64px;margin:-32px 0 0 -32px;border-radius:50%;
    border:3px solid ${st.accent};background:color-mix(in srgb,${st.accent} 40%,transparent);box-shadow:0 0 0 1.5px rgba(0,0,0,.35),0 0 14px ${st.accent};opacity:0;animation:__rip .65s ease-out forwards}
  @keyframes __rip{0%{transform:scale(.15);opacity:.95}70%{opacity:.5}100%{transform:scale(1);opacity:0}}
  #__spot{position:fixed;z-index:2147483590;pointer-events:none;opacity:0;transition:opacity .45s;left:0;top:0;width:0;height:0;
    box-shadow:0 0 0 9999px rgba(${st.bandRgb},.72),0 0 0 3px ${st.accent}}
  #__spot.on{opacity:1}
  html{overflow-x:hidden} body{transition:transform .9s ${spring}}`;
  const mount = () => {
    if (document.getElementById('__cap')) return;
    const s = document.createElement('style'); s.textContent = css; document.documentElement.appendChild(s);
    const cap = document.createElement('div'); cap.id = '__cap'; cap.innerHTML = '<div class="k"></div><div class="t"></div>';
    const cur = document.createElement('div'); cur.id = '__cur';
    cur.innerHTML = '<svg width="22" height="22" viewBox="0 0 22 22"><path d="M3 2l14 8-6 1.6L8 18z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    document.documentElement.append(cap, cur);
    addEventListener('mousemove', (e) => { cur.style.left = e.clientX + 'px'; cur.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', (e) => {
      cur.classList.add('down');
      if (!ripple) return;
      const r = document.createElement('div'); r.className = '__rip'; r.style.left = e.clientX + 'px'; r.style.top = e.clientY + 'px';
      r.addEventListener('animationend', () => r.remove()); document.documentElement.appendChild(r);
    }, true);
    addEventListener('mouseup', () => cur.classList.remove('down'), true);
    // The camera never stays zoomed into the wrong place: any scroll or in-page navigation resets it.
    addEventListener('scroll', () => { if (zoomed && (Math.abs(scrollY - zoomed.y) > 3 || Math.abs(scrollX - zoomed.x) > 3)) window.__zoom(); }, { passive: true });
    for (const ev of ['popstate', 'hashchange']) addEventListener(ev, () => window.__zoom());
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
  window.__cap = (label, text) => {
    mount(); const c = document.getElementById('__cap');
    if (!text) { c.classList.remove('on'); return; }
    c.querySelector('.k').textContent = label || ''; c.querySelector('.t').textContent = text; c.classList.add('on');
  };
  // Camera: scale the body around the VIEWPORT centre (never the element centre: that clips sideways).
  // html{overflow-x:hidden} hides the overflow; putting it on body would break sticky headers.
  // Optional (ox, oy) are viewport coordinates to zoom around (used by click `focus`); default is the centre.
  let zoomed = null;
  window.__zoom = (s, ox, oy) => {
    const b = document.body;
    if (!s || s === 1) { zoomed = null; b.style.transform = ''; return; }
    zoomed = { x: scrollX, y: scrollY };
    b.style.transformOrigin = `${(ox ?? innerWidth / 2) + scrollX}px ${(oy ?? innerHeight / 2) + scrollY}px`;
    b.style.transform = `scale(${Math.min(s, maxZoom)})`;
  };
  // Spotlight: dim everything except one element. A rAF loop eases the hole toward the element's live
  // rectangle, so it also follows scrolling and moves smoothly from one element to the next.
  let spotEl = null, spotRaf = 0;
  window.__spot = (el, pad = 10, radius = 12) => {
    mount();
    let d = document.getElementById('__spot');
    if (!d) { d = document.createElement('div'); d.id = '__spot'; document.documentElement.appendChild(d); }
    if (!el) { d.classList.remove('on'); spotEl = null; return; }
    const first = !spotEl; spotEl = el;
    let cur = null, last = performance.now();
    const tick = (now) => {
      if (!spotEl) return;
      const r = spotEl.getBoundingClientRect(), dt = Math.min(0.1, (now - last) / 1000); last = now;
      const g = { x: r.left - pad, y: r.top - pad, w: r.width + 2 * pad, h: r.height + 2 * pad };
      const a = first && !cur ? 1 : 1 - Math.exp(-dt / 0.11);
      cur = cur ? { x: cur.x + (g.x - cur.x) * a, y: cur.y + (g.y - cur.y) * a, w: cur.w + (g.w - cur.w) * a, h: cur.h + (g.h - cur.h) * a } : g;
      d.style.cssText += `;left:${cur.x}px;top:${cur.y}px;width:${cur.w}px;height:${cur.h}px;border-radius:${radius}px`;
      spotRaf = requestAnimationFrame(tick);
    };
    cancelAnimationFrame(spotRaf); spotRaf = requestAnimationFrame(tick);
    d.classList.add('on');
  };
}, { st, maxZoom, ripple: (cfg.cursor?.ripple ?? true) });

const page = await ctx.newPage(); // the video starts here
page.setDefaultTimeout(8000); // a wrong selector fails in 8 s with a clear message, not 30 s
const t0 = Date.now();
const now = () => (Date.now() - t0) / 1000;
const pause = (ms) => page.waitForTimeout(preview ? ms / previewDiv : ms);
const shots = join(outDir, 'shots');
mkdirSync(shots, { recursive: true });
let shotN = 0;
const shot = async (n) => { shotN++; await page.screenshot({ path: join(shots, `${String(shotN).padStart(2, '0')}-${n}.png`) }); };
const timeline = [], vo = [];
let capOn = false, mx = W / 2, my = H / 3;

const speak = (text) => {
  if (!voiceOn || !text) return 0;
  const v = tts(spoken(text));
  vo.push({ at: now() + 0.35, file: v.file, dur: v.dur, text });
  return v.dur;
};
const card = (t, s) => 'data:text/html;charset=utf-8,' + encodeURIComponent(`<!doctype html><meta charset="utf-8"><body style="margin:0;height:100vh;
  display:flex;flex-direction:column;justify-content:center;align-items:center;background:${st.background};color:${st.text};font-family:${st.font}">
  <div style="font-size:${st.titlePx}px;font-weight:600;text-align:center;max-width:90%">${esc(t)}</div>
  <div style="font-size:${st.subtitlePx}px;color:${st.accent};margin-top:.6em;text-align:center;max-width:80%;line-height:1.35">${esc(s)}</div></body>`);
const esc = (s = '') => String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const loc = (sel) => page.locator(sel).first();
// Cursor path: a cubic Bezier with two off-axis control points, eased in and out, that overshoots the target
// a little and settles back (the idea of ghost-cursor, MIT, re-implemented). Seeded, so a re-record is identical.
// `config.cursor.path: "straight"` restores the old straight line.
const cursorCfg = { path: 'bezier', ...(cfg.cursor ?? {}) };
let seed = 20240607;
const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
const easeInOut = (t) => (t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2);
const easeOut = (t) => 1 - Math.pow(1 - t, 3);
// Calls fn(t) for t in 0..1 over `ms`, moving the real mouse each time (the overlay cursor follows mousemove).
async function sweep(ms, fn) {
  const s = Date.now();
  for (;;) {
    const t = Math.min(1, (Date.now() - s) / ms), [x, y] = fn(t);
    await page.mouse.move(x, y);
    if (t >= 1) return;
    await pause(6);
  }
}
const glide = async (x, y, steps = 18) => {
  const x0 = mx, y0 = my, d = Math.hypot(x - x0, y - y0);
  mx = x; my = y;
  if (cursorCfg.path === 'straight' || d < 6) { await page.mouse.move(x, y, { steps }); return; }
  const ux = (x - x0) / d, uy = (y - y0) / d, nx = -uy, ny = ux; // unit direction and its normal
  const side = rnd() < 0.5 ? -1 : 1, b1 = side * d * (0.08 + rnd() * 0.12), b2 = side * d * (0.03 + rnd() * 0.08);
  const over = d > 140 ? Math.min(14, d * 0.04) : 0; // overshoot distance in px
  const ex = x + ux * over, ey = y + uy * over;      // the Bezier ends past the target
  const p1 = [x0 + (ex - x0) * 0.3 + nx * b1, y0 + (ey - y0) * 0.3 + ny * b1];
  const p2 = [x0 + (ex - x0) * 0.75 + nx * b2, y0 + (ey - y0) * 0.75 + ny * b2];
  const bez = (t) => {
    const u = 1 - t, a = u * u * u, b = 3 * u * u * t, c = 3 * u * t * t, e = t * t * t;
    return [a * x0 + b * p1[0] + c * p2[0] + e * ex, a * y0 + b * p1[1] + c * p2[1] + e * ey];
  };
  await sweep(Math.min(1100, Math.max(420, 300 + d * 0.9)), (t) => bez(easeInOut(t)));
  if (over) await sweep(170, (t) => { const e = easeOut(t); return [ex + (x - ex) * e, ey + (y - ey) * e]; });
  await page.mouse.move(x, y);
};
const centreOf = async (sel) => {
  const l = loc(sel);
  await l.scrollIntoViewIfNeeded();
  const b = await l.boundingBox();
  if (!b) throw new Error(`no box for selector: ${sel}`);
  return b;
};
// After a navigation the fake cursor is recreated: move the mouse 1 px so it shows up again.
const wake = async () => { await page.mouse.move(mx + 1, my); mx += 1; };
const uncaption = async () => { if (!capOn) return; capOn = false; await page.evaluate(() => window.__cap()); await pause(400); };
// focus: true (or a scale) zooms gently toward the click point while the cursor presses, then back out.
const clickOn = async (sel, focus) => {
  const b = await centreOf(sel), cx = b.x + b.width / 2, cy = b.y + b.height / 2;
  await glide(cx, cy);
  if (focus) { await page.evaluate(([s, x, y]) => window.__zoom(s, x, y), [focus === true ? 1.06 : focus, cx, cy]); await pause(500); }
  else await pause(250);
  await page.mouse.down(); await pause(110); await page.mouse.up(); await pause(500);
  if (focus) { await page.evaluate(() => window.__zoom()); await pause(600); }
};

const actions = {
  async title(s) {
    await page.goto(card(s.title, s.subtitle));
    const dur = speak(s.say);
    await pause(Math.max(3500, dur * 1000 + 900));
    capOn = false;
  },
  async goto(s) {
    await uncaption();
    let url = s.url;
    if (!url) {
      if (!s.file) throw new Error('goto needs "url" or "file"');
      url = pathToFileURL(isAbsolute(s.file) ? s.file : join(baseDir, s.file)).href;
    }
    await page.goto(url); await page.waitForLoadState('load'); await pause(s.waitMs ?? 500); await wake();
  },
  // Voice first: the caption stays until the voice ends (or the reading time, if longer).
  async caption(s) {
    const say = s.say === false ? '' : (s.say ?? s.text);
    const dur = speak(say);
    timeline.push({ at: +now().toFixed(1), label: s.label ?? '', text: s.text, shot: s.shot ?? '' });
    await page.evaluate(([l, t]) => window.__cap(l, t), [s.label ?? '', s.text]);
    capOn = true;
    await pause(700); // fade-in
    if (s.shot) await shot(s.shot);
    await pause(Math.max(2800, s.text.length * 70, dur * 1000 + 700) - 700 + (s.extraMs ?? 0));
  },
  uncaption,
  async click(s) { await clickOn(s.selector, s.focus); },
  // Dim everything except the element. Stays until `unspotlight` (it follows scrolling).
  async spotlight(s) {
    const l = loc(s.selector);
    await l.scrollIntoViewIfNeeded();
    await l.evaluate((el, [pad, radius]) => window.__spot(el, pad, radius), [s.padding ?? 10, s.radius ?? 12]);
    await pause(s.ms ?? 900);
  },
  async unspotlight() { await page.evaluate(() => window.__spot()); await pause(600); },
  async hover(s) { const b = await centreOf(s.selector); await glide(b.x + b.width / 2, b.y + b.height / 2); await pause(s.ms ?? 500); },
  async type(s) {
    await clickOn(s.selector);
    if (s.clear) await loc(s.selector).fill('');
    await loc(s.selector).pressSequentially(s.text, { delay: s.delayMs ?? 45 });
    await pause(400);
  },
  async select(s) {
    const b = await centreOf(s.selector);
    await glide(b.x + b.width / 2, b.y + b.height / 2); await pause(300);
    await loc(s.selector).selectOption(s.value); // native dropdowns would render open in screenshots
    await pause(700);
  },
  async scroll(s) {
    if (!s.keepCaption) await uncaption(); // a stale caption over unrelated content looks wrong
    const top = s.offset ?? 80;
    await page.evaluate(([sel, top]) => {
      const el = sel.startsWith('text:')
        ? [...document.querySelectorAll('h1,h2,h3,h4,h5,h6,[role=heading]')].find((h) => h.textContent.includes(sel.slice(5)))
        : document.querySelector(sel);
      if (!el) throw new Error('scroll target not found: ' + sel);
      window.scrollTo({ top: el.getBoundingClientRect().top + scrollY - top, behavior: 'smooth' });
    }, [s.to, top]);
    await pause(s.ms ?? 1100);
  },
  async zoom(s) {
    if (s.selector) { // bring the target to the middle of the screen first, then zoom around the centre
      await page.evaluate((sel) => { document.querySelector(sel)?.scrollIntoView({ block: 'center', behavior: 'smooth' }); }, s.selector);
      await pause(900);
    }
    await page.evaluate((v) => window.__zoom(v), s.scale ?? 1.1); await pause(1000);
  },
  async unzoom() { await page.evaluate(() => window.__zoom()); await pause(1000); },
  async drag(s) {
    const b = await centreOf(s.selector);
    const y = b.y + b.height / 2, x = s.grip === 'right-edge' ? b.x + b.width - 3 : b.x + b.width / 2;
    await glide(x, y); await pause(500);
    await page.mouse.down(); await page.mouse.move(x + (s.dx ?? 0), y + (s.dy ?? 0), { steps: s.steps ?? 36 });
    await pause(250); await page.mouse.up(); mx = x + (s.dx ?? 0); my = y + (s.dy ?? 0); await pause(s.ms ?? 1200);
  },
  async hscroll(s) {
    await page.evaluate(([c, to, off]) => {
      const box = document.querySelector(c), el = document.querySelector(to);
      if (!box || !el) throw new Error('hscroll target not found');
      const left = box.scrollLeft + el.getBoundingClientRect().left - box.getBoundingClientRect().left - off;
      box.scrollTo({ left: Math.max(0, left), behavior: 'smooth' });
    }, [s.container, s.toSelector, s.offset ?? 0]);
    await pause(s.ms ?? 1200);
  },
  async wait(s) { await pause(s.ms ?? 1000); },
  async shot(s) { await shot(s.name ?? 'shot'); },
  // Escape hatch for site-specific needs: `js` is evaluated in the page as an expression.
  async evaluate(s) { await page.evaluate(s.js); await pause(s.ms ?? 500); },
};

// ── Run the storyboard ───────────────────────────────────────────────────────────────────────
// The video starts at page creation: open on a dark card so the first frames are never a half-loaded page.
await page.goto(card('', ''));
await pause(400);

// cue = script-clock time when the first REAL page (title card or site) has been committed. Everything
// before it is the dark opening card. Written to vo.json as `cue`; mix/export may trim up to lead + cue.
let cue = null, navs = 0;
page.on('framenavigated', (f) => { if (f === page.mainFrame() && ++navs === 1 && cue === null) cue = +(now() + 0.1).toFixed(2); });

const INTERACTIVE = new Set(['click', 'type', 'select', 'drag', 'hscroll', 'hover']);
const holdAfter = cfg.holdAfterActionMs ?? 400; // breathing room after every interactive action
const stepLog = [];

// `expect`: { visible | hidden: selector, text: [selector, substring], url: substring, timeoutMs? } or a list of them.
async function check(expect) {
  for (const e of Array.isArray(expect) ? expect : [expect]) {
    const limit = Date.now() + (e.timeoutMs ?? 3000);
    const poll = async (what, ok) => { // retries until the timeout, then throws with the last observation
      let seen;
      for (;;) {
        try { const r = await ok(); if (r.ok) return; seen = r.seen; } catch (err) { seen = err.message.split('\n')[0]; }
        if (Date.now() > limit) throw new Error(`expected ${what}; ${seen}`);
        await page.waitForTimeout(100);
      }
    };
    if (e.visible) await poll(`"${e.visible}" to be visible`, async () => { const v = await loc(e.visible).isVisible(); return { ok: v, seen: v ? '' : 'not visible' }; });
    if (e.hidden) await poll(`"${e.hidden}" to be hidden`, async () => { const v = await loc(e.hidden).isVisible(); return { ok: !v, seen: 'still visible' }; });
    if (e.text) await poll(`"${e.text[0]}" to contain "${e.text[1]}"`, async () => {
      const t = (await loc(e.text[0]).textContent({ timeout: 500 })) ?? ''; return { ok: t.includes(e.text[1]), seen: `found "${t.trim().slice(0, 80)}"` };
    });
    if (e.url) await poll(`the URL to contain "${e.url}"`, async () => ({ ok: page.url().includes(e.url), seen: `URL is ${page.url().slice(0, 120)}` }));
  }
}
async function fail(si, scene, i, step, err) {
  const file = join(shots, `FAIL-s${si + 1}-step${i + 1}-${step.action}.png`);
  await page.screenshot({ path: file }).catch(() => {});
  console.error(`\nSTEP FAILED in scene ${si + 1} "${scene.name ?? ''}", step ${i + 1} (${step.action}): ${err.message.split('\n')[0]}\n` +
    `  step: ${JSON.stringify(step)}\n  screenshot: ${file}`);
  await ctx.close().catch(() => {}); await browser.close().catch(() => {});
  process.exit(1);
}

for (const [si, scene] of (story.scenes ?? []).entries()) {
  console.log(`scene ${si + 1}: ${scene.name ?? ''}`);
  for (const [i, step] of (scene.steps ?? []).entries()) {
    const fn = actions[step.action];
    if (!fn) throw new Error(`unknown action "${step.action}" in scene ${scene.name ?? si + 1}`);
    const ts = now();
    try {
      await fn(step);
      if (INTERACTIVE.has(step.action)) { const h = step.holdMs ?? holdAfter; if (h > 0) await pause(h); }
      if (step.expect) await check(step.expect);
    } catch (err) { await fail(si, scene, i, step, err); }
    stepLog.push({ scene: si + 1, step: i + 1, action: step.action, start: +ts.toFixed(2), sec: +(now() - ts).toFixed(2) });
  }
}
await uncaption();
await pause(600);
const tEnd = now();
writeFileSync(join(outDir, preview ? 'preview-steps.json' : 'steps.json'), JSON.stringify({ totalSec: +tEnd.toFixed(2), steps: stepLog }, null, 1));

if (preview) {
  await ctx.close(); await browser.close();
  console.log(`preview done in ${tEnd.toFixed(1)} s (holds / ${previewDiv}), ${shotN} shots in ${shots}. No video, no voice.`);
  process.exit(0);
}
const video = page.video();
await ctx.close();
await browser.close();
const dest = join(outDir, `${name}.webm`);
renameSync(await video.path(), dest);
writeFileSync(join(outDir, 'timeline.json'), JSON.stringify(timeline, null, 1));
writeFileSync(join(outDir, 'vo.json'), JSON.stringify({ name, video: `${name}.webm`, tEnd, cue: cue ?? 0, lines: vo }, null, 1));
console.log(dest, `${tEnd.toFixed(0)} s logged`, `cue ${cue} s`, `${shotN} shots`, `${vo.length} voice lines`);
