// Verifies a recording by measuring, not trusting: frames every N seconds, one sync frame per voice
// line (taken after the caption has faded in), a loudness report (ebur128) and automatic detectors
// (blackdetect, freezedetect, silencedetect) summarised as PASS/WARN in report.md.
//
// usage: node review.mjs <outDir> [--every 5] [--ffmpeg p] [--ffprobe p] [--tools dir]
//        [--black-min 0.3] [--freeze-max 6] [--silence-min 0.8]
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

// 4. Automatic detectors (full ffmpeg): black frames, frozen stretches, silence inside voice lines.
// Times below are VIDEO times of the final file. Script-clock times (steps.json, vo.json) + lead = video time.
const detect = (args) => spawnSync(ffmpeg, ['-v', 'info', '-nostats', '-i', final, ...args, '-f', 'null', '-'], { encoding: 'utf8' }).stderr ?? '';
const spans = (txt, startRe, endRe, durRe) => { // pair start/end lines into [start, end]
  const out = []; let s = null;
  for (const line of txt.split('\n')) {
    const a = startRe.exec(line), b = endRe.exec(line);
    if (a) s = Number(a[1]);
    if (b && s !== null) { out.push([s, Number(b[1])]); s = null; }
  }
  if (s !== null) out.push([s, mix.duration]); // still running at the end of the file
  return out;
};
const lead = mix.lead ?? 0, cue = vo.cue ?? 0;
const stepsFile = join(outDir, 'steps.json');
const steps = existsSync(stepsFile) ? JSON.parse(readFileSync(stepsFile, 'utf8')).steps : [];
const window = (t0, t1) => [t0 + lead, t1 + lead];
const titleWins = steps.filter((s) => s.action === 'title').map((s) => window(s.start, s.start + s.sec));
const capTimes = (existsSync(join(outDir, 'timeline.json')) ? JSON.parse(readFileSync(join(outDir, 'timeline.json'), 'utf8')) : []).map((c) => c.at + lead);
const overlaps = ([a, b], [c, d]) => a < d && c < b;
const checks = [];
const check = (name, ok, detail) => checks.push({ name, status: ok ? 'PASS' : 'WARN', detail });

const blackMin = Number(flag('--black-min') ?? 0.3), freezeMax = Number(flag('--freeze-max') ?? 6), silenceMin = Number(flag('--silence-min') ?? 0.8);
// Title cards are dark by design and the opening card ends at lead + cue: neither counts as a defect.
const black = spans(detect(['-an', '-vf', `blackdetect=d=${blackMin}:pix_th=0.02`]), /black_start:([\d.]+)/, /black_end:([\d.]+)/)
  .filter((sp) => sp[0] >= lead + cue - 0.05 && !titleWins.some((w) => overlaps(sp, w)));
check('Black frames', !black.length, black.length ? black.map(([a, b]) => `${a.toFixed(1)}-${b.toFixed(1)} s`).join(', ') + ` (>= ${blackMin} s, outside title cards)` : 'none outside title cards');
// A long still with no caption starting inside it is dead air; a still page under a fresh caption is fine.
const frozen = spans(detect(['-an', '-vf', `freezedetect=n=-55dB:d=${freezeMax}`]), /freeze_start: ([\d.]+)/, /freeze_end: ([\d.]+)/)
  .filter((sp) => !titleWins.some((w) => overlaps(sp, w)) && !capTimes.some((t) => t >= sp[0] - 0.5 && t <= sp[1]));
check(`Frozen video >= ${freezeMax} s without a new caption`, !frozen.length, frozen.length ? frozen.map(([a, b]) => `${a.toFixed(1)}-${b.toFixed(1)} s`).join(', ') : 'none');
if (mix.hasVoice) {
  const sil = spans(detect(['-vn', '-af', `silencedetect=n=-35dB:d=${silenceMin}`]), /silence_start: ([\d.]+)/, /silence_end: ([\d.]+)/);
  const inside = sil.map(([a, b]) => ({ a, b, line: vo.lines.findIndex((l) => a > l.at + lead + 0.15 && b < l.at + lead + l.dur - 0.05) }))
    .filter((x) => x.line >= 0);
  check(`Silence >= ${silenceMin} s inside a voice line`, !inside.length,
    inside.length ? inside.map((x) => `line ${x.line + 1} at ${x.a.toFixed(1)}-${x.b.toFixed(1)} s`).join(', ') : 'none (gaps between lines are allowed)');
  const dead = sil.filter(([a, b]) => b - a >= 8 && !titleWins.some((w) => overlaps([a, b], w)));
  check('Dead air >= 8 s between lines', !dead.length, dead.length ? dead.map(([a, b]) => `${a.toFixed(1)}-${b.toFixed(1)} s`).join(', ') : 'none');
}

const md = [
  `# Review of ${final}`, '',
  `- Duration: ${mix.duration.toFixed(1)} s, head start ${mix.lead.toFixed(2)} s, cue ${cue.toFixed(2)} s (first real frame at ${(lead + cue).toFixed(2)} s in the video)`,
  `- Loudness: ${loud} ${verdict}`,
  `- Automatic checks: ${checks.every((c) => c.status === 'PASS') ? 'PASS' : 'WARN'}`,
  ...checks.map((c) => `  - ${c.status}: ${c.name}: ${c.detail}`),
  `- Overview frames: ${join(rev, 'frames')} (one every ${every} s)`, '',
  '## Sync frames', '',
  'Open each image: the caption on screen must match the voice line below.', '',
  ...rows.map((x) => `${x.n}. t=${x.t.toFixed(1)} s ${x.file}\n   voice: "${x.text}"`), '',
  'Not verifiable here: how the voice sounds (pronunciation, pacing). A human has to listen.', '',
].join('\n');
writeFileSync(join(rev, 'report.md'), md);
console.log(md);
