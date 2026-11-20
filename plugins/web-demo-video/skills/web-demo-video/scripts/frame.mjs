// Post-process: places a finished demo video inside a browser-window mockup (title bar with three dots,
// an address bar with a label) on a gradient or solid background, with padding, rounded corners and a
// soft shadow. The audio is kept. The static frame is rendered once as a PNG with Playwright (CSS gives
// the shadow and the rounded corners for free); ffmpeg then overlays the video through a rounded mask.
//
// Idea credit: the framed "browser window on a gradient" look comes from hookforge and truedemo (both MIT).
// No code was copied; see docs/related-work.md.
//
// usage: node frame.mjs <input.mp4|webm> <output.mp4> [--label "demo.example.com"] [--bg "#1b2a6b,#6a2cff"]
//          [--size 1920x1080] [--padding 72] [--radius 14] [--title "Window title"] [--no-chrome]
//          [--tools dir] [--browser exe] [--ffmpeg p] [--ffprobe p] [--crf 20]
// --bg: one colour for a solid background, two or more comma-separated colours for a diagonal gradient.
import { spawnSync } from 'node:child_process';
import { writeFileSync, mkdtempSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { tmpdir } from 'node:os';
import { createRequire } from 'node:module';

const argv = process.argv.slice(2);
const flag = (n) => { const i = argv.indexOf(n); if (i < 0) return undefined; const [, v] = argv.splice(i, 2); return v; };
const bool = (n) => { const i = argv.indexOf(n); if (i < 0) return false; argv.splice(i, 1); return true; };
const tools = flag('--tools'), browserExe = flag('--browser') ?? process.env.WEB_DEMO_VIDEO_BROWSER;
let ffmpeg = flag('--ffmpeg'), ffprobe = flag('--ffprobe');
const label = flag('--label') ?? 'demo.example.com';
const bg = (flag('--bg') ?? '#16225c,#5b2bd6,#d6479c').split(',').map((s) => s.trim());
const [CW, CH] = (flag('--size') ?? '1920x1080').split('x').map(Number);
const pad = Number(flag('--padding') ?? Math.round(CH * 0.07));
const radius = Number(flag('--radius') ?? 14);
const title = flag('--title') ?? '';
const noChrome = bool('--no-chrome');
const crf = flag('--crf') ?? '20';
const [inArg, outArg] = argv;
if (!inArg || !outArg) { console.error('usage: node frame.mjs <input> <output.mp4> [--label text] [--bg c1,c2] [--size WxH] [--padding px] [--radius px] [--title t] [--no-chrome] [--tools dir] [--browser exe]'); process.exit(2); }
const input = resolve(inArg), output = resolve(outArg);

const fromNpm = (pkg, pick) => {
  for (const from of [tools && join(resolve(tools), 'x.js'), join(process.cwd(), 'x.js')].filter(Boolean)) {
    try { return pick(createRequire(from)(pkg)); } catch { /* next */ }
  }
};
ffmpeg ??= fromNpm('ffmpeg-static', (m) => m) ?? 'ffmpeg';
ffprobe ??= fromNpm('ffprobe-static', (m) => m.path) ?? 'ffprobe';
async function loadPlaywright() {
  try { return await import('playwright-core'); } catch { /* next */ }
  for (const from of [tools && join(resolve(tools), 'x.js'), join(process.cwd(), 'x.js')].filter(Boolean)) {
    try { return createRequire(from)('playwright-core'); } catch { /* next */ }
  }
  throw new Error('playwright-core not found (npm i playwright-core, or --tools <dir>).');
}
const { chromium } = await loadPlaywright();

// Source size, to keep its aspect ratio.
const probe = spawnSync(ffprobe, ['-v', 'error', '-select_streams', 'v:0', '-show_entries', 'stream=width,height', '-of', 'csv=p=0', input], { encoding: 'utf8' });
const [vw, vh] = probe.stdout.trim().split(',').map(Number);
if (!(vw > 0 && vh > 0)) throw new Error('could not read the video size; check --ffprobe');

// Layout (all even numbers, as yuv420p needs). The window holds a title bar and the video.
const barH = noChrome ? 0 : Math.round(CH * 0.043);
const availW = CW - 2 * pad, availH = CH - 2 * pad - barH;
let dw = availW, dh = Math.round(dw * vh / vw);
if (dh > availH) { dh = availH; dw = Math.round(dh * vw / vh); }
dw -= dw % 2; dh -= dh % 2;
const winW = dw, winH = dh + barH;
const winX = Math.round((CW - winW) / 2), winY = Math.round((CH - winH) / 2);
const vx = winX, vy = winY + barH;

const background = bg.length === 1 ? bg[0] : `linear-gradient(135deg, ${bg.join(', ')})`;
const bar = noChrome ? '' : `
  <div class="bar"><div class="dots"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i></div>
    <div class="addr"><svg width="${barH * 0.3}" height="${barH * 0.3}" viewBox="0 0 16 16"><path d="M8 1a4 4 0 0 0-4 4v2H3v8h10V7h-1V5a4 4 0 0 0-4-4zm-2.5 4a2.5 2.5 0 0 1 5 0v2h-5z" fill="#8a8f98"/></svg><span>${label.replace(/</g, '&lt;')}</span></div>
    <div class="ttl">${title.replace(/</g, '&lt;')}</div></div>`;
const s = barH / 44; // scale of the title bar details
const page = (inner, body) => `<!doctype html><meta charset="utf-8"><style>
  html,body{margin:0;width:${CW}px;height:${CH}px;overflow:hidden;font-family:"Segoe UI",system-ui,Helvetica,Arial,sans-serif;${body}}
  .win{position:absolute;left:${winX}px;top:${winY}px;width:${winW}px;height:${winH}px;border-radius:${radius}px;overflow:hidden;
    background:#0b0d12;box-shadow:0 ${Math.round(CH * 0.03)}px ${Math.round(CH * 0.08)}px rgba(0,0,0,.45),0 ${Math.round(CH * 0.006)}px ${Math.round(CH * 0.015)}px rgba(0,0,0,.35)}
  .bar{height:${barH}px;background:#2b2e36;display:flex;align-items:center;position:relative}
  .dots{display:flex;gap:${12 * s}px;padding-left:${18 * s}px}.dots i{width:${13 * s}px;height:${13 * s}px;border-radius:50%;display:block}
  .addr{position:absolute;left:50%;transform:translateX(-50%);width:44%;height:${28 * s}px;border-radius:${14 * s}px;background:#1b1d23;color:#c9cdd4;
    display:flex;align-items:center;gap:${8 * s}px;padding:0 ${14 * s}px;font-size:${14 * s}px;box-sizing:border-box;overflow:hidden;white-space:nowrap}
  .ttl{position:absolute;right:${18 * s}px;color:#8a8f98;font-size:${13 * s}px}
  ${inner}</style>`;

const tmp = mkdtempSync(join(tmpdir(), 'wdv-frame-'));
const bgPng = join(tmp, 'bg.png'), maskPng = join(tmp, 'mask.png');
const launchOpts = { headless: true };
if (browserExe) launchOpts.executablePath = browserExe;
const browser = await chromium.launch(launchOpts);
const pg = await browser.newPage({ viewport: { width: CW, height: CH }, deviceScaleFactor: 1 });
// 1) Background + shadow + window with its title bar. The video area stays dark; the video is laid over it.
await pg.setContent(page('', `background:${background}`) + `<div class="win">${bar}</div>`);
await pg.screenshot({ path: bgPng });
// 2) Mask: white where the video shows (the lower part of the window, bottom corners rounded).
await pg.setContent(`<!doctype html><meta charset="utf-8"><style>html,body{margin:0;background:#000;width:${CW}px;height:${CH}px}
  div{position:absolute;left:${vx}px;top:${vy}px;width:${dw}px;height:${dh}px;background:#fff;
  border-radius:${noChrome ? radius : 0}px ${noChrome ? radius : 0}px ${radius}px ${radius}px}</style><div></div>`);
await pg.screenshot({ path: maskPng });
await browser.close();

const dur = spawnSync(ffprobe, ['-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', input], { encoding: 'utf8' }).stdout.trim();
const filter = `[0:v]scale=${dw}:${dh}:flags=lanczos,format=yuva420p[v];[2:v]crop=${dw}:${dh}:${vx}:${vy},format=gray[m];[v][m]alphamerge[vm];[1:v][vm]overlay=${vx}:${vy}:shortest=1,format=yuv420p[out]`;
const args = ['-y', '-v', 'error', '-i', input, '-loop', '1', '-i', bgPng, '-loop', '1', '-i', maskPng,
  '-filter_complex', filter, '-map', '[out]', '-map', '0:a?', '-r', '25',
  '-c:v', 'libx264', '-preset', 'medium', '-crf', crf, '-c:a', 'aac', '-b:a', '160k', '-t', dur, '-movflags', '+faststart', output];
const r = spawnSync(ffmpeg, args, { encoding: 'utf8' });
rmSync(tmp, { recursive: true, force: true });
if (r.status) throw new Error(r.stderr || String(r.error));
console.log(`${output}  (${CW}x${CH}, video ${dw}x${dh} at ${vx},${vy}, source ${vw}x${vh})`);
