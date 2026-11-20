// Generates a royalty-free, seamlessly loopable music bed (a soft Am7 chord with a slow tremolo) from
// pure sine sources with ffmpeg lavfi, so a demo can have background music with no assets to license.
// Every frequency and the tremolo complete a whole number of cycles in 8 s, so the loop has no click.
//
// usage: node make-music-bed.mjs <out.mp3|out.wav> [--ffmpeg <path>] [--tools <dir>]
import { spawnSync } from 'node:child_process';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';

const argv = process.argv.slice(2);
const flag = (n) => { const i = argv.indexOf(n); if (i < 0) return undefined; const [, v] = argv.splice(i, 2); return v; };
let ffmpeg = flag('--ffmpeg');
const tools = flag('--tools');
const [out] = argv;
if (!out) { console.error('usage: node make-music-bed.mjs <out.mp3|out.wav> [--ffmpeg p] [--tools dir]'); process.exit(2); }
for (const from of [tools && join(resolve(tools), 'x.js'), join(process.cwd(), 'x.js')].filter(Boolean)) {
  if (ffmpeg) break;
  try { ffmpeg = createRequire(from)('ffmpeg-static'); } catch { /* next */ }
}
ffmpeg ??= 'ffmpeg';

const hz = [110, 220, 262, 330, 392]; // A2 A3 C4 E4 G4 (Am7), integer cycles in 8 s
const sines = hz.map((f, i) => `${i ? 0.18 : 0.3}*sin(2*PI*${f}*t)`).join('+');
const expr = `(${sines})*(0.8+0.2*sin(2*PI*0.25*t))`;
const r = spawnSync(ffmpeg, ['-y', '-v', 'error', '-f', 'lavfi', '-i', `aevalsrc=${expr}:s=44100:d=8`,
  '-af', 'lowpass=f=1800,volume=0.5', '-ac', '2', resolve(out)], { encoding: 'utf8' });
if (r.status) { console.error(r.stderr || r.error); process.exit(1); }
console.log(resolve(out));
