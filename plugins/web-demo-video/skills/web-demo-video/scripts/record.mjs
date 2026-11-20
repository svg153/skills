// Records a product-demo video of a web page that already exists, driving a real browser with
// Playwright from a JSON storyboard. Nothing is rebuilt: the video is the real page plus overlays
// (caption band, fake cursor, camera zoom) and optional offline voice-over (Piper).
//
// usage: node record.mjs <storyboard.json> <outDir> [--tools <dir>] [--no-voice] [--browser <chrome.exe>]
//
// <tools dir> (optional) may hold: node_modules/playwright-core, piper/piper(.exe), voices/<model>.onnx.
// Writes to <outDir>: <name>.webm, vo.json (voice lines + timing), timeline.json, shots/*.png, vo-cache/*.wav.
import { pathToFileURL } from 'node:url';
import { createRequire } from 'node:module';
import { join, dirname, resolve, isAbsolute } from 'node:path';
import { renameSync, mkdirSync, writeFileSync, existsSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';

const argv = process.argv.slice(2);
const flag = (n) => { const i = argv.indexOf(n); if (i < 0) return undefined; const [, v] = argv.splice(i, 2); return v; };
const toolsDir = flag('--tools');
const browserFlag = flag('--browser') ?? process.env.WEB_DEMO_VIDEO_BROWSER;
const noVoiceFlag = argv.includes('--no-voice');
const [storyPath, outArg] = argv.filter((a) => !a.startsWith('--'));
if (!storyPath || !outArg) {
  console.error('usage: node record.mjs <storyboard.json> <outDir> [--tools <dir>] [--no-voice] [--browser <chrome.exe>]');
  process.exit(2);
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
const ctx = await browser.newContext({ viewport: { width: W, height: H }, recordVideo: { dir: outDir, size: { width: W, height: H } } });

// Overlays are installed on every page (they are recreated after each navigation).
await ctx.addInitScript(({ st, maxZoom }) => {
  const css = `
  #__cap{position:fixed;left:0;right:0;bottom:0;height:24%;z-index:2147483600;pointer-events:none;display:flex;
    flex-direction:column;justify-content:flex-end;align-items:center;padding:0 5% 2.2%;opacity:0;transition:opacity .45s;box-sizing:border-box;
    background:linear-gradient(to top,rgba(${st.bandRgb},.92) 0%,rgba(${st.bandRgb},.75) 45%,rgba(${st.bandRgb},0) 100%);font-family:${st.font}}
  #__cap.on{opacity:1}
  #__cap .k{font-size:${st.labelPx}px;letter-spacing:.14em;text-transform:uppercase;color:${st.accent};font-weight:600;margin-bottom:.4em}
  #__cap .t{font-size:${st.captionPx}px;line-height:1.25;color:${st.text};font-weight:500;text-align:center;max-width:85%}
  #__cur{position:fixed;z-index:2147483602;width:22px;height:22px;margin:-3px 0 0 -3px;pointer-events:none;left:-50px;top:-50px;transition:transform .12s}
  #__cur.down{transform:scale(.8)}
  html{overflow-x:hidden} body{transition:transform .9s cubic-bezier(.4,0,.2,1)}`;
  const mount = () => {
    if (document.getElementById('__cap')) return;
    const s = document.createElement('style'); s.textContent = css; document.documentElement.appendChild(s);
    const cap = document.createElement('div'); cap.id = '__cap'; cap.innerHTML = '<div class="k"></div><div class="t"></div>';
    const cur = document.createElement('div'); cur.id = '__cur';
    cur.innerHTML = '<svg width="22" height="22" viewBox="0 0 22 22"><path d="M3 2l14 8-6 1.6L8 18z" fill="#fff" stroke="#111" stroke-width="1.6" stroke-linejoin="round"/></svg>';
    document.documentElement.append(cap, cur);
    addEventListener('mousemove', (e) => { cur.style.left = e.clientX + 'px'; cur.style.top = e.clientY + 'px'; }, true);
    addEventListener('mousedown', () => cur.classList.add('down'), true);
    addEventListener('mouseup', () => cur.classList.remove('down'), true);
  };
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', mount); else mount();
  window.__cap = (label, text) => {
    mount(); const c = document.getElementById('__cap');
    if (!text) { c.classList.remove('on'); return; }
    c.querySelector('.k').textContent = label || ''; c.querySelector('.t').textContent = text; c.classList.add('on');
  };
  // Camera: scale the body around the VIEWPORT centre (never the element centre: that clips sideways).
  // html{overflow-x:hidden} hides the overflow; putting it on body would break sticky headers.
  window.__zoom = (s) => {
    const b = document.body;
    if (!s || s === 1) { b.style.transform = ''; return; }
    b.style.transformOrigin = `${innerWidth / 2 + scrollX}px ${innerHeight / 2 + scrollY}px`;
    b.style.transform = `scale(${Math.min(s, maxZoom)})`;
  };
}, { st, maxZoom });

const page = await ctx.newPage(); // the video starts here
const t0 = Date.now();
const now = () => (Date.now() - t0) / 1000;
const pause = (ms) => page.waitForTimeout(ms);
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
const glide = async (x, y, steps = 18) => { mx = x; my = y; await page.mouse.move(x, y, { steps }); };
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
const clickOn = async (sel) => {
  const b = await centreOf(sel);
  await glide(b.x + b.width / 2, b.y + b.height / 2); await pause(250);
  await page.mouse.down(); await pause(90); await page.mouse.up(); await pause(500);
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
  async click(s) { await clickOn(s.selector); },
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
for (const [si, scene] of (story.scenes ?? []).entries()) {
  console.log(`scene ${si + 1}: ${scene.name ?? ''}`);
  for (const step of scene.steps ?? []) {
    const fn = actions[step.action];
    if (!fn) throw new Error(`unknown action "${step.action}" in scene ${scene.name ?? si + 1}`);
    await fn(step);
  }
}
await uncaption();
await pause(600);
const tEnd = now();

const video = page.video();
await ctx.close();
await browser.close();
const dest = join(outDir, `${name}.webm`);
renameSync(await video.path(), dest);
writeFileSync(join(outDir, 'timeline.json'), JSON.stringify(timeline, null, 1));
writeFileSync(join(outDir, 'vo.json'), JSON.stringify({ name, video: `${name}.webm`, tEnd, lines: vo }, null, 1));
console.log(dest, `${tEnd.toFixed(0)} s logged`, `${shotN} shots`, `${vo.length} voice lines`);
