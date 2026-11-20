// Verifies a recording by measuring, not trusting: frames every N seconds, one sync frame per voice
// line (taken after the caption has faded in) and a loudness report (ebur128).
//
// usage: node review.mjs <outDir> [--every 5] [--ffmpeg p] [--ffprobe p] [--tools dir]
// Reads vo.json, timeline.json and mix.json (written by record.mjs / mix.mjs).
// Writes <outDir>/review/frames/f%03d.png, <outDir>/review/sync/NN.png and <outDir>/review/report.md
import { spawnSync } from 'node:child_process';
import { readFileSync, writeFileSync, mkdirSync, existsSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { createRequire } from 'node:module';

const argv = process.argv.slice(2);
const flag = (n) => { const i = argv.indexOf(n); if (i < 0) return undefined; const [, v] = argv.splice(i, 2); return v; };
let ffmpeg = flag('--ffmpeg');
flag('--tools'); // accepted for symmetry with the other scripts; the ffmpeg path comes from mix.json
const every = Number(flag('--every') ?? 5);
flag('--ffprobe');
const [outArg] = argv;
if (!outArg) { console.error('usage: node review.mjs <outDir> [--every N] [--ffmpeg p] [--tools dir]'); process.exit(2); }
const outDir = resolve(outArg);
const mix = JSON.parse(readFileSync(join(outDir, 'mix.json'), 'utf8'));
const vo = JSON.parse(readFileSync(join(outDir, 'vo.json'), 'utf8'));
ffmpeg ??= mix.ffmpeg; // mix.mjs records the ffmpeg it used
const final = existsSync(mix.mp4) ? mix.mp4 : mix.webm;
const rev = join(outDir, 'review');
mkdirSync(join(rev, 'frames'), { recursive: true });
mkdirSync(join(rev, 'sync'), { recursive: true });
const ff = (args) => spawnSync(ffmpeg, ['-y', '-v', 'error', ...args], { encoding: 'utf8' });

// 1. Overview frames every N seconds.
const r1 = ff(['-i', final, '-vf', `fps=1/${every}`, join(rev, 'frames', 'f%03d.png')]);
if (r1.status) throw new Error(r1.stderr);

// 2. Sync frames: video time = line start + head start + 0.9 s (caption fully visible).
const rows = [];
for (const [i, l] of vo.lines.entries()) {
  const t = l.at + mix.lead + 0.9;
  const file = join(rev, 'sync', `${String(i + 1).padStart(2, '0')}.png`);
  ff(['-ss', t.toFixed(2), '-i', final, '-frames:v', '1', file]);
  rows.push({ n: i + 1, t, file, text: l.text });
}

// 3. Loudness: integrated about -16 LUFS, true peak below -1 dBFS.
let loud = 'no audio track (captions only)';
let verdict = '';
if (mix.hasVoice) {
  const r = spawnSync(ffmpeg, ['-v', 'info', '-nostats', '-i', final, '-af', 'ebur128=peak=true', '-f', 'null', '-'], { encoding: 'utf8' });
  const s = r.stderr.slice(r.stderr.lastIndexOf('Summary:'));
  const I = Number(/I:\s+(-?[\d.]+) LUFS/.exec(s)?.[1]);
  const P = Number(/Peak:\s+(-?[\d.]+) dBFS/.exec(s)?.[1]);
  loud = `integrated ${I} LUFS, true peak ${P} dBFS`;
  verdict = Math.abs(I + 16) <= 1.5 && P < -1 ? 'OK' : 'CHECK (target -16 LUFS, peak < -1 dBFS)';
}

const md = [
  `# Review of ${final}`, '',
  `- Duration: ${mix.duration.toFixed(1)} s, head start ${mix.lead.toFixed(2)} s`,
  `- Loudness: ${loud} ${verdict}`,
  `- Overview frames: ${join(rev, 'frames')} (one every ${every} s)`, '',
  '## Sync frames', '',
  'Open each image: the caption on screen must match the voice line below.', '',
  ...rows.map((x) => `${x.n}. t=${x.t.toFixed(1)} s ${x.file}\n   voice: "${x.text}"`), '',
  'Not verifiable here: how the voice sounds (pronunciation, pacing). A human has to listen.', '',
].join('\n');
writeFileSync(join(rev, 'report.md'), md);
console.log(md);
